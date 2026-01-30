import replicate
import os
import asyncio
from typing import List
import sys
from retry import retry
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.utils.logger import get_logger
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()
logger = get_logger("video_engine")

class VideoPrompt(BaseModel):
    """video prompt with task and optional images."""
    target: str # target of the video (e.g. "a video of a cat", "a video of a dog", "a video of a bird")
    aesthetics: List[str] = [] # list of aesthetics to apply to the video (e.g. "realistic", "cartoon")
    exemptions: List[str] = [] # list of exemptions from the aesthetics
    output_path: str # path to save the video

class VideoEngine:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("REPLICATE_API_TOKEN")
        if not api_key:
            raise ValueError("replicate api key is required")
        logger.info(f"initializing video engine with replicate api key")
        self.client = replicate.Client(api_token=api_key)
        self.model = "bytedance/seedance-1-lite"
        self.duration = 5
        self.resolution = "480p"
        self.fps = 24
        self.aspect_ratio = "16:9"
        self.camera_fixed = False

    @retry(tries=5, delay=2, backoff=4)
    def _generate_video(self, prompt: VideoPrompt) -> str:
        """
        generate a video based on the prompt.
        """
        assert prompt.output_path.endswith(".mp4"), "output path must end with .mp4"
        logger.info(f"generating video based on prompt: {prompt.target}")
        prompt_str = f"{prompt.target},{','.join(prompt.aesthetics) if prompt.aesthetics else 'No aesthetic limitations'},{','.join(prompt.exemptions) if prompt.exemptions else 'No exemptions'}"
        output = self.client.run(
            self.model,
            input={"prompt": prompt_str, 
                   "duration": self.duration, 
                   "resolution": self.resolution, 
                   "fps": self.fps, 
                   "aspect_ratio": self.aspect_ratio, 
                   "camera_fixed": self.camera_fixed}
        )
        logger.info(f"video generated saving to output path")
        # save the video to the output directory
        if prompt.output_path:
            # create the output path if it does not exist (use Path as in voiceover_generator)
            Path(os.path.dirname(prompt.output_path)).mkdir(parents=True, exist_ok=True)

            with open(prompt.output_path, "wb") as f:
                f.write(output.read())
            logger.info(f"video saved to output path: {prompt.output_path}")
        return prompt.output_path
    
    async def _generate_video_async(self, prompt: VideoPrompt) -> str:
        """run the synchronous blocking api call in a thread pool to enable parallelism"""
        return await asyncio.to_thread(self._generate_video, prompt)
        
    async def generate_videos(self, prompts: List[VideoPrompt]) -> List[str]:
        """
        generate multiple videos sequentially with rate limiting.
        """
        results = []
        for i, prompt in enumerate(prompts, 1):
            logger.info(f"generating video {i}/{len(prompts)}")
            output_path = await self._generate_video_async(prompt)
            results.append(output_path)
            
            # wait 10 seconds between requests to avoid rate limiting (except for the last one)
            if i < len(prompts):
                logger.info(f"waiting 10 seconds before next video generation to avoid rate limiting...")
                await asyncio.sleep(10)
        
        return results


async def generate_videos(prompts: List[VideoPrompt]) -> List[str]:
    """async module-level function for generating videos."""
    video_engine = VideoEngine()
    return await video_engine.generate_videos(prompts)


if __name__ == "__main__":
    prompts = [
        VideoPrompt(
            target="A majestic lion in a jungle rouring intensely",
            aesthetics=["realistic", "detailed", "colorful", "vivid"],
            exemptions=["no animals", "no humans"],
            output_path="test_video1.mp4"
        ),
        VideoPrompt(
            target="A serene mountain landscape helicopter camera shot",
            aesthetics=["realistic", "detailed", "colorful", "vivid"],
            exemptions=[],
            output_path="test_video2.mp4"
        ),
    ]
    video_engine = VideoEngine()
    output_paths = asyncio.run(video_engine.generate_videos(prompts))
    print(f"videos saved to output paths: {output_paths}")
