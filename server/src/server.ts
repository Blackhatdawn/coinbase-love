import 'dotenv/config';
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import helmet from 'helmet';
import { initializeDatabase } from '@/config/database';
import authRoutes from '@/routes/auth';
import cryptoRoutes from '@/routes/cryptocurrencies';
import portfolioRoutes from '@/routes/portfolio';
import orderRoutes from '@/routes/orders';
import transactionRoutes from '@/routes/transactions';
import {
  generalLimiter,
  getCorsOptions,
  securityHeaders,
} from '@/middleware/security';

const app = express();
const PORT = process.env.PORT || 5000;
const NODE_ENV = process.env.NODE_ENV || 'development';

// ============================================================================
// SECURITY MIDDLEWARE (Applied First)
// ============================================================================

// Helmet for security headers
app.use(helmet());

// Custom security headers
app.use(securityHeaders);

// CORS with dynamic origin configuration
app.use(cors(getCorsOptions()));

// Rate limiting (general API - applied to all routes except health)
app.use(generalLimiter);

// ============================================================================
// BODY PARSING MIDDLEWARE
// ============================================================================

// Parse JSON with size limit to prevent large payload attacks
app.use(express.json({ limit: '10kb' }));

// Parse URL-encoded bodies
app.use(express.urlencoded({ extended: true, limit: '10kb' }));

// Request logging middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path} - ${res.statusCode} - ${duration}ms`);
  });
  next();
});

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/crypto', cryptoRoutes);
app.use('/api/portfolio', portfolioRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/transactions', transactionRoutes);

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({
    error: 'Not found',
    path: req.path,
    method: req.method,
  });
});

// Error handling middleware
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
  });
});

// Initialize database and start server
const startServer = async () => {
  try {
    console.log('🔧 Initializing database...');
    await initializeDatabase();
    console.log('✓ Database initialized');

    app.listen(PORT, '0.0.0.0', () => {
      console.log(`✓ Server running on port ${PORT}`);
      console.log(`  Health check: http://localhost:${PORT}/health`);
      console.log(`  API docs:`);
      console.log(`    Auth: POST /api/auth/signup, /api/auth/login`);
      console.log(`    Crypto: GET /api/crypto`);
      console.log(`    Portfolio: GET /api/portfolio`);
      console.log(`    Orders: GET/POST /api/orders`);
      console.log(`    Transactions: GET /api/transactions`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();

export default app;
