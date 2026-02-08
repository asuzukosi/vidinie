/**
 * stripe webhook handlers
 */

import Stripe from "stripe";
import { db } from "@/lib/auth"; // database client
import {
  sendSubscriptionActivatedEmail,
  sendSubscriptionUpdatedEmail,
  sendSubscriptionCanceledEmail,
  sendPaymentSucceededEmail,
  sendPaymentFailedEmail,
} from "@/lib/emails";

async function getUserByStripeCustomerId(customerId: string) {
    const userDoc = await db.collection('users').findOne({
      stripe_customer_id: customerId,
    });
    if (!userDoc) {
      return null;
    }
    return userDoc;
}

function getPlanNameFromPriceId(priceId: string | undefined): string {
  if (!priceId) return "unknown";
  if (priceId === process.env.NEXT_PUBLIC_STARTER_PLAN_PRICE_ID) {
    return "starter";
  } else if (priceId === process.env.NEXT_PUBLIC_PROFESSIONAL_PLAN_PRICE_ID) {
    return "professional";
  }
  return "unknown";
}

function getCreditsToAddByPlan(planName: string): number {
  if (planName === "starter") {
    return 5;
  } else if (planName === "professional") {
    return 20;
  }
  return 0;
}


async function updateUserVideosRemaining(userId: string, planName: string): Promise<number> {
    // get credits to add based on plan
    const creditsToAdd = getCreditsToAddByPlan(planName);

    if (creditsToAdd === 0) {
        console.log(`no credits to add for plan: ${planName}`);
        return 0;
    }

    // get current user to check current videos_remaining value
    const user = await db.collection('users').findOne({ id: userId });
    if (!user) {
        console.warn(`user not found with id: ${userId}`);
        return 0;
    }
    const currentVideosRemaining = (user as any).videos_remaining || 0;
    const newVideosRemaining = currentVideosRemaining + creditsToAdd;
    // update user directly in database
    await db.collection('users').updateOne(
        { id: userId },
        { $set: { videos_remaining: newVideosRemaining } }
    );
    console.log(`updated videos_remaining for user ${userId}: ${currentVideosRemaining} -> ${newVideosRemaining} (added ${creditsToAdd} for ${planName} plan)`);
    return creditsToAdd;
}

export async function handleSubscriptionComplete(
  subscription: Stripe.Subscription,
  customer: Stripe.Customer
) {
    console.log("subscription complete called");
    console.log(`subscription ${subscription.id} completed for customer ${customer.id}`);
    const user = await getUserByStripeCustomerId(customer.id);
    if (!user) {
        console.warn(`user not found for customer ${customer.id}`);
        return;
        }
    const priceId = subscription.items.data[0]?.price.id;
    const planName = getPlanNameFromPriceId(priceId);
    if (user.email) {
        void sendSubscriptionActivatedEmail(user.email, planName).catch((error) => {
            console.error('failed to send subscription activated email:', error);
        });
    }
    console.log(`subscription completed for user ${user.email} on plan ${planName}`);
}

export async function handleSubscriptionCreated(
  subscription: Stripe.Subscription,
  customer: Stripe.Customer
) {
  console.log("subscription created called");
  console.log(`subscription ${subscription.id} created for customer ${customer.id}`);
  const user = await getUserByStripeCustomerId(customer.id);
  if (!user) {
    console.warn(`user not found for customer ${customer.id}`);
    return;
  }
  const priceId = subscription.items.data[0]?.price.id;
  const planName = getPlanNameFromPriceId(priceId);

  console.log(`subscription created for user ${user.email} on plan ${planName}`);
  if (user.email) {
      void sendSubscriptionActivatedEmail(user.email, planName).catch((error) => {
        console.error('Failed to send subscription created email:', error);
      });
  }
}

export async function handleSubscriptionUpdated(
  subscription: Stripe.Subscription,
  customer: Stripe.Customer
) {
  console.log("subscription updated called");
  console.log(`subscription ${subscription.id} updated for customer ${customer.id}`);
    const user = await getUserByStripeCustomerId(customer.id);
    if (!user) {
      console.warn(`user not found for customer ${customer.id}`);
      return;
    }
    const priceId = subscription.items.data[0]?.price.id;
    const planName = getPlanNameFromPriceId(priceId);
    if (user.email) {
      void sendSubscriptionUpdatedEmail(user.email, planName).catch((error) => {
        console.error('failed to send subscription updated email:', error);
      });
    }
    console.log(`subscription updated for user ${user.email} to plan ${planName}`);
}

export async function handleSubscriptionCanceled(
  subscription: Stripe.Subscription,
  customer: Stripe.Customer
) {
  console.log("subscription canceled called");
  console.log(`subscription ${subscription.id} canceled for customer ${customer.id}`);
  const user = await getUserByStripeCustomerId(customer.id);
  if (!user) {
    console.warn(`user not found for customer ${customer.id}`);
    return;
  }
    const priceId = subscription.items.data[0]?.price.id;
    const planName = getPlanNameFromPriceId(priceId);
    const cancelAt = subscription.cancel_at 
      ? new Date(subscription.cancel_at * 1000).toLocaleDateString()
      : undefined;
    if (user.email) {
      void sendSubscriptionCanceledEmail(user.email, planName, cancelAt).catch((error) => {
        console.error('Failed to send subscription canceled email:', error);
      });
    }   
    console.log(`subscription canceled for user ${user.email} on plan ${planName}`);
}

