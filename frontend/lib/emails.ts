import { Resend } from 'resend';

const resend = new Resend(process.env.NEXT_PUBLIC_RESEND_API_KEY || '');

interface EmailOptions {
  to: string;
  subject: string;
  body: string;
  replyTo?: string;
}

/**
 * send an email using Resend
 * @param options email options including recipient, subject, and body
 * @returns promise with email send result
 */
export async function sendEmail({ to, subject, body, replyTo = 'hello@vidinie.com' }: EmailOptions) {
  try {
    const { data, error } = await resend.emails.send({
      from: 'Vidinie <hello@vidinie.com>',
      to,
      replyTo,
      subject,
      text: body,
    });

    if (error) {
      console.error('Error sending email:', error);
      throw error;
    }

    console.log(`Email ${data?.id} sent successfully to ${to}`);
    return data;
  } catch (error) {
    console.error('Failed to send email:', error);
    throw error;
  }
}

/**
 * send welcome email to new users
 */
export async function sendWelcomeEmail(email: string, name?: string) {
  const greeting = name ? `Hey ${name}! 👋` : 'Hey there! 👋';
  
  const body = `${greeting}
Welcome to Vidinie, you're all set to turn documents and links into stunning videos in minutes.

Get started now:
🎥 Upload a document or paste a link
⚡ Let AI create your video
🎨 Customize and download

No complicated editors. No steep learning curve. Just fast, beautiful videos.

Ready to create? Jump in and make your first video!

Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie

P.S. Got ideas or feedback? I'm listening! 🙌`;

  return sendEmail({
    to: email,
    subject: 'Welcome to Vidinie! 🎬✨',
    body,
  });
}

/**
 * send email verification email
 */
export async function sendVerificationEmail(email: string, url: string) {
  const body = `Hey there! 👋

Thanks for signing up for Vidinie! To get started, please verify your email address by clicking the link below:

${url}

This link will expire in 24 hours.
If you didn't create an account, you can safely ignore this email.
Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie`;

  return sendEmail({
    to: email,
    subject: 'Verify your email address ✉️',
    body,
  });
}

/**
 * send password reset email
 */
export async function sendPasswordResetEmail(email: string, url: string) {
  const body = `Hey there! 👋

We received a request to reset your password for your Vidinie account.

Click the link below to reset your password:

${url}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.

Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie`;

  return sendEmail({
    to: email,
    subject: 'Reset your password 🔐',
    body,
  });
}

/**
 * send subscription activated email
 */
export async function sendSubscriptionActivatedEmail(email: string, planName: string) {
  const body = `Hey there! 👋

Great news! Your ${planName} subscription has been activated! 🎉

You now have access to:
✨ All premium features
🎥 More video creation capacity
🚀 Priority support

Start creating amazing videos right away!
Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie

P.S. Thank you for supporting Vidinie! 🙌`;

  return sendEmail({
    to: email,
    subject: `Your ${planName} subscription is active! 🎉`,
    body,
  });
}

/**
 * send subscription updated email
 */
export async function sendSubscriptionUpdatedEmail(email: string, planName: string) {
  const body = `Hey there! 👋

Your subscription has been updated to ${planName}! 🎉

Your new plan features are now active. Enjoy your upgraded experience!
Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie`;

  return sendEmail({
    to: email,
    subject: 'Subscription updated ✨',
    body,
  });
}

/**
 * send subscription canceled email
 */
export async function sendSubscriptionCanceledEmail(email: string, planName: string, cancellationDate?: string) {
  const body = `Hey there! 👋

We're sorry to see you go! Your ${planName} subscription has been canceled.

${cancellationDate ? `Your subscription will remain active until ${cancellationDate}.` : 'Your subscription has been canceled immediately.'}
You'll continue to have access to your account and can reactivate your subscription anytime.
We'd love to hear your feedback - what could we have done better?
Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie

P.S. We hope to see you back soon! 🙌`;

  return sendEmail({
    to: email,
    subject: 'Subscription canceled',
    body,
  });
}

/**
 * send invoice payment succeeded email
 */
export async function sendPaymentSucceededEmail(
  email: string,
  amount: number,
  currency: string,
  planName: string,
  creditsAdded: number
) {
  const formattedAmount = (amount / 100).toFixed(2);
  const currencyUpper = currency.toUpperCase();
  
  const body = `Hey there! 👋

Great news! Your payment of ${currencyUpper} ${formattedAmount} has been successfully processed! ✅

Your ${planName} subscription payment was successful and your account has been credited with ${creditsAdded} video credits. 🎉

You can now continue creating amazing videos with your updated credits.
Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie

P.S. Thank you for your continued support! 🙌`;

  return sendEmail({
    to: email,
    subject: 'Payment successful! ✅',
    body,
  });
}

/**
 * send invoice payment failed email
 */
export async function sendPaymentFailedEmail(
  email: string,
  amount: number,
  currency: string,
  planName: string,
  attemptCount: number,
  errorMessage?: string
) {
  const formattedAmount = (amount / 100).toFixed(2);
  const currencyUpper = currency.toUpperCase();
  
  const body = `Hey there! 👋

We encountered an issue processing your payment of ${currencyUpper} ${formattedAmount} for your ${planName} subscription. ❌

${attemptCount > 1 ? `This is attempt #${attemptCount}.` : 'This was the first attempt.'}
${errorMessage ? `Error: ${errorMessage}` : 'Please check your payment method and try again.'}

To resolve this:
1. Check that your payment method is valid and has sufficient funds
2. Update your payment method in your account settings if needed
3. We'll automatically retry the payment

Your subscription will remain active during this time. If the issue persists, please update your payment method or contact us.
Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie

P.S. Need help? We're here to assist! 🙌`;

  return sendEmail({
    to: email,
    subject: 'Payment failed - action required ⚠️',
    body,
  });
}

