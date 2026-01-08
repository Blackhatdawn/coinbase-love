# CryptoVault Backend

Express.js backend server for CryptoVault cryptocurrency trading platform.

## Prerequisites

- Node.js 18+
- PostgreSQL 12+
- npm or yarn

## Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb cryptovault
   
   # Update .env with your database credentials
   cp .env.example .env
   ```

3. **Configure environment variables** (`.env`)
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/cryptovault
   JWT_SECRET=your_secret_key
   CORS_ORIGIN=http://localhost:8080
   PORT=5000
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

The server will initialize the database schema automatically on startup.

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Sign in user
- `POST /api/auth/logout` - Sign out user
- `GET /api/auth/me` - Get current user profile (requires auth)

### Cryptocurrencies
- `GET /api/crypto` - Get all cryptocurrencies with market data
- `GET /api/crypto/:symbol` - Get specific cryptocurrency data

### Portfolio
- `GET /api/portfolio` - Get user portfolio and holdings (requires auth)
- `GET /api/portfolio/holding/:symbol` - Get specific holding (requires auth)
- `POST /api/portfolio/holding` - Add/update holding (requires auth)
- `DELETE /api/portfolio/holding/:symbol` - Delete holding (requires auth)

### Orders
- `GET /api/orders` - Get all user orders (requires auth)
- `POST /api/orders` - Create new order (requires auth)
- `GET /api/orders/:id` - Get specific order (requires auth)
- `POST /api/orders/:id/cancel` - Cancel order (requires auth)

### Transactions
- `GET /api/transactions` - Get transaction history (requires auth)
- `GET /api/transactions/:id` - Get specific transaction (requires auth)
- `POST /api/transactions` - Create transaction (requires auth)
- `GET /api/transactions/stats/overview` - Get transaction statistics (requires auth)

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

Tokens are returned on successful signup/login and expire after 7 days.

## Database Schema

### Tables
- `users` - User accounts
- `portfolios` - User portfolio information
- `holdings` - User cryptocurrency holdings
- `orders` - Trading orders
- `transactions` - Transaction history

## Development

### Build for production
```bash
npm run build
```

### Start production server
```bash
npm start
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | - | PostgreSQL connection string |
| DB_HOST | localhost | Database host |
| DB_PORT | 5432 | Database port |
| DB_NAME | cryptovault | Database name |
| DB_USER | postgres | Database user |
| DB_PASSWORD | postgres | Database password |
| JWT_SECRET | secret | JWT signing secret (change in production!) |
| JWT_EXPIRY | 7d | JWT expiration time |
| NODE_ENV | development | Environment |
| PORT | 5000 | Server port |
| CORS_ORIGIN | http://localhost:8080 | CORS allowed origin |

## Error Handling

All endpoints return consistent error responses:
```json
{
  "error": "Error message"
}
```

HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad request
- `401` - Unauthorized
- `404` - Not found
- `500` - Server error
