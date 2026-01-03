import { NextRequest, NextResponse } from "next/server";
import stripe from "@/lib/stripe";
import { headers } from "next/headers";

// map stripe price ids to subscription types
const PRICE_TO_SUBSCRIPTION: Record<string, string> = {
    "price_1SdQlk2M9n75azYSm0Q7ffjU": "starter", // starter plan
    "price_professional": "professional", // professional plan
};

// map subscription types to backend enum values
const SUBSCRIPTION_MAP: Record<string, string> = {
    "starter": "starter",
    "professional": "professional",
    "free": "free",
};

export async function POST(req: NextRequest){
    const body = await req.text();
    const headersList = await headers();
    const sig = headersList.get("stripe-signature")!;
    
    let event;
    try {
        event = stripe.webhooks.constructEvent(body, 
            sig, 
            process.env.STRIPE_WEBHOOK_SECRET!
        );
    } catch (err: any) {
        return NextResponse.json({ error: `Webhook Error: ${err.message}` }, { status: 400 });
    }

    // handle event
    switch (event.type){
        case "checkout.session.completed":
            const session = event.data.object as any;
            const customerId = session.customer;
            
            if (customerId) {
                try {
                    // get customer from stripe to find user email
                    const customer = await stripe.customers.retrieve(customerId);
                    
                    if (customer && !customer.deleted && typeof customer === 'object' && 'email' in customer) {
                        const customerEmail = (customer as any).email;
                        
                        // customer id should already be saved by checkout route, but update as backup
                        console.log('Checkout completed for customer', customerId, 'with email', customerEmail);
                        // TODO: update database with new subscription
                    }
                } catch (error) {
                    console.error("Error processing checkout.session.completed:", error);
                }
            }
            
            console.log('Subscription created for customer', customerId);
            // TODO: update database with new subscription
            break;
        case "payment_intent.succeeded":
            const paymentIntent = event.data.object;
            console.log('Payment intent succeeded', paymentIntent);
            // TODO: update database with new payment
            break;
        default:
            console.log(`Unhandled event type ${event.type}`);
            break;
    }
    
    return NextResponse.json({ received: true }, { status: 200 });
}