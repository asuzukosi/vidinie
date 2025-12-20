import { betterAuth } from "better-auth";
import { mongodbAdapter } from "better-auth/adapters/mongodb";
import { getMongoClient } from "@/lib/db";

const client = await getMongoClient();
const db = client.db(process.env.DB_NAME || "mydatabase");

export const auth = betterAuth({
  appName: "Vidinie",
  database: mongodbAdapter(db, { client }),
  emailAndPassword: {
    enabled: true,
  },
  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_OAUTH_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_OAUTH_CLIENT_SECRET as string,
      prompt: "select_account",
    },
  },
});
