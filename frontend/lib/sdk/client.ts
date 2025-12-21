import { ContextChunk, CreateVideoOutlineRequest, DeletePipelineImageResponse, DeletePipelineResponse, DeletePipelineSectionResponse, ImageMetadata,
        ParsedContentDataMinimal, ParsedContentSection, PipelineData, PipelineReviewRequest, PipelineStageDetails,
        ScriptData,
        StartPipelineRequest, SummaryPipelineDataResponse, UpdatePipelineImageMetadataRequest, 
        VideoGenerationRequest, 
        VideoOutline, VideoSegment,
        VideoSegmentBackground} from "./types";

export class VidinieAPIClient {
    private baseUrl: string;
    private apiKey: string;

    constructor(baseUrl: string, apiKey: string) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    async setAPIKey(apiKey: string) {
        this.apiKey = apiKey;
    }

    async getAPIKey() {
        return this.apiKey;
    }

    async getBaseUrl() {
        return this.baseUrl;
    }

    async getClient() {
        return this;
    }

    async startPipelineWithFile(
        name: string,
        description: string,
        tags: string[],
        projects: string[],
        file: File
    ): Promise<SummaryPipelineDataResponse> {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('description', description);
        tags.forEach(tag => formData.append('tags', tag));
        projects.forEach(project => formData.append('projects', project));
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/pipelines/start_pipeline_with_file`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                // Note: Do not set Content-Type when using FormData; browser will set the correct boundary.
            },
            body: formData
        });
        return response.json() as Promise<SummaryPipelineDataResponse>;
    }
    async startPipelieWithUrl(request: StartPipelineRequest): Promise<SummaryPipelineDataResponse> {
        const response = await fetch(`${this.baseUrl}/pipelines/start_pipeline_with_url`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request)
        });
        return response.json() as Promise<SummaryPipelineDataResponse>;
    }

    async getAllPipelines(): Promise<SummaryPipelineDataResponse[]> {
        const response = await fetch(`${this.baseUrl}/pipelines/get_all_pipelines`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<SummaryPipelineDataResponse[]>;
    }

    async deletePipeline(pipelineId: string): Promise<DeletePipelineResponse> {
        const response = await fetch(`${this.baseUrl}/pipelines/delete_pipeline/${pipelineId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<DeletePipelineResponse>;
    }

    async getPipelineDetails(pipelineId: string): Promise<PipelineData> {
        const response = await fetch(`${this.baseUrl}/pipelines/get_pipeline_details/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<PipelineData>;
    }

    async getPipelineStageDetails(pipelineId: string): Promise<PipelineStageDetails> {
        const response = await fetch(`${this.baseUrl}/pipelines/get_pipeline_stage_details/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<PipelineStageDetails>;
    }

    async viewPipelineImages(pipelineId: string): Promise<ImageMetadata[]> {
        const response = await fetch(`${this.baseUrl}/pipelines/view_pipeline_images/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<ImageMetadata[]>;
    }

    async addPipelineImage(
        pipelineId: string,
        image: File,
        textContext: string = "",
        label: boolean = false
    ): Promise<ImageMetadata> {
        const formData = new FormData();
        formData.append('image', image);
        formData.append('text_context', textContext);
        formData.append('label', String(label));

        const response = await fetch(`${this.baseUrl}/pipelines/add_pipeline_image/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
            },
            body: formData
        });
        return response.json() as Promise<ImageMetadata>;
    }

