import crypto from 'crypto';

/**
 * Generate a random verification token
 */
export const generateVerificationToken = (): string => {
  return crypto.randomBytes(32).toString('hex');
};

/**
 * Calculate expiry time (24 hours from now)
 */
export const getVerificationTokenExpiry = (): Date => {
  const expiry = new Date();
  expiry.setHours(expiry.getHours() + 24);
  return expiry;
};

/**
 * Production email service with SendGrid support
 * Requires: npm install @sendgrid/mail
 * Environment variables:
 *   - SENDGRID_API_KEY: Your SendGrid API key
 *   - SENDER_EMAIL: From address (e.g., noreply@cryptovault.com)
 *   - FRONTEND_URL: Frontend URL for verification links
 */
export const sendVerificationEmail = async (
  email: string,
  name: string,
  verificationToken: string
): Promise<boolean> => {
  try {
    const verificationLink = `${process.env.FRONTEND_URL || 'http://localhost:5173'}/auth/verify?token=${verificationToken}&email=${encodeURIComponent(email)}`;
    const htmlContent = generateVerificationEmailHTML(name, verificationLink);

    // PRODUCTION: Use SendGrid if API key is configured
    if (process.env.SENDGRID_API_KEY && process.env.NODE_ENV === 'production') {
      try {
        // Dynamic import to allow optional dependency
        const sgMail = await import('@sendgrid/mail').then((m) => m.default);

        sgMail.setApiKey(process.env.SENDGRID_API_KEY);

        const senderEmail =
          process.env.SENDER_EMAIL || 'noreply@cryptovault.com';

        const msg = {
          to: email,
          from: senderEmail,
          subject: 'Verify Your CryptoVault Account',
          html: htmlContent,
          replyTo: 'support@cryptovault.com',
        };

        await sgMail.send(msg);

        console.log(`✅ Verification email sent to ${email}`);
        return true;
      } catch (sendGridError: any) {
        console.error('❌ SendGrid email failed:', sendGridError.message);

        // Log the error but don't fail the signup - user can request resend
        // In production, you might want to alert your monitoring system
        return false;
      }
    }

    // DEVELOPMENT: Log to console
    if (process.env.NODE_ENV === 'development') {
      console.log(`
        📧 EMAIL VERIFICATION (Development Mode)
        =====================================
        To: ${email}
        Name: ${name}

        Verification Link:
        ${verificationLink}

        Token: ${verificationToken}
        =====================================
      `);
      return true;
    }

    // FALLBACK: Log warning in non-development, non-configured production
    console.warn(
      '⚠️  Email service not configured. Verification email not sent to:',
      email
    );
    console.warn(
      'Configure SENDGRID_API_KEY environment variable to enable email sending'
    );
    return true; // Don't fail signup if email is misconfigured
  } catch (error) {
    console.error('❌ Failed to send verification email:', error);
    return false;
  }
};

/**
 * Generate HTML template for verification email
 */
export const generateVerificationEmailHTML = (name: string, verificationLink: string): string => {
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 8px; }
          .content { padding: 20px; background: #f9f9f9; border-radius: 8px; margin: 20px 0; }
          .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; margin: 20px 0; }
          .footer { color: #999; font-size: 12px; text-align: center; margin-top: 20px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>Welcome to CryptoVault!</h1>
          </div>
          
          <div class="content">
            <p>Hi ${name},</p>
            
            <p>Thank you for creating your CryptoVault account. To complete your registration and secure your account, please verify your email address.</p>
            
            <center>
              <a href="${verificationLink}" class="button">Verify Email Address</a>
            </center>
            
            <p>Or copy and paste this link in your browser:</p>
            <p>${verificationLink}</p>
            
            <p><strong>This link will expire in 24 hours.</strong></p>
            
            <p>If you didn't create this account, please ignore this email.</p>
          </div>
          
          <div class="footer">
            <p>CryptoVault © 2024. All rights reserved.</p>
            <p>This is an automated message, please do not reply to this email.</p>
          </div>
        </div>
      </body>
    </html>
  `;
};
