"use client";

import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { LoadingPage } from "@/components/utils/loading-page";
import { Badge } from "@/components/ui/badge";
import { Checkout } from "@/components/utils/checkout-page";
import type { RootState } from "@/lib/store/store";
import { getCurrentSubscription, getAllSubscriptions, createCustomerPortalSession } from "@/lib/stripe";
import type { SubscriptionInfo } from "@/lib/stripe";

export default function SettingsPage() {
  const user = useSelector((state: RootState) => state.auth.user);
  const [isLoadingPortal, setIsLoadingPortal] = useState(false);
  const [isLoadingSubscriptions, setIsLoadingSubscriptions] = useState(true);
  const [subscriptions, setSubscriptions] = useState<SubscriptionInfo[]>([]);
  const [activeSubscription, setActiveSubscription] = useState<SubscriptionInfo | null>(null);
  useEffect(() => {
    loadSubscriptions();
  }, []);

  const loadSubscriptions = async () => {
    try {
      setIsLoadingSubscriptions(true);
      // get all subscriptions from Better Auth
      const allSubscriptions = await getAllSubscriptions();
      setSubscriptions(allSubscriptions);
      
      // get the active subscription
      const active = await getCurrentSubscription();
      setActiveSubscription(active);
    } catch (error: any) {
      console.error("Failed to load subscriptions:", error);
      toast.error("Failed to load subscriptions", {
        description: error.message,
      });
    } finally {
      setIsLoadingSubscriptions(false);
    }
  };

  // derive subscription status from active subscription
  const subscriptionStatus = activeSubscription?.plan || "free";

  const handleManageBilling = async () => {
    setIsLoadingPortal(true);
    try {
      const url = await createCustomerPortalSession(
        `${window.location.origin}/settings`
      );
      window.location.href = url;
    } catch (error: any) {
      toast.error("Failed to open billing portal", {
        description: error.message,
      });
    } finally {
      setIsLoadingPortal(false);
    }
  };


  if (!user) {
    return <LoadingPage />;
  }

  const subscriptionPlans = [
    {
      id: "free",
      name: "Free",
      price: "$0",
      priceId: "cancel",
      period: "forever",
      features: ["Basic features", "Limited usage"],
    },
    {
      id: "starter",
      name: "Starter",
      price: "$19.99",
      period: "per month",
      priceId: process.env.NEXT_PUBLIC_STARTER_PLAN_PRICE_ID,
      features: ["PDF & website support", 
        "Basic templates", 
        "Email support", 
        "5 Videos per month", 
        "Download videos",
      ],
    },
    {
      id: "professional",
      name: "Professional",
      price: "$49.99",
      period: "per month",
      priceId: process.env.NEXT_PUBLIC_PROFESSIONAL_PLAN_PRICE_ID,
      features: [
        "Everything in Starter",
        "Premium templates",
        "Custom branding",
        "20 Videos per month",
        "Download videos",
      ],
    },
  ];

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account settings, payment methods, and subscription
        </p>
      </div>

      <div className="grid gap-6">
        {/* Subscription Information */}
        <Card>
          <CardHeader>
            <CardTitle>Subscription</CardTitle>
            <CardDescription>
              Manage your subscription plan and billing
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FieldGroup>
              <Field>
                <FieldLabel>Current Plan</FieldLabel>
                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      subscriptionStatus === "free"
                        ? "secondary"
                        : subscriptionStatus === "professional"
                        ? "default"
                        : "outline"
                    }
                    className="capitalize"
                  >
                    {subscriptionStatus || "Free"}
                  </Badge>
                  {subscriptionStatus !== "free" && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleManageBilling}
                      disabled={isLoadingPortal}
                    >
                      Manage Subscription
                    </Button>
                  )}
                </div>
                <FieldDescription>
                  {subscriptionStatus === "free"
                    ? "You're currently on the free plan"
                    : `You're subscribed to the ${subscriptionStatus} plan`}
                </FieldDescription>
              </Field>

              <Separator />

              <Field>
                <FieldLabel>Available Plans</FieldLabel>
                <div className="grid gap-4 md:grid-cols-3 mt-4">
                  {subscriptionPlans.map((plan) => (
                    <Card
                      key={plan.id}
                      className={`flex flex-col border ${subscriptionStatus === plan.id
                          ? "border-primary"
                          : "border-border"
                      }`}
                    >
                      <CardHeader>
                        <CardTitle className="text-lg">{plan.name}</CardTitle>
                        <div className="text-2xl font-bold">
                          {plan.price}
                          {plan.period !== "forever" && (
                            <span className="text-sm font-normal text-muted-foreground">
                              /{plan.period}
                            </span>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent className="flex flex-col flex-1">
                        <ul className="space-y-2 mb-4 flex-1">
                          {plan.features.map((feature, idx) => (
                            <li key={idx} className="text-sm flex items-start gap-2">
                              <span>✓</span>
                              <span>{feature}</span>
                            </li>
                          ))}
                        </ul>
                        <div className="mt-auto">
                          {subscriptionStatus === plan.id ? (
                            <Button disabled variant="outline" className="w-full border-primary text-foreground">
                              Current Plan
                            </Button>
                          ) : plan.id !== "free" ? (
                            <Checkout
                              plan={plan.id}
                              planName={plan.name}
                              planPrice={plan.price}
                              buttonText="Upgrade"
                              showCard={false}
                              buttonVariant="default"
                              buttonSize="default"
                              className="w-full"
                            />
                          ) : (
                            <Button
                              variant="outline"
                              className="w-full"
                              disabled
                            >
                              Cancel Subscription
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </Field>

              {activeSubscription && (
                <>
                  <Separator />
                  <Field>
                    <Button
                      variant="outline"
                      onClick={handleManageBilling}
                      disabled={isLoadingPortal}
                    >
                      {isLoadingPortal
                        ? "Loading..."
                        : "Open Billing Portal"}
                    </Button>
                    <FieldDescription>
                      Access your billing portal to view invoices, update payment
                      methods, and manage your subscription
                    </FieldDescription>
                  </Field>
                </>
              )}

              <Separator />

              <Field>
                <FieldLabel>Subscription History</FieldLabel>
                {isLoadingSubscriptions ? (
                  <div className="text-sm text-muted-foreground">Loading subscriptions...</div>
                ) : subscriptions.length > 0 ? (
                  <div className="space-y-3">
                    {subscriptions.map((subscription) => (
                      <div
                        key={subscription.id}
                        className="flex items-center justify-between p-4 border border-border rounded-none"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium capitalize">
                              {subscription.plan}
                            </span>
                            <Badge variant={
                              subscription.status === "active" || subscription.status === "trialing" ? "default" :
                              subscription.status === "canceled" ? "secondary" : "outline"
                            }>
                              {subscription.status}
                            </Badge>
                            {subscription.id === activeSubscription?.id && (
                              <Badge variant="secondary" className="text-xs">
                                Active
                              </Badge>
                            )}
                          </div>
                          {subscription.currentPeriodStart && subscription.currentPeriodEnd && (
                            <div className="text-sm text-muted-foreground mt-1">
                              {subscription.currentPeriodStart.toLocaleDateString()} - {subscription.currentPeriodEnd.toLocaleDateString()}
                            </div>
                          )}
                          {subscription.cancelAtPeriodEnd && (
                            <div className="text-xs text-muted-foreground mt-1">
                              Cancels at period end
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No subscription history found.
                  </p>
                )}
              </Field>
            </FieldGroup>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
