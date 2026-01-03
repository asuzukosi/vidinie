"""
vidinie image labeler module
uses openai vision api to analyze and label images extracted from pdf documents.
generates descriptions, labels, and context for each image.
"""

import os
import base64
import json
from typing import List, Dict, Optional, Any, Union
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from core.utils.logger import get_logger
from core.utils.config_loader import get_config
from core.data import VideoPipeline, VideoPipelineImageMetadata

logger = get_logger(__name__)


class ImageLabeler:
    """label and describe images using ai vision models."""
    
    def __init__(self, api_key: Optional[str] = None, prompts_dir: Optional[Path] = None):
        """
        initialize image labeler.
        args:
            api_key: openai api key (defaults to environment variable)
            prompts_dir: path to prompts directory (from config)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("openai api key is required. set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # gpt-4 with vision
        
        # initialize jinja2 environment for prompt templates
        if prompts_dir is None:
            config = get_config()
            prompts_dir = config.get_prompts_directory()
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def label_image(self, image_path: str, text_context: str = "") -> Dict[str, str]:
        """
        generate label and description for a single image.
        args:
            image_path: path to image file
            text_context: surrounding text context from pdf
        returns:
            dictionary with label, description, and analysis
        """
        logger.info(f"Labeling image: {image_path}")
        
        try:
            image_data = self._encode_image_to_base64(image_path)
            mime_type = self._get_mime(image_path)
            prompt = self._create_labeling_prompt(text_context)
            result_text = self._generate_label(prompt, mime_type, image_data)
            result = self._parse_vision_response(result_text)

            logger.info(f"Successfully labeled: {result.get('label', 'Unknown')}")
            return result

        except Exception as e:
            logger.error(f"Error labeling image {image_path}: {str(e)}")
            return {
                "label": "Unlabeled Image",
                "description": "Could not analyze image",
                "image_type": "unknown",
                "key_elements": [],
                "relevance": "unknown"
            }

    def label_images_batch(self, images_metadata: List[VideoPipelineImageMetadata]) -> List[VideoPipelineImageMetadata]:
        """
        label multiple images from metadata list.
        args:
            images_metadata: list of image metadata dictionaries
        returns:
            updated metadata list with labels and descriptions
        """
        logger.info(f"Starting batch labeling for {len(images_metadata)} images")
        
        for i, img_meta in enumerate(images_metadata, 1):
            logger.info(f"processing image {i}/{len(images_metadata)}")
            
            # skip if already labeled
            if img_meta.label and img_meta.description:
                logger.info(f"Image already labeled: {img_meta.get('label')}")
                continue
            
            image_path = img_meta.filepath
            text_context = img_meta.text_context
            result = self.label_image(image_path, text_context)
            img_meta.label = result.get('label', 'Unlabeled')
            img_meta.description = result.get('description', '')
            img_meta.image_type = result.get('image_type', 'unknown')
            img_meta.key_elements = result.get('key_elements', [])
            img_meta.ai_relevance = result.get('relevance', 'medium')
        
        logger.info("batch labeling complete")
        return images_metadata

    @staticmethod
    def _encode_image_to_base64(image_path: str) -> str:
        """
        encode an image file to a base64 string.
        args:
            image_path: path to image file
        returns:
            base64 encoded string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @staticmethod
    def _get_mime(image_path: str) -> str:
        """
        extract the correct mime type based on file extension.
        args:
            image_path: path to image file
        returns:
            mime type string (e.g. 'image/jpeg')
        """
        ext = os.path.splitext(image_path)[1].lower()
        return {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/jpeg')

    def _generate_label(self, prompt: str, mime_type: str, image_data: str) -> str:
        """
        call the openai vision api to generate labels/descriptions.
        args:
            prompt: prompt string for vision model
            mime_type: image mime type
            image_data: base64 data for image
        returns:
            vision model response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        return response.choices[0].message.content

    def _create_labeling_prompt(self, text_context: str) -> str:
        """
        create a prompt for the vision model.
        args:
            text_context: text context from pdf
        returns:
            prompt string
        """
        # load and render template
        template = self.jinja_env.get_template('image_labeling_instruction.j2')
        prompt = template.render(text_context=text_context)
        
        return prompt

    def _parse_vision_response(self, response_text: str) -> Dict[str, str]:
        """
        parse the vision model response into structured data.
        args:
            response_text: raw response from vision model
        returns:
            structured dictionary
        """
        result = {
            "label": "",
            "description": "",
            "image_type": "",
            "key_elements": [],
            "relevance": "medium"
        }
        # configure the model to provide a structured response to prevent long parsing process
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('LABEL:'):
                result['label'] = line.replace('LABEL:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                result['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('TYPE:'):
                result['image_type'] = line.replace('TYPE:', '').strip()
            elif line.startswith('KEY_ELEMENTS:'):
                elements_str = line.replace('KEY_ELEMENTS:', '').strip()
                result['key_elements'] = [e.strip() for e in elements_str.split(',')]
            elif line.startswith('RELEVANCE:'):
                result['relevance'] = line.replace('RELEVANCE:', '').strip().lower()
        
        # fallback if parsing failed
        if not result['label']:
            result['label'] = "Unlabeled Image"
        if not result['description']:
            result['description'] = response_text[:200]
        
        return result
    
    def save_labeled_metadata(self, images_metadata: List[VideoPipelineImageMetadata], output_path: str):
        """
        save labeled metadata to JSON file.
        args:
            images_metadata: list of image metadata
            output_path: path to save json file
        """
        with open(output_path, 'w') as f:
            data = [img.model_dump(mode="json") for img in images_metadata]
            json.dump(data, f, indent=2)
        logger.info(f"saved labeled metadata to {output_path}")


def label_images(images_metadata: List[VideoPipelineImageMetadata], 
                 api_key: Optional[str] = None) -> List[VideoPipelineImageMetadata]:
    """
    convenience function to label images.
    args:
        images_metadata: list of image metadata
        api_key: openai api key
    returns:
        updated metadata with labels
    """
    labeler = ImageLabeler(api_key)
    return labeler.label_images_batch(images_metadata)


def save_image_file(image: Any, output_path: str) -> int:
    """save an uploaded image file to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image_content = image.file.read()
    image.file.seek(0)
    with open(output_path, 'wb') as f:
        f.write(image_content)
    return len(image_content)


def create_image_metadata(
    image: Any,
    filepath: str,
    text_context: Optional[str] = None,
    size_bytes: Optional[int] = None
) -> VideoPipelineImageMetadata:
    """create image metadata object from uploaded image."""
    return VideoPipelineImageMetadata(
        filename=image.filename or "unknown",
        filepath=filepath,
        page_number=1,
        width=image.size[0] if hasattr(image, 'size') and image.size else None,
        height=image.size[1] if hasattr(image, 'size') and image.size else None,
        format=image.content_type.split("/")[1] if image.content_type else None,
        mode="RGB",
        size_bytes=size_bytes or 0,
        text_context=text_context or "",
        xref=None,
        index_on_page=0
    )


def label_image_metadata(
    image_metadata: VideoPipelineImageMetadata,
    openai_api_key: str,
    prompts_dir: Union[Path, str]
) -> VideoPipelineImageMetadata:
    """Label an image using AI."""
    labeler = ImageLabeler(openai_api_key, prompts_dir)
    labeled_metadata = labeler.label_images_batch([image_metadata])
    return labeled_metadata[0] if labeled_metadata else image_metadata


def add_image_to_pipeline(
    video_pipeline: VideoPipeline,
    image: Any,
    text_context: Optional[str] = None,
    label: bool = False,
    openai_api_key: Optional[str] = None,
    prompts_dir: Optional[Union[Path, str]] = None
) -> VideoPipelineImageMetadata:
    """Add an image to a video pipeline."""
    if not image.filename or not image.filename.endswith((".png", ".jpg", ".jpeg", ".gif")):
        raise ValueError("Invalid image type must be a PNG, JPG, or JPEG file")
    
    path_id = video_pipeline.path_id
    if not path_id:
        raise ValueError("Path ID not found for this pipeline. Create a new pipeline object to continue")
    
    image_path = os.path.join(path_id, "images", image.filename)
    size_bytes = save_image_file(image, image_path)
    image_metadata = create_image_metadata(image, image_path, text_context, size_bytes)
    
    if label and openai_api_key and prompts_dir:
        image_metadata = label_image_metadata(image_metadata, openai_api_key, prompts_dir)
    
    video_pipeline.images_metadata.append(image_metadata)
    return image_metadata


def update_image_metadata(
    image_metadata: VideoPipelineImageMetadata,
    filename: Optional[str] = None,
    text_context: Optional[str] = None,
    description: Optional[str] = None,
    relevance_score: Optional[float] = None,
    image_type: Optional[str] = None,
    key_elements: Optional[List[str]] = None,
    ai_relevance: Optional[str] = None
) -> VideoPipelineImageMetadata:
    """update image metadata fields."""
    if filename is not None:
        image_metadata.filename = filename
    if text_context is not None:
        image_metadata.text_context = text_context
    if description is not None:
        image_metadata.description = description
    if relevance_score is not None:
        image_metadata.relevance_score = relevance_score
    if image_type is not None:
        image_metadata.image_type = image_type
    if key_elements is not None:
        image_metadata.key_elements = key_elements
    if ai_relevance is not None:
        image_metadata.ai_relevance = ai_relevance
    return image_metadata


def update_image_in_pipeline(
    video_pipeline: VideoPipeline,
    index: int,
    **kwargs
) -> VideoPipelineImageMetadata:
    """update image metadata in a video pipeline."""
    if index < 0 or index >= len(video_pipeline.images_metadata):
        raise IndexError(f"Image index {index} out of range")
    image_metadata = video_pipeline.images_metadata[index]
    return update_image_metadata(image_metadata, **kwargs)


def delete_image_file(filepath: str) -> bool:
    """delete an image file from disk."""
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete image file {filepath}: {str(e)}")
            return False
    return False


def delete_image_from_pipeline(
    video_pipeline: VideoPipeline,
    index: int
) -> VideoPipelineImageMetadata:
    """delete an image from a video pipeline."""
    if index < 0 or index >= len(video_pipeline.images_metadata):
        raise IndexError(f"Image index {index} out of range")
    image_metadata = video_pipeline.images_metadata.pop(index)
    if image_metadata.filepath:
        delete_image_file(image_metadata.filepath)
    return image_metadata