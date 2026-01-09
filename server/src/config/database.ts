import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'cryptovault',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',

  // Pool sizing configuration (optimized for typical load)
  max: parseInt(process.env.DB_POOL_MAX || '20'),        // Max 20 connections
  min: parseInt(process.env.DB_POOL_MIN || '5'),         // Min 5 connections
  idleTimeoutMillis: 30000,                               // Close idle connections after 30s
  connectionTimeoutMillis: 2000,                          // Fail fast if can't connect

  // Connection settings
  statement_timeout: '30s',                               // Query timeout
  application_name: 'cryptovault',
});

pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
});

export const query = async (text: string, params?: any[]) => {
  const start = Date.now();
  try {
    const result = await pool.query(text, params);
    const duration = Date.now() - start;
    console.log('Executed query', { text, duration, rows: result.rowCount });
    return result;
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  }
};

export const getClient = () => pool.connect();

// Initialize database schema
export const initializeDatabase = async () => {
  try {
    // Create pgcrypto extension for UUID generation
    await query('CREATE EXTENSION IF NOT EXISTS pgcrypto');

    // Users table
    await query(`
      CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        email_verified BOOLEAN DEFAULT FALSE,
        email_verification_token VARCHAR(255),
        email_verification_expires TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Portfolios table
    await query(`
      CREATE TABLE IF NOT EXISTS portfolios (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        total_balance DECIMAL(20, 8) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Holdings table (user's cryptocurrency amounts)
    await query(`
      CREATE TABLE IF NOT EXISTS holdings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
        symbol VARCHAR(10) NOT NULL,
        name VARCHAR(255) NOT NULL,
        amount DECIMAL(20, 8) NOT NULL DEFAULT 0,
        value DECIMAL(20, 8) NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(portfolio_id, symbol)
      )
    `);

    // Trading Orders table
    await query(`
      CREATE TABLE IF NOT EXISTS orders (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        trading_pair VARCHAR(20) NOT NULL,
        order_type VARCHAR(20) NOT NULL,
        side VARCHAR(10) NOT NULL,
        amount DECIMAL(20, 8) NOT NULL,
        price DECIMAL(20, 8) NOT NULL,
        total DECIMAL(20, 8) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Transactions table
    await query(`
      CREATE TABLE IF NOT EXISTS transactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        transaction_type VARCHAR(20) NOT NULL,
        amount DECIMAL(20, 8) NOT NULL,
        symbol VARCHAR(10),
        description VARCHAR(500),
        status VARCHAR(20) DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Revoked Refresh Tokens table (for explicit token revocation on logout)
    await query(`
      CREATE TABLE IF NOT EXISTS revoked_refresh_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_jti VARCHAR(255) NOT NULL UNIQUE,
        revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
      )
    `);

    // Create indexes
    await query(`CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)`);
    await query(`CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id)`);
    await query(`CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_id ON holdings(portfolio_id)`);
    await query(`CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)`);
    await query(`CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)`);

    console.log('✓ Database schema initialized');
  } catch (error) {
    console.error('Failed to initialize database:', error);
    throw error;
  }
};

export default pool;
