import { z } from 'zod';

export const signUpSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
});

export const signInSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Password required'),
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
