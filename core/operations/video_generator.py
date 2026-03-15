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


# USING CUSTOM TOOLS
# from claude_agent_sdk import (
#     tool,
#     create_sdk_mcp_server,
#     ClaudeSDKClient,
#     ClaudeAgentOptions,
# )
# # Define a custom tool using the @tool decorator
# @tool(
#     "get_weather",
#     "Get current temperature for a location using coordinates",
#     {"latitude": float, "longitude": float},
# )
# async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
#     # Call weather API
#     async with aiohttp.ClientSession() as session:
#         async with session.get(
#             f"https://api.open-meteo.com/v1/forecast?latitude={args['latitude']}&longitude={args['longitude']}&current=temperature_2m&temperature_unit=fahrenheit"
#         ) as response:
#             data = await response.json()

#     return {
#         "content": [
#             {
#                 "type": "text",
#                 "text": f"Temperature: {data['current']['temperature_2m']}°F",
#             }
#         ]
#     }


# # Create an SDK MCP server with the custom tool
# custom_server = create_sdk_mcp_server(
#     name="my-custom-tools",
#     version="1.0.0",
#     tools=[get_weather],  # Pass the decorated function
# )

# from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
# import asyncio

# # Use the custom tools with Claude
# options = ClaudeAgentOptions(
#     mcp_servers={"my-custom-tools": custom_server},
#     allowed_tools=[
#         "mcp__my-custom-tools__get_weather",  # Allow the weather tool
#         # Add other tools as needed
#     ],
# )




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
        available = os.path.exists(os.path.join(target_path, config.pipeline_public_path))
        if not available:
            logger.error(f"composition assets are not available at {target_path}")
            return []
        else:
            logger.info(f"composition assets are available at {target_path}")
        return recursive_listdir(os.path.join(target_path, config.pipeline_public_path))

    
    def _render_video_in_target(self, target_path: str) -> subprocess.CompletedProcess:
        """render video in the target path."""
        composition_path = os.path.join(target_path)
        entry_file = 'src/index.ts'
        return subprocess.run(
            ['npx', 'remotion', 'render', entry_file, f'--public-dir={os.path.join(target_path, config.pipeline_public_path)}', 'VidinieComposition', 'result/video.mp4'],
            cwd=composition_path,
            check=False
        )

    async def _agentic_video_modification(self, target_path: str, user_query: str, error_message: str) -> bool:
        raise NotImplementedError("video modification is not implemented")
    
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
            cwd=os.path.join(target_path) # limit the scope of the agent to the composition directory

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
        xml_prompt_context = to_xml_prompt_context(script_data)
        # check if remotion tool is available
        if not self._check_remotion_tool():
            raise ValueError("remotion tool is not available")
        # initiate agent with context of the task and location of the remotion project, video outline data and media assets
        await self._agentic_video_generation(xml_prompt_context, target_path)
        # render video in target path
        self._render_video_in_target(target_path)
        # return the path to the generated video
        return os.path.join(target_path, config.pipeline_result_path, 'video.mp4')

if __name__ == "__main__":
    logger.info("starting video generator experiment")
    video_generator = VideoGenerator()
    logger.info("dependencies installed in target path")
    video_generator._render_video_in_target('temp/696fed125aaee84dd0d1bbd1')
    logger.info("video rendered in target path")
    video_generator._move_remotion_output_to_target_output('temp/696fed125aaee84dd0d1bbd1')
    logger.info("remotion output moved to target output path")
    # asyncio.run(test_agent())