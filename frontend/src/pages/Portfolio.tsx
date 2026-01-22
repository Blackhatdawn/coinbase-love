/**
 * Portfolio Page - Comprehensive portfolio view
 * Shows detailed holdings, performance metrics, and analytics
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  RefreshCw,
  Download,
  Plus,
  Trash2,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { api } from '@/lib/apiClient';
import { useAuth } from '@/contexts/AuthContext';
import { usePriceWebSocket } from '@/hooks/usePriceWebSocket';
import { useCryptoData } from '@/hooks/useCryptoData';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import DashboardCard from '@/components/dashboard/DashboardCard';
import { Link } from 'react-router-dom';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } }
};

const Portfolio = () => {
  const { user } = useAuth();
  const { prices } = usePriceWebSocket();
  const { data: cryptoData } = useCryptoData({ refreshInterval: 30000 });
  const [selectedTimeframe, setSelectedTimeframe] = useState<'24h' | '7d' | '30d' | '1y' | 'all'>('7d');

  // Create a map for quick lookup of crypto data
  const cryptoMap = (cryptoData || []).reduce((acc: Record<string, any>, crypto: any) => {
    acc[crypto.symbol?.toLowerCase()] = crypto;
    return acc;
  }, {});

  // Fetch portfolio data
  const { data: portfolioData, isLoading: portfolioLoading, refetch: refetchPortfolio } = useQuery({
    queryKey: ['portfolio'],
    queryFn: () => api.portfolio.get(),
    refetchInterval: 30000,
  });

  // Calculate real-time portfolio metrics
  const holdings = portfolioData?.portfolio?.holdings || [];
  const originalTotalValue = portfolioData?.portfolio?.totalBalance || 0;

  // Calculate real-time value using WebSocket prices
  const realTimeValue = holdings.reduce((sum: number, holding: any) => {
    const wsPrice = prices[holding.symbol?.toLowerCase()];
    if (wsPrice) {
      return sum + (parseFloat(wsPrice) * holding.amount);
    }
    return sum + (holding.value || 0);
  }, 0);

  const totalValue = realTimeValue || originalTotalValue;
  const portfolioChange = originalTotalValue > 0
    ? ((totalValue - originalTotalValue) / originalTotalValue) * 100
    : 0;

  // Calculate asset allocation
  const totalAllocation = holdings.reduce((sum: number, holding: any) => {
    const wsPrice = prices[holding.symbol?.toLowerCase()];
    const value = wsPrice ? parseFloat(wsPrice) * holding.amount : holding.value;
    return sum + value;
  }, 0);

  const holdingsWithAllocation = holdings.map((holding: any) => {
    const wsPrice = prices[holding.symbol?.toLowerCase()];
    const value = wsPrice ? parseFloat(wsPrice) * holding.amount : holding.value;
    const allocation = totalAllocation > 0 ? (value / totalAllocation) * 100 : 0;
    const cryptoInfo = cryptoMap[holding.symbol?.toLowerCase()];
    const change24h = cryptoInfo?.change_24h || 0;
    return { ...holding, value, allocation, change24h };
  });

  // Sort by value
  const sortedHoldings = [...holdingsWithAllocation].sort((a, b) => b.value - a.value);

  // Calculate portfolio 24h change based on holdings and their respective changes (weighted)
  const change24h = sortedHoldings.reduce((weightedChange: number, holding: any) => {
    const weight = totalAllocation > 0 ? (holding.value / totalAllocation) : 0;
    return weightedChange + (holding.change24h * weight);
  }, 0);
  
  const profit24h = totalValue * (change24h / 100);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-white">
            Portfolio
          </h1>
          <p className="text-gray-400 mt-1">
            Track your investments and performance
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchPortfolio()}
            className="border-white/10 hover:bg-white/5"
            data-testid="refresh-portfolio"
          >
            <RefreshCw className={cn(
              'h-4 w-4 mr-2',
              portfolioLoading && 'animate-spin'
            )} />
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

      {/* Main Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6"
      >
        {/* Total Value Card */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <DashboardCard
            title="Total Portfolio Value"
            icon={<DollarSign className="h-5 w-5" />}
            className="h-full"
            glowColor="gold"
          >
            <div className="space-y-6">
              <div className="flex items-baseline gap-3">
                <span className="text-3xl sm:text-4xl font-display font-bold text-white">
                  ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <div className={cn(
                  'flex items-center gap-1 px-2 py-1 rounded-lg text-sm font-semibold',
                  portfolioChange >= 0
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : 'bg-red-500/10 text-red-400'
                )}>
                  {portfolioChange >= 0 ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  {portfolioChange >= 0 ? '+' : ''}{portfolioChange.toFixed(2)}%
                </div>
              </div>

              {/* 24h Performance */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-white/5 rounded-lg">
                <div>
                  <p className="text-xs text-gray-400 mb-1">24h Change</p>
                  <p className={cn(
                    'text-lg font-semibold',
                    change24h >= 0 ? 'text-emerald-400' : 'text-red-400'
                  )}>
                    {change24h >= 0 ? '+' : ''}{change24h.toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-1">24h Profit/Loss</p>
                  <p className={cn(
                    'text-lg font-semibold',
                    profit24h >= 0 ? 'text-emerald-400' : 'text-red-400'
                  )}>
                    {profit24h >= 0 ? '+' : ''}${Math.abs(profit24h).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex flex-wrap gap-3 pt-2">
                <Link to="/wallet/deposit" className="flex-1 min-w-[140px]">
                  <Button className="w-full bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold">
                    <ArrowDownRight className="h-4 w-4 mr-2" />
                    Deposit
                  </Button>
                </Link>
                <Link to="/wallet/withdraw" className="flex-1 min-w-[140px]">
                  <Button variant="outline" className="w-full border-white/10 hover:bg-white/5">
                    <ArrowUpRight className="h-4 w-4 mr-2" />
                    Withdraw
                  </Button>
                </Link>
                <Link to="/trade" className="flex-1 min-w-[140px]">
                  <Button variant="outline" className="w-full border-gold-500/30 text-gold-400 hover:bg-gold-500/10">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Trade
                  </Button>
                </Link>
              </div>
            </div>
          </DashboardCard>
        </motion.div>

        {/* Asset Allocation */}
        <motion.div variants={itemVariants}>
          <DashboardCard
            title="Asset Allocation"
            icon={<PieChart className="h-5 w-5" />}
            className="h-full"
          >
            <div className="space-y-3">
              {sortedHoldings.slice(0, 5).map((holding: any, index: number) => (
                <div key={holding.symbol} className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center font-bold text-gold-400 text-sm">
                    {holding.symbol?.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium text-white truncate">
                        {holding.symbol}
                      </p>
                      <p className="text-sm text-gray-400">
                        {holding.allocation.toFixed(1)}%
                      </p>
                    </div>
                    <div className="w-full bg-white/5 rounded-full h-1.5">
                      <div
                        className="bg-gradient-to-r from-gold-500 to-gold-600 h-1.5 rounded-full transition-all"
                        style={{ width: `${Math.min(holding.allocation, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
              {holdings.length > 5 && (
                <p className="text-xs text-gray-500 text-center pt-2">
                  +{holdings.length - 5} more assets
                </p>
              )}
            </div>
          </DashboardCard>
        </motion.div>
      </motion.div>

      {/* Holdings Table */}
      <motion.div variants={itemVariants}>
        <DashboardCard
          title="Your Holdings"
          action={
            <Link to="/trade">
              <Button size="sm" variant="outline" className="border-white/10 hover:bg-white/5">
                <Plus className="h-4 w-4 mr-2" />
                Add Asset
              </Button>
            </Link>
          }
        >
          {portfolioLoading ? (
            <HoldingsTableSkeleton />
          ) : holdings.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Asset</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">Amount</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">Price</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">Value</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">24h %</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedHoldings.map((holding: any) => {
                    const wsPrice = prices[holding.symbol?.toLowerCase()];
                    const currentPrice = wsPrice ? parseFloat(wsPrice) : holding.value / holding.amount;
                    const holdingChange24h = holding.change24h || 0;

                    return (
                      <tr key={holding.symbol} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center font-bold text-gold-400 text-xs">
                              {holding.symbol?.charAt(0)}
                            </div>
                            <div>
                              <p className="font-medium text-white">{holding.symbol}</p>
                              <p className="text-xs text-gray-500">{holding.name}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <p className="text-white">{holding.amount.toFixed(6)}</p>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <p className={cn('text-white', wsPrice && 'text-gold-400')}>
                            ${currentPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                          </p>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <p className="font-semibold text-white">
                            ${holding.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                          </p>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className={cn(
                            'inline-flex items-center gap-1 text-sm font-medium',
                            holdingChange24h >= 0 ? 'text-emerald-400' : 'text-red-400'
                          )}>
                            {holdingChange24h >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                            {holdingChange24h >= 0 ? '+' : ''}{holdingChange24h.toFixed(2)}%
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <Link to={`/trade?coin=${holding.symbol?.toLowerCase()}`}>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="hover:bg-gold-500/10 hover:text-gold-400"
                            >
                              <TrendingUp className="h-4 w-4" />
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyPortfolio />
          )}
        </DashboardCard>
      </motion.div>
    </div>
  );
};

// Skeleton loader
const HoldingsTableSkeleton = () => (
  <div className="space-y-4">
    {[1, 2, 3].map((i) => (
      <div key={i} className="flex items-center gap-4 animate-pulse">
        <div className="w-8 h-8 rounded-full bg-white/5" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-24 bg-white/5 rounded" />
          <div className="h-3 w-32 bg-white/5 rounded" />
        </div>
      </div>
    ))}
  </div>
);

// Empty state
const EmptyPortfolio = () => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
      <PieChart className="h-8 w-8 text-gray-600" />
    </div>
    <p className="font-medium text-gray-400 mb-2">Your portfolio is empty</p>
    <p className="text-sm text-gray-500 mb-6">
      Start building your crypto portfolio by depositing funds or trading
    </p>
    <div className="flex gap-3">
      <Link to="/wallet/deposit">
        <Button className="bg-gold-500 hover:bg-gold-400 text-black">
          Deposit Funds
        </Button>
      </Link>
      <Link to="/trade">
        <Button variant="outline" className="border-white/10 hover:bg-white/5">
          Start Trading
        </Button>
      </Link>
    </div>
  </div>
);

export default Portfolio;
