import { NextRequest, NextResponse } from "next/server";
import stripe from "@/lib/stripe";
import { headers } from "next/headers";

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
            const session = event.data.object
            // TODO: handle subscription created
            console.log('Subscription created for customer', session.customer);
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