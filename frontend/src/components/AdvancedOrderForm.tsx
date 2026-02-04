/**
 * Advanced Order Form Component
 * Supports Stop-Loss, Take-Profit, and Stop-Limit orders
 * Implements the ghost feature: Advanced order types
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info, TrendingUp, TrendingDown, Shield, Target, Zap } from 'lucide-react';
import { api } from '@/lib/apiClient';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import type { AdvancedOrderCreate } from '@/types/api';

interface AdvancedOrderFormProps {
  tradingPair?: string;
  currentPrice?: number;
  onSuccess?: () => void;
}

const AdvancedOrderForm = ({ tradingPair = '', currentPrice = 0, onSuccess }: AdvancedOrderFormProps) => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Form state
  const [orderType, setOrderType] = useState<'stop_loss' | 'take_profit' | 'stop_limit'>('stop_loss');
  const [side, setSide] = useState<'buy' | 'sell'>('sell'); // Stop-loss is usually sell
  const [amount, setAmount] = useState('');
  const [limitPrice, setLimitPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');
  const [timeInForce, setTimeInForce] = useState<'GTC' | 'IOC' | 'FOK'>('GTC');

  // Mutation for creating advanced order
  const createOrderMutation = useMutation({
    mutationFn: (data: AdvancedOrderCreate) => api.trading.createAdvancedOrder(data),
    onSuccess: (response) => {
      toast({
        title: 'Advanced Order Created',
        description: `${orderType.replace('_', ' ')} order placed successfully`,
      });
      // Reset form
      setAmount('');
      setLimitPrice('');
      setStopPrice('');
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['balance'] });
      onSuccess?.();
    },
    onError: (error: any) => {
      toast({
        title: 'Order Failed',
        description: error.message || 'Failed to create advanced order',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = () => {
    if (!tradingPair) {
      toast({
        title: 'Missing Trading Pair',
        description: 'Please select a trading pair',
        variant: 'destructive',
      });
      return;
    }

    if (!amount || parseFloat(amount) <= 0) {
      toast({
        title: 'Invalid Amount',
        description: 'Please enter a valid amount',
        variant: 'destructive',
      });
      return;
    }

    if (!stopPrice || parseFloat(stopPrice) <= 0) {
      toast({
        title: 'Invalid Stop Price',
        description: 'Please enter a valid stop price',
        variant: 'destructive',
      });
      return;
    }

    // Stop-limit requires both stop and limit price
    if (orderType === 'stop_limit' && (!limitPrice || parseFloat(limitPrice) <= 0)) {
      toast({
        title: 'Invalid Limit Price',
        description: 'Stop-limit orders require a limit price',
        variant: 'destructive',
      });
      return;
    }

    const orderData: AdvancedOrderCreate = {
      trading_pair: tradingPair,
      order_type: orderType,
      side: side,
      amount: parseFloat(amount),
      stop_price: parseFloat(stopPrice),
      time_in_force: timeInForce,
    };

    // Add limit price for stop-limit orders
    if (orderType === 'stop_limit' && limitPrice) {
      orderData.price = parseFloat(limitPrice);
    }

    createOrderMutation.mutate(orderData);
  };

  // Helper to calculate suggested stop-loss (5% below current price for sell)
  const suggestedStopLoss = currentPrice > 0 ? (currentPrice * 0.95).toFixed(2) : '';
  // Helper to calculate suggested take-profit (10% above current price for sell)
  const suggestedTakeProfit = currentPrice > 0 ? (currentPrice * 1.10).toFixed(2) : '';

  return (
    <Card className="p-6 border-border/50 bg-secondary/20 backdrop-blur">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="h-5 w-5 text-primary" />
          <h2 className="font-display text-xl font-bold">Advanced Orders</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Protect your portfolio with stop-loss and take-profit orders
        </p>
      </div>

      <Tabs value={orderType} onValueChange={(v) => setOrderType(v as any)} className="mb-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="stop_loss" className="flex items-center gap-1">
            <TrendingDown className="h-3 w-3" />
            Stop-Loss
          </TabsTrigger>
          <TabsTrigger value="take_profit" className="flex items-center gap-1">
            <Target className="h-3 w-3" />
            Take-Profit
          </TabsTrigger>
          <TabsTrigger value="stop_limit" className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            Stop-Limit
          </TabsTrigger>
        </TabsList>

        {/* Stop-Loss */}
        <TabsContent value="stop_loss" className="mt-4 space-y-4">
          <Alert className="border-amber-500/20 bg-amber-500/10">
            <Info className="h-4 w-4 text-amber-500" />
            <AlertDescription className="text-sm text-amber-200">
              Stop-loss sells your asset when price drops to the stop price, limiting losses.
            </AlertDescription>
          </Alert>

          {/* Side Selection */}
          <div>
            <Label className="mb-2">Side</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={side === 'sell' ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => setSide('sell')}
              >
                Sell (Protect Long)
              </Button>
              <Button
                type="button"
                variant={side === 'buy' ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => setSide('buy')}
              >
                Buy (Protect Short)
              </Button>
            </div>
          </div>

          {/* Amount */}
          <div>
            <Label className="mb-2">Amount</Label>
            <Input
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              step="0.00000001"
            />
          </div>

          {/* Stop Price */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>Stop Price</Label>
              {currentPrice > 0 && (
                <button
                  type="button"
                  onClick={() => setStopPrice(suggestedStopLoss)}
                  className="text-xs text-primary hover:underline"
                >
                  Suggested: ${suggestedStopLoss}
                </button>
              )}
            </div>
            <Input
              type="number"
              placeholder="Trigger price"
              value={stopPrice}
              onChange={(e) => setStopPrice(e.target.value)}
              step="0.01"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Order triggers when price reaches this level
            </p>
          </div>
        </TabsContent>

        {/* Take-Profit */}
        <TabsContent value="take_profit" className="mt-4 space-y-4">
          <Alert className="border-emerald-500/20 bg-emerald-500/10">
            <Info className="h-4 w-4 text-emerald-500" />
            <AlertDescription className="text-sm text-emerald-200">
              Take-profit automatically sells when your target price is reached, securing profits.
            </AlertDescription>
          </Alert>

          {/* Side Selection */}
          <div>
            <Label className="mb-2">Side</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={side === 'sell' ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => setSide('sell')}
              >
                Sell (Take Profit)
              </Button>
              <Button
                type="button"
                variant={side === 'buy' ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => setSide('buy')}
              >
                Buy (Close Short)
              </Button>
            </div>
          </div>

          {/* Amount */}
          <div>
            <Label className="mb-2">Amount</Label>
            <Input
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              step="0.00000001"
            />
          </div>

          {/* Stop Price (Target Price) */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>Target Price</Label>
              {currentPrice > 0 && (
                <button
                  type="button"
                  onClick={() => setStopPrice(suggestedTakeProfit)}
                  className="text-xs text-primary hover:underline"
                >
                  Suggested: ${suggestedTakeProfit}
                </button>
              )}
            </div>
            <Input
              type="number"
              placeholder="Target price"
              value={stopPrice}
              onChange={(e) => setStopPrice(e.target.value)}
              step="0.01"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Order triggers when price reaches this level
            </p>
          </div>
        </TabsContent>

        {/* Stop-Limit */}
        <TabsContent value="stop_limit" className="mt-4 space-y-4">
          <Alert className="border-blue-500/20 bg-blue-500/10">
            <Info className="h-4 w-4 text-blue-500" />
            <AlertDescription className="text-sm text-blue-200">
              Stop-limit combines stop and limit orders for more price control.
            </AlertDescription>
          </Alert>

          {/* Side */}
          <div>
            <Label className="mb-2">Side</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={side === 'buy' ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => setSide('buy')}
              >
                Buy
              </Button>
              <Button
                type="button"
                variant={side === 'sell' ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => setSide('sell')}
              >
                Sell
              </Button>
            </div>
          </div>

          {/* Amount */}
          <div>
            <Label className="mb-2">Amount</Label>
            <Input
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              step="0.00000001"
            />
          </div>

          {/* Stop Price */}
          <div>
            <Label className="mb-2">Stop Price</Label>
            <Input
              type="number"
              placeholder="Trigger price"
              value={stopPrice}
              onChange={(e) => setStopPrice(e.target.value)}
              step="0.01"
            />
          </div>

          {/* Limit Price */}
          <div>
            <Label className="mb-2">Limit Price</Label>
            <Input
              type="number"
              placeholder="Execution price"
              value={limitPrice}
              onChange={(e) => setLimitPrice(e.target.value)}
              step="0.01"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Maximum buy price or minimum sell price
            </p>
          </div>
        </TabsContent>
      </Tabs>

      {/* Time in Force */}
      <div className="mb-6">
        <Label className="mb-2">Time in Force</Label>
        <Select value={timeInForce} onValueChange={(v: any) => setTimeInForce(v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="GTC">Good Till Cancelled (GTC)</SelectItem>
            <SelectItem value="IOC">Immediate or Cancel (IOC)</SelectItem>
            <SelectItem value="FOK">Fill or Kill (FOK)</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground mt-1">
          {timeInForce === 'GTC' && 'Order remains active until filled or manually cancelled'}
          {timeInForce === 'IOC' && 'Fill immediately, cancel unfilled portion'}
          {timeInForce === 'FOK' && 'Fill entire order immediately or cancel'}
        </p>
      </div>

      {/* Current Price Info */}
      {currentPrice > 0 && (
        <div className="p-4 bg-secondary/50 rounded-lg border border-border/50 mb-6">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Current Price</span>
            <span className="font-display font-bold text-lg">${currentPrice.toFixed(2)}</span>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={createOrderMutation.isPending}
        size="lg"
        className="w-full"
        variant="hero"
      >
        {createOrderMutation.isPending ? 'Creating Order...' : `Create ${orderType.replace('_', ' ')} Order`}
      </Button>
    </Card>
  );
};

export default AdvancedOrderForm;
