import { NextRequest, NextResponse } from "next/server";
import stripe from "@/lib/stripe";

export async function POST(req: NextRequest) {
  try {
    const { customerId, returnUrl } = await req.json();
    
    if (!customerId) {
      return NextResponse.json(
        { error: "Customer ID is required" },
        { status: 400 }
      );
    }

    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: returnUrl || `${req.headers.get("origin")}/settings`,
    });

    return NextResponse.json({ url: session.url }, { status: 200 });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}

