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
} from "@/lib/emails";

// initialize stripe client for better-auth plugin
const stripeClient = new Stripe(process.env.NEXT_PUBLIC_STRIPE_SECRET_KEY || "", {
  apiVersion: "2025-11-17.clover",
});

// mongodb database client
const client = new MongoClient(process.env.MONGODB_URI || "mongodb://mongodb:27017/database");
const db = client.db(process.env.DB_NAME || "vidinie");

// Export db for use in webhook handlers (using the same connection Better Auth uses)
export { db };

export const auth = betterAuth({
    // mongodb database adapter
  database: mongodbAdapter(db, {client, transaction: false}),
  // database hooks for user lifecycle events
  databaseHooks: {
    user: {
      create: {
        after: async (user) => {
          // send welcome email to newly created user
          void sendWelcomeEmail(user.email, user.name || undefined).catch((error) => {
            console.error('Failed to send welcome email:', error);
          });
        },
      },
    },
  },
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
        console.log(`${user.email} has been successfully verified! request: ${request}`);
    },
  },
  // allow for email updates
  user: {
    changeEmail: {
      enabled: true,
      updateEmailWithoutVerification: true,
    },
    additionalFields: {
      videos_remaining: {
        type: "number",
        required: false,
        min: 0,
        defaultValue: 2,
        input: true,
      },
      videos_generated: {
        type: "number",
        required: false,
        defaultValue: 0,
        input: true,
      },
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
      // Note: Webhook handling is done in /api/webhooks/stripe/route.ts
      // stripeWebhookSecret is required by the plugin type but not used for webhook handling
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
      },
    }),
  ],
});

export type Session = typeof auth.$Infer.Session;

