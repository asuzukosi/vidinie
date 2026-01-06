import { CreateVideoPipelineOutlineRequest, DeleteVideoPipelineImageResponse, DeleteVideoPipelineResponse, DeleteVideoPipelineSectionResponse, VideoPipelineImageMetadata,
        VideoPipelineContentSection, VideoPipeline, VideoPipelineReviewRequest,
        CreateVideoPipelineRequest, VideoPipelineSummary,
        GenerateVideoPipelineRequest,
        VideoPipelineSegment,
        LoginResponse, RegisterResponse, User,
        Subscription} from "./types";
import frontendClient from "@/lib/api/client";

export class VidinieAPIClient {
    private baseUrl: string;
    private token: string | null = null;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    setToken(token: string | null): void {
        this.token = token;
        // Also set token on frontend client to keep them in sync
        frontendClient.setToken(token);
    }

    private getTokenFromMemory(): string | null {
        return this.token;
    }

    private getAuthHeader(): string | null {
        const token = this.getTokenFromMemory();
        return token ? `Bearer ${token}` : null;
    }

    private getAuthHeaders(additionalHeaders: Record<string, string> = {}): Record<string, string> {
        const authHeader = this.getAuthHeader();
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
        description: string,
        tags: string[],
        projects: string[],
        file: File
    ): Promise<VideoPipelineSummary> {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('description', description);
        tags.forEach(tag => formData.append('tags', tag));
        projects.forEach(project => formData.append('projects', project));
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/video-pipelines/from-file`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: formData
        });
        return this.handleResponse<VideoPipelineSummary>(response, "Create video pipeline from file");
    }

    async createVideoPipelineFromUrl(request: CreateVideoPipelineRequest): Promise<VideoPipelineSummary> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/from-url`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipelineSummary>(response, "Create video pipeline from URL");
    }

    async getAllVideoPipelines(): Promise<VideoPipelineSummary[]> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipelineSummary[]>(response, "Get all video pipelines");
    }

    async getVideoPipelineDetails(videoPipelineId: string): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipeline>(response, "Get video pipeline details");
    }

    async deleteVideoPipeline(videoPipelineId: string): Promise<DeleteVideoPipelineResponse> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<DeleteVideoPipelineResponse>(response, "Delete video pipeline");
    }

    async addVideoPipelineImage(
        videoPipelineId: string,
        image: File,
        textContext: string = "",
        label: boolean = false
    ): Promise<VideoPipelineImageMetadata> {
        const formData = new FormData();
        formData.append('image', image);
        formData.append('text_context', textContext);
        formData.append('label', String(label));

        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/images`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: formData
        });
        return this.handleResponse<VideoPipelineImageMetadata>(response, "Add video pipeline image");
    }

    async deleteVideoPipelineImage(videoPipelineId: string, index: number): Promise<DeleteVideoPipelineImageResponse> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/images/${index}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
        });
        return this.handleResponse<DeleteVideoPipelineImageResponse>(response, "Delete video pipeline image");
    }

    async addVideoPipelineSection(videoPipelineId: string, section: VideoPipelineContentSection): Promise<VideoPipelineContentSection> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/sections`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(section)
        });
        return this.handleResponse<VideoPipelineContentSection>(response, "Add video pipeline section");
    }

    async deleteVideoPipelineSection(videoPipelineId: string, index: number): Promise<DeleteVideoPipelineSectionResponse> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/sections/${index}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<DeleteVideoPipelineSectionResponse>(response, "Delete video pipeline section");
    }

    async processVideoPipelineContent(videoPipelineId: string, request: CreateVideoPipelineOutlineRequest): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/process`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipeline>(response, "Process video pipeline content");
    }

    async addVideoPipelineOutlineSegment(videoPipelineId: string, segment: VideoPipelineSegment): Promise<VideoPipelineSegment> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/outline/segments`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(segment)
        });
        return this.handleResponse<VideoPipelineSegment>(response, "Add video pipeline outline segment");
    }

    async generateVideoPipelineScripts(videoPipelineId: string, provider: string = 'elevenlabs'): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/generate-scripts`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ provider })
        });
        return this.handleResponse<VideoPipeline>(response, "Generate video pipeline scripts");
    }

    async generateVideoPipelineOutput(videoPipelineId: string, request: GenerateVideoPipelineRequest): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/generate`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipeline>(response, "Generate video pipeline output");
    }

    async downloadVideoPipelineOutput(videoPipelineId: string): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/output/download`, {
            method: 'GET',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
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
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
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
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipeline>(response, "Add video pipeline review");
    }

    // ===== Authentication Methods =====

    async login(email: string, password: string): Promise<LoginResponse> {
        const response = await fetch(`${this.baseUrl}/users/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await this.handleResponse<LoginResponse>(response, "Login");
        
        if (data.token) {
            this.setToken(data.token);
        }

        return data;
    }

    async register(email: string, password: string): Promise<RegisterResponse> {
        const response = await fetch(`${this.baseUrl}/users/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        return this.handleResponse<RegisterResponse>(response, "Register");
    }

    async getCurrentUser(): Promise<User | null> {
        const token = this.getTokenFromMemory();
        if (!token) {
            return null;
        }

        try {
            const response = await fetch(`${this.baseUrl}/users/me`, {
                method: 'GET',
                headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user');
            }

            return await response.json();
        } catch (error) {
            this.setToken(null);
            return null;
        }
    }

    async updateUser(data: { email?: string }): Promise<User> {
        const response = await fetch(`${this.baseUrl}/users/me`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(data),
        });

        return this.handleResponse<User>(response, "Update user");
    }

    logout(): void {
        this.setToken(null);
    }

    async changePassword(currentPassword: string, newPassword: string): Promise<void> {
        const response = await fetch(`${this.baseUrl}/users/change-password`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
            }),
        });

        await this.handleResponse<{ message: string }>(response, "Change password");
    }

    async uploadProfilePicture(file: File): Promise<{ message: string; profile_picture: string }> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/users/profile-picture`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: formData
        });

        return this.handleResponse<{ message: string; profile_picture: string }>(response, "Upload profile picture");
    }
    
    async deleteProfilePicture(): Promise<{ message: string }> {
        const response = await fetch(`${this.baseUrl}/users/profile-picture`, {
            method: 'DELETE',
            headers: this.getAuthHeaders()
        });

        return this.handleResponse<{ message: string }>(response, "Delete profile picture");
    }

    getProfilePictureUrl(profilePicturePath: string | null | undefined): string | null {
        if (!profilePicturePath) return null;
        return `${this.baseUrl}/media/${profilePicturePath}`;
    }

    async updateSubscription(subscription: string): Promise<User> {
        const response = await fetch(`${this.baseUrl}/users/subscription`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ subscription }),
        });

        return this.handleResponse<User>(response, "Update subscription");
    }

    async getSubscriptions(): Promise<Subscription[]> {
        const response = await fetch(`${this.baseUrl}/users/subscriptions`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        return this.handleResponse<Subscription[]>(response, "Get subscriptions");
    }

    async getActiveSubscription(): Promise<Subscription | null> {
        const response = await fetch(`${this.baseUrl}/users/subscriptions/active`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to get active subscription');
        }

        const data = await response.json();
        return data === null ? null : data as Subscription;
    }

    async getSubscription(subscriptionId: string): Promise<Subscription> {
        const response = await fetch(`${this.baseUrl}/users/subscriptions/${subscriptionId}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        return this.handleResponse<Subscription>(response, "Get subscription");
    }
}

// create a singleton instance of the client
const client = new VidinieAPIClient(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
);

export default client;
