/**
 * Price Alerts Page
 * Create and manage cryptocurrency price alerts
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  Bell,
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Loader2,
  BellRing,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

interface PriceAlert {
  id: string;
  symbol: string;
  targetPrice: number;
  condition: 'above' | 'below';
  isActive: boolean;
  createdAt: string;
  triggeredAt?: string;
}

const CRYPTO_OPTIONS = [
  { value: 'BTC', label: 'Bitcoin', price: 95000 },
  { value: 'ETH', label: 'Ethereum', price: 3300 },
  { value: 'BNB', label: 'BNB', price: 700 },
  { value: 'SOL', label: 'Solana', price: 145 },
  { value: 'XRP', label: 'Ripple', price: 2.15 },
  { value: 'ADA', label: 'Cardano', price: 0.85 },
  { value: 'DOGE', label: 'Dogecoin', price: 0.32 },
];

const PriceAlerts = () => {
  const navigate = useNavigate();
  
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  // Form state
  const [symbol, setSymbol] = useState('BTC');
  const [targetPrice, setTargetPrice] = useState('');
  const [condition, setCondition] = useState<'above' | 'below'>('above');
  const [notifyPush, setNotifyPush] = useState(true);
  const [notifyEmail, setNotifyEmail] = useState(true);

  // Fetch alerts on mount
  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await api.alerts.getAll();
      setAlerts(response.alerts || []);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();

    const price = parseFloat(targetPrice);
    if (isNaN(price) || price <= 0) {
      toast.error('Please enter a valid price');
      return;
    }

    setIsCreating(true);

    try {
      const response = await api.alerts.create({
        symbol,
        targetPrice: price,
        condition,
        notifyPush,
        notifyEmail,
      });

      setAlerts(prev => [response.alert, ...prev]);
      toast.success(`Alert created for ${symbol} ${condition} $${price.toLocaleString()}`);
      
      // Reset form
      setTargetPrice('');
      setShowCreateForm(false);
    } catch (error: any) {
      toast.error(error.message || 'Failed to create alert');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    try {
      await api.alerts.delete(alertId);
      setAlerts(prev => prev.filter(a => a.id !== alertId));
      toast.success('Alert deleted');
    } catch (error) {
      toast.error('Failed to delete alert');
    }
  };

  const handleToggleAlert = async (alertId: string, isActive: boolean) => {
    try {
      await api.alerts.update(alertId, { isActive });
      setAlerts(prev => prev.map(a => 
        a.id === alertId ? { ...a, isActive } : a
      ));
    } catch (error) {
      toast.error('Failed to update alert');
    }
  };

  const getCurrentPrice = (sym: string) => {
    const crypto = CRYPTO_OPTIONS.find(c => c.value === sym);
    return crypto?.price || 0;
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4 sm:px-6 max-w-3xl">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="font-display text-2xl sm:text-3xl font-bold mb-1">
                Price <span className="text-gradient">Alerts</span>
              </h1>
              <p className="text-muted-foreground text-sm sm:text-base">
                Get notified when crypto reaches your target price
              </p>
            </div>
            <Button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="bg-gold-500 hover:bg-gold-600 text-black min-h-[44px]"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Alert
            </Button>
          </div>

          {/* Create Alert Form */}
          {showCreateForm && (
            <Card className="glass-card border-gold-500/10 mb-6 animate-slide-up">
              <CardHeader>
                <CardTitle className="text-lg">New Price Alert</CardTitle>
                <CardDescription>Set up a new price notification</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateAlert} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Cryptocurrency Select */}
                    <div className="space-y-2">
                      <Label>Cryptocurrency</Label>
                      <Select value={symbol} onValueChange={setSymbol}>
                        <SelectTrigger className="h-12">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CRYPTO_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label} ({option.value})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        Current: ${getCurrentPrice(symbol).toLocaleString()}
                      </p>
                    </div>

                    {/* Target Price */}
                    <div className="space-y-2">
                      <Label>Target Price (USD)</Label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                        <Input
                          type="number"
                          placeholder="0.00"
                          value={targetPrice}
                          onChange={(e) => setTargetPrice(e.target.value)}
                          className="pl-8 h-12"
                          step="0.01"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  {/* Condition */}
                  <div className="space-y-2">
                    <Label>Alert When Price Goes</Label>
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => setCondition('above')}
                        className={cn(
                          'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border transition-all',
                          condition === 'above'
                            ? 'border-emerald-500 bg-emerald-500/10 text-emerald-500'
                            : 'border-border hover:border-emerald-500/50'
                        )}
                      >
                        <ArrowUp className="h-4 w-4" />
                        Above
                      </button>
                      <button
                        type="button"
                        onClick={() => setCondition('below')}
                        className={cn(
                          'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border transition-all',
                          condition === 'below'
                            ? 'border-red-500 bg-red-500/10 text-red-500'
                            : 'border-border hover:border-red-500/50'
                        )}
                      >
                        <ArrowDown className="h-4 w-4" />
                        Below
                      </button>
                    </div>
                  </div>

                  {/* Notification Options */}
                  <div className="space-y-3">
                    <Label>Notify Me Via</Label>
                    <div className="flex flex-col sm:flex-row gap-4">
                      <div className="flex items-center justify-between sm:justify-start gap-3 p-3 bg-muted/50 rounded-lg flex-1">
                        <div className="flex items-center gap-2">
                          <BellRing className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">Push Notification</span>
                        </div>
                        <Switch checked={notifyPush} onCheckedChange={setNotifyPush} />
                      </div>
                      <div className="flex items-center justify-between sm:justify-start gap-3 p-3 bg-muted/50 rounded-lg flex-1">
                        <div className="flex items-center gap-2">
                          <Bell className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">Email</span>
                        </div>
                        <Switch checked={notifyEmail} onCheckedChange={setNotifyEmail} />
                      </div>
                    </div>
                  </div>

                  {/* Submit */}
                  <div className="flex gap-3 pt-2">
                    <Button
                      type="button"
                      variant="outline"
                      className="flex-1 min-h-[44px]"
                      onClick={() => setShowCreateForm(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      className="flex-1 bg-gold-500 hover:bg-gold-600 text-black min-h-[44px]"
                      disabled={isCreating}
                    >
                      {isCreating ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        'Create Alert'
                      )}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Alerts List */}
          <div className="space-y-4">
            {isLoading ? (
              <div className="text-center py-12">
                <Loader2 className="h-8 w-8 animate-spin mx-auto text-gold-400" />
              </div>
            ) : alerts.length === 0 ? (
              <Card className="glass-card border-gold-500/10">
                <CardContent className="py-12 text-center">
                  <Bell className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p className="text-muted-foreground">
                    No price alerts yet. Create one to get started!
                  </p>
                </CardContent>
              </Card>
            ) : (
              alerts.map((alert) => (
                <Card 
                  key={alert.id} 
                  className={cn(
                    'glass-card border-gold-500/10 transition-all',
                    !alert.isActive && 'opacity-60'
                  )}
                >
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 min-w-0">
                        {/* Icon */}
                        <div className={cn(
                          'h-10 w-10 sm:h-12 sm:w-12 rounded-lg flex items-center justify-center flex-shrink-0',
                          alert.condition === 'above' 
                            ? 'bg-emerald-500/10' 
                            : 'bg-red-500/10'
                        )}>
                          {alert.condition === 'above' ? (
                            <ArrowUp className="h-5 w-5 sm:h-6 sm:w-6 text-emerald-500" />
                          ) : (
                            <ArrowDown className="h-5 w-5 sm:h-6 sm:w-6 text-red-500" />
                          )}
                        </div>
                        
                        {/* Info */}
                        <div className="min-w-0">
                          <div className="font-semibold text-sm sm:text-base">
                            {alert.symbol}
                          </div>
                          <div className="text-xs sm:text-sm text-muted-foreground">
                            {alert.condition === 'above' ? '↑ Above' : '↓ Below'} ${alert.targetPrice.toLocaleString()}
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 sm:gap-3">
                        {alert.triggeredAt && (
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        )}
                        <Switch
                          checked={alert.isActive}
                          onCheckedChange={(checked) => handleToggleAlert(alert.id, checked)}
                        />
                        <button
                          onClick={() => handleDeleteAlert(alert.id)}
                          className="p-2 text-muted-foreground hover:text-red-500 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default PriceAlerts;
