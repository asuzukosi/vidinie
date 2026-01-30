import replicate
import os
from typing import List
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.utils.logger import get_logger
from pydantic import BaseModel
from dotenv import load_dotenv
from retry import retry


load_dotenv()
logger = get_logger("image_engine")

class ImagePrompt(BaseModel):
    """image prompt with task and optional images."""
    target: str # target of the image (e.g. "a photo of a cat", "a photo of a dog", "a photo of a bird")
    aesthetics: List[str] = [] # list of aesthetics to apply to the image (e.g. "realistic", "cartoon")
    exemptions: List[str] = [] # list of exemptions from the aesthetics
    output_path: str # path to save the image

class ImageEngine:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("REPLICATE_API_TOKEN")
        if not api_key:
            raise ValueError("replicate api key is required")
        logger.info(f"initializing image engine with replicate api key")
        self.client = replicate.Client(api_token=api_key)
        self.model = "black-forest-labs/flux-schnell"

     @retry(tries=5, delay=2, backoff=4)
    def _generate_image(self, prompt: ImagePrompt) -> str:
        """
        generate an image based on the prompt.
        """
        assert prompt.output_path.endswith(".png"), "output path must end with .png"
        logger.info(f"generating image based on prompt: {prompt.target}")
        prompt_str = f"{prompt.target},{','.join(prompt.aesthetics) if prompt.aesthetics else 'No aesthetic limitations'},{','.join(prompt.exemptions) if prompt.exemptions else 'No exemptions'}"
        output = self.client.run(
            self.model,
            input={"prompt": prompt_str}
        )
        logger.info(f"image generated saving to output path")
        # save the image to the output directory
        if prompt.output_path:
            # create the output path if it does not exist (use Path as in voiceover_generator)
            Path(os.path.dirname(prompt.output_path)).mkdir(parents=True, exist_ok=True)
            with open(prompt.output_path, "wb") as f:
                f.write(output[0].read())
            logger.info(f"image saved to output path: {prompt.output_path}")
        return prompt.output_path
    
    async def _generate_image_async(self, prompt: ImagePrompt) -> str:
        """run the synchronous blocking api call in a thread pool to enable parallelism"""
        return await asyncio.to_thread(self._generate_image, prompt)

    async def generate_images(self, prompts: List[ImagePrompt]) -> List[str]:
        """
        image engine function takes a list of prompts and runs all in parallel
        then returns the list of output paths
        """
        tasks = [self._generate_image_async(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return results


async def generate_images(prompts: List[ImagePrompt]) -> List[str]:
    """async module-level function for generating images."""
    image_engine = ImageEngine()
    return await image_engine.generate_images(prompts)


if __name__ == "__main__":
    prompts = [
        ImagePrompt(
            target="A majestic lion in a jungle",
            aesthetics=["realistic", "detailed", "colorful", "vivid"],
            exemptions=["no animals", "no humans"],
            output_path="test_image1.png"
        ),
        ImagePrompt(
            target="A serene mountain landscape",
            aesthetics=["realistic", "detailed", "colorful", "vivid"],
            exemptions=[],
            output_path="test_image2.png"
        ),
    ]
    image_engine = ImageEngine()
    output_paths = asyncio.run(image_engine.generate_images(prompts))
    print(f"images saved to output paths: {output_paths}")
