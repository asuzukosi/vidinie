from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from core.pipeline_data import PipelineData, SourceType, PipelineStage,\
                               PipelineStatus, ParsedContent, VideoSegment, \
                                ParsedContentMetadata, ParsedContentSection, \
                                ImageMetadata, ContextChunk, ContextProcessorInfo, \
                               PipelineStageStatistics, get_next_stage, get_previous_stage, VideoOutline
from utils.logger import setup_logging, get_logger
from pydantic import BaseModel
from core.image_labeler import ImageLabeler
from typing import List, Any, Dict, Union
import os
from pathlib import Path
from api.core.db import pipelines_collection
from utils.config_loader import get_config
from core.processors.pdf_processor import PDFProcessor
from core.processors.html_processor import HTMLProcessor
from core.context_processor import ContextProcessor
from core.content_analyzer import ContentAnalyzer
from core.stock_image_fetcher import StockImageFetcher
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional
from pydantic import Field
import shutil
import requests

# setup logging
setup_logging(log_dir='temp')
logger = get_logger('pipelines')

# get config
config = get_config()

router = APIRouter(tags=["pipelines"])

class StartPipelineRequest(BaseModel):
    url: str
    name: str
    description: str
    tags: Optional[List[str]] = None
    projects: Optional[List[str]] = None


class SummaryPipelineDataResponse(BaseModel):
    # identification
    id: str
    path_id: Optional[str] = None # id used by mongodb for internal use
    name: str = Field(default="")
    description: str = Field(default="")
    tags: List[str] = Field(default_factory=list, nullable=True)  # tags of the pipeline
    projects: List[str] = Field(default_factory=list, nullable=True)  # projects of the pipeline
    
    # timing information
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # source document
    source_path: Optional[str] = None
    source_type: Optional[SourceType] = None

@router.post("/start_pipeline_with_file", name="start pipeline with file")
async def start_pipeline_with_file(
    name: str = Form(...),
    description: str = Form(...),
    tags: Optional[List[str]] = Form(...),
    projects: Optional[List[str]] = Form(...),
    file: UploadFile = File(...),
) -> SummaryPipelineDataResponse:
    logger.info("received request to start pipeline with file")
    if file.filename == "" or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type must be a PDF file")
    # create pipeline data object
    logger.info("creating pipeline data object")
    pipeline_data = PipelineData()
    pipeline_data.name = name
    pipeline_data.description = description
    pipeline_data.tags = tags[0].split(",") or []
    pipeline_data.projects = projects[0].split(",") or []
    pipeline_data.source_type = SourceType.PDF
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.IN_PROGRESS)
    logger.info("pipeline data object created")

    # create temp directory for metadata
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline_data.id, 'images')
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"created temp directory for metadata: {images_dir}")
    # save file to temp directory
    with open(os.path.join(temp_dir, pipeline_data.id, file.filename), 'wb') as f:
        f.write(file.file.read())
    logger.info(f"saved file to temp directory: {os.path.join(temp_dir, pipeline_data.id, file.filename)}")
    pipeline_data.source_path = os.path.join(temp_dir, pipeline_data.id, file.filename)
    
    # process pdf file
    with PDFProcessor(pipeline_data.source_path, images_output_dir=images_dir) as processor:
        content: ParsedContent = processor.extract_structured_content()
        pipeline_data.parsed_content = content

        # logging content info
        logger.info(f"title: {content.title}")
        logger.info(f"total pages: {content.total_pages}")
        logger.info(f"sections: {len(content.sections)}")

         # extract and label images if requested
        logger.info("labeling images")
        processor.label_images(config.openai_api_key, config.get_prompts_directory())
        pipeline_data.images_metadata = processor.images_metadata
        logger.info(f"labeled {len(processor.images_metadata)} images")
    
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.COMPLETED)

    # save pipeline data to database
    logger.info("saving pipeline data to database")
    pipeline_data.path_id = pipeline_data.id
    db_pipeline = await pipelines_collection.insert_one(pipeline_data.model_dump(mode="json"))
    pipeline_data.id = str(db_pipeline.inserted_id)
    # we have to update the id to the actual id because the id is generated by mongodb and not by us
    await pipelines_collection.update_one(
            {"_id": ObjectId(db_pipeline.inserted_id)}, 
            {"$set": {"id": pipeline_data.id}}
        )
    logger.info(f"pipeline data saved to database with id: {pipeline_data.id}")
    return SummaryPipelineDataResponse(**pipeline_data.model_dump(mode="json"))

