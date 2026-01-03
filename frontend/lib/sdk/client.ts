import { VideoPipelineContextChunk, CreateVideoPipelineOutlineRequest, DeleteVideoPipelineImageResponse, DeleteVideoPipelineResponse, DeleteVideoPipelineSectionResponse, VideoPipelineImageMetadata,
        VideoPipelineContentMinimal, VideoPipelineContentSection, VideoPipeline, VideoPipelineReviewRequest, VideoPipelineStageDetails,
        VideoPipelineScript,
        CreateVideoPipelineRequest, VideoPipelineSummary, UpdateVideoPipelineImageRequest,
        GenerateVideoPipelineRequest,
        VideoPipelineOutline, VideoPipelineSegment,
        VideoPipelineSegmentBackground, LoginResponse, RegisterResponse, User,
        PaymentMethod, CreatePaymentMethodRequest, UpdatePaymentMethodRequest} from "./types";
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
            // Note: Do not set Content-Type when using FormData; browser will set the correct boundary.
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

    async deleteVideoPipeline(videoPipelineId: string): Promise<DeleteVideoPipelineResponse> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<DeleteVideoPipelineResponse>(response, "Delete video pipeline");
    }

    async getVideoPipelineDetails(videoPipelineId: string): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipeline>(response, "Get video pipeline details");
    }

    async getVideoPipelineStageDetails(videoPipelineId: string): Promise<VideoPipelineStageDetails> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/stages/stage`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipelineStageDetails>(response, "Get video pipeline stage details");
    }

    async getVideoPipelineImages(videoPipelineId: string): Promise<VideoPipelineImageMetadata[]> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/images`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipelineImageMetadata[]>(response, "Get video pipeline images");
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
            // Note: Do not set Content-Type when using FormData; browser will set the correct boundary.
            body: formData
        });
        return this.handleResponse<VideoPipelineImageMetadata>(response, "Add video pipeline image");
    }

    async updateVideoPipelineImage(videoPipelineId: string, request: UpdateVideoPipelineImageRequest): Promise<VideoPipelineImageMetadata> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/images`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });

        return this.handleResponse<VideoPipelineImageMetadata>(response, "Update video pipeline image");
    }

    async deleteVideoPipelineImage(videoPipelineId: string, index: number): Promise<DeleteVideoPipelineImageResponse> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/images/${index}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
        });
        return this.handleResponse<DeleteVideoPipelineImageResponse>(response, "Delete video pipeline image");
    }

    async getVideoPipelineContentInfo(videoPipelineId: string): Promise<VideoPipelineContentMinimal> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/content`, {
            method: 'GET',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
        });
        return this.handleResponse<VideoPipelineContentMinimal>(response, "Get video pipeline content info");
    }

    async getVideoPipelineSections(videoPipelineId: string): Promise<VideoPipelineContentSection[]> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/sections`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipelineContentSection[]>(response, "Get video pipeline sections");
    }

    async addVideoPipelineSection(videoPipelineId: string, section: VideoPipelineContentSection): Promise<VideoPipelineContentSection> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/sections`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(section)
        });
        return this.handleResponse<VideoPipelineContentSection>(response, "Add video pipeline section");
    }

    async updateVideoPipelineSection(videoPipelineId: string, index: number, section: VideoPipelineContentSection): Promise<VideoPipelineContentSection> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/sections/${index}`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(section)
        });
        return this.handleResponse<VideoPipelineContentSection>(response, "Update video pipeline section");
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

    async getVideoPipelineContextChunks(videoPipelineId: string): Promise<VideoPipelineContextChunk[]> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/context-chunks`, {
            method: 'GET',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
        });
        return this.handleResponse<VideoPipelineContextChunk[]>(response, "Get video pipeline context chunks");
    }

    async getVideoPipelineOutline(videoPipelineId: string): Promise<VideoPipelineOutline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/outline`, {
            method: 'GET',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
        });
        return this.handleResponse<VideoPipelineOutline>(response, "Get video pipeline outline");
    }

    async getVideoPipelineOutlineSegments(videoPipelineId: string): Promise<VideoPipelineSegment[]> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/outline/segments`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });
        return this.handleResponse<VideoPipelineSegment[]>(response, "Get video pipeline outline segments");
    }

    async addVideoPipelineOutlineSegment(videoPipelineId: string, segment: VideoPipelineSegment): Promise<VideoPipelineSegment> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/outline/segments`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(segment)
        });
        return this.handleResponse<VideoPipelineSegment>(response, "Add video pipeline outline segment");
    }

    async updateVideoPipelineOutlineSegment(videoPipelineId: string, index: number, segment: VideoPipelineSegment): Promise<VideoPipelineSegment> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/outline/segments/${index}`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(segment)
        });
        return this.handleResponse<VideoPipelineSegment>(response, "Update video pipeline outline segment");
    }

    async deleteVideoPipelineOutlineSegment(videoPipelineId: string, index: number): Promise<VideoPipelineSegment> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/outline/segments/${index}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
        });
        return this.handleResponse<VideoPipelineSegment>(response, "Delete video pipeline outline segment");
    }

    async generateVideoPipelineSegmentImages(videoPipelineId: string, indexes: number[]): Promise<VideoPipelineSegment[]> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/generate-segment-images`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(indexes)
        });
        return this.handleResponse<VideoPipelineSegment[]>(response, "Generate video pipeline segment images");
    }

    async generateVideoPipelineScripts(videoPipelineId: string, provider: string = 'elevenlabs'): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/generate-scripts`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ provider })
        });
        return this.handleResponse<VideoPipeline>(response, "Generate video pipeline scripts");
    }

    async getVideoPipelineScripts(videoPipelineId: string): Promise<VideoPipelineScript> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/scripts`, {
            method: 'GET',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
        });
        return this.handleResponse<VideoPipelineScript>(response, "Get video pipeline scripts");
    }

    async updateVideoPipelineScripts(videoPipelineId: string, scriptData: VideoPipelineScript): Promise<VideoPipelineScript> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/scripts`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(scriptData)
        });
        return this.handleResponse<VideoPipelineScript>(response, "Update video pipeline scripts");
    }

    async generateVideoPipelineOutput(videoPipelineId: string, request: GenerateVideoPipelineRequest): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/generate`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request)
        });
        return this.handleResponse<VideoPipeline>(response, "Generate video pipeline output");
    }

    async updateVideoPipelineSegmentBackground(videoPipelineId: string, index: number, background: VideoPipelineSegmentBackground): Promise<VideoPipelineOutline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/segments/${index}/background`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(background)
        });
        return this.handleResponse<VideoPipelineOutline>(response, "Update video pipeline segment background");
    }

    async regenerateVideoPipelineSegmentAudio(videoPipelineId: string, provider: string = 'elevenlabs'): Promise<VideoPipeline> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/${videoPipelineId}/regenerate-audio`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ provider })
        });
        return this.handleResponse<VideoPipeline>(response, "Regenerate video pipeline segment audio");
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
            // throw error - components should catch and show toast notifications
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
            // throw error - components should catch and show toast notifications
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

    async getVideoPipelineImageWithPath(path: string): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/video-pipelines/images/${path}`, {
            method: 'GET',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
        });

        if (!response.ok) {
            let errorMessage = "Operation failed: Get video pipeline image with path";
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || errorData.message || errorMessage;
            } catch {
                errorMessage = response.statusText || errorMessage;
            }
            // throw error - components should catch and show toast notifications
            throw new Error(errorMessage);
        }

        return response.blob() as Promise<Blob>;
    }

    // authentication methods
    async login(email: string, password: string): Promise<LoginResponse> {
        const response = await fetch(`${this.baseUrl}/users/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await this.handleResponse<LoginResponse>(response, "Login");
        
        // store token in memory (will be synced from redux)
        if (data.token) {
            this.setToken(data.token);
        }

        return data;
    }

    async register(username: string, email: string, password: string): Promise<RegisterResponse> {
        const response = await fetch(`${this.baseUrl}/users/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password }),
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
            // if token is invalid, clear it
            this.setToken(null);
            return null;
        }
    }

    async updateUser(data: { username?: string; email?: string }): Promise<User> {
        const response = await fetch(`${this.baseUrl}/users/me`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(data),
        });

        return this.handleResponse<User>(response, "Update user");
    }

    logout(): void {
        this.setToken(null);
        // frontend client token is already cleared by setToken above
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

    getUser(): { id: string; username: string; email: string } | null {
        // user data should be retrieved from Redux, not local storage
        // this method is kept for backward compatibility but should not be used
        return null;
    }

    async uploadProfilePicture(file: File): Promise<{ message: string; profile_picture: string }> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/users/profile-picture`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            // note: do not set Content-Type when using FormData; browser will set the correct boundary.
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

    async getPaymentMethods(): Promise<PaymentMethod[]> {
        const response = await fetch(`${this.baseUrl}/users/payment-methods`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        return this.handleResponse<PaymentMethod[]>(response, "Get payment methods");
    }

    async createPaymentMethod(request: CreatePaymentMethodRequest): Promise<PaymentMethod> {
        const response = await fetch(`${this.baseUrl}/users/payment-methods`, {
            method: 'POST',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request),
        });

        return this.handleResponse<PaymentMethod>(response, "Create payment method");
    }

    async getPaymentMethod(paymentMethodId: string): Promise<PaymentMethod> {
        const response = await fetch(`${this.baseUrl}/users/payment-methods/${paymentMethodId}`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        return this.handleResponse<PaymentMethod>(response, "Get payment method");
    }

    async updatePaymentMethod(paymentMethodId: string, request: UpdatePaymentMethodRequest): Promise<PaymentMethod> {
        const response = await fetch(`${this.baseUrl}/users/payment-methods/${paymentMethodId}`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(request),
        });

        return this.handleResponse<PaymentMethod>(response, "Update payment method");
    }

    async deletePaymentMethod(paymentMethodId: string): Promise<{ message: string }> {
        const response = await fetch(`${this.baseUrl}/users/payment-methods/${paymentMethodId}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders()
        });

        return this.handleResponse<{ message: string }>(response, "Delete payment method");
    }

    async getCustomerId(): Promise<{ stripe_customer_id: string | null }> {
        const response = await fetch(`${this.baseUrl}/users/customer-id`, {
            method: 'GET',
            headers: this.getAuthHeaders()
        });

        return this.handleResponse<{ stripe_customer_id: string | null }>(response, "Get customer ID");
    }

    async updateCustomerId(stripeCustomerId: string): Promise<User> {
        const response = await fetch(`${this.baseUrl}/users/customer-id`, {
            method: 'PUT',
            headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ stripe_customer_id: stripeCustomerId }),
        });

        return this.handleResponse<User>(response, "Update customer ID");
    }
}

// create a singleton instance of the client
const client = new VidinieAPIClient(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
);

export default client;
