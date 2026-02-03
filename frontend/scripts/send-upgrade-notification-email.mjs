/**
 * Script to send upgrade notification email to users
 * 
 * Usage:
 *   node scripts/send-upgrade-notification-email.mjs <email@example.com>
 * 
 * Make sure to update the Resend API key in this file
 */

import { Resend } from 'resend';

const resend = new Resend('re_xxxx...xxxxxx');

/**
 * Send upgrade notification email to a user
 */
async function sendUpgradeNotificationEmail(email) {
  if (!email) {
    console.error('Error: Email address is required');
    console.log('Usage: node scripts/send-upgrade-notification-email.mjs <email@example.com>');
    process.exit(1);
  }

  const body = `Hey there! 👋

Thank you for using Vidinie! We wanted to reach out and let you know about some amazing upgrades we've made to the platform since you last used it. 🚀

We've been working hard to build a better platform for you, and here's what's new:

✨ Dynamic User Guiding - Get personalized guidance throughout your video creation journey
🎬 Animated Compositions - Create more amazing videos with beautiful animated compositions
🎨 Generated Videos & Images - AI-generated visuals within video compositions to represent complex ideas
🎵 Background Music - Add music to enhance your videos
🎤 Voice Selection - Choose from multiple voice options for your narration
...and so much more!

We've worked tirelessly to build a better platform for you, and we'll continue to improve it based on your feedback.

Ready to see what's new? Try logging into Vidinie again or create a new account if you don't have one yet. We look forward to seeing what amazing videos you create! 🎥

Questions? Just hit reply, I read everything. 💬

From Kosi 😄
Builder, Vidinie

P.S. We can't wait to see what you create with the new features! 🙌`;

  try {
    const { data, error } = await resend.emails.send({
      from: 'Vidinie <hello@vidinie.com>',
      to: email,
      replyTo: 'hello@vidinie.com',
      subject: 'Vidinie has major upgrades! 🚀✨',
      text: body,
    });

    if (error) {
      console.error('Error sending email:', error);
      throw error;
    }

    console.log(`✅ Email ${data?.id} sent successfully to ${email}`);
    return data;
  } catch (error) {
    console.error('Failed to send email:', error);
    throw error;
  }
}

// Get email from command line arguments
const email = process.argv[2];

// Send the email
sendUpgradeNotificationEmail(email)
  .then(() => {
    console.log('Email sent successfully!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('Failed to send email:', error);
    process.exit(1);
  });