@router.post("/start_pipeline_with_url", name="start pipeline with url")
async def start_pipeline_with_url(request: StartPipelineRequest) -> SummaryPipelineDataResponse:
    # validate if url is valid
    logger.info("received request to start pipeline with url")
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL must start with http or https")
    # validate if url is reachable
    response = None
    try:
        response = requests.get(request.url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download file")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=400, detail="Failed to download file")
    
    logger.info("creating pipeline data object")
    pipeline_data = PipelineData()
    pipeline_data.name = request.name
    pipeline_data.description = request.description
    pipeline_data.tags = request.tags or []
    pipeline_data.projects = request.projects or []
    pipeline_data.source_type = SourceType.HTML
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, 
                               PipelineStatus.IN_PROGRESS)
    
    
    logger.info("pipeline data object created")
    # create temp directory for metadata
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline_data.id, 'images')
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"created temp directory for metadata: {images_dir}")
    # save file to temp directory
    with open(os.path.join(temp_dir, pipeline_data.id, 'data.html'), 'wb') as f:
        f.write(response.content)
    logger.info(f"saved file to temp directory: {os.path.join(temp_dir, pipeline_data.id, 'data.html')}")
    pipeline_data.source_path = os.path.join(temp_dir, pipeline_data.id, 'data.html')
    
   # process html file
    with HTMLProcessor(html_path=request.url, images_output_dir=images_dir) as processor:
        content: ParsedContent = processor.extract_structured_content()
        pipeline_data.parsed_content = content

        # logging content info
        logger.info(f"title: {content.title}")
        logger.info(f"total pages: {content.total_pages}")
        logger.info(f"sections: {len(content.sections)}")

         # extract and label images if requested
        logger.info("labeling images")
        processor.label_images(config.openai_api_key, config.get_prompts_directory())
        pipeline_data.images_metadata = processor.images_metadata
        logger.info(f"labeled {len(processor.images_metadata)} images")
    
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.COMPLETED)

    # save pipeline data to database
    logger.info("saving pipeline data to database")
    pipeline_data.path_id = pipeline_data.id
    db_pipeline = await pipelines_collection.insert_one(pipeline_data.model_dump(mode="json"))
    pipeline_data.id = str(db_pipeline.inserted_id)
    logger.info(f"pipeline data saved to database with id: {pipeline_data.id}")
    # we have to update the id to the actual id because the id is generated by mongodb and not by us
    await pipelines_collection.update_one(
            {"_id": ObjectId(db_pipeline.inserted_id)}, 
            {"$set": {"id": pipeline_data.id}}
        )
    return SummaryPipelineDataResponse(**pipeline_data.model_dump(mode="json"))


@router.get("/get_all_pipelines", name="get all pipelines")
async def get_all_pipelines() -> List[SummaryPipelineDataResponse]:
    logger.info("received request to get all pipelines")
    pipelines: List[SummaryPipelineDataResponse] = []
    async for pipeline in pipelines_collection.find():
        pipelines.append(SummaryPipelineDataResponse(**pipeline))
    return pipelines

class DeletePipelineResponse(BaseModel):
    pipeline_id: str
    message: str