export async function handleSubscriptionDeleted(
  subscription: Stripe.Subscription,
  customer: Stripe.Customer
) {
  console.log("subscription deleted called");
  console.log(`subscription ${subscription.id} deleted for customer ${customer.id}`);
  const user = await getUserByStripeCustomerId(customer.id);
  if (!user) {
    console.warn(`user not found for customer ${customer.id}`);
    return;
  }
    const priceId = subscription.items.data[0]?.price.id;
    const planName = getPlanNameFromPriceId(priceId);
    if (user.email) {
      void sendSubscriptionCanceledEmail(user.email, planName).catch((error) => {
        console.error('Failed to send subscription deleted email:', error);
      });
    }
    console.log(`subscription deleted for user ${user.email} on plan ${planName}`);
}
export async function handlePaymentSucceeded(
  invoice: Stripe.Invoice,
  customer: Stripe.Customer
) {
  console.log("payment succeeded called");
  console.log(`payment succeeded for invoice ${invoice.id}`);
  console.log(`customer id: ${customer.id}`);
  
  const subscriptionId = typeof (invoice as any).subscription === 'string' 
    ? (invoice as any).subscription 
    : (invoice as any).subscription?.id || "N/A";
  console.log(`subscription id: ${subscriptionId}`);
  
  // get price ID and plan name from invoice
  const lineItem = invoice.lines?.data[0];
  const priceId = (lineItem as any)?.price?.id || (lineItem as any)?.plan?.id || null;
  const planName = getPlanNameFromPriceId(priceId);
  console.log(`plan: ${planName}`);
  const user = await getUserByStripeCustomerId(customer.id);
  if (!user) {
    console.warn(`user not found for customer ${customer.id}`);
    return;
  }
  const isSubscriptionInvoice = invoice.billing_reason === 'subscription_create' || 
                                 invoice.billing_reason === 'subscription_cycle';
  let creditsAdded = 0;
  if (isSubscriptionInvoice && subscriptionId !== "N/A") {
    creditsAdded = await updateUserVideosRemaining(user.id, planName);
    console.log(`credits added: ${creditsAdded} (billing_reason: ${invoice.billing_reason})`);
  } else {
    console.log(`skipping credit addition - not a subscription invoice (billing_reason: ${invoice.billing_reason})`);
  }
  
  console.log(`payment succeeded for user ${user.email}`);
  console.log(`amount paid: ${(invoice.amount_paid / 100).toFixed(2)} ${invoice.currency?.toUpperCase()}`);
  
  // send payment succeeded email
  if (user.email) {
    void sendPaymentSucceededEmail(
      user.email,
      invoice.amount_paid,
      invoice.currency || 'usd',
      planName,
      creditsAdded
    ).catch((error) => {
      console.error('failed to send payment succeeded email:', error);
    });
  }
}

export async function handlePaymentFailed(
  invoice: Stripe.Invoice,
  customer: Stripe.Customer
) {
  console.log("payment failed called");
  console.log(`payment failed for invoice ${invoice.id}`);
  console.log(`customer id: ${customer.id}`);
  
  const subscriptionId = typeof (invoice as any).subscription === 'string' 
    ? (invoice as any).subscription 
    : (invoice as any).subscription?.id || "N/A";
  console.log(`subscription id: ${subscriptionId}`);
  
  // get price ID and plan name from invoice
  const lineItem = invoice.lines?.data[0];
  const priceId = (lineItem as any)?.price?.id || (lineItem as any)?.plan?.id || null;
  const planName = getPlanNameFromPriceId(priceId);
  console.log(`plan: ${planName}`);
  
  const user = await getUserByStripeCustomerId(customer.id);
  if (!user) {
    console.warn(`user not found for customer ${customer.id}`);
    return;
  }
  
  // get payment error details
  const lastPaymentError = (invoice as any).last_payment_error;
  const errorMessage = lastPaymentError?.message || undefined;
  const attemptCount = invoice.attempt_count || 0;
  
  console.log(`payment failed for user ${user.email}`);
  console.log(`amount attempted: ${(invoice.amount_due / 100).toFixed(2)} ${invoice.currency?.toUpperCase()}`);
  console.log(`attempt count: ${attemptCount}`);
  if (errorMessage) {
    console.log(`payment error: ${errorMessage}`);
  }
  
  // send payment failed email
  if (user.email) {
    void sendPaymentFailedEmail(
      user.email,
      invoice.amount_due,
      invoice.currency || 'usd',
      planName,
      attemptCount,
      errorMessage
    ).catch((error) => {
      console.error('failed to send payment failed email:', error);
    });
  }
}
