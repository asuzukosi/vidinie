import { CreateVideoOutlineRequest, DeleteVideoPipelineImageResponse, DeleteVideoPipelineResponse, DeleteVideoPipelineSectionResponse, ImageMetadata,
        ContentSection, VideoPipeline, VideoPipelineReviewRequest,
        CreateVideoPipelineRequest, VideoPipelineSummary,
        GenerateVideoPipelineRequest,
        VideoSegment} from "@/lib/sdk/types";
import { authClient } from "@/lib/auth-client";

export class VidinieAPIClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private async getTokenFromSession(): Promise<string | null> {
        try {
            // get jwt token from better-auth session
            const session = await authClient.getSession();
            if (session?.data?.session?.token) {
                return session.data.session.token;
            }
            return null;
        } catch (error) {
            console.error("error getting token from better-auth session:", error);
            return null;
        }
    }

    private async getAuthHeader(): Promise<string | null> {
        const token = await this.getTokenFromSession();
        return token ? `Bearer ${token}` : null;
    }

    private async getAuthHeaders(additionalHeaders: Record<string, string> = {}): Promise<Record<string, string>> {
        const authHeader = await this.getAuthHeader();
        if (!authHeader) {
            throw new Error('Not authenticated. Please log in.');
        }
        return {
            'Authorization': authHeader,
            ...additionalHeaders,
        };
    }

    private async handleResponse<T>(response: Response, operationName: string): Promise<T> {
        if (!response.ok) {
            let errorMessage = `Operation failed: ${operationName}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || errorData.message || errorMessage;
            } catch {
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }
        return await response.json() as T;
    }

    async getBaseUrl() {
        return this.baseUrl;
    }

    async getClient() {
        return this;
    }

    async createVideoPipelineFromFile(
        name: string,
        instructions: string,
        voice: string,
        file: File
    ): Promise<VideoPipelineSummary> {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('instructions', instructions);
        formData.append('voice', voice);
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/video-pipelines/from-file`, {
            method: 'POST',
            headers: await this.getAuthHeaders(),
            body: formData
        });
        return this.handleResponse<VideoPipelineSummary>(response, "Create video pipeline from file");
    }

    async createVideoPipelineFromUrl(request: CreateVideoPipelineRequest): Promise<VideoPipelineSummary> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/from-url`, {
            method: 'POST',
            headers: await this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipelineSummary>(response, "Create video pipeline from URL");
    }

    async getAllVideoPipelines(): Promise<VideoPipelineSummary[]> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/`, {
            method: 'GET',
            headers: await this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipelineSummary[]>(response, "Get all video pipelines");
    }

    async getVideoPipelineDetails(videoPipelineId: string): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}`, {
            method: 'GET',
            headers: await this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipeline>(response, "Get video pipeline details");
    }

    async deleteVideoPipeline(videoPipelineId: string): Promise<DeleteVideoPipelineResponse> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}`, {
            method: 'DELETE',
            headers: await this.getAuthHeaders()
        });
        return this.handleResponse<DeleteVideoPipelineResponse>(response, "Delete video pipeline");
    }

    async addVideoPipelineImage(
        videoPipelineId: string,
        image: File,
        textContext: string = "",
        label: boolean = false
    ): Promise<ImageMetadata> {
        const formData = new FormData();
        formData.append('image', image);
        formData.append('text_context', textContext);
        formData.append('label', String(label));

        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/images`, {
            method: 'POST',
            headers: await this.getAuthHeaders(),
            body: formData
        });
        return this.handleResponse<ImageMetadata>(response, "Add video pipeline image");
    }

    async deleteVideoPipelineImage(videoPipelineId: string, index: number): Promise<DeleteVideoPipelineImageResponse> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/images/${index}`, {
            method: 'DELETE',
            headers: await this.getAuthHeaders()
        });
        return this.handleResponse<DeleteVideoPipelineImageResponse>(response, "Delete video pipeline image");
    }

    async addVideoPipelineSection(videoPipelineId: string, section: ContentSection): Promise<ContentSection> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/sections`, {
            method: 'POST',
            headers: await this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(section)
        });
        return this.handleResponse<ContentSection>(response, "Add video pipeline section");
    }

    async deleteVideoPipelineSection(videoPipelineId: string, index: number): Promise<DeleteVideoPipelineSectionResponse> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/sections/${index}`, {
            method: 'DELETE',
            headers: await this.getAuthHeaders()
        });
        return this.handleResponse<DeleteVideoPipelineSectionResponse>(response, "Delete video pipeline section");
    }

    async processVideoPipelineContent(videoPipelineId: string, request: CreateVideoOutlineRequest): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/process`, {
            method: 'POST',
            headers: await this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipeline>(response, "Process video pipeline content");
    }

    async addVideoOutlineSegment(videoPipelineId: string, segment: VideoSegment): Promise<VideoSegment> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/outline/segments`, {
            method: 'POST',
            headers: await this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(segment)
        });
        return this.handleResponse<VideoSegment>(response, "Add video pipeline outline segment");
    }

    async generateVideoPipelineScripts(videoPipelineId: string, provider: string = 'elevenlabs'): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/generate-scripts`, {
            method: 'POST',
            headers: await this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ provider })
        });
        return this.handleResponse<VideoPipeline>(response, "Generate video pipeline scripts");
    }

    async generateVideoPipelineOutput(videoPipelineId: string, request: GenerateVideoPipelineRequest): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/generate`, {
            method: 'POST',
            headers: await this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipeline>(response, "Generate video pipeline output");
    }

    async downloadVideoPipelineOutput(videoPipelineId: string): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/output/download`, {
            method: 'GET',
            headers: await this.getAuthHeaders()
        });

        if (!response.ok) {
            let errorMessage = "Operation failed: Download video pipeline output";
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || errorData.message || errorMessage;
            } catch {
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        return response.blob() as Promise<Blob>;
    }

    async streamVideoPipelineOutput(videoPipelineId: string): Promise<Response> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/output/stream`, {
            method: 'GET',
            headers: await this.getAuthHeaders()
        });

        if (!response.ok) {
            let errorMessage = "Operation failed: Stream video pipeline output";
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || errorData.message || errorMessage;
            } catch {
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        return response;
    }

    async addVideoPipelineReview(videoPipelineId: string, request: VideoPipelineReviewRequest): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/review`, {
            method: 'POST',
            headers: await this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipeline>(response, "Add video pipeline review");
    }
    
    async uploadProfilePicture(file: File): Promise<{ message: string; profile_picture: string }> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/users/profile-picture`, {
            method: 'POST',
            headers: await this.getAuthHeaders(),
            body: formData
        });

        return this.handleResponse<{ message: string; profile_picture: string }>(response, "Upload profile picture");
    }

    getProfilePictureUrl(profilePicturePath: string | null | undefined): string | null {
        if (!profilePicturePath) return null;
        return `${this.baseUrl}/media/${profilePicturePath}`;
    }

}

// create a singleton instance of the client
const client = new VidinieAPIClient(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
);

export default client;
