import { betterAuth } from "better-auth";
import { mongodbAdapter } from "better-auth/adapters/mongodb";
import { getDatabase } from "./db";
export const auth = betterAuth({
  database: mongodbAdapter(await getDatabase()),
  emailAndPassword: {
    enabled: true,
    autoSignIn: true,
  },
});
