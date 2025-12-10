import { NextRequest, NextResponse } from "next/server";
import stripe from "@/lib/stripe";

export async function POST(req: NextRequest){
    try {
        const { priceId, quantity } = await req.json();
        const session = await stripe.checkout.sessions.create({
            line_items: [{ price: priceId, quantity }],
            mode: "subscription", // setup recurring payments
            success_url: `${req.headers.get("origin")}/success?session_id={CHECKOUT_SESSION_ID}`,
            cancel_url: `${req.headers.get("origin")}/cancel`,
        });
        return NextResponse.json({ sessionId: session.id }, { status: 200 });

    }catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
