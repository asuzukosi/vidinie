"""
vidinie unified video generator
creates presentation-style explainer videos with the remotion engine using a claude agent.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from typing import List
import shutil
import subprocess
from enum import Enum
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.utils.config_loader import config
from core.data import (
    VideoOutline, 
)
from core.data.segment_models import to_xml_prompt_context
from claude_agent_sdk import query # function to query the agent
from claude_agent_sdk.types import ClaudeAgentOptions # class for the agent options
from claude_agent_sdk.types import AssistantMessage # class for the assistant message
from claude_agent_sdk.types import ResultMessage # class for the result of the agent
from core.utils.logger import get_logger
logger = get_logger("video_generator")

def recursive_listdir(path: str, full_list: List[str] = []) -> List[str]:
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            full_list.append(os.path.join(path, file))
        else:
            recursive_listdir(os.path.join(path, file), full_list)
    return full_list

class VideoResolution(str, Enum):
    """video resolution."""
    RESOLUTION_1080P = "1080P"
    RESOLUTION_720P = "720P"
    RESOLUTION_480P = "480P"


class VideoGenerator:
    """agentic video generator using the remotion engine."""
    
    def __init__(self,
                 resolution: Optional[VideoResolution] = VideoResolution.RESOLUTION_720P,
                 user_instructions: str = ""):
        """
        initialize video generator.
        """
        self.resolution = resolution
        self.user_instructions = user_instructions
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(config.prompts_directory)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.base_project_path = config.base_project_path
        self.remotion_tool_path = config.remotion_tool_path
        logger.info(f"initialized video generator: {self.resolution}")

        if not self._check_remotion_tool():
            raise ValueError("remotion tool is not available")
        if not self._check_base_project():
            raise ValueError("base project is not available")

    def _check_remotion_tool(self) -> bool:
        """check if the remotion tool is available."""
        logger.info(f"checking if remotion tool is available at {self.remotion_tool_path}")
        available = os.path.exists(self.remotion_tool_path)
        if not available:
            logger.error(f"remotion tool is not available at {self.remotion_tool_path}")
        else:
            logger.info(f"remotion tool is available at {self.remotion_tool_path}")
        return available
    
    def _check_composition_assets(self, target_path: str) -> bool:
        """check if the composition assets are available."""
        logger.info(f"checking if composition assets are available at {target_path}")
        available = os.path.exists(os.path.join(target_path, 'composition', 'public'))
        if not available:
            logger.error(f"composition assets are not available at {target_path}")
            return []
        else:
            logger.info(f"composition assets are available at {target_path}")
        return recursive_listdir(os.path.join(target_path, 'composition', 'public'))

    
    def _check_base_project(self) -> bool:
        """check if the base project is available."""
        logger.info(f"checking if base project is available at {self.base_project_path}")
        available = os.path.exists(self.base_project_path)
        if not available:
            logger.error(f"base project is not available at {self.base_project_path}")
        else:
            logger.info(f"base project is available at {self.base_project_path}")
        return available
    
    def _copy_base_to_target(self, target_path: str) -> bool:
        """copy the base project to the target path."""
        copy_target_path = os.path.join(target_path, 'composition')
        if os.path.exists(copy_target_path):
            logger.info(f"removing existing composition at {copy_target_path}")
            shutil.rmtree(copy_target_path)
        logger.info(f"copying base project to {copy_target_path}")
        return shutil.copytree(self.base_project_path, copy_target_path)
    
    def _install_dependencies_in_target(self, target_path: str) -> bool:
        """install dependencies in the target path."""
        composition_path = os.path.join(target_path, 'composition')
        return subprocess.run(
            ['npm', 'install'],
            cwd=composition_path,
            check=False
        )
    
    def _move_assets_from_target_to_remotion_public(self, target_path: str) -> bool:
        """move assets from the target path to the remotion public folder."""
        composition_path = os.path.join(target_path, 'composition')
        composition_public_path = os.path.join(composition_path, 'public')
        if not os.path.exists(composition_public_path):
            os.makedirs(composition_public_path)
        # move audio
        audio_path = os.path.join(target_path, 'audio')
        if os.path.exists(audio_path):
            shutil.copytree(audio_path, os.path.join(composition_public_path, 'audio'))
         # move music
        music_path = os.path.join(target_path, 'music')
        if os.path.exists(audio_path):
            shutil.copytree(music_path, os.path.join(composition_public_path, 'music'))
        # move source
        source_path = os.path.join(target_path, 'source')
        if os.path.exists(source_path):
            shutil.copytree(source_path, os.path.join(composition_public_path, 'source'))
        # move images
        images_path = os.path.join(target_path, 'images')
        if os.path.exists(images_path):
            shutil.copytree(images_path, os.path.join(composition_public_path, 'images'))
        # move video clips
        video_clips_path = os.path.join(target_path, 'video_clips')
        if os.path.exists(video_clips_path):
            shutil.copytree(video_clips_path, os.path.join(composition_public_path, 'video_clips'))
    
    def _render_video_in_target(self, target_path: str) -> str:
        composition_path = os.path.join(target_path, 'composition')
        entry_file = 'src/index.ts'
        return subprocess.run(
            ['npx', 'remotion', 'render', entry_file],
            cwd=composition_path,
            check=False
        )
    
    def _move_remotion_output_to_target_output(self, target_path: str) -> bool:
        """copy remotion output to the target output path."""
        remotion_output_path = os.path.join(target_path, 'composition', 'out', 'VidinieComposition.mp4')
        target_output_dir = os.path.join(target_path, 'result')
        target_output_path = os.path.join(target_output_dir, 'vidinie_video.mp4')
        if not os.path.exists(remotion_output_path):
            logger.error(f"remotion output not found at {remotion_output_path}")
            return False
        # create target directory if it doesn't exist
        os.makedirs(target_output_dir, exist_ok=True)
        logger.info(f"copying remotion output from {remotion_output_path} to {target_output_path}")
        shutil.copy2(remotion_output_path, target_output_path)
        logger.info(f"remotion output copied to {target_output_path}")
        return True
    
    async def _agentic_video_generation(self, xml_prompt_context: str, target_path: str):
        """agentic video generation."""
        system_prompt = self.jinja_env.get_template('video_generation_system.j2').render(
            user_instructions=self.user_instructions if self.user_instructions else None
        )
        composition_assets = self._check_composition_assets(target_path)
        composition_assets_string: str = "\n".join(composition_assets)
        composition_assets_string: str = composition_assets_string.replace(os.path.join(target_path, "composition", "public"), "public")
        xml_prompt_context: str = xml_prompt_context.replace(target_path, "public")
        prompt = self.jinja_env.get_template('video_generation_instruction.j2').render(video_outline=xml_prompt_context, 
                                                                                       composition_assets=composition_assets_string)
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            setting_sources=["project"],  # load skills from the project file system
            allowed_tools=["Skill", "Read", "Write"], # allow tools to read and write files only - NO bash commands
            permission_mode="acceptEdits",  # allow file edits
            cwd=os.path.join(target_path, "composition") # limit the scope of the agent to the composition directory

        )
        message_usages = []
        async for message in query(prompt=prompt,options=options):
            # process assistant message
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        logger.info(f"*** AGENT REASONING: {block.text} ***\n")# agent reasoning
                    if hasattr(block, "tool_use_id"):
                        logger.info(f"*** AGENT TOOL USE ID: {block.tool_use_id} ***\n")   # tool use id
                    if hasattr(block, "id"):
                        logger.info(f"*** AGENT ID: {block.id} ***\n")   # agent id
                    if hasattr(block, "is_error"):
                        logger.info(f"*** AGENT ERROR: {block.is_error} ***\n")   # agent error
                    if hasattr(block, "signature"):
                        logger.info(f"*** AGENT SIGNATURE: {block.signature} ***\n")   # agent signature
                    if hasattr(block, "name"):
                        logger.info(f"*** EXECUTED TOOL: {block.name} ***\n")   # tool being called
                    if hasattr(block, "thinking"):
                        logger.info(f"*** AGENT THINKING: {block.thinking} ***\n")   # agent thinking
                    if hasattr(block, "input"):
                        logger.info(f"*** AGENT INPUT: {block.input} ***\n")   # agent input
                    if hasattr(block, "content"):
                        logger.info(f"*** AGENT CONTENT: {block.content} ***\n")   # agent content
                logger.info("--------------------------------------------------\n")
            # process result message
            elif isinstance(message, ResultMessage):
                logger.info("*** FINAL RESULT MESSAGE ***\n")
                logger.info(f"*** RESULT MESSAGE: {message.result} ***\n")
                logger.info("--------------------------------------------------\n")
            # calculate message token usage
            if hasattr(message, "usage"):
                message_usages.append(message.usage["output_tokens"])
        
        # calculate total token usage
        total_token_usage = sum(message_usages)
        logger.info("--------------------------------------------------\n")
        logger.info(f"TOTAL TOKEN USAGE: {total_token_usage}\n")
        logger.info("--------------------------------------------------\n")


    async def generate_video(self, script_data: VideoOutline, target_path: str) -> str:
        # copy reference content into provided output path
        self._copy_base_to_target(target_path)
        # install dependencies in target path
        self._move_assets_from_target_to_remotion_public(target_path)
        # install dependencies in target path
        self._install_dependencies_in_target(target_path)
        # convert video outline into json and store in task temp file
        xml_prompt_context = to_xml_prompt_context(script_data)
        # check if remotion tool is available
        if not self._check_remotion_tool():
            raise ValueError("remotion tool is not available")
        # initiate agent with context of the task and location of the remotion project, video outline data and media assets
        await self._agentic_video_generation(xml_prompt_context, target_path)
        # render video in target path
        self._render_video_in_target(target_path)
        # move remotion output to target output path
        self._move_remotion_output_to_target_output(target_path)
        # return the path to the generated video
        return os.path.join(target_path, 'result', 'vidinie_video.mp4')

if __name__ == "__main__":
    logger.info("starting video generator experiment")
    video_generator = VideoGenerator()
    logger.info("video generator initialized")
    video_generator._copy_base_to_target('temp/696fed125aaee84dd0d1bbd1')
    logger.info("base project copied to target path")
    video_generator._move_assets_from_target_to_remotion_public('temp/696fed125aaee84dd0d1bbd1')
    logger.info("assets moved to remotion public folder")
    video_generator._install_dependencies_in_target('temp/696fed125aaee84dd0d1bbd1')
    logger.info("dependencies installed in target path")
    video_generator._render_video_in_target('temp/696fed125aaee84dd0d1bbd1')
    logger.info("video rendered in target path")
    video_generator._move_remotion_output_to_target_output('temp/696fed125aaee84dd0d1bbd1')
    logger.info("remotion output moved to target output path")
    # asyncio.run(test_agent())