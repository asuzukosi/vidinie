import Checkout from '@/components/utils/Checkout';

export default function PricingPage() {
  // todo: replace with actual priceId from your pricing plans
  // this is a placeholder - you should fetch pricing plans and allow users to select one
  const placeholderPriceId = process.env.NEXT_PUBLIC_STRIPE_PRICE_ID || '';

  if (!placeholderPriceId) {
    return (
      <div className="p-4">
        <h1>Pricing</h1>
        <p className="text-muted-foreground">
          Please configure a Stripe price ID to enable checkout.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4">
      <h1>Buy Our Product</h1>
      <Checkout 
        priceId={placeholderPriceId}
        planName="Subscription Plan"
        buttonText="Subscribe Now"
      />
    </div>
  );
}