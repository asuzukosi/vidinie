'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import client from '@/lib/sdk/client';
import { useAppSelector } from '@/lib/store/hooks';

// Map Stripe price IDs to subscription types
const PRICE_TO_SUBSCRIPTION: Record<string, string> = {
    "price_1SdQlk2M9n75azYSm0Q7ffjU": "starter", // starter plan
    "price_professional": "professional", // professional plan
};

// Map subscription types to backend enum values
const SUBSCRIPTION_MAP: Record<string, string> = {
    "starter": "starter",
    "professional": "professional",
    "free": "free",
};

export default function SuccessPage() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [message, setMessage] = useState<string>('Processing your payment...');
    const user = useAppSelector((state) => state.auth.user);

    useEffect(() => {
        const processCheckout = async () => {
            const sessionId = searchParams.get('session_id');
            
            if (!sessionId) {
                setStatus('error');
                setMessage('No session ID found. Please contact support if you completed a payment.');
                return;
            }

            if (!user?.token) {
                setStatus('error');
                setMessage('Please log in to complete your subscription setup.');
                setTimeout(() => {
                    router.push('/signin');
                }, 2000);
                return;
            }

            try {
                // Set token on client if not already set
                client.setToken(user.token);

                // Retrieve checkout session from checkout API route
                const sessionResponse = await fetch(`/api/checkout?session_id=${sessionId}`);
                
                if (!sessionResponse.ok) {
                    throw new Error('Failed to retrieve checkout session');
                }

                const { session } = await sessionResponse.json();

                // Extract subscription type from price ID
                // line_items can be either a Stripe list object or an array
                const lineItemsData = session.line_items?.data || 
                                     (Array.isArray(session.line_items) ? session.line_items : []);
                let subscriptionType: string | null = null;
                
                if (lineItemsData.length > 0) {
                    const priceId = lineItemsData[0].price?.id || 
                                   (typeof lineItemsData[0].price === 'string' ? lineItemsData[0].price : null);
                    subscriptionType = priceId ? (PRICE_TO_SUBSCRIPTION[priceId] || null) : null;
                }

                // Map to backend subscription enum value
                const backendSubscription = subscriptionType 
                    ? SUBSCRIPTION_MAP[subscriptionType] 
                    : null;

                if (!backendSubscription) {
                    throw new Error('Could not determine subscription type from checkout session');
                }

                // Update subscription on backend
                await client.updateSubscription(backendSubscription);

                // Extract payment method information if available
                const paymentIntent = session.payment_intent;
                const customerId = session.customer;

                // If we have payment intent, try to get payment method details
                if (paymentIntent && typeof paymentIntent === 'string') {
                    try {
                        // Note: We would need to retrieve payment intent details from Stripe
                        // For now, we'll just update the subscription
                        // Payment method can be handled separately or via webhook
                    } catch (error) {
                        console.error('Error processing payment method:', error);
                        // Non-critical error, continue
                    }
                }

                // Update customer ID if we have one and user doesn't have it yet
                if (customerId && !user.stripe_customer_id) {
                    try {
                        await client.updateCustomerId(customerId);
                    } catch (error) {
                        console.error('Error updating customer ID:', error);
                        // Non-critical error, continue
                    }
                }

                setStatus('success');
                setMessage('Your subscription has been successfully activated!');
                
                // Redirect to dashboard after a short delay
                setTimeout(() => {
                    router.push('/tasks');
                }, 2000);
            } catch (error: any) {
                console.error('Error processing checkout:', error);
                setStatus('error');
                setMessage(error.message || 'An error occurred while processing your payment. Please contact support.');
            }
        };

        processCheckout();
    }, [searchParams, user, router]);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            {status === 'loading' && (
                <>
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mb-4"></div>
                    <h1 className="text-4xl font-bold mb-4">Processing Payment...</h1>
                    <p className="text-gray-600">{message}</p>
                </>
            )}
            {status === 'success' && (
                <>
                    <div className="text-green-500 text-6xl mb-4">✓</div>
                    <h1 className="text-4xl font-bold mb-4 text-green-600">Payment Successful!</h1>
                    <p className="text-gray-600">{message}</p>
                </>
            )}
            {status === 'error' && (
                <>
                    <div className="text-red-500 text-6xl mb-4">✗</div>
                    <h1 className="text-4xl font-bold mb-4 text-red-600">Payment Processing Error</h1>
                    <p className="text-gray-600">{message}</p>
                </>
            )}
        </div>
    );
}