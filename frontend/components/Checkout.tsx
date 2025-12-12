"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

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
                body: JSON.stringify({ priceId: "price_1SdQlk2M9n75azYSm0Q7ffjU", quantity: 1 }),
            });

            if (!response.ok) {
                throw new Error("Failed to create checkout session");
            }

            const { sessionId, url } = await response.json();
            console.log("sessionId", sessionId);

            if (url) {
                window.location.href = url;
                return;
            }

            throw new Error("No checkout URL returned from server");
        } catch (error: any) {
            console.error("error checking out", error);
            alert(error.message || "An error occurred during checkout");
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