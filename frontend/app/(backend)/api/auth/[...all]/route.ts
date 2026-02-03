import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";
import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import {
  handleSubscriptionComplete,
  handleSubscriptionCreated,
  handleSubscriptionUpdated,
  handleSubscriptionCanceled,
  handleSubscriptionDeleted,
  handlePaymentSucceeded,
  handlePaymentFailed,
} from "@/lib/stripe-webhooks";

const handler = toNextJsHandler(auth);

// Initialize Stripe client
const stripe = new Stripe(process.env.NEXT_PUBLIC_STRIPE_SECRET_KEY || "", {
  apiVersion: "2025-11-17.clover",
});

const webhookSecret = process.env.NEXT_PUBLIC_STRIPE_WEBHOOK_SECRET || "";

export async function POST(req: NextRequest) {
  const url = new URL(req.url);
  // check if this is a Stripe webhook request
  const isStripeWebhook = url.pathname.includes("/stripe/webhook");
  const stripeSignature = req.headers.get("stripe-signature");

  if (isStripeWebhook && stripeSignature) {
    return await handleStripeWebhook(req, stripeSignature);
  }
  return await handler.POST(req);
}

/**
 * handle Stripe webhook events
 */
async function handleStripeWebhook(req: NextRequest, signature: string) {
  const body = await req.text();

  if (!webhookSecret) {
    console.error("missing webhook secret in environment");
    return NextResponse.json(
      { error: "webhook secret not configured" },
      { status: 500 }
    );
  }

  let event: Stripe.Event;

  try {
    // verify webhook signature
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
    console.log("verified event:", event.type, event.id);
  } catch (err) {
    const error = err as Error;
    console.error("signature verification failed:", error.message);
    return NextResponse.json(
      { error: `signature verification failed: ${error.message}` },
      { status: 400 }
    );
  }

  try {
    // handle different event types
    switch (event.type) {
      case "checkout.session.completed": {
        console.log("checkout session completed event:", event);
        const session = event.data.object as Stripe.Checkout.Session;
        console.log("session data:", session.id, session.mode, session.subscription, session.customer, session.metadata);

        // get subscription and customer
        if (session.mode === "subscription" && session.subscription && session.customer) {
          const subscription = await stripe.subscriptions.retrieve(
            session.subscription as string
          );
          const customer = await stripe.customers.retrieve(
            session.customer as string
          ) as Stripe.Customer;
          await handleSubscriptionComplete(subscription, customer);
        }
        break;
      }

      case "customer.subscription.created": {
        const subscription = event.data.object as Stripe.Subscription;
        console.log("subscription created:", subscription.id);
        if (subscription.customer) {
          const customer = await stripe.customers.retrieve(
            subscription.customer as string
          ) as Stripe.Customer;
          await handleSubscriptionCreated(subscription, customer);
        }
        break;
      }

      case "customer.subscription.updated": {
        const subscription = event.data.object as Stripe.Subscription;
        console.log("subscription updated:", subscription.id);

        if (subscription.customer) {
          const customer = await stripe.customers.retrieve(
            subscription.customer as string
          ) as Stripe.Customer;
          // check if subscription was canceled
          if (subscription.status === "canceled" || subscription.status === "unpaid") {
            await handleSubscriptionCanceled(subscription, customer);
          } else {
            await handleSubscriptionUpdated(subscription, customer);
          }
        }
        break;
      }

      case "customer.subscription.deleted": {
        const subscription = event.data.object as Stripe.Subscription;
        console.log("subscription deleted:", subscription.id);
        if (subscription.customer) {
          const customer = await stripe.customers.retrieve(
            subscription.customer as string
          ) as Stripe.Customer;
          await handleSubscriptionDeleted(subscription, customer);
        }
        break;
      }

      case "invoice.payment_succeeded": {
        const invoice = event.data.object as Stripe.Invoice;
        console.log("invoice payment succeeded:", invoice.id);
        if (invoice.customer) {
          const customer = await stripe.customers.retrieve(
            invoice.customer as string
          ) as Stripe.Customer;
          await handlePaymentSucceeded(invoice, customer);
        }
        break;
      }

      case "invoice.payment_failed": {
        const invoice = event.data.object as Stripe.Invoice;
        console.log("invoice payment failed:", invoice.id);
        if (invoice.customer) {
          const customer = await stripe.customers.retrieve(
            invoice.customer as string
          ) as Stripe.Customer;

          await handlePaymentFailed(invoice, customer);
        }
        break;
      }

      default:
        console.log(`unhandled event type: ${event.type}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error("error processing webhook:", error);
    return NextResponse.json(
      { error: "webhook processing failed" },
      { status: 500 }
    );
  }
}

export const { GET } = handler;

