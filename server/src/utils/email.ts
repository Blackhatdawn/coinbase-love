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
 * Email service - currently a mock for development
 * In production, integrate with SendGrid, AWS SES, or similar service
 */
export const sendVerificationEmail = async (email: string, name: string, verificationToken: string): Promise<boolean> => {
  try {
    const verificationLink = `${process.env.FRONTEND_URL || 'http://localhost:5173'}/verify-email?token=${verificationToken}&email=${encodeURIComponent(email)}`;
    
    // Mock email logging for development
    if (process.env.NODE_ENV === 'development') {
      console.log(`
        📧 EMAIL VERIFICATION LINK (Development Only)
        =====================================
        To: ${email}
        Name: ${name}
        
        Verification Link:
        ${verificationLink}
        
        Copy and paste the token in your app:
        Token: ${verificationToken}
        =====================================
      `);
      return true;
    }

    // In production, integrate with email service here
    // Example with SendGrid:
    // const sgMail = require('@sendgrid/mail');
    // sgMail.setApiKey(process.env.SENDGRID_API_KEY);
    // await sgMail.send({
    //   to: email,
    //   from: 'noreply@cryptovault.com',
    //   subject: 'Verify your CryptoVault email address',
    //   html: generateVerificationEmailHTML(name, verificationLink),
    // });

    console.log(`Email verification sent to ${email}`);
    return true;
  } catch (error) {
    console.error('Failed to send verification email:', error);
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
