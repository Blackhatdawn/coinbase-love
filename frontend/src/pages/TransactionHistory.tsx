/**
 * TransactionHistory - Transaction History Page
 * Premium Bybit-style transaction list with filters
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowUpRight,
  ArrowDownRight,
  Filter,
  CalendarIcon,
  Download,
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { api } from '@/lib/apiClient';
import DashboardCard from '@/components/dashboard/DashboardCard';

interface Transaction {
  id: string;
  type: string;
  symbol?: string;
  amount: number;
  description?: string;
  createdAt: string;
  status?: string;
}

const TransactionHistory = () => {
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  // Fetch transactions
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['transactions', page, typeFilter],
    queryFn: () => api.transactions.getAll(page * limit, limit, typeFilter !== 'all' ? typeFilter : undefined),
  });

  const transactions = data?.transactions || [];
  const totalCount = data?.total || 0;
  const totalPages = Math.ceil(totalCount / limit);

  // Filter by search
  const filteredTransactions = transactions.filter((tx: Transaction) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      tx.symbol?.toLowerCase().includes(query) ||
      tx.type?.toLowerCase().includes(query) ||
      tx.description?.toLowerCase().includes(query)
    );
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-white">
            Transaction History
          </h1>
          <p className="text-gray-400 mt-1">
            View and manage your trading activity
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="border-white/10 hover:bg-white/5"
            disabled={isFetching}
          >
            <RefreshCw className={cn('h-4 w-4 mr-2', isFetching && 'animate-spin')} />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="border-white/10 hover:bg-white/5"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <DashboardCard>
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <Input
              placeholder="Search transactions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-white/5 border-white/10 focus:border-gold-500/50"
            />
          </div>

          {/* Type Filter */}
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-full sm:w-[160px] bg-white/5 border-white/10">
              <Filter className="h-4 w-4 mr-2 text-gray-500" />
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent className="bg-[#1a1a2e] border-white/10">
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="buy">Buy</SelectItem>
              <SelectItem value="sell">Sell</SelectItem>
              <SelectItem value="deposit">Deposit</SelectItem>
              <SelectItem value="withdraw">Withdraw</SelectItem>
              <SelectItem value="transfer">Transfer</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </DashboardCard>

      {/* Transactions List */}
      <DashboardCard noPadding>
        {/* Table Header */}
        <div className="hidden sm:grid grid-cols-5 gap-4 px-6 py-3 border-b border-white/5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          <div>Type</div>
          <div>Asset</div>
          <div>Amount</div>
          <div>Date</div>
          <div className="text-right">Status</div>
        </div>

        {/* Loading State */}
        {isLoading ? (
          <div className="divide-y divide-white/5">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="px-6 py-4 animate-pulse">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-white/5" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-24 bg-white/5 rounded" />
                    <div className="h-3 w-32 bg-white/5 rounded" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="p-4 bg-white/5 rounded-full mb-4">
              <CalendarIcon className="h-8 w-8 text-gray-500" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">No transactions found</h3>
            <p className="text-gray-400 max-w-sm">
              {searchQuery || typeFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Your transaction history will appear here'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {filteredTransactions.map((tx: Transaction, index: number) => (
              <TransactionRow key={tx.id} transaction={tx} index={index} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-white/5">
            <p className="text-sm text-gray-500">
              Showing {page * limit + 1}-{Math.min((page + 1) * limit, totalCount)} of {totalCount}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="border-white/10 hover:bg-white/5"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-gray-400 min-w-[80px] text-center">
                Page {page + 1} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="border-white/10 hover:bg-white/5"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </DashboardCard>
    </div>
  );
};

// Transaction Row Component
const TransactionRow = ({
  transaction,
  index
}: {
  transaction: Transaction;
  index: number;
}) => {
  const isBuy = transaction.type === 'buy' || transaction.type === 'deposit';
  const txDate = new Date(transaction.createdAt);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="grid grid-cols-1 sm:grid-cols-5 gap-2 sm:gap-4 px-6 py-4 hover:bg-white/5 transition-colors"
    >
      {/* Type */}
      <div className="flex items-center gap-3">
        <div className={cn(
          'p-2 rounded-lg',
          isBuy ? 'bg-emerald-500/10' : 'bg-red-500/10'
        )}>
          {isBuy ? (
            <ArrowDownRight className="h-5 w-5 text-emerald-400" />
          ) : (
            <ArrowUpRight className="h-5 w-5 text-red-400" />
          )}
        </div>
        <div className="sm:hidden">
          <p className="font-medium text-white capitalize">{transaction.type}</p>
          <p className="text-xs text-gray-500">{format(txDate, 'MMM d, yyyy HH:mm')}</p>
        </div>
        <span className="hidden sm:block font-medium text-white capitalize">{transaction.type}</span>
      </div>

      {/* Asset */}
      <div className="hidden sm:flex items-center">
        <span className="text-white">{transaction.symbol || '-'}</span>
      </div>

      {/* Amount */}
      <div className="flex items-center justify-between sm:justify-start">
        <span className="sm:hidden text-xs text-gray-500">Amount</span>
        <span className={cn(
          'font-semibold',
          isBuy ? 'text-emerald-400' : 'text-red-400'
        )}>
          {isBuy ? '+' : '-'}${Math.abs(transaction.amount).toLocaleString()}
        </span>
      </div>

      {/* Date */}
      <div className="hidden sm:flex items-center">
        <span className="text-gray-400">{format(txDate, 'MMM d, yyyy HH:mm')}</span>
      </div>

      {/* Status */}
      <div className="flex items-center justify-between sm:justify-end">
        <span className="sm:hidden text-xs text-gray-500">Status</span>
        <span className={cn(
          'px-2 py-0.5 text-xs font-medium rounded-full',
          transaction.status === 'completed' || !transaction.status
            ? 'bg-emerald-500/10 text-emerald-400'
            : transaction.status === 'pending'
            ? 'bg-yellow-500/10 text-yellow-400'
            : 'bg-red-500/10 text-red-400'
        )}>
          {transaction.status || 'Completed'}
        </span>
      </div>
    </motion.div>
  );
};

export default TransactionHistory;
