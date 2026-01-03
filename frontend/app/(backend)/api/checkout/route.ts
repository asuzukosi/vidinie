import { NextRequest, NextResponse } from "next/server";
import stripe from "@/lib/stripe";

export async function POST(req: NextRequest){
    try {
        const { priceId, quantity } = await req.json();
        const authHeader = req.headers.get("authorization");
        
        let customerId: string | null = null;
        
        // if user is authenticated, get or create stripe customer
        if (authHeader && authHeader.startsWith("Bearer ")) {
            const token = authHeader.substring(7);
            try {
                // get user info from backend to get email and existing customer id
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const userResponse = await fetch(`${apiUrl}/users/me`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (userResponse.ok) {
                    const user = await userResponse.json();
                    
                    // check if user already has a stripe customer id
                    if (user.stripe_customer_id) {
                        customerId = user.stripe_customer_id;
                    } else {
                        // create a new stripe customer
                        const customer = await stripe.customers.create({
                            email: user.email,
                            name: user.username,
                            metadata: {
                                user_id: user.id
                            }
                        });
                        customerId = customer.id;
                        
                        // save customer id to backend
                        await fetch(`${apiUrl}/users/customer-id`, {
                            method: 'PUT',
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ stripe_customer_id: customerId })
                        });
                    }
                }
            } catch (error) {
                // if we can't get user info, continue without customer (stripe will create one)
                console.error("Error getting user info for checkout:", error);
            }
        }
        
        const sessionParams: any = {
            line_items: [{ price: priceId, quantity }],
            mode: "subscription",
            success_url: `${req.headers.get("origin")}/success?session_id={CHECKOUT_SESSION_ID}`,
            cancel_url: `${req.headers.get("origin")}/cancel`,
        };
        
        // associate customer with session if we have one
        if (customerId) {
            sessionParams.customer = customerId;
        }
        
        const session = await stripe.checkout.sessions.create(sessionParams);
        
        // return both session id and url for client-side redirect without redirectToCheckout
        return NextResponse.json({ 
            sessionId: session.id, 
            url: session.url,
            customerId: session.customer as string | null
        }, { status: 200 });

    }catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
