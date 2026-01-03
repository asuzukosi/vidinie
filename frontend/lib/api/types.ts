
export interface CheckoutRequest {
    priceId: string;
    quantity?: number;
  }
  
  export interface CheckoutResponse {
    sessionId: string;
    url: string;
    customerId?: string | null;
  }
  
  export interface CustomerPortalRequest {
    customerId: string;
    returnUrl?: string;
  }
  
  export interface CustomerPortalResponse {
    url: string;
  }