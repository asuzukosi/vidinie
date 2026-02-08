/**
 * better-auth stripe subscription management helpers
 */

import { authClient } from "@/lib/auth-client";

export interface SubscriptionInfo {
  id: string;
  subscriptionId: string | undefined;
  status: string;
  referenceId: string;
  plan: string;
  priceId: string;
  currentPeriodStart: Date;
  currentPeriodEnd: Date;
  cancelAtPeriodEnd: boolean | undefined;
  limits: Record<string, unknown> | undefined;
}

/**
 * convert better-auth subscription to SubscriptionInfo format
 */
function convertSubscriptionToInfo(sub: any): SubscriptionInfo {
  return {
    id: sub.id,
    subscriptionId: sub.stripeSubscriptionId,
    status: sub.status,
    plan: sub.plan,
    referenceId: sub.referenceId,
    priceId: sub.priceId || "",
    currentPeriodStart: sub.periodStart ? new Date(sub.periodStart) : new Date(),
    currentPeriodEnd: sub.periodEnd ? new Date(sub.periodEnd) : new Date(),
    cancelAtPeriodEnd: sub.cancelAtPeriodEnd || false,
    limits: sub.limits,
  };
}

/**
 * get all subscriptions from better-auth
 */
export async function getAllSubscriptions(): Promise<SubscriptionInfo[]> {
  try {
    const { data: subscriptions, error } = await authClient.subscription.list();
    if (error) {
      console.error("error listing subscriptions:", error);
      return [];
    }
    if (!subscriptions || subscriptions.length === 0) {
      return [];
    }
    return subscriptions.map(convertSubscriptionToInfo);
  } catch (error) {
    console.error("error getting subscriptions:", error);
    return [];
  }
}

/*
 * get current subscription from better-auth
*/
export async function getCurrentSubscription(): Promise<SubscriptionInfo | null> {
  try {
    // get all subscriptions
    const subscriptions = await getAllSubscriptions();
    // if there are no subscriptions, return null
    if (subscriptions.length === 0) {
      return null;
    }
    // get the active subscription (status is "active" or "trialing")
    const activeSubscription = subscriptions.find(
      (sub) => sub.status === "active" || sub.status === "trialing"
    );

    return activeSubscription || null;
  } catch (error) {
    // if there is an error, return null
    console.error("error getting subscription:", error);
    return null;
  }
}

/*
 * create or upgrade subscription to a plan
*/
export async function createOrUpgradeSubscription(
  plan: string,
  successUrl?: string,
  cancelUrl?: string
): Promise<{ url: string }> {
  // get the current subscription
  const currentSubscription = await getCurrentSubscription();
  // if the current subscription is the same as the plan, return
  if (currentSubscription?.plan === plan) {
    throw new Error("subscription is already on the same plan");
  }
  // create or upgrade subscription
  const result = await authClient.subscription.upgrade({
    plan,
    successUrl: successUrl || `${window.location.origin}/success`,
    cancelUrl: cancelUrl || `${window.location.origin}/cancel`,
    subscriptionId: currentSubscription?.subscriptionId || undefined,
  });
  // if there is an error, throw an error
  if (result.error) {
    throw new Error(result.error.message || "failed to create/upgrade subscription");
  }
  // if there is no checkout url, throw an error
  if (!result.data.url) {
    throw new Error("no checkout URL returned");
  }
  return { url: result.data.url };
}

/*
 * cancel subscription
*/
export async function cancelSubscription(referenceId: string, 
    customerType: "user" | "organization" | undefined, 
    subscriptionId: string | undefined, 
    returnUrl: string): Promise<void> {

  // cancel subscription
  const result = await authClient.subscription.cancel({ referenceId, customerType, subscriptionId, returnUrl });
  
  // if there is an error, throw an error
  if (result.error) {
    throw new Error(result.error.message || "failed to cancel subscription");
  }
}

/*
 * reactivate a cancelled subscription
*/
export async function reactivateSubscription(referenceId: string, 
    customerType: "user" | "organization" | undefined, 
    subscriptionId: string | undefined, 
    ): Promise<void> {
  const result = await authClient.subscription.restore({ referenceId, customerType, subscriptionId });
  
  if (result.error) {
    throw new Error(result.error.message || "Failed to reactivate subscription");
  }
}

/**
 * create billing portal session for self-service billing management
 */
export async function createCustomerPortalSession(
  returnUrl: string,
): Promise<string> {
  // get current subscription to get referenceId
  const currentSubscription = await getCurrentSubscription();
  // create billing portal session
  const { data, error } = await authClient.subscription.billingPortal({
    referenceId: currentSubscription?.referenceId,
    customerType: "user", // default to user
    returnUrl,
  });
  // if there is an error, throw an error
  if (error || !data?.url) {
    throw new Error(error?.message || "Failed to create billing portal session");
  }
  // return the billing portal url
  return data.url;
}

/**
 * get subscription limits for the current active subscription
 */
export async function getSubscriptionLimits(): Promise<Record<string, unknown> | undefined> {
  const subscription = await getCurrentSubscription();
  return subscription?.limits || undefined;
}
