"""
font loader utility
loads and manages fonts for video generation.
"""

import os
import platform
from pathlib import Path
from typing import Optional, Dict, List
from PIL import ImageFont
from utils.logger import get_logger
from utils.config_loader import Config

logger = get_logger(__name__)


class FontLoader:
    """utility class for loading and managing fonts."""
    
    def __init__(self, config: Config):
        """
        initialize font loader.
        
        args:
            config: configuration object
        """
        self.config = config
        self.fonts_dir = self._get_fonts_directory()
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
        
    def _get_fonts_directory(self) -> Path:
        """get fonts directory path."""
        fonts_dir = self.config.get('fonts.fonts_directory', 'fonts')
        
        # if relative path, make it relative to project root
        if not os.path.isabs(fonts_dir):
            project_root = Path(__file__).parent.parent
            fonts_dir = project_root / fonts_dir
        else:
            fonts_dir = Path(fonts_dir)
        
        return fonts_dir
    
    def _get_system_font_directories(self) -> List[Path]:
        """
        get system font directories based on the operating system.
        
        returns:
            list of system font directory paths
        """
        system = platform.system()
        font_dirs = []
        
        if system == "Darwin":  # macOS
            font_dirs = [
                Path("/System/Library/Fonts"),
                Path("/Library/Fonts"),
                Path.home() / "Library/Fonts",
            ]
        elif system == "Windows":
            font_dirs = [
                Path("C:/Windows/Fonts"),
                Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts",
            ]
        else:  # Linux and others
            font_dirs = [
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
                Path.home() / ".fonts",
                Path.home() / ".local/share/fonts",
            ]
        
        # filter to only existing directories
        return [d for d in font_dirs if d.exists() and d.is_dir()]
    
    def _find_system_font(self, font_name: str) -> Optional[Path]:
        """
        find a font by name in system font directories.
        searches for fonts matching the name (case-insensitive).
        
        args:
            font_name: font name or filename (e.g., "Roboto", "Roboto-Bold.ttf")
        
        returns:
            path to font file if found, None otherwise
        """
        if not font_name:
            return None
        
        # normalize font name - remove extension and spaces, convert to lowercase
        font_base = Path(font_name).stem.lower().replace(' ', '').replace('-', '').replace('_', '')
        
        system_dirs = self._get_system_font_directories()
        font_extensions = {'.ttf', '.otf', '.ttc', '.woff', '.woff2'}
        
        for font_dir in system_dirs:
            try:
                # search recursively in system font directories
                for font_file in font_dir.rglob('*'):
                    if font_file.suffix.lower() in font_extensions:
                        # check if font name matches
                        file_base = font_file.stem.lower().replace(' ', '').replace('-', '').replace('_', '')
                        if font_base in file_base or file_base in font_base:
                            logger.debug(f"found system font: {font_file}")
                            return font_file
            except (PermissionError, OSError) as e:
                logger.debug(f"could not search {font_dir}: {e}")
                continue
        
        return None
    
    def _resolve_font_path(self, font_path: Optional[str]) -> Optional[Path]:
        """
        resolve font path to absolute path.
        first checks system fonts by name, then checks fonts folder.
        supports absolute paths, relative paths from fonts directory, 
        relative paths from project root, or system font paths.
        
        args:
            font_path: font path from config (can be font name, relative or absolute path)
        
        returns:
            resolved path or None if not found
        """
        if not font_path:
            return None
        
        # first, try to find in system fonts by name
        system_font = self._find_system_font(font_path)
        if system_font:
            logger.info(f"found font in system fonts: {system_font}")
            return system_font
        
        # if absolute path, use as-is
        if os.path.isabs(font_path):
            path = Path(font_path)
            if path.exists():
                return path
            logger.warning(f"font path not found: {font_path}")
            return None
        
        # try relative to fonts directory (downloaded fonts)
        path = self.fonts_dir / font_path
        if path.exists():
            logger.info(f"found font in fonts directory: {path}")
            return path
        
        # try relative to project root
        project_root = Path(__file__).parent.parent
        path = project_root / font_path
        if path.exists():
            return path
        
        # try as-is (might be a system font path or relative to current directory)
        path = Path(font_path)
        if path.exists():
            return path
        
        # try relative to current working directory
        path = Path.cwd() / font_path
        if path.exists():
            return path
        
        logger.warning(f"font path not found: {font_path} (checked system fonts and: {self.fonts_dir / font_path}, {project_root / font_path}, {Path(font_path)}, {path})")
        return None
    
    def load_font(self, font_path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
        """
        load a font file from the provided path.
        if path is provided, it will be loaded from that location.
        if path is None or not found, falls back to system default font.
        
        args:
            font_path: path to font file (from config, can be absolute or relative)
            size: font size
        
        returns:
            PIL ImageFont object
        """
        # check cache first
        cache_key = f"{font_path}:{size}"
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        # try to load specified font if path is provided
        if font_path:
            resolved_path = self._resolve_font_path(font_path)
            if resolved_path:
                try:
                    font = ImageFont.truetype(str(resolved_path), size)
                    self.font_cache[cache_key] = font
                    logger.info(f"loaded font: {resolved_path} (size: {size})")
                    return font
                except Exception as e:
                    logger.warning(f"failed to load font {resolved_path}: {e}")
                    logger.warning(f"falling back to system default font")
            else:
                logger.warning(f"font path not found: {font_path}, falling back to system default")
        
        # fallback to system default font only if no path provided or path not found
        font = self._load_system_font(size)
        self.font_cache[cache_key] = font
        return font
    
    def _load_system_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        load system default font with fallbacks.
        
        args:
            size: font size
        
        returns:
            PIL ImageFont object
        """
        # try common system fonts
        system_fonts = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/System/Library/Fonts/Supplemental/Helvetica.ttc",  # macOS alternative
            "C:/Windows/Fonts/arial.ttf",  # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux alternative
        ]
        
        for font_path in system_fonts:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue
        
        # final fallback to default font
        logger.warning(f"using default font (size: {size})")
        return ImageFont.load_default()
    
    def get_font(self, font_name: Optional[str], size: int) -> ImageFont.FreeTypeFont:
        """
        get a font by its name/path or use default if not available.
        logs an error if the requested font is not available and falls back to default font.
        args:
            font_name: font name or filename or relative/absolute path
            size: font size
        returns:
            PIL ImageFont object
        """
        if font_name:
            font = self._try_load_font(font_name, size)
            if font:
                return font
            logger.error(f"Font '{font_name}' not available. Falling back to default font.")
        # use default font from config, or fallback to system
        return self.get_default_font(size)
    
    def get_default_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        get default font.
        uses default_font from config if available, otherwise system default.
        args:
            size: font size
        returns:
            PIL ImageFont object
        """
        font_path = self.config.get('fonts.default_font')
        return self.load_font(font_path, size)
    
    def _try_load_font(self, font_path: Optional[str], size: int) -> Optional[ImageFont.FreeTypeFont]:
        """
        try to load a font, returning None if it fails.
        does not fall back to system font.
        
        args:
            font_path: path to font file
            size: font size
        
        returns:
            PIL ImageFont object or None if not found/failed
        """
        if not font_path:
            return None
        
        resolved_path = self._resolve_font_path(font_path)
        if not resolved_path:
            return None
        
        try:
            cache_key = f"{font_path}:{size}"
            if cache_key in self.font_cache:
                return self.font_cache[cache_key]
            
            font = ImageFont.truetype(str(resolved_path), size)
            self.font_cache[cache_key] = font
            logger.debug(f"loaded font: {resolved_path} (size: {size})")
            return font
        except Exception as e:
            logger.debug(f"failed to load font {resolved_path}: {e}")
            return None

    def list_available_fonts(self) -> List[str]:
        """
        list all available font files in fonts directory.
        
        returns:
            list of font file paths
        """
        if not self.fonts_dir.exists():
            return []
        
        font_extensions = {'.ttf', '.otf', '.ttc'}
        fonts = []
        
        for font_file in self.fonts_dir.iterdir():
            if font_file.suffix.lower() in font_extensions:
                fonts.append(str(font_file.relative_to(self.fonts_dir)))
        
        return sorted(fonts)

