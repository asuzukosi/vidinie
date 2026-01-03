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
import frontendClient from "@/lib/api/client";

interface CheckoutProps extends Omit<React.ComponentProps<"div">, "onError"> {
  priceId: string;
  planName?: string;
  planPrice?: string;
  planDescription?: string;
  quantity?: number;
  onSuccess?: () => void;
  onCheckoutError?: (error: Error) => void;
  buttonText?: string;
  showCard?: boolean;
  buttonVariant?: VariantProps<typeof buttonVariants>["variant"];
  buttonSize?: VariantProps<typeof buttonVariants>["size"];
  buttonClassName?: string;
}

export default function Checkout({
  priceId,
  planName,
  planPrice,
  planDescription,
  quantity = 1,
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

  const handleCheckout = async () => {
    if (!priceId) {
      toast.error("Invalid price ID", {
        description: "Please select a valid subscription plan.",
      });
      return;
    }
    setLoading(true);
    try {
      const { url } = await frontendClient.createCheckoutSession({
        priceId,
        quantity,
      });

      if (url) {
        if (onSuccess) {
          onSuccess();
        }
        // Redirect to Stripe checkout
        window.location.href = url;
        return;
      }

      throw new Error("No checkout URL returned from server");
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
          disabled={loading || !priceId}
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