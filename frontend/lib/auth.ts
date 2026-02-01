import { betterAuth } from "better-auth";
import { jwt } from "better-auth/plugins"
import { stripe } from "@better-auth/stripe";
import { MongoClient } from "mongodb";
import { mongodbAdapter } from "better-auth/adapters/mongodb";
import Stripe from "stripe";
import {
  sendVerificationEmail,
  sendPasswordResetEmail,
  sendWelcomeEmail,
  sendSubscriptionActivatedEmail,
  sendSubscriptionUpdatedEmail,
  sendSubscriptionCanceledEmail,
} from "@/lib/emails";

// initialize stripe client for better-auth plugin
const stripeClient = new Stripe(process.env.NEXT_PUBLIC_STRIPE_SECRET_KEY || "", {
  apiVersion: "2025-11-17.clover",
});

// mongodb database client
const client = new MongoClient(process.env.MONGODB_URI || "mongodb://localhost:27017/database");
const db = client.db(process.env.DB_NAME || "vidinie");


export const auth = betterAuth({
    // mongodb database adapter
  database: mongodbAdapter(db, {client, transaction: false}),
  // email verification
  emailVerification: {
    // send verification email on sign up
    sendOnSignUp: true,
    // automatically sign in user after email verification
    autoSignIn: true,
    // send verification email on sign up function
    sendVerificationEmail: async ({ user, url, token }) => {
        void sendVerificationEmail(user.email, url).catch((error) => {
          console.error('Failed to send verification email:', error);
        });
      },
    // after email verification function
    async afterEmailVerification(user, request) {
        // send welcome email after email verification
        void sendWelcomeEmail(user.email, user.name || undefined).catch((error) => {
          console.error('Failed to send welcome email:', error);
        });
        console.log(`${user.email} has been successfully verified! request: ${request}`);
    },
  },
  // allow for email updates
  user: {
    changeEmail: {
      enabled: true,
    },
  },
  // email and password authentication
  emailAndPassword: {
    enabled: true,
  },
  // password reset configuration
  forgotPassword: {
    // send password reset email function
    sendPasswordResetEmail: async ({ user, url, token }: { user: { email: string }, url: string, token: string }) => {
      void sendPasswordResetEmail(user.email, url).catch((error) => {
        console.error('Failed to send password reset email:', error);
      });
    },
    // after password reset callback
    async afterPasswordReset(user: { email: string }, request: any) {
      // log password reset event
      console.log(`${user.email} has successfully reset their password! request: ${request}`);
    },
  },
  // social providers for authentication
  socialProviders: {
    // google authentication
    google: {
      clientId: process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID || "",
      clientSecret: process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_SECRET || "",
    },
  },
  // plugins for authentication
  plugins: [
    // jwt plugin for token verification used by the backend
    jwt(),
    // stripe plugin for subscription management
    stripe({
      // stripe client for subscription management
      stripeClient,
      // stripe webhook secret for verifying webhook signatures
      stripeWebhookSecret: process.env.NEXT_PUBLIC_STRIPE_WEBHOOK_SECRET || "",
      // create stripe customer on signup
      createCustomerOnSignUp: true, // automatically create stripe customer on signup
      // subscription management configuration
      subscription: {
        enabled: true,
        // subscription plans configuration
        plans: [
          {
            name: "starter",
            priceId: process.env.NEXT_PUBLIC_STARTER_PLAN_PRICE_ID || "",
            // annualDiscountPriceId: process.env.NEXT_PUBLIC_STARTER_PLAN_ANNUAL_DISCOUNT_PRICE_ID || "",
            limits: {
              videos: 5, // 5 videos per month
            },
          },
          {
            name: "professional",
            priceId: process.env.NEXT_PUBLIC_PROFESSIONAL_PLAN_PRICE_ID || "",
            // annualDiscountPriceId: process.env.NEXT_PUBLIC_PROFESSIONAL_PLAN_ANNUAL_DISCOUNT_PRICE_ID || "",
            limits: {
              videos: 20, // 20 videos per month
            },
          },
        ],
        onSubscriptionComplete: async ({ event, subscription, stripeSubscription, plan }) => {
            // called when a subscription is successfully created via checkout
            console.log(`Subscription ${subscription.id} completed for plan ${plan.name} with stripe subscription ${stripeSubscription.id} and event ${event}`);
            
            // get user email from subscription using referenceId (which is the userId)
            const sub = subscription as any;
            const userId = sub.userId || sub.referenceId;
            if (userId) {
              const user = await db.collection('users').findOne({ id: userId });
              if (user?.email) {
                void sendSubscriptionActivatedEmail(user.email, plan.name).catch((error) => {
                  console.error('Failed to send subscription activated email:', error);
                });
              }
            }
        },
        onSubscriptionCreated: async ({ event, subscription, stripeSubscription, plan }) => {
            // called when a subscription is created outside the checkout flow (e.g. Stripe dashboard)
            console.log(`Subscription ${subscription.id} created for plan ${plan.name} with stripe subscription ${stripeSubscription.id} and event ${event}`);
            
            // get user email from subscription using referenceId (which is the userId)
            const sub = subscription as any;
            const userId = sub.userId || sub.referenceId;
            if (userId) {
              const user = await db.collection('users').findOne({ id: userId });
              if (user?.email) {
                void sendSubscriptionActivatedEmail(user.email, plan.name).catch((error) => {
                  console.error('Failed to send subscription created email:', error);
                });
              }
            }
        },
        onSubscriptionUpdate: async ({ event, subscription }) => {
            // called when a subscription is updated
            console.log(`Subscription ${subscription.id} updated with event ${event}`);
            
            // get user email and plan from subscription
            const sub = subscription as any;
            const userId = sub.userId || sub.referenceId;
            const planName = sub.plan;
            if (userId && planName) {
              const user = await db.collection('users').findOne({ id: userId });
              if (user?.email) {
                void sendSubscriptionUpdatedEmail(user.email, planName).catch((error) => {
                  console.error('Failed to send subscription updated email:', error);
                });
              }
            }
        },
        onSubscriptionCancel: async ({ event, subscription, stripeSubscription, cancellationDetails }) => {
            // called when a subscription is canceled
            console.log(`Subscription ${subscription.id} canceled with stripe subscription ${stripeSubscription.id} and cancellation details ${cancellationDetails} and event ${event}`);
            
            // get user email and plan from subscription
            const sub = subscription as any;
            const userId = sub.userId || sub.referenceId;
            const planName = sub.plan;
            const cancelDetails = cancellationDetails as any;
            const cancelAt = cancelDetails?.cancelAt ? new Date(cancelDetails.cancelAt * 1000).toLocaleDateString() : 
                           cancelDetails?.cancel_at ? new Date(cancelDetails.cancel_at * 1000).toLocaleDateString() : undefined;
            
            if (userId && planName) {
              const user = await db.collection('users').findOne({ id: userId });
              if (user?.email) {
                void sendSubscriptionCanceledEmail(user.email, planName, cancelAt).catch((error) => {
                  console.error('Failed to send subscription canceled email:', error);
                });
              }
            }
        },
        onSubscriptionDeleted: async ({ event, subscription, stripeSubscription }) => {
            // called when a subscription is deleted
            console.log(`Subscription ${subscription.id} deleted with stripe subscription ${stripeSubscription.id} and event ${event}`);
            
            // get user email and plan from subscription
            const sub = subscription as any;
            const userId = sub.userId || sub.referenceId;
            const planName = sub.plan;
            
            if (userId && planName) {
              const user = await db.collection('users').findOne({ id: userId });
              if (user?.email) {
                void sendSubscriptionCanceledEmail(user.email, planName).catch((error) => {
                  console.error('Failed to send subscription deleted email:', error);
                });
              }
            }
        }
      },
    }),
  ],
//   not sure what these are for, will add them if needed
//   baseURL: process.env.BETTER_AUTH_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000",
//   basePath: "/api/auth",
//   trustedOrigins: (process.env.BETTER_AUTH_TRUSTED_ORIGINS || "http://localhost:3000,http://localhost:8000").split(","),
});

export type Session = typeof auth.$Infer.Session;

