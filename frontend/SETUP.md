# CryptoVault - Complete Setup Guide

This guide will help you set up and run the CryptoVault cryptocurrency trading platform locally.

## Project Structure

```
.
├── code/                 # Frontend (Vite + React)
├── server/              # Backend (Express.js)
├── docker-compose.yml   # PostgreSQL database
└── SETUP.md            # This file
```

## Prerequisites

- **Node.js** 18+ (download from https://nodejs.org/)
- **npm** or **yarn** (comes with Node.js)
- **PostgreSQL** 12+ (or use Docker)
- **Git** (optional, for version control)

## Quick Start (Recommended)

### 1. Start the Database

If you have Docker installed:
```bash
docker-compose up -d
```

If you have PostgreSQL installed locally:
```bash
createdb cryptovault
```

### 2. Setup Backend

```bash
cd server

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Update .env with your database credentials (if using local PostgreSQL)
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cryptovault

# Start backend server
npm run dev
```

Server will run on http://localhost:5000

### 3. Setup Frontend

```bash
# From root directory (not in server folder)
cd code  # or just "npm install" if you're in root

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on http://localhost:8080

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:8080
```

## Detailed Setup Instructions

### Backend Setup

#### Step 1: Navigate to Server Directory
```bash
cd server
```

#### Step 2: Install Dependencies
```bash
npm install
```

#### Step 3: Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cryptovault
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cryptovault
DB_USER=postgres
DB_PASSWORD=postgres
JWT_SECRET=your_secret_key_change_in_production
CORS_ORIGIN=http://localhost:8080
PORT=5000
NODE_ENV=development
```

#### Step 4: Start Backend Server
```bash
npm run dev
```

You should see:
```
✓ Database initialized
✓ Server running on port 5000
  Health check: http://localhost:5000/health
```

### Frontend Setup

#### Step 1: Navigate to Frontend Directory
```bash
cd code
```

#### Step 2: Install Dependencies
```bash
npm install
```

#### Step 3: Start Development Server
```bash
npm run dev
```

You should see:
```
VITE v5.4.19  ready in XXX ms

➜  Local:   http://localhost:8080/
➜  press h to show help
```

### Database Setup (PostgreSQL with Docker)

#### Using Docker Compose

```bash
# Start PostgreSQL
docker-compose up -d

# Check if database is running
docker-compose ps

# Stop database
docker-compose down
```

#### Using Local PostgreSQL

```bash
# Create database
createdb cryptovault

# Login to PostgreSQL
psql -U postgres

# In psql console
\l  # List databases (you should see cryptovault)
\q  # Quit
```

## API Endpoints

Once the backend is running, you can access these endpoints:

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Sign in
- `GET /api/auth/me` - Get current user (requires token)

### Cryptocurrencies
- `GET /api/crypto` - Get all cryptocurrencies
- `GET /api/crypto/BTC` - Get specific crypto data

### Portfolio
- `GET /api/portfolio` - Get user portfolio
- `POST /api/portfolio/holding` - Add holding
- `DELETE /api/portfolio/holding/BTC` - Delete holding

### Orders
- `GET /api/orders` - Get all orders
- `POST /api/orders` - Create new order

### Transactions
- `GET /api/transactions` - Get transaction history

## Testing the Application

### 1. Sign Up
1. Navigate to http://localhost:8080/auth
2. Click "Sign up"
3. Fill in name, email, and password
4. Click "Create Account"

### 2. View Markets
1. Go to http://localhost:8080/markets
2. You should see cryptocurrency list loaded from the backend
3. Try searching and filtering

### 3. View Dashboard
1. Go to http://localhost:8080/dashboard
2. You should see your portfolio (initially empty or with default holdings)

### 4. Place Order
1. Go to http://localhost:8080/trade
2. Select a trading pair, order type, side, amount, and price
3. Click "Place Order"

### 5. View Transactions
1. From dashboard, click "History" button
2. You should see your transaction history

## Troubleshooting

### Port Already in Use

**Frontend (Port 8080)**:
```bash
# Windows
netstat -ano | findstr :8080

# Mac/Linux
lsof -i :8080
```

Change port in `vite.config.ts`:
```typescript
server: {
  port: 8081,  // Change this
}
```

**Backend (Port 5000)**:
```bash
# Update PORT in server/.env
PORT=5001
```

### Database Connection Error

**Check PostgreSQL is running:**
```bash
# Docker
docker-compose ps

# Local
psql -U postgres -c "SELECT 1"
```

**Verify credentials in .env:**
```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

### API Not Responding

1. Make sure backend is running: `npm run dev` in `/server`
2. Check backend logs for errors
3. Verify CORS_ORIGIN in `.env` matches frontend URL
4. Check Vite proxy config in `vite.config.ts`

### Database Schema Not Created

The schema is created automatically on backend startup. If it fails:

1. Check backend logs for errors
2. Verify database exists: `psql -U postgres -l`
3. Try connecting directly: `psql -U postgres -d cryptovault`

## Development Workflow

1. **Make changes to frontend** → Changes auto-reload (Vite HMR)
2. **Make changes to backend** → Restart backend with `npm run dev`
3. **Database changes** → Schema auto-initializes on startup

## Production Build

### Frontend
```bash
cd code
npm run build
npm run preview
```

### Backend
```bash
cd server
npm run build
npm start
```

## Environment Variables

### Frontend
No environment variables needed (uses `/api` proxy to backend)

### Backend (.env)
```
DATABASE_URL              # PostgreSQL connection string
JWT_SECRET               # Secret for signing JWT tokens
CORS_ORIGIN             # Frontend URL (for CORS)
PORT                    # Backend server port (default: 5000)
NODE_ENV                # development or production
```

## File Locations

| Component | Location | Purpose |
|-----------|----------|---------|
| Frontend | `code/` | React application |
| Backend | `server/src/` | Express API server |
| Database Config | `server/src/config/database.ts` | PostgreSQL setup |
| Auth API | `server/src/routes/auth.ts` | Authentication endpoints |
| Crypto API | `server/src/routes/cryptocurrencies.ts` | Market data endpoints |
| Portfolio API | `server/src/routes/portfolio.ts` | User holdings endpoints |

## Getting Help

- Check the logs: `npm run dev` shows detailed error messages
- Review API documentation: `server/README.md`
- Check network tab in browser DevTools for API errors
- Verify .env files are correctly configured

## Next Steps

1. ✅ Start database
2. ✅ Start backend
3. ✅ Start frontend
4. ✅ Sign up a test account
5. ✅ Explore the application
6. Customize and extend as needed!

Happy trading! 🚀
