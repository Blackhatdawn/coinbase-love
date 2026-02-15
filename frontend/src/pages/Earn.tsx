/**
 * Earn Page - Staking and Passive Income
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { TrendingUp, Lock, Percent, Clock, Shield, Info, ChevronRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import DashboardCard from '@/components/dashboard/DashboardCard';
import { api } from '@/lib/apiClient';
import { toast } from 'sonner';

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

type StakingProduct = {
  id: string;
  token: string;
  name: string;
  type: 'flexible' | 'locked';
  apy: number;
  minAmount: number;
  lockPeriod: string;
  tvl: number;
  icon: string;
  color: string;
  popular?: boolean;
  hot?: boolean;
  new?: boolean;
};

type ActiveStake = {
  id: string;
  product: string;
  token: string;
  amount: number;
  apy: number;
  rewards: number;
  startDate: string;
  lockPeriod: string;
  daysRemaining?: number;
  status: string;
  productId?: string;
};

const Earn = () => {
  const [activeTab, setActiveTab] = useState<'products' | 'active'>('products');
  const [selectedType, setSelectedType] = useState<'all' | 'flexible' | 'locked'>('all');
  const [stakeAmounts, setStakeAmounts] = useState<Record<string, string>>({});
  const queryClient = useQueryClient();

  const { data: productsData } = useQuery({ queryKey: ['earn-products'], queryFn: api.earn.getProducts });
  const { data: positionsData } = useQuery({ queryKey: ['earn-positions'], queryFn: api.earn.getPositions });

  const stakeMutation = useMutation({
    mutationFn: api.earn.stake,
    onSuccess: () => {
      toast.success('Stake created successfully.');
      queryClient.invalidateQueries({ queryKey: ['earn-positions'] });
      queryClient.invalidateQueries({ queryKey: ['wallet-balance'] });
    },
    onError: (error: any) => toast.error(error?.message || 'Failed to create stake'),
  });

  const redeemMutation = useMutation({
    mutationFn: api.earn.redeem,
    onSuccess: () => {
      toast.success('Stake redeemed successfully.');
      queryClient.invalidateQueries({ queryKey: ['earn-positions'] });
      queryClient.invalidateQueries({ queryKey: ['wallet-balance'] });
    },
    onError: (error: any) => toast.error(error?.message || 'Failed to redeem stake'),
  });

  const stakingProducts: StakingProduct[] = productsData?.products || [];
  const activeStakes: ActiveStake[] = positionsData?.positions || [];

  const filteredProducts = stakingProducts.filter((p) => (selectedType === 'all' ? true : p.type === selectedType));

  const totalStaked = activeStakes.reduce((sum, s) => sum + s.amount, 0);
  const totalRewards = activeStakes.reduce((sum, s) => sum + s.rewards, 0);

  const handleStake = (product: StakingProduct) => {
    const raw = stakeAmounts[product.id] || '';
    const amount = Number(raw);
    if (!Number.isFinite(amount) || amount <= 0) {
      toast.error('Please enter a valid amount.');
      return;
    }
    if (amount < product.minAmount) {
      toast.error(`Minimum stake is ${product.minAmount} ${product.token}.`);
      return;
    }

    stakeMutation.mutate(
      { product_id: product.id, amount },
      {
        onSuccess: () => {
          setStakeAmounts((prev) => ({ ...prev, [product.id]: '' }));
        },
      },
    );
  };

  const handleRedeem = (stakeId: string) => {
    redeemMutation.mutate({ stake_id: stakeId });
  };

  const handleStake = (product: StakingProduct) => {
    const raw = window.prompt(`Enter amount to stake (minimum ${product.minAmount} ${product.token})`);
    if (!raw) return;
    const amount = Number(raw);
    if (!Number.isFinite(amount) || amount <= 0) {
      toast.error('Please enter a valid amount.');
      return;
    }

    stakeMutation.mutate({ product_id: product.id, amount });
  };

  const handleRedeem = (stakeId: string) => {
    redeemMutation.mutate({ stake_id: stakeId });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-white flex items-center gap-3">
            <Sparkles className="h-7 w-7 text-gold-400" />
            Earn
          </h1>
          <p className="text-gray-400 mt-1">Put your crypto to work and earn passive income</p>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <Shield className="h-4 w-4 text-emerald-400" />
          <span className="text-emerald-400">All staking products are fully insured</span>
        </div>
      </div>

      <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div variants={itemVariants}><DashboardCard className="h-full"><div className="flex items-center gap-3"><div className="p-3 bg-gold-500/10 rounded-xl"><Lock className="h-6 w-6 text-gold-400" /></div><div><p className="text-sm text-gray-400">Total Staked</p><p className="text-2xl font-bold text-white">{totalStaked.toLocaleString(undefined, { maximumFractionDigits: 4 })}</p></div></div></DashboardCard></motion.div>
        <motion.div variants={itemVariants}><DashboardCard className="h-full"><div className="flex items-center gap-3"><div className="p-3 bg-emerald-500/10 rounded-xl"><TrendingUp className="h-6 w-6 text-emerald-400" /></div><div><p className="text-sm text-gray-400">Total Rewards</p><p className="text-2xl font-bold text-emerald-400">+{totalRewards.toLocaleString(undefined, { maximumFractionDigits: 6 })}</p></div></div></DashboardCard></motion.div>
        <motion.div variants={itemVariants}><DashboardCard className="h-full"><div className="flex items-center gap-3"><div className="p-3 bg-violet-500/10 rounded-xl"><Percent className="h-6 w-6 text-violet-400" /></div><div><p className="text-sm text-gray-400">Avg. APY</p><p className="text-2xl font-bold text-white">{((activeStakes.reduce((sum, s) => sum + (s.apy || 0), 0) / (activeStakes.length || 1)) || 0).toFixed(1)}%</p></div></div></DashboardCard></motion.div>
        <motion.div variants={itemVariants}><DashboardCard className="h-full"><div className="flex items-center gap-3"><div className="p-3 bg-blue-500/10 rounded-xl"><Clock className="h-6 w-6 text-blue-400" /></div><div><p className="text-sm text-gray-400">Active Stakes</p><p className="text-2xl font-bold text-white">{activeStakes.length}</p></div></div></DashboardCard></motion.div>
      </motion.div>

      <div className="flex items-center gap-4 border-b border-white/5 pb-4">
        <button onClick={() => setActiveTab('products')} className={cn('px-4 py-2 text-sm font-medium rounded-lg transition-colors', activeTab === 'products' ? 'bg-gold-500/10 text-gold-400' : 'text-gray-400 hover:text-white hover:bg-white/5')}>Staking Products</button>
        <button onClick={() => setActiveTab('active')} className={cn('px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2', activeTab === 'active' ? 'bg-gold-500/10 text-gold-400' : 'text-gray-400 hover:text-white hover:bg-white/5')}>My Stakes{activeStakes.length > 0 && (<span className="px-1.5 py-0.5 text-[10px] bg-gold-500 text-black rounded-full font-bold">{activeStakes.length}</span>)}</button>
      </div>

      {activeTab === 'products' && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">{['all', 'flexible', 'locked'].map((type) => (<button key={type} onClick={() => setSelectedType(type as any)} className={cn('px-3 py-1.5 text-xs font-medium rounded-lg transition-colors capitalize', selectedType === type ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-gray-300')}>{type}</button>))}</div>
          <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredProducts.map((product) => (
              <motion.div key={product.id} variants={itemVariants}>
                <StakingProductCard
                  product={product}
                  amount={stakeAmounts[product.id] || ''}
                  onAmountChange={(value) => setStakeAmounts((prev) => ({ ...prev, [product.id]: value }))}
                  onStake={handleStake}
                  loading={stakeMutation.isPending}
                />
              </motion.div>
            ))}
          </motion.div>
        </div>
      )}

      {activeTab === 'active' && (
        <div className="space-y-4">
          {activeStakes.length > 0 ? activeStakes.map((stake) => (<ActiveStakeCard key={stake.id} stake={stake} onRedeem={handleRedeem} loading={redeemMutation.isPending} />)) : (
            <DashboardCard><div className="flex flex-col items-center justify-center py-12 text-center"><div className="p-4 bg-white/5 rounded-full mb-4"><Lock className="h-8 w-8 text-gray-500" /></div><h3 className="text-lg font-semibold text-white mb-2">No active stakes</h3><p className="text-gray-400 mb-4">Start earning by staking your crypto</p><Button onClick={() => setActiveTab('products')} className="bg-gold-500 hover:bg-gold-400 text-black">Browse Products</Button></div></DashboardCard>
          )}
        </div>
      )}

      <DashboardCard title="How Earn Works" icon={<Info className="h-5 w-5" />}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <HowItWorksStep step={1} title="Choose a Product" description="Select from flexible or locked staking options based on your preference" />
          <HowItWorksStep step={2} title="Stake Your Crypto" description="Stake from token balance or USD equivalent (auto-converted)" />
          <HowItWorksStep step={3} title="Earn Rewards" description="Receive principal and accrued rewards on redemption" />
        </div>
      </DashboardCard>
    </div>
  );
};

const StakingProductCard = ({
  product,
  amount,
  onAmountChange,
  onStake,
  loading,
}: {
  product: StakingProduct;
  amount: string;
  onAmountChange: (value: string) => void;
  onStake: (product: StakingProduct) => void;
  loading: boolean;
}) => {
  const colorClasses = {
    orange: 'from-orange-500/20 to-orange-600/20 border-orange-500/20',
    violet: 'from-violet-500/20 to-violet-600/20 border-violet-500/20',
    emerald: 'from-emerald-500/20 to-emerald-600/20 border-emerald-500/20',
    purple: 'from-purple-500/20 to-purple-600/20 border-purple-500/20',
  };

  const iconColors = {
    orange: 'text-orange-400 bg-orange-500/10',
    violet: 'text-violet-400 bg-violet-500/10',
    emerald: 'text-emerald-400 bg-emerald-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
  };

  return (
    <motion.div whileHover={{ y: -2, scale: 1.01 }} className={cn('relative p-5 rounded-2xl border bg-gradient-to-br transition-all duration-300', colorClasses[product.color as keyof typeof colorClasses] || colorClasses.orange, 'hover:shadow-lg')}>
      <div className="absolute top-4 right-4 flex gap-2">{product.popular && (<span className="px-2 py-0.5 text-[10px] font-bold bg-gold-500 text-black rounded-full">POPULAR</span>)}{product.hot && (<span className="px-2 py-0.5 text-[10px] font-bold bg-red-500 text-white rounded-full">HOT</span>)}{product.new && (<span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500 text-white rounded-full">NEW</span>)}</div>
      <div className="flex items-center gap-3 mb-4"><div className={cn('w-12 h-12 rounded-xl flex items-center justify-center text-2xl font-bold', iconColors[product.color as keyof typeof iconColors] || iconColors.orange)}>{product.icon}</div><div><h3 className="font-semibold text-white">{product.name}</h3><p className="text-xs text-gray-400 capitalize">{product.type} • {product.lockPeriod}</p></div></div>
      <div className="mb-4"><p className="text-xs text-gray-400 mb-1">Annual Percentage Yield</p><p className="text-3xl font-bold text-white">{product.apy}%<span className="text-sm font-normal text-gray-400 ml-1">APY</span></p></div>
      <div className="flex items-center justify-between text-sm mb-4 pb-4 border-b border-white/5"><div><p className="text-gray-500">Min. Stake</p><p className="text-white font-medium">{product.minAmount} {product.token}</p></div><div className="text-right"><p className="text-gray-500">TVL</p><p className="text-white font-medium">${(product.tvl / 1000000).toFixed(0)}M</p></div></div>
      <div className="space-y-2">
        <Input
          type="number"
          min={product.minAmount}
          step="any"
          value={amount}
          onChange={(e) => onAmountChange(e.target.value)}
          placeholder={`Amount (${product.token})`}
        />
        <Button className="w-full bg-white/10 hover:bg-white/20 text-white" onClick={() => onStake(product)} disabled={loading}>{loading ? 'Submitting...' : 'Stake Now'}<ChevronRight className="h-4 w-4 ml-1" /></Button>
      </div>
    </motion.div>
  );
};

const ActiveStakeCard = ({ stake, onRedeem, loading }: { stake: ActiveStake; onRedeem: (stakeId: string) => void; loading: boolean }) => (
  <DashboardCard>
    <div className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center font-bold text-gold-400">{stake.token.charAt(0)}</div>
        <div>
          <h3 className="font-semibold text-white">{stake.product}</h3>
          <p className="text-sm text-gray-400">{stake.amount} {stake.token} • {stake.apy}% APY</p>
        </div>
      </div>

      <div className="text-right">
        <p className="text-sm text-gray-400">Rewards Earned</p>
        <p className="text-lg font-semibold text-emerald-400">+{stake.rewards} {stake.token}</p>
        {stake.daysRemaining !== undefined && (<p className="text-xs text-gray-500">{stake.daysRemaining} days remaining</p>)}
        <Button variant="outline" size="sm" className="mt-2" onClick={() => onRedeem(stake.id)} disabled={loading || (stake.daysRemaining ?? 0) > 0}>Redeem</Button>
      </div>
    </div>
  </DashboardCard>
);

const HowItWorksStep = ({ step, title, description }: { step: number; title: string; description: string }) => (
  <div className="flex gap-4">
    <div className="w-10 h-10 rounded-full bg-gold-500/10 flex items-center justify-center text-gold-400 font-bold flex-shrink-0">{step}</div>
    <div><h4 className="font-semibold text-white mb-1">{title}</h4><p className="text-sm text-gray-400">{description}</p></div>
  </div>
);

export default Earn;
