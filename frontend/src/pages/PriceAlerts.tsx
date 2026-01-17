/**
 * Price Alerts Page - Dashboard Version
 * Premium Bybit-style price alert management
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  Bell,
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Mail,
  Smartphone
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/apiClient';
import { cn } from '@/lib/utils';
import DashboardCard from '@/components/dashboard/DashboardCard';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

const CRYPTO_OPTIONS = [
  { value: 'BTC', label: 'Bitcoin', icon: '₿' },
  { value: 'ETH', label: 'Ethereum', icon: 'Ξ' },
  { value: 'SOL', label: 'Solana', icon: 'S' },
  { value: 'XRP', label: 'Ripple', icon: 'X' },
  { value: 'DOGE', label: 'Dogecoin', icon: 'D' },
];

interface Alert {
  id: string;
  symbol: string;
  targetPrice: number;
  condition: 'above' | 'below';
  isActive: boolean;
  notifyEmail: boolean;
  notifyPush: boolean;
  createdAt: string;
  triggeredAt?: string;
}

const PriceAlerts = () => {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newAlert, setNewAlert] = useState({
    symbol: 'BTC',
    targetPrice: '',
    condition: 'above' as 'above' | 'below',
    notifyEmail: true,
    notifyPush: true,
  });

  // Fetch alerts
  const { data: alertsData, isLoading } = useQuery({
    queryKey: ['priceAlerts'],
    queryFn: () => api.alerts.getAll(),
  });

  // Create alert mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newAlert) => api.alerts.create({
      symbol: data.symbol,
      targetPrice: parseFloat(data.targetPrice),
      condition: data.condition,
      notifyEmail: data.notifyEmail,
      notifyPush: data.notifyPush,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['priceAlerts'] });
      toast.success('Alert created successfully!');
      setIsCreateOpen(false);
      setNewAlert({ symbol: 'BTC', targetPrice: '', condition: 'above', notifyEmail: true, notifyPush: true });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create alert');
    },
  });

  // Delete alert mutation
  const deleteMutation = useMutation({
    mutationFn: (alertId: string) => api.alerts.delete(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['priceAlerts'] });
      toast.success('Alert deleted');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to delete alert');
    },
  });

  // Toggle alert mutation
  const toggleMutation = useMutation({
    mutationFn: ({ alertId, isActive }: { alertId: string; isActive: boolean }) =>
      api.alerts.update(alertId, { isActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['priceAlerts'] });
    },
  });

  const alerts: Alert[] = alertsData?.alerts || [];
  const activeAlerts = alerts.filter(a => a.isActive);
  const triggeredAlerts = alerts.filter(a => a.triggeredAt);

  const handleCreateAlert = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAlert.targetPrice || parseFloat(newAlert.targetPrice) <= 0) {
      toast.error('Please enter a valid price');
      return;
    }
    createMutation.mutate(newAlert);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-white flex items-center gap-3">
            <Bell className="h-7 w-7 text-gold-400" />
            Price Alerts
          </h1>
          <p className="text-gray-400 mt-1">Get notified when prices hit your targets</p>
        </div>

        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold">
              <Plus className="h-4 w-4 mr-2" />
              Create Alert
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#1a1a2e] border-white/10 sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white">Create Price Alert</DialogTitle>
              <DialogDescription className="text-gray-400">
                Get notified when a cryptocurrency reaches your target price.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateAlert} className="space-y-4 mt-4">
              {/* Asset Select */}
              <div className="space-y-2">
                <Label className="text-gray-300">Asset</Label>
                <Select value={newAlert.symbol} onValueChange={(v) => setNewAlert({ ...newAlert, symbol: v })}>
                  <SelectTrigger className="bg-white/5 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1a1a2e] border-white/10">
                    {CRYPTO_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{option.icon}</span>
                          <span>{option.label}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Condition Select */}
              <div className="space-y-2">
                <Label className="text-gray-300">Condition</Label>
                <Select value={newAlert.condition} onValueChange={(v: 'above' | 'below') => setNewAlert({ ...newAlert, condition: v })}>
                  <SelectTrigger className="bg-white/5 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1a1a2e] border-white/10">
                    <SelectItem value="above">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-emerald-400" />
                        <span>Price goes above</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="below">
                      <div className="flex items-center gap-2">
                        <TrendingDown className="h-4 w-4 text-red-400" />
                        <span>Price goes below</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Target Price */}
              <div className="space-y-2">
                <Label className="text-gray-300">Target Price (USD)</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <Input
                    type="number"
                    placeholder="0.00"
                    value={newAlert.targetPrice}
                    onChange={(e) => setNewAlert({ ...newAlert, targetPrice: e.target.value })}
                    className="pl-8 bg-white/5 border-white/10"
                    step="0.01"
                    required
                  />
                </div>
              </div>

              {/* Notification Options */}
              <div className="space-y-3 pt-2">
                <Label className="text-gray-300">Notifications</Label>
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">Email</span>
                  </div>
                  <Switch
                    checked={newAlert.notifyEmail}
                    onCheckedChange={(v) => setNewAlert({ ...newAlert, notifyEmail: v })}
                  />
                </div>
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Smartphone className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">Push Notification</span>
                  </div>
                  <Switch
                    checked={newAlert.notifyPush}
                    onCheckedChange={(v) => setNewAlert({ ...newAlert, notifyPush: v })}
                  />
                </div>
              </div>

              {/* Submit */}
              <Button
                type="submit"
                className="w-full bg-gold-500 hover:bg-gold-400 text-black"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Alert'
                )}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <DashboardCard>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gold-500/10 rounded-xl">
              <Bell className="h-6 w-6 text-gold-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Alerts</p>
              <p className="text-2xl font-bold text-white">{alerts.length}</p>
            </div>
          </div>
        </DashboardCard>

        <DashboardCard glowColor="emerald">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-500/10 rounded-xl">
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Active</p>
              <p className="text-2xl font-bold text-white">{activeAlerts.length}</p>
            </div>
          </div>
        </DashboardCard>

        <DashboardCard glowColor="violet">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-violet-500/10 rounded-xl">
              <AlertCircle className="h-6 w-6 text-violet-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Triggered</p>
              <p className="text-2xl font-bold text-white">{triggeredAlerts.length}</p>
            </div>
          </div>
        </DashboardCard>
      </div>

      {/* Alerts List */}
      <DashboardCard title="Your Alerts" icon={<Bell className="h-5 w-5" />}>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 bg-white/5 rounded-xl animate-pulse">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-white/10" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-24 bg-white/10 rounded" />
                    <div className="h-3 w-32 bg-white/10 rounded" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12">
            <div className="p-4 bg-white/5 rounded-full w-fit mx-auto mb-4">
              <Bell className="h-8 w-8 text-gray-500" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">No alerts yet</h3>
            <p className="text-gray-400 mb-4">Create your first price alert to get started</p>
            <Button onClick={() => setIsCreateOpen(true)} className="bg-gold-500 hover:bg-gold-400 text-black">
              <Plus className="h-4 w-4 mr-2" />
              Create Alert
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                onToggle={(isActive) => toggleMutation.mutate({ alertId: alert.id, isActive })}
                onDelete={() => deleteMutation.mutate(alert.id)}
                isDeleting={deleteMutation.isPending}
              />
            ))}
          </div>
        )}
      </DashboardCard>
    </div>
  );
};