    async updatePipelineImageMetadata(pipelineId: string, request: UpdatePipelineImageMetadataRequest): Promise<ImageMetadata> {
        const response = await fetch(`${this.baseUrl}/pipelines/update_pipeline_image_metadata/${pipelineId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(request)
        });

        return response.json() as Promise<ImageMetadata>
    }

    async deletePipelineImage(pipelineId: string, index: number): Promise<DeletePipelineImageResponse> {
        const response = await fetch(`${this.baseUrl}/pipelines/delete_pipeline_image/${pipelineId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<DeletePipelineImageResponse>;
    }

    async getPipelineParsedContentInfo(pipelineId: string): Promise<ParsedContentDataMinimal> {
        const response = await fetch(`${this.baseUrl}/pipelines/get_pipeline_parsed_content_info/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<ParsedContentDataMinimal>;
    }

    async getPipelineSections(pipelineId: string): Promise<ParsedContentSection[]> {
        const response = await fetch(`${this.baseUrl}/pipelines/get_pipeline_sections/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<ParsedContentSection[]>;
    }

    async addPipelineSection(pipelineId: string, section: ParsedContentSection): Promise<ParsedContentSection> {
        const response = await fetch(`${this.baseUrl}/pipelines/add_pipeline_section/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(section)
        });
        return response.json() as Promise<ParsedContentSection>;
    }

    async updatePipelineSection(pipelineId: string, index: number, section: ParsedContentSection): Promise<ParsedContentSection> {
        const response = await fetch(`${this.baseUrl}/pipelines/update_pipeline_section/${pipelineId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(section)
        });
        return response.json() as Promise<ParsedContentSection>;
    }

    async deletePipelineSection(pipelineId: string, index: number): Promise<DeletePipelineSectionResponse> {
        const response = await fetch(`${this.baseUrl}/pipelines/delete_pipeline_section/${pipelineId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });

        return response.json() as Promise<DeletePipelineSectionResponse>;
    }

    async processContent(pipelineId: string, request: CreateVideoOutlineRequest): Promise<PipelineData> {
        const response = await fetch(`${this.baseUrl}/pipelines/process_content/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(request)
        });
        return response.json() as Promise<PipelineData>;
    }   

    async getPipelineContextChunks(pipelineId: string): Promise<ContextChunk[]> {
        const response = await fetch(`${this.baseUrl}/pipelines/get_pipeline_context_chunks/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<ContextChunk[]>;
    }

    async getPipelineVideoOutline(pipelineId: string): Promise<VideoOutline> {
        const response = await fetch(`${this.baseUrl}/pipelines/get_pipeline_video_outline/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<VideoOutline>;
    }

    async getPipelineVideoOutlineSegments(pipelineId: string): Promise<VideoSegment[]> {
        const response = await fetch(`${this.baseUrl}/pipelines/get_pipeline_video_outline_segments/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<VideoSegment[]>;
    }

    async addPipelineVideoOutlineSegment(pipelineId: string, segment: VideoSegment): Promise<VideoSegment> {
        const response = await fetch(`${this.baseUrl}/pipelines/add_pipeline_video_outline_segment/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(segment)
        });
        return response.json() as Promise<VideoSegment>;
    }

    async updatePipelineVideoOutlineSegment(pipelineId: string, index: number, segment: VideoSegment): Promise<VideoSegment> {
        const response = await fetch(`${this.baseUrl}/pipelines/update_pipeline_video_outline_segment/${pipelineId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(segment)
        });
        return response.json() as Promise<VideoSegment>;
    }

    async deletePipelineVideoOutlineSegment(pipelineId: string, index: number): Promise<VideoSegment> {
        const response = await fetch(`${this.baseUrl}/pipelines/delete_pipeline_video_outline_segment/${pipelineId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.json() as Promise<VideoSegment>;
    }

    async generateImagesForPipelineSegments(pipelineId: string, indexes: number[]): Promise<VideoSegment[]> {
        const response = await fetch(`${this.baseUrl}/pipelines/generate_images_for_pipeline_segments/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(indexes)
        });
        return response.json() as Promise<VideoSegment[]>;
    }

    async generateScriptsAndVoiceovers(pipelineId: string, provider: string = 'elevenlabs'): Promise<PipelineData> {
        const response = await fetch(`${this.baseUrl}/pipelines/generate_scripts_and_voiceovers/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({ provider })
        });
        return response.json() as Promise<PipelineData>;
    }

    async viewPipelineScriptData(pipelineId: string): Promise<ScriptData> {
        const response = await fetch(`${this.baseUrl}/pipelines/view_pipeline_script_data/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }   
        });
        return response.json() as Promise<ScriptData>;
    }

    async updatePipelineScriptData(pipelineId: string, scriptData: ScriptData): Promise<ScriptData> {
        const response = await fetch(`${this.baseUrl}/pipelines/update_pipeline_script_data/${pipelineId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(scriptData)
        });
        return response.json() as Promise<ScriptData>;
    }

    async generateVideo(pipelineId: string, request: VideoGenerationRequest): Promise<PipelineData> {
        const response = await fetch(`${this.baseUrl}/pipelines/generate_video/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(request)
        });
        return response.json() as Promise<PipelineData>;
    }

    async updateVideoSegmentBackground(pipelineId: string, index: number, background: VideoSegmentBackground): Promise<VideoOutline> {
        const response = await fetch(`${this.baseUrl}/pipelines/update_video_segment_background/${pipelineId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(background)
        });
        return response.json() as Promise<VideoOutline>;
    }

    async regenerateAudioForPipelineSegments(pipelineId: string, provider: string = 'elevenlabs'): Promise<PipelineData> {
        const response = await fetch(`${this.baseUrl}/pipelines/regenerate_audio_for_pipeline_segments/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`   
            },
            body: JSON.stringify({ provider })
        });
        return response.json() as Promise<PipelineData>;
    }

    async downloadVideo(pipelineId: string): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/pipelines/download_video/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response.blob() as Promise<Blob>;
    }

    async streamVideo(pipelineId: string): Promise<Response> {
        const response = await fetch(`${this.baseUrl}/pipelines/stream_video/${pipelineId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        return response;
    }

    async addPipelineReview(pipelineId: string, request: PipelineReviewRequest): Promise<PipelineData> {
        const response = await fetch(`${this.baseUrl}/pipelines/add_pipeline_review/${pipelineId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(request)
        });
        return response.json() as Promise<PipelineData>;
    }
}

// create a singleton instance of the client
const client = new VidinieAPIClient(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
     process.env.NEXT_PUBLIC_API_KEY || '');

export default client;
