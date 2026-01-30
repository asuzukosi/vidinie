import { betterAuth } from "better-auth";
import { jwt } from "better-auth/plugins"
import { stripe } from "@better-auth/stripe";
import { MongoClient } from "mongodb";
import { mongodbAdapter } from "better-auth/adapters/mongodb";

import Stripe from "stripe";

// initialize stripe client for better-auth plugin
const stripeClient = new Stripe(process.env.NEXT_PUBLIC_STRIPE_SECRET_KEY || "", {
  apiVersion: "2025-11-17.clover",
});

// mongodb database client
const client = new MongoClient(process.env.MONGODB_URI || "mongodb://localhost:27017/database");
const db = client.db(process.env.DB_NAME || "vidinie");

// dummy email sending function for email verification
const sendEmail = async ({ to, subject, text, token }: { to: string, subject: string, text: string, token: string }) => {
    console.log(`Sending email to ${to} with subject ${subject} and text ${text}`);
    console.log(`Verification token: ${token}`);
};

// separate email sending function for password reset
const sendPasswordResetEmail = async ({ user, url, token }: { user: { email: string }, url: string, token: string }) => {
    console.log(`Sending password reset email to ${user.email}`);
    console.log(`Password reset URL: ${url}`);
    console.log(`Reset token: ${token}`);
};

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
        void sendEmail({
          to: user.email,
          subject: "Verify your email address",
          text: `Click the link to verify your email: ${url}`,
          token,    // verification token
        });
      },
    // after email verification function
    async afterEmailVerification(user, request) {
        // custom logic here, e.g., grant access to premium features
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
      void sendPasswordResetEmail({
        user,
        url,
        token,
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
        },
        onSubscriptionCreated: async ({ event, subscription, stripeSubscription, plan }) => {
            // called when a subscription is created outside the checkout flow (e.g. Stripe dashboard)
            console.log(`Subscription ${subscription.id} created for plan ${plan.name} with stripe subscription ${stripeSubscription.id} and event ${event}`);
        },
        onSubscriptionUpdate: async ({ event, subscription }) => {
            // called when a subscription is updated
            console.log(`Subscription ${subscription.id} updated with event ${event}`);
        },
        onSubscriptionCancel: async ({ event, subscription, stripeSubscription, cancellationDetails }) => {
            // called when a subscription is canceled
            console.log(`Subscription ${subscription.id} canceled with stripe subscription ${stripeSubscription.id} and cancellation details ${cancellationDetails} and event ${event}`);
        },
        onSubscriptionDeleted: async ({ event, subscription, stripeSubscription }) => {
            // called when a subscription is deleted
            console.log(`Subscription ${subscription.id} deleted with stripe subscription ${stripeSubscription.id} and event ${event}`);
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

