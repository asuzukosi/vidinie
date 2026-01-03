"use client";

import { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { LoadingPage } from "@/components/utils/LoadingPage";
import { Badge } from "@/components/ui/badge";
import Checkout from "@/components/utils/Checkout";
import frontendClient from "@/lib/api/client";
import type { RootState } from "@/lib/store/store";
import client from "@/lib/sdk/client";
import type { PaymentMethod } from "@/lib/sdk/types";
import { setUser } from "@/lib/store/slices/userSlice";

export default function SettingsPage() {
  const user = useSelector((state: RootState) => state.auth.user);
  const dispatch = useDispatch();
  const [isLoadingPortal, setIsLoadingPortal] = useState(false);
  const [isLoadingPaymentMethods, setIsLoadingPaymentMethods] = useState(true);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [isLoadingCustomerId, setIsLoadingCustomerId] = useState(true);
  
  const subscriptionStatus = user?.current_subscription || "free";

  useEffect(() => {
    loadPaymentMethods();
    loadCustomerId();
  }, []);

  const loadCustomerId = async () => {
    try {
      setIsLoadingCustomerId(true);
      // first check if customer ID is in Redux state
      if (user?.stripe_customer_id) {
        setCustomerId(user.stripe_customer_id);
        setIsLoadingCustomerId(false);
        return;
      }
      
      // if not in Redux, fetch from backend
      const response = await client.getCustomerId();
      setCustomerId(response.stripe_customer_id);
      
      // update Redux if customer ID was found
      if (response.stripe_customer_id && user) {
        dispatch(setUser({
          ...user,
          stripe_customer_id: response.stripe_customer_id,
        }));
      }
    } catch (error: any) {
      console.error("Failed to load customer ID:", error);
    } finally {
      setIsLoadingCustomerId(false);
    }
  };

  const loadPaymentMethods = async () => {
    try {
      setIsLoadingPaymentMethods(true);
      const methods = await client.getPaymentMethods();
      setPaymentMethods(methods);
    } catch (error: any) {
      console.error("Failed to load payment methods:", error);
      toast.error("Failed to load payment methods", {
        description: error.message,
      });
    } finally {
      setIsLoadingPaymentMethods(false);
    }
  };

  const handleManageBilling = async () => {
    setIsLoadingPortal(true);
    try {
      // get customer id from state or fetch from backend
      let currentCustomerId = customerId;
      
      if (!currentCustomerId) {
        // try to get from backend
        try {
          const response = await client.getCustomerId();
          currentCustomerId = response.stripe_customer_id;
          setCustomerId(currentCustomerId);
          
          // update redux if customer id was found
          if (currentCustomerId && user) {
            dispatch(setUser({
              ...user,
              stripe_customer_id: currentCustomerId,
            }));
          }
        } catch (error) {
          // customer id doesn't exist yet
        }
      }
      
      if (!currentCustomerId) {
        toast.error("No customer account found", {
          description: "Please complete a subscription purchase first to create a customer account.",
        });
        setIsLoadingPortal(false);
        return;
      }
      
      const { url } = await frontendClient.createCustomerPortalSession({
        customerId: currentCustomerId,
        returnUrl: `${window.location.origin}/settings`,
      });

      if (url) {
        window.location.href = url;
      }
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
      period: "forever",
      features: ["Basic features", "Limited usage"],
    },
    {
      id: "starter",
      name: "Starter",
      price: "$9.99",
      period: "per month",
      priceId: "price_1SdQlk2M9n75azYSm0Q7ffjU", // replace with your actual price id
      features: ["All basic features", "Increased usage", "Priority support"],
    },
    {
      id: "professional",
      name: "Professional",
      price: "$29.99",
      period: "per month",
      priceId: "price_professional", // replace with your actual price id
      features: [
        "All starter features",
        "Unlimited usage",
        "Advanced features",
        "24/7 support",
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
        {/* payment information */}
        <Card>
          <CardHeader>
            <CardTitle>Payment Information</CardTitle>
            <CardDescription>
              Manage your payment methods and billing details
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FieldGroup>
              {isLoadingPaymentMethods ? (
                <Field>
                  <FieldLabel>Payment Methods</FieldLabel>
                  <div className="text-sm text-muted-foreground">Loading payment methods...</div>
                </Field>
              ) : paymentMethods.length > 0 ? (
                <>
                  <Field>
                    <FieldLabel>Payment Methods</FieldLabel>
                    <div className="space-y-3">
                      {paymentMethods.map((method) => (
                        <div
                          key={method.id}
                          className="flex items-center justify-between p-4 border rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <div className="text-2xl">
                              💳
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium capitalize">
                                  {method.card?.brand || method.type} ••••{" "}
                                  {method.card?.last4}
                                </span>
                                {method.is_default && (
                                  <Badge variant="secondary" className="text-xs">
                                    Default
                                  </Badge>
                                )}
                              </div>
                              {method.card && (
                                <div className="text-sm text-muted-foreground">
                                  Expires {String(method.card.exp_month).padStart(2, '0')}/
                                  {method.card.exp_year}
                                </div>
                              )}
                              <div className="text-xs text-muted-foreground mt-1">
                                Added {new Date(method.created_at).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {!method.is_default && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={async () => {
                                  try {
                                    await client.updatePaymentMethod(method.id, { is_default: true });
                                    toast.success("Payment method set as default");
                                    loadPaymentMethods();
                                  } catch (error: any) {
                                    toast.error("Failed to update payment method", {
                                      description: error.message,
                                    });
                                  }
                                }}
                              >
                                Set Default
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={async () => {
                                if (confirm("Are you sure you want to delete this payment method?")) {
                                  try {
                                    await client.deletePaymentMethod(method.id);
                                    toast.success("Payment method deleted");
                                    loadPaymentMethods();
                                  } catch (error: any) {
                                    toast.error("Failed to delete payment method", {
                                      description: error.message,
                                    });
                                  }
                                }
                              }}
                            >
                              Delete
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Field>
                  <Field>
                    <Button
                      variant="outline"
                      onClick={handleManageBilling}
                      disabled={isLoadingPortal}
                    >
                      {isLoadingPortal
                        ? "Loading..."
                        : "Manage Payment Methods"}
                    </Button>
                    <FieldDescription>
                      Add, update, or remove payment methods through Stripe
                    </FieldDescription>
                  </Field>
                </>
              ) : (
                <Field>
                  <FieldLabel>No Payment Methods</FieldLabel>
                  <p className="text-sm text-muted-foreground mb-4">
                    You don't have any payment methods on file. Add one to
                    subscribe to a plan.
                  </p>
                  <Button
                    variant="outline"
                    onClick={handleManageBilling}
                    disabled={isLoadingPortal}
                  >
                    {isLoadingPortal ? "Loading..." : "Add Payment Method"}
                  </Button>
                </Field>
              )}
            </FieldGroup>
          </CardContent>
        </Card>

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
                      className={
                        subscriptionStatus === plan.id
                          ? "border-primary"
                          : ""
                      }
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
                      <CardContent>
                        <ul className="space-y-2 mb-4">
                          {plan.features.map((feature, idx) => (
                            <li key={idx} className="text-sm flex items-start gap-2">
                              <span>✓</span>
                              <span>{feature}</span>
                            </li>
                          ))}
                        </ul>
                        {subscriptionStatus === plan.id ? (
                          <Button disabled variant="outline" className="w-full">
                            Current Plan
                          </Button>
                        ) : plan.priceId ? (
                          <Checkout
                            priceId={plan.priceId}
                            planName={plan.name}
                            planPrice={plan.price}
                            buttonText={plan.id === "free" ? "Downgrade" : "Upgrade"}
                            showCard={false}
                            buttonVariant={plan.id === "professional" ? "default" : "outline"}
                            buttonSize="default"
                            className="w-full"
                          />
                        ) : (
                          <Button
                            variant="outline"
                            className="w-full"
                            disabled
                          >
                            Current Plan
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </Field>

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
            </FieldGroup>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
