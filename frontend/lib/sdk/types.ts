export interface CreateVideoPipelineRequest {
    url?: string;
    file?: File;
    name: string;
    description: string;
    tags: string[];
    projects: string[];
}

export enum SourceType {
    PDF = 'pdf',
    HTML = 'html',
}
export interface VideoPipelineSummary {
    id: string;
    name: string;
    description: string;
    tags: string[];
    projects: string[];
    updated_at: string;
    created_at: string;
    source_path: string;
    source_type: SourceType;
}

export interface DeleteVideoPipelineResponse {
    video_pipeline_id: string;
    message: string;
}

export interface VideoPipelineContentSection {
    title: string;
    content: string;
    level: number;
}

export interface VideoPipelineContentMetadata {
    title: string;
    creator: string;
    producer: string;
    creation_date: string;
    modification_date: string;
}

export interface VideoPipelineParsedContent {
    title: string;
    total_pages: number;
    sections: VideoPipelineContentSection[];
    metadata: VideoPipelineContentMetadata;
}

export interface VideoPipelineImageMetadata {
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
    relevance_score?: number;
    image_type?: string;
    key_elements?: string[];
    ai_relevance?: string;
}

export interface VideoPipelineContextChunk {
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

export interface VideoPipelineSegmentImage {
    source: ImageSource;
    query: string;
    path: string;
}

export interface VideoPipelineSegment {
    title: string;
    purpose: string;
    content: string;
    key_points: string[];
    visual_keywords: string[];
    script: string;
    word_count: number;
    duration: number;
    image: VideoPipelineSegmentImage;
    transition_to: string;
    transition_type: string;
    audio_file: string;
    audio_duration: number;
    voiceover_provider: string;
    background_colors: string[];
    background_type: BackgroundType;
    background_image_path: string;
}

export interface VideoPipelineOutline {
    title: string;
    total_segments: number;
    estimated_duration: number;
    segments: VideoPipelineSegment[];
}

export interface VideoPipelineScript {
    title: string;
    total_segments: number;
    segments: VideoPipelineSegment[];
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

// stage status tracking
export interface VideoPipelineStageStatuses {
    [VideoPipelineStage.INITIALIZED]?: VideoPipelineStatus;
    [VideoPipelineStage.DOCUMENT_PROCESSING]?: VideoPipelineStatus;
    [VideoPipelineStage.IMAGE_PROCESSING]?: VideoPipelineStatus;
    [VideoPipelineStage.CONTENT_ANALYSIS]?: VideoPipelineStatus;
    [VideoPipelineStage.SCRIPT_GENERATION]?: VideoPipelineStatus;
    [VideoPipelineStage.VIDEO_GENERATION]?: VideoPipelineStatus;
    [VideoPipelineStage.REVIEW_AND_FEEDBACK]?: VideoPipelineStatus;
}

export interface VideoPipeline {
    id: string;
    name: string;
    description: string;
    tags: string[];
    projects: string[];
    updated_at: string;
    created_at: string;
    source_path: string;
    source_type: SourceType;
    parsed_content?: VideoPipelineParsedContent;
    images_metadata?: VideoPipelineImageMetadata[];
    chunks?: VideoPipelineContextChunk[];
    video_outline?: VideoPipelineOutline;
    script_data?: VideoPipelineScript;
    full_audio_path?: string;
    full_audio_duration?: number;
    video_path?: string;
    output_path?: string;
    current_stage?: VideoPipelineStage;
    status?: VideoPipelineStatus;
    stage_statuses?: VideoPipelineStageStatuses;
    rating?: number;
    feedback?: string;
    stage_statistics?: VideoPipelineStageStatisticsManager;
}

export interface VideoPipelineStageDetails {
    stage: VideoPipelineStage;
    status: VideoPipelineStatus;
    next_stage: VideoPipelineStage;
    previous_stage: VideoPipelineStage;
    stage_statistics: VideoPipelineStageStatistics;
}

export interface UpdateVideoPipelineImageRequest {
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

export interface DeleteVideoPipelineImageResponse {
    video_pipeline_id: string;
    filename: string;
    message: string;
}

export interface VideoPipelineContentMinimal {
    title: string;
    total_pages?: number;
    num_sections?: number;
    metadata?: VideoPipelineContentMetadata;
}

export interface DeleteVideoPipelineSectionResponse {
    video_pipeline_id: string;
    index: number;
    message: string;
    title?: string;
}

export interface CreateVideoPipelineOutlineRequest {
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

export interface GenerateVideoPipelineRequest {
    title: string;
    subtitle: string;
    resolution: VideoResolution;
    fps: number;
    title_duration: number;
    end_duration: number;
    transition_duration: number;
    background_type: BackgroundType;
}

export interface VideoPipelineSegmentBackground {
    colors: string[];
    type: BackgroundType;
    image_path: string;
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

// authentication types
export interface LoginResponse {
    id: string;
    username: string;
    email: string;
    token: string;
    created_at: string;
    updated_at: string;
    is_verified: boolean;
    current_subscription?: string;
    profile_picture?: string | null;
    stripe_customer_id?: string | null;
}

export interface RegisterResponse {
    id: string;
    username: string;
    email: string;
    created_at: string;
    updated_at: string;
    is_verified: boolean;
    current_subscription?: string;
}

export interface User {
    id: string;
    username: string;
    email: string;
    created_at: string;
    updated_at: string;
    is_verified: boolean;
    current_subscription?: string;
    profile_picture?: string | null;
    stripe_customer_id?: string | null;
}

// payment Method Types
export interface PaymentMethodCard {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
}

export interface PaymentMethod {
    id: string;
    user_id: string;
    stripe_payment_method_id: string;
    type: string;
    card?: PaymentMethodCard | null;
    is_default: boolean;
    created_at: string;
    updated_at: string;
}

export interface CreatePaymentMethodRequest {
    stripe_payment_method_id: string;
    type?: string;
    card?: PaymentMethodCard | null;
    is_default?: boolean;
}

export interface UpdatePaymentMethodRequest {
    is_default?: boolean;
    card?: PaymentMethodCard | null;
}
