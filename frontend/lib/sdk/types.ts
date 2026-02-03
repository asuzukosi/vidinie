export type AudioVoice = 
    | "Narrative Expressive Male"
    | "Fun Vibrant Female"
    | "Calm Narrative Male"
    | "Calm Soothing Female"
    | "Soothing British Male"
    | "Expressive Professional Male";

export interface CreateVideoPipelineRequest {
    url?: string;
    file?: File;
    name: string;
    instructions: string;
    voice: AudioVoice;
}

export enum SourceType {
    PDF = 'pdf',
    HTML = 'html',
}
export interface VideoPipelineSummary {
    id: string;
    name: string;
    instructions: string;
    voice: string;
    updated_at: string;
    created_at: string;
    source_path: string;
    source_type: SourceType;
}

export interface DeleteVideoPipelineResponse {
    video_pipeline_id: string;
    message: string;
}

export interface ContentSection {
    title: string;
    content: string;
    level: number;
}

export interface ContentMetadata {
    title: string;
    creator: string;
    producer: string;
    creation_date: string;
    modification_date: string;
}

export interface ParsedContent {
    title: string;
    total_pages: number;
    sections: ContentSection[];
    metadata: ContentMetadata;
}

export interface ImageMetadata {
    filename: string;
    filepath: string;
    page_number?: number;
    width?: number;
    height?: number;
    format?: string;
    mode?: string;
    size_bytes?: number;
    text_context?: string;
    xref?: number;
    index_on_page?: number;
    label?: string;
    description?: string;
    image_type?: string;
    key_elements?: string[];
    relevance?: string;
}

export enum BackgroundType {
    GRADIENT = 'gradient',
    SOLID = 'solid',
    IMAGE = 'image',
}

export enum ImageSource {
    PDF = 'pdf',
    STOCK = 'stock',
    AI_GENERATED = 'ai_generated',
    USER_UPLOADED = 'user_uploaded',
}

export interface SegmentImage {
    source: ImageSource;
    query: string;
    path: string;
}

export interface VideoSegment {
    title: string;
    purpose: string;
    content: string;
    key_points: string[];
    visual_keywords: string[];
    script: string;
    word_count: number;
    duration: number;
    image: SegmentImage;
    transition_to: string;
    transition_type: string;
    audio_file: string;
    audio_duration: number;
}

export interface VideoOutline {
    title: string;
    total_segments: number;
    estimated_duration: number;
    segments: VideoSegment[];
}

export interface VideoPipelineScript {
    title: string;
    total_segments: number;
    segments: VideoSegment[];
    full_script: string;
}

export enum VideoPipelineStage {
    INITIALIZED = 'initialized',
    DOCUMENT_PROCESSING = 'document_processing',
    IMAGE_PROCESSING = 'image_processing',
    CONTENT_ANALYSIS = 'content_analysis',
    SCRIPT_GENERATION = 'script_generation',
    VIDEO_GENERATION = 'video_generation',
    REVIEW_AND_FEEDBACK = 'review_and_feedback',
}

export enum VideoPipelineStatus {
    PENDING = 'pending',
    IN_PROGRESS = 'in_progress',
    COMPLETED = 'completed',
    FAILED = 'failed',
}

export interface VideoPipelineStageStatistics {
    start_time: string;
    end_time: string;
    duration: number;
    status: VideoPipelineStatus;
}


export interface VideoPipelineStageStatisticsManager {
    [VideoPipelineStage.DOCUMENT_PROCESSING]?: VideoPipelineStageStatistics;
    [VideoPipelineStage.IMAGE_PROCESSING]?: VideoPipelineStageStatistics;
    [VideoPipelineStage.CONTENT_ANALYSIS]?: VideoPipelineStageStatistics;
    [VideoPipelineStage.SCRIPT_GENERATION]?: VideoPipelineStageStatistics;
    [VideoPipelineStage.VIDEO_GENERATION]?: VideoPipelineStageStatistics;
}

export interface VideoPipeline {
    id: string;
    name: string;
    instructions: string;
    voice: string;
    updated_at: string;
    created_at: string;
    source_path: string;
    source_type: SourceType;
    parsed_content?: ParsedContent;
    images_metadata?: ImageMetadata[];
    content?: string;
    video_outline?: VideoOutline;
    script_data?: VideoPipelineScript;
    full_audio_path?: string;
    full_audio_duration?: number;
    video_path?: string;
    output_path?: string;
    current_stage?: VideoPipelineStage;
    status?: VideoPipelineStatus;
    // flat status fields for each stage
    initialized_status?: VideoPipelineStatus;
    document_processing_status?: VideoPipelineStatus;
    image_processing_status?: VideoPipelineStatus;
    content_analysis_status?: VideoPipelineStatus;
    script_generation_status?: VideoPipelineStatus;
    video_generation_status?: VideoPipelineStatus;
    rating?: number;
    feedback?: string;
    stage_statistics?: VideoPipelineStageStatisticsManager;
}

export interface VideoPipelineStageDetails {
    stage: VideoPipelineStage;
    status: VideoPipelineStatus;
    next_stage: VideoPipelineStage;
    previous_stage: VideoPipelineStage;
}

export interface UpdateVideoPipelineImageRequest {
    index: number;
    filename: string;
    text_context: string;
    label: boolean;
    description: string;
    image_type: string;
    key_elements: string[];
    relevance: string;
}

export interface DeleteVideoPipelineImageResponse {
    video_pipeline_id: string;
    filename: string;
    message: string;
}

export interface VideoPipelineContentMinimal {
    title: string;
    total_pages?: number;
    num_sections?: number;
    metadata?: ContentMetadata;
}

export interface DeleteVideoPipelineSectionResponse {
    video_pipeline_id: string;
    index: number;
    message: string;
    title?: string;
}

export interface CreateVideoOutlineRequest {
    skip_stock: boolean;
    target_segments: number;
    segment_duration: number;
}

export enum VideoResolution {
    RESOLUTION_1080P = '1080P',
    RESOLUTION_720P = '720P',
    RESOLUTION_480P = '480P',
}

export interface GenerateVideoPipelineRequest {
    title: string;
    subtitle: string;
    resolution: VideoResolution;
    fps: number;
    title_duration: number;
    end_duration: number;
    transition_duration: number;
}

export interface VideoPipelineReviewRequest {
    rating?: number;
    feedback?: string;
}


export interface VideoPipelineProcessingStage {
    id: VideoPipelineStage;
    title: string;
    description: string;
    completed: boolean;
    actionLabel: string;
    start_time?: string;
    end_time?: string;
    duration?: number;
}