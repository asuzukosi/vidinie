"""
vidinie image labeler module
uses openai vision api to analyze and label images extracted from pdf documents.
generates descriptions, labels, and context for each image.
"""

import os
import base64
import json
from typing import List, Dict, Optional
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from utils.logger import get_logger

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
            from utils.config_loader import get_config
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

    def label_images_batch(self, images_metadata: List[Dict]) -> List[Dict]:
        """
        label multiple images from metadata list.
        args:
            images_metadata: list of image metadata dictionaries
        returns:
            updated metadata list with labels and descriptions
        """
        logger.info(f"Starting batch labeling for {len(images_metadata)} images")
        
        for i, img_meta in enumerate(images_metadata, 1):
            logger.info(f"Processing image {i}/{len(images_metadata)}")
            
            # skip if already labeled
            if img_meta.get('label') and img_meta.get('description'):
                logger.info(f"Image already labeled: {img_meta.get('label')}")
                continue
            
            image_path = img_meta['filepath']
            text_context = img_meta.get('text_context', '')
            result = self.label_image(image_path, text_context)
            img_meta['label'] = result.get('label', 'Unlabeled')
            img_meta['description'] = result.get('description', '')
            img_meta['image_type'] = result.get('image_type', 'unknown')
            img_meta['key_elements'] = result.get('key_elements', [])
            img_meta['ai_relevance'] = result.get('relevance', 'medium')
        
        logger.info("Batch labeling complete")
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
    
    def save_labeled_metadata(self, images_metadata: List[Dict], output_path: str):
        """
        save labeled metadata to JSON file.
        args:
            images_metadata: list of image metadata
            output_path: path to save json file
        """
        with open(output_path, 'w') as f:
            json.dump(images_metadata, f, indent=2)
        
        logger.info(f"Saved labeled metadata to {output_path}")


def label_images(images_metadata: List[Dict], api_key: Optional[str] = None) -> List[Dict]:
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


if __name__ == "__main__":
    # test vidinie image labeler
    import sys
    
    if len(sys.argv) < 2:
        print("usage: python image_labeler.py <images_metadata.json>")
        print("first run image_extractor.py to generate the metadata file")
        sys.exit(1)
    
    metadata_path = sys.argv[1]
    
    print(f"\n**** loading image metadata ****")
    with open(metadata_path, 'r') as f:
        images_metadata = json.load(f)
    
    print(f"loaded {len(images_metadata)} images\n")
    
    print("**** starting image labeling ****\n")
    
    labeler = ImageLabeler()
    labeled_metadata = labeler.label_images_batch(images_metadata)
    
    print("\n**** labeling results ****\n")
    for i, img in enumerate(labeled_metadata, 1):
        print(f"{i}. {img['filename']}")
        print(f"- label: {img.get('label', 'Unknown')}")
        print(f"- type: {img.get('image_type', 'Unknown')}")
        print(f"- description: {img.get('description', 'Unknown')}")
        print(f"- relevance: {img.get('ai_relevance', 'Unknown')}")
        print()
    
    # save updated metadata
    output_path = metadata_path.replace('.json', '_labeled.json')
    labeler.save_labeled_metadata(labeled_metadata, output_path)
    
    print(f"**** labeling complete ****")
    print(f"saved to: {output_path}\n")

