"""
image operations for the api.
handles image labeling, adding images to pipelines, and image management.
"""

import os
from fastapi import UploadFile
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import VideoPipeline, ImageMetadata
from core.operations.image_labeler import ImageLabeler

logger = get_logger(__name__)


def _save_image_file(image: UploadFile, output_path: str) -> int:
    """save an uploaded image file to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image_content = image.file.read()
    image.file.seek(0)
    with open(output_path, 'wb') as f:
        f.write(image_content)
    return len(image_content)


def _create_image_metadata(
    image: UploadFile,
    filepath: str
) -> ImageMetadata:
    """create image metadata object from uploaded image."""
    return ImageMetadata(
        filename=image.filename or "unknown",
        filepath=filepath
    )


def _label_image_metadata(
    image_metadata: ImageMetadata
) -> ImageMetadata:
    """label an image using ai."""
    labeler = ImageLabeler(user_instructions="")  # Image operations don't have pipeline context, use empty instructions
    labeled_metadata = labeler.label_images_batch([image_metadata])
    return labeled_metadata[0] if labeled_metadata else image_metadata


def add_image_to_pipeline(
    video_pipeline: VideoPipeline,
    image: UploadFile,
    label: bool = False
) -> ImageMetadata:
    """add an image to a video pipeline."""
    if not image.filename or not image.filename.endswith((".png", ".jpg", ".jpeg", ".gif")):
        raise ValueError("Invalid image type must be a PNG, JPG, or JPEG file")
    
    if not video_pipeline.id:
        raise ValueError("Pipeline ID not found for this pipeline. Create a new pipeline object to continue")
    
    output_dir = str(config.output_directory)
    image_path = os.path.join(output_dir, video_pipeline.id, "images", image.filename)
    _save_image_file(image, image_path)
    image_metadata = _create_image_metadata(image, image_path)
    
    if label:
        image_metadata = _label_image_metadata(image_metadata)
    
    video_pipeline.images_metadata.append(image_metadata)
    return image_metadata


def _delete_image_file(filepath: str) -> bool:
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
) -> ImageMetadata:
    """delete an image from a video pipeline."""
    if index < 0 or index >= len(video_pipeline.images_metadata):
        raise IndexError(f"Image index {index} out of range")
    image_metadata = video_pipeline.images_metadata.pop(index)
    if image_metadata.filepath:
        _delete_image_file(image_metadata.filepath)
    return image_metadata
