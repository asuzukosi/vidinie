'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentSubscription } from '@/lib/stripe';

export default function SuccessPage() {
    const router = useRouter();
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [message, setMessage] = useState<string>('Processing your payment...');

    useEffect(() => {
        const verifySubscription = async () => {
            try {

                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // verify subscription was created by checking better-auth
                const subscription = await getCurrentSubscription();
                
                if (subscription) {
                    setStatus('success');
                    setMessage('Your subscription has been successfully activated!');
                    
                    // redirect to dashboard after a short delay
                    setTimeout(() => {
                        router.push('/video-pipelines');
                    }, 2000);
                } else {
                    // subscription might still be processing via webhook
                    // better-auth webhooks will handle it automatically
                    setStatus('success');
                    setMessage('Your payment was successful! Your subscription is being activated...');
                    
                    // redirect to dashboard
                    setTimeout(() => {
                        router.push('/video-pipelines');
                    }, 2000);
                }
            } catch (error: any) {
                console.error('error verifying subscription:', error);
                setStatus('success');
                setMessage('Your payment was successful! Your subscription is being activated...');
                
                setTimeout(() => {
                    router.push('/video-pipelines');
                }, 2000);
            }
        };

        verifySubscription();
    }, [router]);

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