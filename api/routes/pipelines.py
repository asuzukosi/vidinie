from fastapi import APIRouter
from pipeline.stage1_parsing import parse_document
from pipeline.stage2_content import create_video_outline
from pipeline.stage3_script import generate_scripts_and_voiceovers
from pipeline.stage4_video import generate_video
from core.pipeline_data import PipelineData
from pydantic import BaseModel
from typing import Optional


router = APIRouter(tags=["pipelines"])

class ParseDocumentRequest(BaseModel):
    pdf_path: str
    extract_images: bool = True

@router.post("/parse_document")
async def parse_document_route(request: ParseDocumentRequest) -> PipelineData:
    pipeline_data = parse_document(request.pdf_path, request.extract_images)
    return pipeline_data

class CreateVideoOutlineRequest(BaseModel):
    skip_stock: bool = False
    target_segments: int = 7
    segment_duration: int = 45

@router.post("/create_video_outline/{pipeline_id}")
async def create_video_outline_route(pipeline_id: str, 
                                    request: CreateVideoOutlineRequest) -> PipelineData:
    pipeline_data = create_video_outline(pipeline_id, request.skip_stock, request.target_segments, request.segment_duration)
    return pipeline_data

class GenerateScriptsAndVoiceoversRequest(BaseModel):
    provider: Optional[str] = None

@router.post("/generate_scripts_and_voiceovers/{pipeline_id}")
async def generate_scripts_and_voiceovers_route(pipeline_id: str, 
                                                request: GenerateScriptsAndVoiceoversRequest) -> PipelineData:
    pipeline_data = generate_scripts_and_voiceovers(pipeline_id, request.provider)
    return pipeline_data

class GenerateVideoRequest(BaseModel):
    output_path: Optional[str] = None

@router.post("/generate_video/{pipeline_id}")
async def generate_video_route(pipeline_id: str, 
                                request: GenerateVideoRequest) -> PipelineData:
    pipeline_data = generate_video(pipeline_id, request.output_path)
    return pipeline_data

class RunFullPipelineRequest(BaseModel):
    pdf_path: str
    extract_images: bool = True
    skip_stock: bool = False
    target_segments: int = 7
    segment_duration: int = 45
    provider: Optional[str] = None
    output_path: Optional[str] = None

@router.post("/run_full_pipeline")
async def run_full_pipeline(request: RunFullPipelineRequest) -> PipelineData:
    pipeline_data = parse_document(request.pdf_path, request.extract_images)
    pipeline_data = create_video_outline(pipeline_data.id, request.skip_stock, request.target_segments, request.segment_duration)
    pipeline_data = generate_scripts_and_voiceovers(pipeline_data.id, request.provider)
    pipeline_data = generate_video(pipeline_data.id, request.output_path)
    return pipeline_data

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