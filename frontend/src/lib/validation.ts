import { z } from 'zod';

/**
 * Sign Up Form Validation Schema
 * - Email: valid email format
 * - Password: minimum 8 chars, 1 uppercase, 1 lowercase, 1 number
 * - Name: 2-100 characters
 */
export const signUpSchema = z.object({
  email: z.string()
    .email('Invalid email address')
    .min(1, 'Email is required'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters long')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  name: z.string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must not exceed 100 characters'),
  phone_number: z.string()
    .min(7, 'Phone number must be at least 7 characters')
    .max(20, 'Phone number is too long')
    .optional()
    .or(z.literal('')),
  country: z.string().min(2, 'Country is required').max(60, 'Country is too long').optional().or(z.literal('')),
  city: z.string().max(80, 'City is too long').optional().or(z.literal('')),
  referral_code: z.string()
    .regex(/^[A-Z0-9]{4,20}$/, 'Referral code must be 4-20 letters/numbers')
    .optional()
    .or(z.literal('')),
});

/**
 * Sign In Form Validation Schema
 * - Email: valid email format
 * - Password: at least 1 character
 */
export const signInSchema = z.object({
  email: z.string()
    .email('Invalid email address')
    .min(1, 'Email is required'),
  password: z.string()
    .min(1, 'Password is required'),
});

/**
 * Email Verification Schema
 * - Token: verification token from email
 * - Email: user's email address
 */
export const emailVerificationSchema = z.object({
  token: z.string()
    .min(1, 'Verification token is required'),
  email: z.string()
    .email('Invalid email address'),
});

export type SignUpFormData = z.infer<typeof signUpSchema>;
export type SignInFormData = z.infer<typeof signInSchema>;
export type EmailVerificationData = z.infer<typeof emailVerificationSchema>;

/**
 * Validate form data and return errors
 * Returns an object with field names as keys and error messages as values
 */
export const validateFormData = <T extends Record<string, any>>(
  schema: z.ZodSchema,
  data: T
): Record<string, string> => {
  try {
    schema.parse(data);
    return {};
  } catch (error) {
    if (error instanceof z.ZodError) {
      const fieldErrors: Record<string, string> = {};
      error.errors.forEach((err) => {
        const fieldName = err.path[0] as string;
        fieldErrors[fieldName] = err.message;
      });
      return fieldErrors;
    }
    return { form: 'Validation failed' };
  }
};
