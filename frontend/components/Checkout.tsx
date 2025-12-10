"use client";

import { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { Button } from "@/components/ui/button";


const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

export default function Checkout() {
    const [loading, setLoading] = useState(false);

    const handleCheckout = async () => {
        setLoading(true);
        try {
            const response = await fetch("/api/checkout", {
                headers: {
                    "Content-Type": "application/json",
                },
                method: "POST",
                body: JSON.stringify({ priceId: "real_price_id", quantity: 1 }),
            });
            const { sessionId } = await response.json();
            const stripe = await stripePromise;
            if (stripe) {
                const { error } = await (stripe as any).redirectToCheckout({ sessionId });
                if (error) {
                    console.error("error redirecting to checkout", error);
                }
            }
        } catch (error: any) {
            console.error("error checking out", error);
        } finally {
            setLoading(false);
        }
    }


    return (
        <Button onClick={handleCheckout} disabled={loading}>
            {loading ? "Loading..." : "Checkout"}
        </Button>
    );
}