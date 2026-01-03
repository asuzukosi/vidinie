/**
 * frontend api client
 * handles requests to Next.js API routes (frontend server)
 */

import type { CheckoutRequest, CheckoutResponse, CustomerPortalRequest, CustomerPortalResponse } from "./types";

export class FrontendAPIClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
  }

  /**
   * sets the json web token for authenticated requests
   * token should be set from Redux state after login
   */
  setToken(token: string | null): void {
    this.token = token;
  }

  /**
   * gets the current json web token from in-memory storage
   */
  private getTokenFromMemory(): string | null {
    return this.token;
  }

  /**
   * checks if user is authenticated before making a request
   * throws error if not authenticated
   */
  private checkAuthentication(): void {
    const token = this.getTokenFromMemory();
    if (!token) {
      throw new Error('Not authenticated. Please log in.');
    }
  }

  /**
   * builds headers for authenticated requests
   */
  private getAuthHeaders(additionalHeaders: Record<string, string> = {}): Record<string, string> {
    const token = this.getTokenFromMemory();
    if (!token) {
      throw new Error('Not authenticated. Please log in.');
    }
    return {
      'Authorization': `Bearer ${token}`,
      ...additionalHeaders,
    };
  }

  /**
   * handles API response and checks for errors
   * throws error if response is not successful
   * components should handle toast notifications individually
   */
  private async handleResponse<T>(response: Response, operationName: string): Promise<T> {
    if (!response.ok) {
      let errorMessage = `Operation failed: ${operationName}`;
      
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorData.detail || errorData.message || errorMessage;
      } catch {
        // if response is not JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }

      // throw error to prevent data from being passed forward
      // components should catch this and show toast notifications as needed
      throw new Error(errorMessage);
    }

    return await response.json() as T;
  }

  /**
   * create a stripe checkout session
   */
  async createCheckoutSession(request: CheckoutRequest): Promise<CheckoutResponse> {
    // Check authentication before making request
    this.checkAuthentication();

    const response = await fetch(`${this.baseUrl}/api/checkout`, {
      method: 'POST',
      headers: this.getAuthHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify({
        priceId: request.priceId,
        quantity: request.quantity || 1,
      }),
    });

    return this.handleResponse<CheckoutResponse>(response, "Create checkout session");
  }

  /**
   * create a stripe customer portal session
   */
  async createCustomerPortalSession(
    request: CustomerPortalRequest
  ): Promise<CustomerPortalResponse> {
    // check authentication before making request
    this.checkAuthentication();

    const response = await fetch(`${this.baseUrl}/api/customer-portal`, {
      method: 'POST',
      headers: this.getAuthHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify({
        customerId: request.customerId,
        returnUrl: request.returnUrl,
      }),
    });

    return this.handleResponse<CustomerPortalResponse>(response, "Create customer portal session");
  }
}

// create a singleton instance of the client
const frontendClient = new FrontendAPIClient();

export default frontendClient;

