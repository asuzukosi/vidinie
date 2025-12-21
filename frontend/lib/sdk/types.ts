export interface StartPipelineRequest {
    url: string;
    name: string;
    description: string;
    tags: string[];
    projects: string[];
}

export enum SourceType {
    PDF = 'pdf',
    HTML = 'html',
}
export interface SummaryPipelineDataResponse {
    id: string;
    path_id: string;
    name: string;
    description: string;
    tags: string[];
    projects: string[];
    updated_at: string;
    created_at: string;
    source_path: string;
    source_type: SourceType;
}

export interface DeletePipelineResponse {
    pipeline_id: string;
    message: string;
}

export interface ParsedContentSection {
    title: string;
    content: string;
    level: number;
}

export interface ParsedContentMetadata {
    title: string;
    creator: string;
    producer: string;
    creation_date: string;
    modification_date: string;
}

export interface ParsedContent {
    title: string;
    total_pages: number;
    sections: ParsedContentSection[];
    metadata: ParsedContentMetadata;
}

export interface ImageMetadata {
    filename: string;
    filepath: string;
    page_number: number;
    width: number;
    height: number;
}

export interface ContextChunk {
    chunk: string;
    summary: string;
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
    voiceover_provider: string;
    background_colors: string[];
    background_type: BackgroundType;
    background_image_path: string;
}

export interface VideoOutline {
    title: string;
    total_segments: number;
    estimated_duration: number;
    segments: VideoSegment[];
}

export interface ScriptData {
    title: string;
    total_segments: number;
    segments: VideoSegment[];
    full_script: string;
}

export enum PipelineStage {
    INITIALIZED = 'initialized',
    DOCUMENT_PROCESSING = 'document_processing',
    IMAGE_PROCESSING = 'image_processing',
    CONTENT_ANALYSIS = 'content_analysis',
    SCRIPT_GENERATION = 'script_generation',
    VIDEO_GENERATION = 'video_generation',
}

export enum PipelineStatus {
    PENDING = 'pending',
    IN_PROGRESS = 'in_progress',
    COMPLETED = 'completed',
    FAILED = 'failed',
}

export interface PipelineStageStatistics {
    start_time: string;
    end_time: string;
    duration: number;
    status: PipelineStatus;
}

export interface PipelineData {
    id: string;
    path_id: string;
    name: string;
    description: string;
    tags: string[];
    projects: string[];
    updated_at: string;
    created_at: string;
    source_path: string;
    source_type: SourceType;
    parsed_content?: ParsedContent;
    images_metadata?: ImageMetadata[];
    chunks?: ContextChunk[];
    video_outline?: VideoOutline;
    script_data?: ScriptData;
    full_audio_path?: string;
    full_audio_duration?: number;
    video_path?: string;
    output_path?: string;
    current_stage?: PipelineStage;
    status?: PipelineStatus;
    rating?: number;
    feedback?: string;
}

export interface PipelineStageDetails {
    stage: PipelineStage;
    status: PipelineStatus;
    next_stage: PipelineStage;
    previous_stage: PipelineStage;
    stage_statistics: PipelineStageStatistics;
}

export interface UpdatePipelineImageMetadataRequest {
    index: number;
    filename: string;
    text_context: string;
    label: boolean;
    description: string;
    relevance_score: number;
    image_type: string;
    key_elements: string[];
    ai_relevance: string;
}

export interface DeletePipelineImageResponse {
    pipeline_id: string;
    filename: string;
    message: string;
    path_id: string;
}

export interface ParsedContentDataMinimal {
    title: string;
    total_pages?: number;
    num_sections?: number;
    metadata?: ParsedContentMetadata;
}

export interface DeletePipelineSectionResponse {
    pipeline_id: string;
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
    RESOLUTION_4K = '4K',
    RESOLUTION_1080P = '1080P',
    RESOLUTION_720P = '720P',
    RESOLUTION_480P = '480P',
}

export interface VideoGenerationRequest {
    title: string;
    subtitle: string;
    resolution: VideoResolution;
    fps: number;
    title_duration: number;
    end_duration: number;
    transition_duration: number;
    background_type: BackgroundType;
}

export interface VideoSegmentBackground {
    colors: string[];
    type: BackgroundType;
    image_path: string;
}

export interface PipelineReviewRequest {
    rating: number;
    feedback: string;
}


export interface PipelineProcessingStage {
    id: string;
    title: string;
    description: string;
    completed: boolean;
    actionLabel: string;
    actionHref: string;
}