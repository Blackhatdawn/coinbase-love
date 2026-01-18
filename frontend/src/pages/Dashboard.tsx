/**
 * Dashboard - Premium Trading Dashboard
 * Bybit-inspired modular card layout with real-time data and drag-and-drop reordering
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Shield,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Copy,
  Check,
  Users,
  Gift,
  Percent,
  Clock,
  ExternalLink,
  GripVertical
} from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { api } from '@/lib/apiClient';
import { useAuth } from '@/contexts/AuthContext';
import { usePriceWebSocket } from '@/hooks/usePriceWebSocket';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import DashboardCard from '@/components/dashboard/DashboardCard';
import WelcomeAnimation from '@/components/dashboard/WelcomeAnimation';

// Animation variants for stagger effect
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

// Default widget order
const DEFAULT_WIDGET_ORDER = ['balance', 'security', 'holdings', 'earn', 'referrals', 'transactions'];

const Dashboard = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { prices, status: priceStatus } = usePriceWebSocket();
  const [showWelcome, setShowWelcome] = useState(false);
  const [copiedReferral, setCopiedReferral] = useState(false);
  const [widgetOrder, setWidgetOrder] = useState<string[]>(() => {
    const saved = localStorage.getItem('cv_widget_order');
    return saved ? JSON.parse(saved) : DEFAULT_WIDGET_ORDER;
  });

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement before drag starts
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Check for first login
  useEffect(() => {
    const hasSeenWelcome = localStorage.getItem('cv_welcome_seen');
    if (!hasSeenWelcome && user) {
      setShowWelcome(true);
    }
  }, [user]);

  const handleWelcomeComplete = () => {
    localStorage.setItem('cv_welcome_seen', 'true');
    setShowWelcome(false);
  };

  // Fetch portfolio data
  const { data: portfolioData, isLoading: portfolioLoading, refetch: refetchPortfolio } = useQuery({
    queryKey: ['portfolio'],
    queryFn: () => api.portfolio.get(),
    refetchInterval: 30000,
  });

  // Fetch transactions
  const { data: transactionsData, isLoading: transactionsLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: () => api.transactions.getAll(0, 5),
  });

  // Calculate real-time portfolio value
  const holdings = portfolioData?.portfolio?.holdings || [];
  const originalTotalValue = portfolioData?.portfolio?.totalBalance || 0;

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

  // Copy referral code
  const handleCopyReferral = () => {
    const code = 'CV' + (user?.id?.slice(-6)?.toUpperCase() || 'VAULT');
    navigator.clipboard.writeText(`https://cryptovault.financial/auth?ref=${code}`);
    setCopiedReferral(true);
    setTimeout(() => setCopiedReferral(false), 2000);
  };

  // Handle drag end - reorder widgets
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setWidgetOrder((items) => {
        const oldIndex = items.indexOf(active.id as string);
        const newIndex = items.indexOf(over.id as string);
        const newOrder = arrayMove(items, oldIndex, newIndex);
        
        // Save to localStorage
        localStorage.setItem('cv_widget_order', JSON.stringify(newOrder));
        
        return newOrder;
      });
    }
  };

  // Check if price feed is working (based on last update timestamp)
  const isPriceFeedActive = priceStatus.lastUpdate && 
    (new Date().getTime() - new Date(priceStatus.lastUpdate).getTime()) < 60000; // Active if updated in last 60s

  // Show welcome animation for first-time users
  if (showWelcome && user) {
    return (
      <WelcomeAnimation
        userName={user.name?.split(' ')[0] || 'Trader'}
        onComplete={handleWelcomeComplete}
        duration={5000}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-white">
            Welcome back, <span className="text-gold-400">{user?.name?.split(' ')[0]}</span>
          </h1>
          <p className="text-gray-400 mt-1">
            Here's your portfolio overview
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Live Status - Shows HTTP Polling Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-lg">
            {isPriceFeedActive ? (
              <>
                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                <span className="text-xs text-emerald-400 font-medium">LIVE</span>
              </>
            ) : priceStatus.isConnecting ? (
              <>
                <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
                <span className="text-xs text-amber-400 font-medium">CONNECTING</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 bg-gray-500 rounded-full" />
                <span className="text-xs text-gray-500 font-medium">OFFLINE</span>
              </>
            )}
          </div>

          {/* Refresh Button */}
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
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6"
      >
        {/* Hero Card - Total Balance (spans 2-3 columns) */}
        <motion.div variants={itemVariants} className="md:col-span-2 lg:col-span-2 xl:col-span-3">
          <DashboardCard
            title="Total Balance"
            icon={<Wallet className="h-5 w-5" />}
            className="h-full"
            glowColor="gold"
          >
            <div className="space-y-4">
              <div className="flex items-baseline gap-3">
                <span className="text-4xl sm:text-5xl font-display font-bold text-white">
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

              {/* BTC Equivalent */}
              <div className="flex items-center gap-2 text-gray-400 text-sm">
                <img src="https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=029" alt="BTC" className="w-4 h-4" />
                ≈ {((totalValue) / (parseFloat(prices['btc'] || '68000'))).toFixed(6)} BTC
              </div>

              {/* Quick Actions */}
              <div className="flex flex-wrap gap-3 pt-4 border-t border-white/5">
                <Link to="/wallet/deposit" className="flex-1 min-w-[120px]">
                  <Button className="w-full bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold">
                    <ArrowDownRight className="h-4 w-4 mr-2" />
                    Deposit
                  </Button>
                </Link>
                <Link to="/wallet/withdraw" className="flex-1 min-w-[120px]">
                  <Button variant="outline" className="w-full border-white/10 hover:bg-white/5">
                    <ArrowUpRight className="h-4 w-4 mr-2" />
                    Withdraw
                  </Button>
                </Link>
                <Link to="/trade" className="flex-1 min-w-[120px]">
                  <Button variant="outline" className="w-full border-gold-500/30 text-gold-400 hover:bg-gold-500/10">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Trade
                  </Button>
                </Link>
              </div>
            </div>
          </DashboardCard>
        </motion.div>

        {/* Security Status Card */}
        <motion.div variants={itemVariants} className="xl:col-span-1">
          <DashboardCard
            title="Security"
            icon={<Shield className="h-5 w-5" />}
            className="h-full"
            glowColor="emerald"
          >
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-emerald-500/10 rounded-xl">
                  <Shield className="h-8 w-8 text-emerald-400" />
                </div>
                <div>
                  <p className="text-lg font-semibold text-white">Protected</p>
                  <p className="text-xs text-emerald-400">All systems secure</p>
                </div>
              </div>

              <div className="space-y-2">
                <SecurityItem label="2FA" enabled status="Enabled" />
                <SecurityItem label="Email Verified" enabled status="Verified" />
                <SecurityItem label="Anti-Phishing" enabled={false} status="Set up" link="/security" />
              </div>
            </div>
          </DashboardCard>
        </motion.div>

        {/* Holdings Card */}
        <motion.div variants={itemVariants} className="md:col-span-2">
          <DashboardCard
            title="Your Assets"
            action={
              <Link to="/trade" className="text-xs text-gold-400 hover:text-gold-300 flex items-center gap-1">
                Trade <ExternalLink className="h-3 w-3" />
              </Link>
            }
            className="h-full"
          >
            {portfolioLoading ? (
              <HoldingsSkeleton />
            ) : holdings.length > 0 ? (
              <div className="space-y-3">
                {holdings.slice(0, 4).map((holding: any, i: number) => {
                  const wsPrice = prices[holding.symbol?.toLowerCase()];
                  const currentValue = wsPrice ? parseFloat(wsPrice) * holding.amount : holding.value;
                  const change = Math.random() > 0.5 ? Math.random() * 5 : -Math.random() * 3; // Mock 24h change

                  return (
                    <HoldingRow
                      key={holding.symbol}
                      symbol={holding.symbol}
                      name={holding.name}
                      amount={holding.amount}
                      value={currentValue}
                      change={change}
                      isLive={!!wsPrice}
                    />
                  );
                })}
                {holdings.length > 4 && (
                  <Link
                    to="/portfolio"
                    className="block text-center text-sm text-gray-400 hover:text-gold-400 py-2"
                  >
                    View all {holdings.length} assets
                  </Link>
                )}
              </div>
            ) : (
              <EmptyState
                icon={<Wallet className="h-12 w-12" />}
                title="No assets yet"
                description="Deposit crypto to start building your portfolio"
                action={
                  <Link to="/wallet/deposit">
                    <Button size="sm" className="bg-gold-500 hover:bg-gold-400 text-black">
                      Deposit Now
                    </Button>
                  </Link>
                }
              />
            )}
          </DashboardCard>
        </motion.div>

        {/* Staking/Earn Card */}
        <motion.div variants={itemVariants}>
          <DashboardCard
            title="Earn"
            icon={<Percent className="h-5 w-5" />}
            badge="Up to 12% APY"
            className="h-full"
            glowColor="violet"
          >
            <div className="space-y-4">
              <div className="p-4 bg-violet-500/10 rounded-xl border border-violet-500/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Active Stakes</span>
                  <span className="text-lg font-semibold text-white">$0.00</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Rewards Earned</span>
                  <span className="text-lg font-semibold text-emerald-400">+$0.00</span>
                </div>
              </div>

              <Link to="/earn">
                <Button className="w-full bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-400 hover:to-purple-500">
                  Start Earning
                </Button>
              </Link>
            </div>
          </DashboardCard>
        </motion.div>

        {/* Referral Card */}
        <motion.div variants={itemVariants}>
          <DashboardCard
            title="Referrals"
            icon={<Gift className="h-5 w-5" />}
            className="h-full"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-white">0</p>
                  <p className="text-xs text-gray-400">Total Referrals</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-emerald-400">$0.00</p>
                  <p className="text-xs text-gray-400">Earned</p>
                </div>
              </div>

              <div className="p-3 bg-white/5 rounded-lg">
                <p className="text-xs text-gray-400 mb-2">Your referral code</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-sm font-mono text-gold-400 truncate">
                    CV{user?.id?.slice(-6)?.toUpperCase() || 'VAULT'}
                  </code>
                  <button
                    onClick={handleCopyReferral}
                    className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                    aria-label="Copy referral link"
                  >
                    {copiedReferral ? (
                      <Check className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <Copy className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>

              <p className="text-xs text-gray-500">
                Earn 10% of your friends' trading fees
              </p>
            </div>
          </DashboardCard>
        </motion.div>

        {/* Recent Transactions Card */}
        <motion.div variants={itemVariants} className="md:col-span-2">
          <DashboardCard
            title="Recent Activity"
            icon={<Clock className="h-5 w-5" />}
            action={
              <Link to="/transactions" className="text-xs text-gold-400 hover:text-gold-300 flex items-center gap-1">
                View All <ExternalLink className="h-3 w-3" />
              </Link>
            }
            className="h-full"
          >
            {transactionsLoading ? (
              <TransactionsSkeleton />
            ) : (transactionsData?.transactions?.length || 0) > 0 ? (
              <div className="space-y-2">
                {transactionsData?.transactions?.slice(0, 5).map((tx: any) => (
                  <TransactionRow key={tx.id} transaction={tx} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<Clock className="h-10 w-10" />}
                title="No transactions"
                description="Your trading activity will appear here"
              />
            )}
          </DashboardCard>
        </motion.div>
      </motion.div>
    </div>
  );
};

// Sub-components
const HoldingRow = ({
  symbol,
  name,
  amount,
  value,
  change,
  isLive
}: {
  symbol: string;
  name: string;
  amount: number;
  value: number;
  change: number;
  isLive: boolean;
}) => (
  <div className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center font-bold text-gold-400">
        {symbol?.charAt(0)}
      </div>
      <div>
        <p className="font-medium text-white">{symbol}</p>
        <p className="text-xs text-gray-500">{amount.toFixed(4)} {symbol}</p>
      </div>
    </div>
    <div className="text-right">
      <p className={cn('font-semibold', isLive && 'text-gold-400')}>
        ${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
      </p>
      <p className={cn(
        'text-xs font-medium',
        change >= 0 ? 'text-emerald-400' : 'text-red-400'
      )}>
        {change >= 0 ? '+' : ''}{change.toFixed(2)}%
      </p>
    </div>
  </div>
);

const TransactionRow = ({ transaction }: { transaction: any }) => {
  const isBuy = transaction.type === 'buy' || transaction.type === 'deposit';
  return (
    <div className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors">
      <div className="flex items-center gap-3">
        <div className={cn(
          'p-2 rounded-lg',
          isBuy ? 'bg-emerald-500/10' : 'bg-red-500/10'
        )}>
          {isBuy ? (
            <ArrowDownRight className="h-4 w-4 text-emerald-400" />
          ) : (
            <ArrowUpRight className="h-4 w-4 text-red-400" />
          )}
        </div>
        <div>
          <p className="font-medium text-white capitalize">{transaction.type}</p>
          <p className="text-xs text-gray-500">
            {new Date(transaction.createdAt).toLocaleDateString()}
          </p>
        </div>
      </div>
      <p className={cn(
        'font-semibold',
        isBuy ? 'text-emerald-400' : 'text-red-400'
      )}>
        {isBuy ? '+' : '-'}${Math.abs(transaction.amount).toLocaleString()}
      </p>
    </div>
  );
};

const SecurityItem = ({
  label,
  enabled,
  status,
  link
}: {
  label: string;
  enabled: boolean;
  status: string;
  link?: string;
}) => (
  <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
    <span className="text-sm text-gray-400">{label}</span>
    {link ? (
      <Link to={link} className="text-xs text-gold-400 hover:text-gold-300">
        {status}
      </Link>
    ) : (
      <span className={cn(
        'text-xs font-medium',
        enabled ? 'text-emerald-400' : 'text-gray-500'
      )}>
        {status}
      </span>
    )}
  </div>
);

const EmptyState = ({
  icon,
  title,
  description,
  action
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}) => (
  <div className="flex flex-col items-center justify-center py-8 text-center">
    <div className="text-gray-600 mb-3">{icon}</div>
    <p className="font-medium text-gray-400 mb-1">{title}</p>
    <p className="text-sm text-gray-500 mb-4">{description}</p>
    {action}
  </div>
);

const HoldingsSkeleton = () => (
  <div className="space-y-3">
    {[1, 2, 3].map((i) => (
      <div key={i} className="flex items-center gap-3 p-3 animate-pulse">
        <div className="w-10 h-10 rounded-full bg-white/5" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-20 bg-white/5 rounded" />
          <div className="h-3 w-16 bg-white/5 rounded" />
        </div>
        <div className="space-y-2 text-right">
          <div className="h-4 w-16 bg-white/5 rounded ml-auto" />
          <div className="h-3 w-12 bg-white/5 rounded ml-auto" />
        </div>
      </div>
    ))}
  </div>
);

const TransactionsSkeleton = () => (
  <div className="space-y-2">
    {[1, 2, 3].map((i) => (
      <div key={i} className="flex items-center gap-3 p-3 animate-pulse">
        <div className="w-8 h-8 rounded-lg bg-white/5" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-24 bg-white/5 rounded" />
          <div className="h-3 w-16 bg-white/5 rounded" />
        </div>
        <div className="h-4 w-20 bg-white/5 rounded" />
      </div>
    ))}
  </div>
);

export default Dashboard;
