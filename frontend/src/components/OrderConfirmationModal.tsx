/**
 * Order Confirmation Modal
 * Shows order details after successful trade execution
 */
import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Copy, ExternalLink, Share2, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

export interface OrderDetails {
  orderId: string;
  type: 'buy' | 'sell';
  symbol: string;
  amount: number;
  price: number;
  total: number;
  fee: number;
  status: 'filled' | 'pending' | 'partial';
  timestamp: string;
  txHash?: string;
}

interface OrderConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: OrderDetails | null;
}

const OrderConfirmationModal = ({ isOpen, onClose, order }: OrderConfirmationModalProps) => {
  const [copied, setCopied] = useState(false);

  if (!order) return null;

  const copyOrderId = async () => {
    await navigator.clipboard.writeText(order.orderId);
    setCopied(true);
    toast.success('Order ID copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatCrypto = (value: number, symbol: string) => {
    return `${value.toFixed(8)} ${symbol}`;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-card border-gold-500/20" data-testid="order-confirmation-modal">
        <DialogHeader className="text-center pb-4">
          {/* Success Icon */}
          <div className="mx-auto mb-4">
            <div className={cn(
              'h-16 w-16 rounded-full flex items-center justify-center',
              order.type === 'buy' 
                ? 'bg-emerald-500/10 text-emerald-500' 
                : 'bg-red-500/10 text-red-500'
            )}>
              {order.type === 'buy' ? (
                <ArrowDownRight className="h-8 w-8" />
              ) : (
                <ArrowUpRight className="h-8 w-8" />
              )}
            </div>
          </div>
          
          <DialogTitle className="text-xl font-display">
            Order {order.status === 'filled' ? 'Completed' : order.status === 'pending' ? 'Pending' : 'Partially Filled'}
          </DialogTitle>
          <DialogDescription>
            Your {order.type} order for {order.symbol} has been {order.status}
          </DialogDescription>
        </DialogHeader>

        {/* Order Details */}
        <div className="space-y-4 py-4">
          {/* Order ID */}
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
            <span className="text-sm text-muted-foreground">Order ID</span>
            <div className="flex items-center gap-2">
              <code className="text-xs font-mono">{order.orderId.slice(0, 8)}...{order.orderId.slice(-4)}</code>
              <button 
                onClick={copyOrderId}
                className="p-1 hover:bg-muted rounded transition-colors"
                aria-label="Copy order ID"
              >
                {copied ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Copy className="h-4 w-4 text-muted-foreground" />
                )}
              </button>
            </div>
          </div>

          {/* Trade Details */}
          <div className="space-y-3 divide-y divide-border/50">
            <div className="flex justify-between py-2">
              <span className="text-muted-foreground">Type</span>
              <span className={cn(
                'font-medium uppercase text-sm px-2 py-0.5 rounded',
                order.type === 'buy' 
                  ? 'bg-emerald-500/10 text-emerald-500' 
                  : 'bg-red-500/10 text-red-500'
              )}>
                {order.type}
              </span>
            </div>

            <div className="flex justify-between py-2">
              <span className="text-muted-foreground">Amount</span>
              <span className="font-mono">{formatCrypto(order.amount, order.symbol)}</span>
            </div>

            <div className="flex justify-between py-2">
              <span className="text-muted-foreground">Price</span>
              <span className="font-mono">{formatCurrency(order.price)}</span>
            </div>

            <div className="flex justify-between py-2">
              <span className="text-muted-foreground">Fee</span>
              <span className="font-mono text-muted-foreground">{formatCurrency(order.fee)}</span>
            </div>

            <div className="flex justify-between py-2">
              <span className="text-muted-foreground font-medium">Total</span>
              <span className="font-mono font-bold text-lg">{formatCurrency(order.total)}</span>
            </div>
          </div>

          {/* Transaction Hash (if available) */}
          {order.txHash && (
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg mt-4">
              <span className="text-sm text-muted-foreground">Transaction</span>
              <a 
                href={`https://etherscan.io/tx/${order.txHash}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-gold-400 hover:text-gold-300"
              >
                View on Explorer
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          )}

          {/* Timestamp */}
          <div className="text-center text-xs text-muted-foreground mt-4">
            Executed at {new Date(order.timestamp).toLocaleString()}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-border/50">
          <Button 
            variant="outline" 
            className="flex-1 min-h-[44px]"
            onClick={onClose}
          >
            Close
          </Button>
          <Button 
            className="flex-1 min-h-[44px] bg-gold-500 hover:bg-gold-600 text-black"
            onClick={() => {
              // Share functionality
              toast.info('Share feature coming soon');
            }}
          >
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default OrderConfirmationModal;
