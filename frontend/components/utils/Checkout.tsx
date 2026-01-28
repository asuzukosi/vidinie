"use client";

import { useState } from "react";
import { Button, type buttonVariants } from "@/components/ui/button";
import type { VariantProps } from "class-variance-authority";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { createOrUpgradeSubscription } from "@/lib/stripe";
import { event } from "@/lib/gtag";
import { useSelector } from "react-redux";
import type { RootState } from "@/lib/store/store";

interface CheckoutProps extends Omit<React.ComponentProps<"div">, "onError"> {
  plan: string; // plan id for better-auth subscription - required
  planName?: string;
  planPrice?: string;
  planDescription?: string;
  onSuccess?: () => void;
  onCheckoutError?: (error: Error) => void;
  buttonText?: string;
  showCard?: boolean;
  buttonVariant?: VariantProps<typeof buttonVariants>["variant"];
  buttonSize?: VariantProps<typeof buttonVariants>["size"];
  buttonClassName?: string;
}

export default function Checkout({
  plan,
  planName,
  planPrice,
  planDescription,
  onSuccess,
  onCheckoutError,
  buttonText = "Subscribe",
  showCard = false,
  buttonVariant = "default",
  buttonSize = "lg",
  buttonClassName,
  className,
  ...props
}: CheckoutProps) {
  const [loading, setLoading] = useState(false);
  const user = useSelector((state: RootState) => state.auth.user);
  const handleCheckout = async () => {
    event({
      action: "checkout_started",
      category: "checkout",
      label: user?.email || "unknown",
      value: 1,
    });
    
    if (!plan) {
      toast.error("Invalid plan", {
        description: "Please select a valid subscription plan.",
      });
      return;
    }
    
    setLoading(true);
    try {
      // create or upgrade subscription using better-auth
      const result = await createOrUpgradeSubscription(
        plan,
        `${window.location.origin}/success`,
        `${window.location.origin}/cancel`
      );

      if (!result.url) {
        throw new Error("link to checkout page not returned");
      }

      if (onSuccess) {
        onSuccess();
      }
      // redirect to stripe checkout page
      window.location.href = result.url;
    } catch (error: any) {
      console.error("Checkout error:", error);
      const errorMessage = error.message || "An error occurred during checkout";
      
      toast.error("Checkout failed", {
        description: errorMessage,
      });

      if (onCheckoutError) {
        onCheckoutError(error);
      }
    } finally {
      setLoading(false);
    }
  };

  const content = (
    <FieldGroup>
      {showCard && planName && (
        <Field>
          <FieldLabel>Selected Plan</FieldLabel>
          <div className="space-y-1">
            <div className="font-semibold">{planName}</div>
            {planPrice && (
              <div className="text-sm text-muted-foreground">{planPrice}</div>
            )}
            {planDescription && (
              <FieldDescription>{planDescription}</FieldDescription>
            )}
          </div>
        </Field>
      )}
      <Field>
        <Button
          onClick={handleCheckout}
          disabled={loading || !plan}
          variant={buttonVariant}
          size={buttonSize}
          className={cn("w-full", buttonClassName)}
        >
          {loading ? "Processing..." : buttonText}
        </Button>
        {showCard && (
          <FieldDescription>
            You will be redirected to Stripe to complete your payment securely.
          </FieldDescription>
        )}
      </Field>
    </FieldGroup>
  );

  if (showCard) {
    return (
      <Card className={cn("", className)} {...props}>
        <CardHeader>
          <CardTitle>Complete Your Subscription</CardTitle>
          <CardDescription>
            Secure payment processing powered by Stripe
          </CardDescription>
        </CardHeader>
        <CardContent>{content}</CardContent>
      </Card>
    );
  }

  return (
    <div className={cn("", className)} {...props}>
      {content}
    </div>
  );
}