@router.delete("/delete_pipeline/{pipeline_id}", name="delete pipeline")
async def delete_pipeline(pipeline_id: str) -> DeletePipelineResponse:
    logger.info("received request to delete pipeline")
    pipeline_data: Optional[Dict[str, Any]] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    path_id = None
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    logger.info(f"deleting pipeline with id: {pipeline_id}")
    result = await pipelines_collection.delete_one({"_id": ObjectId(pipeline_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete pipeline")
    logger.info(f"pipeline deleted successfully with id: {pipeline_id}")
    # delete temp directory
    path_id = pipeline_data.get('path_id', None)
    if path_id:
        temp_dir = config.get('output.temp_directory', 'temp')
        shutil.rmtree(os.path.join(temp_dir, path_id))
        logger.info(f"temp directory deleted successfully with id: {path_id}")
    else:
        logger.info(f"no temp directory found for pipeline with id: {pipeline_id}")
    return DeletePipelineResponse(pipeline_id=pipeline_id, message="Pipeline deleted successfully", path_id=path_id)

@router.get("/get_pipeline_details/{pipeline_id}", name="get pipeline details")
async def get_pipeline_details(pipeline_id: str) -> PipelineData:
    logger.info("received request to get pipeline details")
    pipeline_data: Optional[Dict[str, Any]] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return PipelineData(**pipeline_data)

class PipelineStageDetails(BaseModel):
    stage: str
    status: str
    next_stage: str
    previous_stage: str
    stage_statistics: PipelineStageStatistics

@router.get("/get_pipeline_stage_details/{pipeline_id}", name="get pipeline stage details")
async def get_pipeline_stage_details(pipeline_id: str) -> PipelineStageDetails:
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    next_stage = get_next_stage(pipeline_data.current_stage)
    previous_stage = get_previous_stage(pipeline_data.current_stage)
    current_stage_statistics = pipeline_data.stage_statistics.get(pipeline_data.current_stage, None)

    return PipelineStageDetails(stage=pipeline_data.current_stage, 
                                status=pipeline_data.status, next_stage=next_stage,
                                previous_stage=previous_stage,
                                stage_statistics=current_stage_statistics.model_dump(mode="json"))

@router.get("/view_pipeline_images/{pipeline_id}", name="view pipeline images")
async def view_pipeline_images(pipeline_id: str) -> List[ImageMetadata]:
    logger.info("received request to view pipeline images")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    return pipeline_data.images_metadata

@router.post("/add_pipeline_image/{pipeline_id}", name="add pipeline image")
async def add_pipeline_image(pipeline_id: str, image: UploadFile, 
                             text_context: Optional[str] = None,
                             label: Optional[bool] = False) -> ImageMetadata:
    logger.info("received request to add pipeline image")
    
    # retreive pipeline data
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    
    # validate if image is valid
    if not image.filename.endswith((".png", ".jpg", ".jpeg", ".gif")):
        raise HTTPException(status_code=400, detail="Invalid image type must be a PNG, JPG, or JPEG file")
    
    # save image to path specified by pipeline_id
    path_id = pipeline_data.path_id
    if not path_id:
        raise HTTPException(status_code=500, 
                            detail="Path ID not found for this pipeline you will have to create a new pipeline object to continue")
    image_path = os.path.join(path_id, "images", image.filename)
    with open(image_path, 'wb') as f:
        f.write(image.file.read())
    
    # create image metadata object
    image_metadata = ImageMetadata()
    image_metadata.filename = image.filename
    image_metadata.filepath = image_path
    image_metadata.page_number = 1
    image_metadata.width = image.size[0]
    image_metadata.height = image.size[1]
    image_metadata.format = image.content_type.split("/")[1]
    image_metadata.mode = "RGB"
    image_metadata.size_bytes = len(image.file.read())
    image_metadata.text_context = text_context or ""
    image_metadata.xref = None
    image_metadata.index_on_page = 0

    # if label is true, generate label and description
    if label:
        labeler = ImageLabeler(config.openai_api_key, config.get_prompts_directory())
        image_metadata = labeler.label_images_batch([image_metadata])
    
    # add image metadata to pipeline data
    pipeline_data.images_metadata.append(image_metadata)
    pipeline_data_json: Dict[str, Any] = pipeline_data.model_dump(mode="json")
    
    # update database with new image metadata
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"images_metadata": pipeline_data_json["images_metadata"]}}
    )
    return image_metadata

class UpdatePipelineImageMetadataRequest(BaseModel):
    index: int
    filename: Optional[str] = None
    text_context: Optional[str] = None
    label: Optional[bool] = False
    description: Optional[str] = None
    relevance_score: Optional[float] = None
    image_type: Optional[str] = None
    key_elements: Optional[List[str]] = None
    ai_relevance: Optional[str] = None

