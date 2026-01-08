import { z } from 'zod';

export const signUpSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters long')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  name: z.string().min(2, 'Name must be at least 2 characters').max(100, 'Name is too long'),
});

export const signInSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password required'),
});

export const createOrderSchema = z.object({
  trading_pair: z.string().regex(/^[A-Z]{3,}\/[A-Z]{3,}$/, 'Invalid trading pair format'),
  order_type: z.enum(['market', 'limit', 'stop']),
  side: z.enum(['buy', 'sell']),
  amount: z.number().positive('Amount must be positive'),
  price: z.number().positive('Price must be positive'),
});

export const addHoldingSchema = z.object({
  symbol: z.string().length(1, 20, 'Invalid symbol length'),
  name: z.string().min(1, 'Name required'),
  amount: z.number().positive('Amount must be positive'),
});

export type SignUpInput = z.infer<typeof signUpSchema>;
export type SignInInput = z.infer<typeof signInSchema>;
export type CreateOrderInput = z.infer<typeof createOrderSchema>;
export type AddHoldingInput = z.infer<typeof addHoldingSchema>;
