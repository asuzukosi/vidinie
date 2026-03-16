"""
vidinie image labeler module
uses the reasoning engine to analyze and label images.
"""
from pydantic import BaseModel
from typing import List
from core.clients.reasoning_engine import ReasoningPrompt, reason
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import ImageMetadata

logger = get_logger(__name__)

class ImageLabelOutput(BaseModel):
    label: str
    description: str
    image_type: str
    key_elements: List[str]
    relevance: str


class ImageLabeler:
    """label and describe images using ai vision models."""
    
    def __init__(self, user_instructions: str = ""):
        """
        initialize image labeler.
        """
        self.user_instructions = user_instructions
        # initialize jinja2 environment for prompt templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(config.prompts_directory)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def label_images_batch(self, images_metadata: List[ImageMetadata]) -> List[ImageMetadata]:
        """
        label multiple images from metadata list.
        args:
            images_metadata: list of image metadata dictionaries
        returns:
            updated metadata list with labels and descriptions
        """
        logger.info(f"Starting batch labeling for {len(images_metadata)} images")
        system_prompt = self.jinja_env.get_template('image_labeling_system.j2').render(
            user_instructions=self.user_instructions if self.user_instructions else None
        )
        template = self.jinja_env.get_template('image_labeling_instruction.j2')
        prompts = [ReasoningPrompt(task=template.render(), images=[img_meta.filepath]) for img_meta in images_metadata]
        results: List[ImageLabelOutput] = await reason(system_prompt, prompts, schema=ImageLabelOutput)        
        for idx, result in enumerate(results):
            images_metadata[idx].label = result.label
            images_metadata[idx].description = result.description
            images_metadata[idx].image_type = result.image_type
            images_metadata[idx].key_elements = result.key_elements
            images_metadata[idx].relevance = result.relevance
        logger.info("batch labeling complete")
        return images_metadata