/**
 * Order Management Component
 * Displays active orders with cancel functionality
 * Implements the ghost feature: Cancel order button
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { RefreshCw, X, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import { api } from '@/lib/apiClient';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import type { Order } from '@/types/api';

const OrderManagement = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [cancellingOrderId, setCancellingOrderId] = useState<string | null>(null);

  // Fetch orders
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['orders'],
    queryFn: () => api.trading.getOrders(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const orders = data?.orders || [];

  // Cancel order mutation
  const cancelOrderMutation = useMutation({
    mutationFn: (orderId: string) => api.trading.cancelOrder(orderId),
    onSuccess: (response, orderId) => {
      toast({
        title: 'Order Cancelled',
        description: `Order ${orderId.slice(0, 8)}... has been cancelled`,
      });
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['balance'] });
      setCancellingOrderId(null);
    },
    onError: (error: any, orderId) => {
      toast({
        title: 'Cancellation Failed',
        description: error.message || 'Failed to cancel order',
        variant: 'destructive',
      });
      setCancellingOrderId(null);
    },
  });

  const handleCancelOrder = (orderId: string) => {
    setCancellingOrderId(orderId);
  };

  const confirmCancel = () => {
    if (cancellingOrderId) {
      cancelOrderMutation.mutate(cancellingOrderId);
    }
  };

  const getOrderTypeLabel = (orderType: string) => {
    const labels: Record<string, string> = {
      market: 'Market',
      limit: 'Limit',
      stop_loss: 'Stop-Loss',
      take_profit: 'Take-Profit',
      stop_limit: 'Stop-Limit',
    };
    return labels[orderType] || orderType;
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any; className: string }> = {
      pending: { variant: 'secondary', className: 'bg-amber-500/10 text-amber-500 border-amber-500/20' },
      filled: { variant: 'secondary', className: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
      cancelled: { variant: 'secondary', className: 'bg-red-500/10 text-red-500 border-red-500/20' },
    };
    const config = variants[status] || variants.pending;
    return (
      <Badge variant={config.variant} className={config.className}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  return (
    <>
      <Card className="p-6 border-border/50 bg-secondary/20 backdrop-blur">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <h2 className="font-display text-xl font-bold">Active Orders</h2>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-3" />
            <p>Loading orders...</p>
          </div>
        ) : orders.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No active orders</p>
            <p className="text-sm mt-1">Place an order to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Pair</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Side</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Stop Price</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order: Order) => (
                  <TableRow key={order.id}>
                    <TableCell className="font-medium">{order.trading_pair}</TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {getOrderTypeLabel(order.order_type)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {order.side === 'buy' ? (
                          <>
                            <TrendingUp className="h-3 w-3 text-emerald-500" />
                            <span className="text-emerald-500 uppercase text-sm font-medium">
                              Buy
                            </span>
                          </>
                        ) : (
                          <>
                            <TrendingDown className="h-3 w-3 text-red-500" />
                            <span className="text-red-500 uppercase text-sm font-medium">
                              Sell
                            </span>
                          </>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {order.amount.toFixed(8)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      ${order.price.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {order.stop_price ? `$${order.stop_price.toFixed(2)}` : '-'}
                    </TableCell>
                    <TableCell>{getStatusBadge(order.status)}</TableCell>
                    <TableCell className="text-right">
                      {order.status === 'pending' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCancelOrder(order.id)}
                          disabled={cancelOrderMutation.isPending}
                          className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={!!cancellingOrderId} onOpenChange={() => setCancellingOrderId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Order?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel this order? This action cannot be undone.
              {cancellingOrderId && (
                <div className="mt-3 p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm font-mono">Order ID: {cancellingOrderId.slice(0, 16)}...</p>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={cancelOrderMutation.isPending}>
              Keep Order
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmCancel}
              disabled={cancelOrderMutation.isPending}
              className="bg-red-500 hover:bg-red-600"
            >
              {cancelOrderMutation.isPending ? 'Cancelling...' : 'Yes, Cancel Order'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default OrderManagement;