def clean_dict(dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    helper function to clean a dictionary of None values for updating object
    """
    return {k: v for k, v in dict.items() if v is not None}

@router.put("/update_pipeline_image_metadata/{pipeline_id}", name="update pipeline image metadata")
async def update_pipeline_image_metadata(pipeline_id: str, request: UpdatePipelineImageMetadataRequest) -> ImageMetadata:
    logger.info("received request to update pipeline image metadata")
    # retreive pipeline data
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    image_metadata: Dict[str, Any] = pipeline_data.get("images_metadata", [])[request.index]
    if not image_metadata:
        raise HTTPException(status_code=404, detail="Image metadata not found")
    request_dict: Dict[str, Any] = request.model_dump(mode="json")
    request_dict.pop("index", None)
    request_dict = clean_dict(request_dict)
    image_metadata.update(request_dict)
    # update image metadata
    if len(pipeline_data["images_metadata"]) > request.index:
        pipeline_data["images_metadata"][request.index] = image_metadata
    else:
        pipeline_data["images_metadata"].append(image_metadata)
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"images_metadata": pipeline_data["images_metadata"]}}
    )
    # create response object
    response = ImageMetadata(**image_metadata)
    return response

class DeletePipelineImageResponse(BaseModel):
    pipeline_id: str
    filename: str
    message: str
    path_id: Optional[str] = None

@router.delete("/delete_pipeline_image/{pipeline_id}", name="delete pipeline image")
async def delete_pipeline_image(pipeline_id: str, index: int) -> DeletePipelineImageResponse:
    logger.info("received request to delete pipeline image")
    # retreive pipeline data
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    image_metadata = pipeline_data.images_metadata.pop(index)
    pipeline_data_json: Dict[str, Any] = pipeline_data.model_dump(mode="json")
    # update database with new image metadata
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"images_metadata": pipeline_data_json["images_metadata"]}}
    )
    # delete image file
    if image_metadata.filepath:
        os.remove(image_metadata.filepath)
    # create response object
    response = DeletePipelineImageResponse(pipeline_id=pipeline_id, 
                                           message=f"Image {image_metadata.filename} deleted successfully",
                                           filename=image_metadata.filename,
                                           path_id=pipeline_data.path_id)
    return response

class ParsedContentDataMinimal(BaseModel):
    title: Optional[str] = None
    total_pages: Optional[int] = None
    num_sections: Optional[int] = None
    metadata: Optional[ParsedContentMetadata] = None

@router.get("/get_pipeline_parsed_content_info/{pipeline_id}", name="get pipeline parsed content info")
async def get_pipeline_parsed_content_info(pipeline_id: str) -> ParsedContentDataMinimal:
    logger.info("received request to get pipeline parsed content info")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    return ParsedContentDataMinimal(title=pipeline_data.parsed_content.title,
                                    total_pages=pipeline_data.parsed_content.total_pages,
                                    num_sections=len(pipeline_data.parsed_content.sections),
                                    metadata=pipeline_data.parsed_content.metadata)


@router.get("/get_pipeline_sections/{pipeline_id}", name="get pipeline sections")
async def get_pipeline_sections(pipeline_id: str) -> List[ParsedContentSection]:
    logger.info("received request to get pipeline sections")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    return pipeline_data.parsed_content.sections

@router.post("/add_pipeline_section/{pipeline_id}", name="add pipeline section")
async def add_pipeline_section(pipeline_id: str, section: ParsedContentSection) -> ParsedContentSection:
    logger.info("received request to add pipeline section")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    pipeline_data.parsed_content.sections.append(section)
    pipeline_data_json: Dict[str, Any] = pipeline_data.model_dump(mode="json")
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"parsed_content": pipeline_data_json["parsed_content"]}}
    )
    return section

@router.put("/update_pipeline_section/{pipeline_id}", name="update pipeline section")
async def update_pipeline_section(pipeline_id: str, index: int, section: ParsedContentSection) -> ParsedContentSection:
    logger.info("received request to update pipeline section")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    section_data: Dict[str, Any] = pipeline_data.get("parsed_content", {}).get("sections", [])[index]
    input_section: Dict[str, Any] = section.model_dump(mode="json")
    input_section = clean_dict(input_section)
    section_data.update(input_section)
    if len(pipeline_data["parsed_content"]["sections"]) > index:
        pipeline_data["parsed_content"]["sections"][index] = section_data
    else:
        pipeline_data["parsed_content"]["sections"].append(section_data)
    pipeline_data_json: Dict[str, Any] = pipeline_data.model_dump(mode="json")
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"parsed_content": pipeline_data_json["parsed_content"]}}
    )
    return ParsedContentSection(**section_data)

class DeletePipelineSectionResponse(BaseModel):
    pipeline_id: str
    index: int
    message: str
    title: Optional[str] = None

@router.delete("/delete_pipeline_section/{pipeline_id}", name="delete pipeline section")
async def delete_pipeline_section(pipeline_id: str, index: int) -> DeletePipelineSectionResponse:
    logger.info("received request to delete pipeline section")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    section_data = pipeline_data["parsed_content"]["sections"].pop(index)
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"parsed_content": pipeline_data["parsed_content"]}}
    )
    return DeletePipelineSectionResponse(pipeline_id=pipeline_id,
                                         index=index,
                                         message=f"Section {section_data["title"]} deleted successfully",
                                         title=section_data["title"])


class CreateVideoOutlineRequest(BaseModel):
    skip_stock: bool = False
    target_segments: int = 7
    segment_duration: int = 45

@router.post("/process_content/{pipeline_id}", name="process context")
async def process_content(pipeline_id: str, request: CreateVideoOutlineRequest):
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.IN_PROGRESS)
    # check if openai api key is set
    config = get_config()
    if not config.openai_api_key:
        logger.error("openai api key required")
        pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.FAILED)
        pipelines_collection.update_one(
            {"_id": ObjectId(pipeline_id)},
            {"$set": pipeline_data.model_dump(mode="json")}
        )
        raise HTTPException(status_code=500, detail="OpenAI API key not set")
    # check if parsed content is set
    if not pipeline_data.parsed_content:
        logger.error("parsed content not found in pipeline data")
        pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.FAILED)
        await pipelines_collection.update_one(
            {"_id": ObjectId(pipeline_id)},
            {"$set": pipeline_data.model_dump(mode="json")}
        )
        raise HTTPException(status_code=500, detail="Parsed content not found")
    # process context
    pdf_content = pipeline_data.parsed_content
    images_metadata = pipeline_data.images_metadata or []
    logger.info(f"loaded {len(pdf_content['sections'])} sections and {len(images_metadata)} images")
    # process context into chunks
    logger.info("processing context into chunks")
    all_content = ""
    for section in pdf_content.sections:
        all_content += section.content
    prompts_dir = config.get_prompts_directory()
    chunk_length = config.get('content.chunk_length', 4000)

    context_processor = ContextProcessor(
            all_content,
            config.openai_api_key,
            pdf_content.title,
            chunk_length=chunk_length,
            split_by='\n',
            prompts_dir=prompts_dir
        )
    chunks: List[ContextChunk] = context_processor.get_chunks()
    pipeline_data.chunks = chunks
    # store context processor information
    pipeline_data.context_processor_info = ContextProcessorInfo(
        document_title=pdf_content.title,
        chunk_length=chunk_length,
        split_by='\n',
        total_chunks=len(chunks),
        total_content_length=len(all_content)
    )
    logger.info(f"stored context processor information with total chunks: {len(chunks)} and total content length: {len(all_content)}")
    # create video outline
    logger.info("creating video outline")
    analyzer = ContentAnalyzer(
        api_key=config.openai_api_key,
        target_segments=request.target_segments,
        segment_duration=request.segment_duration,
        prompts_dir=prompts_dir
    )
    outline: VideoOutline = analyzer.analyze_content(
        document_title=pdf_content.title,
        chunks=chunks,
        images_metadata=images_metadata
    )
    logger.info("fetching stock images")
    stock_images_dir = os.path.join(config.get('output.temp_directory', 'temp'), pipeline_data.path_id, 'images', 'stock_images')
    fetcher = StockImageFetcher(config.unsplash_access_key, 
                                config.pexels_api_key, output_dir=stock_images_dir)
    availability = fetcher.is_available()
    if any(availability.values()):
        preferred = config.get('images.preferred_stock_provider', 'unsplash')
        outline.segments = fetcher.fetch_for_segments(outline.segments, preferred)
    else:
        logger.info("no stock image api keys available")
    # update pipeline data
    pipeline_data.video_outline = outline
    pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.COMPLETED)
    # save pipeline data
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": pipeline_data.model_dump(mode="json")}
    )

@router.get("/get_pipeline_context_chunks/{pipeline_id}", name="get pipeline context chunks")
async def get_pipeline_context_chunks(pipeline_id: str) -> List[ContextChunk]:
    logger.info("received request to get pipeline context chunks")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)    
    return pipeline_data.chunks

@router.get("/get_pipeline_video_outline/{pipeline_id}", name="get pipeline video outline")
async def get_pipeline_video_outline(pipeline_id: str) -> VideoOutline:
    logger.info("received request to get pipeline video outline")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    return pipeline_data.video_outline

@router.get("/get_pipeline_video_outline_segments/{pipeline_id}", name="get pipeline video outline segments")
async def get_pipeline_video_outline_segments(pipeline_id: str) -> List[VideoSegment]:
    logger.info("received request to get pipeline video outline segments")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    return pipeline_data.video_outline.segments

@router.post("/add_pipeline_video_outline_segment/{pipeline_id}", name="add pipeline video outline segment")
async def add_pipeline_video_outline_segment(pipeline_id: str, segment: VideoSegment) -> VideoSegment:
    logger.info("received request to add pipeline video outline segment")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    pipeline_data.video_outline.segments.append(segment)
    pipeline_data_json: Dict[str, Any] = pipeline_data.model_dump(mode="json")
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"video_outline": pipeline_data_json["video_outline"]}}
    )
    return VideoSegment(**segment)

@router.put("/update_pipeline_video_outline_segment/{pipeline_id}", name="update pipeline video outline segment")
async def update_pipeline_video_outline_segment(pipeline_id: str, index: int, segment: VideoSegment) -> VideoSegment:
    logger.info("received request to update pipeline video outline segment")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    pipeline_data.video_outline.segments[index] = segment
    
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"video_outline": pipeline_data.model_dump(mode="json")["video_outline"]}}
    )
    return VideoSegment(**segment)

@router.delete("/delete_pipeline_video_outline_segment/{pipeline_id}", name="delete pipeline video outline segment")
async def delete_pipeline_video_outline_segment(pipeline_id: str, index: int) -> VideoSegment:
    logger.info("received request to delete pipeline video outline segment")
    pipeline_data: Union[Dict[str, Any], None] = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline_data: PipelineData = PipelineData(**pipeline_data)
    segment = pipeline_data.video_outline.segments.pop(index)
    await pipelines_collection.update_one(
        {"_id": ObjectId(pipeline_id)},
        {"$set": {"video_outline": pipeline_data.model_dump(mode="json")["video_outline"]}}
    )
    return VideoSegment(**segment)

async def generate_images_for_pipeline_segments(pipeline_id: str, indexes: List[str]):
    pass

# class GenerateScriptsAndVoiceoversRequest(BaseModel):
#     provider: Optional[str] = None

# @router.post("/generate_scripts_and_voiceovers/{pipeline_id}")
# async def generate_scripts_and_voiceovers_route(pipeline_id: str, 
#                                                 request: GenerateScriptsAndVoiceoversRequest) -> PipelineData:
#     pipeline_data = generate_scripts_and_voiceovers(pipeline_id, request.provider)
#     return pipeline_data

# class GenerateVideoRequest(BaseModel):
#     output_path: Optional[str] = None

# @router.post("/generate_video/{pipeline_id}")
# async def generate_video_route(pipeline_id: str, 
#                                 request: GenerateVideoRequest) -> PipelineData:
#     pipeline_data = generate_video(pipeline_id, request.output_path)
#     return pipeline_data

# class RunFullPipelineRequest(BaseModel):
#     pdf_path: str
#     extract_images: bool = True
#     skip_stock: bool = False
#     target_segments: int = 7
#     segment_duration: int = 45
#     provider: Optional[str] = None
#     output_path: Optional[str] = None

# @router.post("/run_full_pipeline")
# async def run_full_pipeline(request: RunFullPipelineRequest) -> PipelineData:
#     pipeline_data = parse_document(request.pdf_path, request.extract_images)
#     pipeline_data = create_video_outline(pipeline_data.id, request.skip_stock, request.target_segments, request.segment_duration)
#     pipeline_data = generate_scripts_and_voiceovers(pipeline_data.id, request.provider)
#     pipeline_data = generate_video(pipeline_data.id, request.output_path)
#     return pipeline_data

# @router.post("/create")
# async def create_pipeline(request: VideoGenerationRequest):
#     return {"message": "Pipeline created successfully"}

# @router.get("/get")
# async def get_pipeline(pipeline_id: str):
#     return {"message": "Pipeline retrieved successfully"}

# @router.put("/update")
# def update_pipeline(pipeline_id: str, request: VideoGenerationRequest):
#     return {"message": "Pipeline updated successfully"}

# @router.delete("/delete")
# def delete_pipeline(pipeline_id: str):
#     return {"message": "Pipeline deleted successfully"}

# @router.get("/list")
# def list_pipelines():
#     return {"message": "Pipelines listed successfully"}

# def get_all_active_pipelines():
#     pass

# def get_all_fonts():
#     pass

# def pause_pipeline(pipeline_id: str):
#     pass

# def resume_pipeline(pipeline_id: str):
#     pass

# def cancel_pipeline(pipeline_id: str):
#     pass

# def get_pipeline_status(pipeline_id: str):
#     pass

# def get_pipeline_progress(pipeline_id: str):
#     pass

# def redo_pipeline_phase(pipeline_id: str, phase: str):
#     pass

# def get_pipeline_logs(pipeline_id: str):
#     pass

# def get_pipeline_errors(pipeline_id: str):
#     pass

# def get_pipeline_warnings(pipeline_id: str):
#     pass

# def get_pipeline_info(pipeline_id: str):
#     pass