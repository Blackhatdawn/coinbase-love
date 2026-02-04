/**
 * Auto-generated TypeScript interfaces from FastAPI Pydantic models
 * CryptoVault API Types
 * 
 * DO NOT EDIT MANUALLY - Regenerate from backend schemas when models change
 * 
 * Generation Date: February 4, 2026
 * Backend Version: 1.0.0
 */

// ============================================
// AUTHENTICATION
// ============================================

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  refresh_token: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name: string;
  email_verified: boolean;
  is_admin: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================
// WALLET
// ============================================

export interface WalletBalance {
  wallet: {
    balances: Record<string, number>; // e.g., {USD: 1000, BTC: 0.5}
    updated_at: string;
  };
}

export interface DepositRequest {
  amount: number;
  currency: string; // "btc" | "eth" | "usdt" | "usdc" | "ltc" | "bnb" | "sol"
}

export interface DepositResponse {
  success: boolean;
  orderId: string;
  paymentId: string;
  amount: number;
  currency: string;
  payAddress: string;
  payAmount: number;
  expiresAt: string;
  qrCode?: string;
  mock: boolean;
}

export interface Deposit {
  orderId: string;
  amount: number;
  currency: string;
  payCurrency: string;
  payAmount: number;
  payAddress: string;
  status: "pending" | "confirming" | "confirmed" | "sending" | "partially_paid" | "finished" | "failed" | "refunded" | "expired";
  createdAt: string;
  expiresAt: string | null;
}

export interface WithdrawRequest {
  amount: number;
  currency: string;
  address: string;
}

export interface WithdrawResponse {
  success: boolean;
  withdrawalId: string;
  amount: number;
  currency: string;
  address: string;
  fee: number;
  totalAmount: number;
  status: "pending";
  estimatedProcessingTime: string;
  note: string;
}

export interface Withdrawal {
  id: string;
  amount: number;
  currency: string;
  address: string;
  status: "pending" | "processing" | "completed" | "failed" | "cancelled";
  fee: number;
  totalAmount: number;
  transactionHash: string | null;
  createdAt: string;
  processedAt: string | null;
  completedAt: string | null;
  notes: string | null;
}

export interface TransferRequest {
  recipient_email: string;
  amount: number;
  currency: string;
  note?: string;
}

export interface TransferResponse {
  success: boolean;
  transferId: string;
  amount: number;
  currency: string;
  recipient: {
    email: string;
    name: string;
  };
  fee: number;
  status: "completed";
  message: string;
}

export interface Transfer {
  id: string;
  amount: number;
  currency: string;
  direction: "sent" | "received";
  otherParty: {
    email: string;
    name: string;
  };
  note: string | null;
  status: "completed";
  createdAt: string;
  completedAt: string | null;
}

// ============================================
// TRADING
// ============================================

export interface OrderCreate {
  trading_pair: string; // e.g., "BTC/USD"
  order_type: "market" | "limit";
  side: "buy" | "sell";
  amount: number; // Must be > 0
  price: number;  // Must be > 0
}

export interface Order {
  id: string;
  user_id: string;
  trading_pair: string;
  order_type: "market" | "limit" | "stop_loss" | "take_profit" | "stop_limit";
  side: "buy" | "sell";
  amount: number;
  price: number;
  stop_price?: number;
  status: "pending" | "filled" | "cancelled";
  created_at: string;
  filled_at: string | null;
  cancelled_at?: string;
}

export interface OrderResponse {
  message: string;
  order: Order;
  fee: number;
  totalCost: number;
}

// Advanced Order Types
export interface AdvancedOrderCreate {
  trading_pair: string;
  order_type: "market" | "limit" | "stop_loss" | "take_profit" | "stop_limit";
  side: "buy" | "sell";
  amount: number;
  price?: number; // Required for limit/stop_limit
  stop_price?: number; // Required for stop orders
  time_in_force?: "GTC" | "IOC" | "FOK" | "GTD";
  expire_time?: string; // ISO 8601 datetime for GTD orders
}

// ============================================
// PORTFOLIO
// ============================================

export interface Portfolio {
  holdings: PortfolioHolding[];
  total_value: number;
  total_change_24h: number;
  total_change_percent_24h: number;
}

export interface PortfolioHolding {
  symbol: string;
  name: string;
  amount: number;
  current_price: number;
  value: number;
  change_24h: number;
  change_percent_24h: number;
}

export interface AddHoldingRequest {
  symbol: string;
  name: string;
  amount: number;
}

// ============================================
// TRANSACTIONS
// ============================================

export interface Transaction {
  id: string;
  user_id: string;
  type: "deposit" | "withdrawal" | "trade" | "transfer_in" | "transfer_out" | "fee";
  amount: number;
  currency: string;
  status: "pending" | "completed" | "failed" | "cancelled";
  reference: string;
  description: string;
  created_at: string;
}

export interface TransactionStats {
  total_deposits: number;
  total_withdrawals: number;
  total_trades: number;
  total_fees: number;
  net_profit_loss: number;
}

// ============================================
// PAGINATION
// ============================================

export type PaginatedDeposits = {
  deposits: Deposit[];
  total: number;
  skip: number;
  limit: number;
};

export type PaginatedWithdrawals = {
  withdrawals: Withdrawal[];
  total: number;
  skip: number;
  limit: number;
};

export type PaginatedTransfers = {
  transfers: Transfer[];
  total: number;
  skip: number;
  limit: number;
};

export type PaginatedTransactions = {
  transactions: Transaction[];
  total: number;
  skip: number;
  limit: number;
};

export type PaginatedOrders = {
  orders: Order[];
};

// ============================================
// ERRORS
// ============================================

export interface APIError {
  error: {
    code: string;
    message: string;
    request_id?: string;
    timestamp?: string;
    details?: Record<string, any>;
  };
}