// Alert Item Component
const AlertItem = ({
  alert,
  onToggle,
  onDelete,
  isDeleting,
}: {
  alert: Alert;
  onToggle: (isActive: boolean) => void;
  onDelete: () => void;
  isDeleting: boolean;
}) => {
  const crypto = CRYPTO_OPTIONS.find(c => c.value === alert.symbol);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'p-4 rounded-xl border transition-all',
        alert.isActive
          ? 'bg-white/5 border-white/10'
          : 'bg-white/2 border-white/5 opacity-60'
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={cn(
            'w-10 h-10 rounded-lg flex items-center justify-center text-xl font-bold',
            alert.condition === 'above' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
          )}>
            {crypto?.icon || alert.symbol.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">{alert.symbol}</span>
              <span className={cn(
                'text-xs px-2 py-0.5 rounded-full',
                alert.condition === 'above'
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : 'bg-red-500/10 text-red-400'
              )}>
                {alert.condition === 'above' ? '↑' : '↓'} ${alert.targetPrice.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
              {alert.notifyEmail && <Mail className="h-3 w-3" />}
              {alert.notifyPush && <Smartphone className="h-3 w-3" />}
              {alert.triggeredAt && (
                <span className="text-gold-400">Triggered</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Switch
            checked={alert.isActive}
            onCheckedChange={onToggle}
          />
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="p-2 hover:bg-red-500/10 rounded-lg text-gray-400 hover:text-red-400 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default PriceAlerts;
