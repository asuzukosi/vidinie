# Fonts Directory

This directory contains font files that can be used in video generation.

## Supported Font Formats
- `.ttf` (TrueType Font) - **Recommended**
- `.otf` (OpenType Font)
- `.ttc` (TrueType Collection)

## How to Use Downloaded Fonts

### Step 1: Download Fonts

Download fonts from these free sources:
- **Google Fonts**: https://fonts.google.com (most popular, free)
- **Font Squirrel**: https://www.fontsquirrel.com (free fonts)
- **Adobe Fonts**: https://fonts.adobe.com (requires subscription)
- **DaFont**: https://www.dafont.com (free fonts)

**Recommended fonts for video:**
- **Roboto** (Google Fonts) - Clean, modern, highly readable
- **Open Sans** (Google Fonts) - Professional, versatile
- **Montserrat** (Google Fonts) - Bold, attention-grabbing
- **Lato** (Google Fonts) - Friendly, readable
- **Poppins** (Google Fonts) - Modern, geometric

### Step 2: Add Fonts to This Directory

1. Download the font files (usually `.ttf` or `.otf` format)
2. Extract the ZIP file if needed
3. Copy the font files directly into this `fonts/` directory

**Example:**
```
fonts/
  ├── Roboto-Bold.ttf
  ├── Roboto-Regular.ttf
  ├── Roboto-Light.ttf
  └── OpenSans-Bold.ttf
```

**Note:** You can use just the filename (e.g., `Roboto-Bold.ttf`) or the full path (e.g., `fonts/Roboto-Bold.ttf`)

### Step 3: Configure Fonts in `config.yaml`

Open `config.yaml` and provide the **path** to your font files. The system supports:

- **Absolute paths**: Full path to the font file
- **Relative to fonts directory**: Just the filename if font is in `fonts/` directory
- **Relative to project root**: Path relative to project root
- **System font paths**: Paths to system-installed fonts

**Examples:**

```yaml
# Using fonts from the fonts/ directory (just filename)
fonts:
  title_font: "Roboto-Bold.ttf"
  body_font: "Roboto-Regular.ttf"
  subtitle_font: "Roboto-Light.ttf"

# Using absolute paths (fonts anywhere on your system)
fonts:
  title_font: "/Users/username/Downloads/fonts/Roboto-Bold.ttf"
  body_font: "/Users/username/Downloads/fonts/Roboto-Regular.ttf"

# Using system fonts
fonts:
  title_font: "/System/Library/Fonts/Helvetica.ttc"
  body_font: "/System/Library/Fonts/Supplemental/Helvetica.ttc"

# Mix of paths
fonts:
  title_font: "fonts/Roboto-Bold.ttf"  # relative to fonts directory
  body_font: "/custom/path/OpenSans-Regular.ttf"  # absolute path
```

**Important:** Provide the actual path to your font file. The system will:
1. Try to load from the exact path you provide
2. If not found, try relative to fonts directory
3. If still not found, try relative to project root
4. If still not found, fall back to system default font

### Step 4: Verify Fonts Are Loaded

When you run the video generator, it will log available fonts:
```
Available fonts: Roboto-Bold.ttf, Roboto-Light.ttf, Roboto-Regular.ttf
```

If a font fails to load, you'll see a warning and the system will fall back to default fonts.

## Font Selection Tips

1. **Titles**: Use bold, attention-grabbing fonts (e.g., `Roboto-Bold.ttf`, `Montserrat-Bold.ttf`)
2. **Body Text**: Use readable, clean fonts (e.g., `Roboto-Regular.ttf`, `OpenSans-Regular.ttf`)
3. **Subtitles**: Use lighter weights (e.g., `Roboto-Light.ttf`, `OpenSans-Light.ttf`)

## Default Fonts

If no custom fonts are specified in the configuration, the system will fall back to:
1. System Helvetica (macOS)
2. Arial (if available)
3. Default system font

## Troubleshooting

**Font not loading?**
- Check the file is in the `fonts/` directory
- Verify the filename matches exactly (case-sensitive on Linux/macOS)
- Ensure the font file is not corrupted
- Check the file format is `.ttf`, `.otf`, or `.ttc`

**Font looks wrong?**
- Make sure you're using the correct weight (Bold, Regular, Light, etc.)
- Some fonts may not support all characters - try a different font
- Check the font file is complete (not a subset font)

## Example: Using Google Fonts

1. Go to https://fonts.google.com
2. Search for "Roboto" and click on it
3. Click "Download family" button
4. Extract the ZIP file
5. Copy `Roboto-Bold.ttf`, `Roboto-Regular.ttf`, and `Roboto-Light.ttf` to this directory
6. Update `config.yaml` as shown above

