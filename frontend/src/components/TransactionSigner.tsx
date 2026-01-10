import React, { useState } from 'react';
import { useWeb3 } from '@/contexts/Web3Context';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertTriangle, CheckCircle2, Send } from 'lucide-react';
import { toast } from 'sonner';

interface TransactionSignerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  type: 'buy' | 'sell';
  coinSymbol: string;
  coinName: string;
  currentPrice: number;
}

export const TransactionSigner: React.FC<TransactionSignerProps> = ({
  open,
  onOpenChange,
  type,
  coinSymbol,
  coinName,
  currentPrice
}) => {
  const { account, balance, sendTransaction, estimateGas, getGasPrice, networkName } = useWeb3();
  
  const [amount, setAmount] = useState('');
  const [recipientAddress, setRecipientAddress] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [gasEstimate, setGasEstimate] = useState<string>('');
  const [gasPrice, setGasPrice] = useState<string>('');

  // Calculate total cost
  const calculateTotal = (): number => {
    const amountValue = parseFloat(amount) || 0;
    return amountValue * currentPrice;
  };

  // Estimate gas when amount changes
  React.useEffect(() => {
    const estimate = async () => {
      if (amount && recipientAddress && parseFloat(amount) > 0) {
        try {
          const gas = await estimateGas(recipientAddress, amount);
          setGasEstimate(gas);
          
          const price = await getGasPrice();
          setGasPrice(price);
        } catch (err) {
          console.error('Gas estimation error:', err);
        }
      }
    };

    estimate();
  }, [amount, recipientAddress]);

  // Handle transaction
  const handleTransaction = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    if (!recipientAddress || recipientAddress.length !== 42) {
      setError('Please enter a valid recipient address');
      return;
    }

    if (!account) {
      setError('Wallet not connected');
      return;
    }

    const amountValue = parseFloat(amount);
    const currentBalance = parseFloat(balance || '0');

    if (type === 'sell' && amountValue > currentBalance) {
      setError('Insufficient balance');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const hash = await sendTransaction(recipientAddress, amount);
      setTxHash(hash);
      
      toast.success('Transaction successful!', {
        description: `${type === 'buy' ? 'Bought' : 'Sold'} ${amount} ${coinSymbol}`
      });

      // Reset form
      setTimeout(() => {
        setAmount('');
        setRecipientAddress('');
        setTxHash(null);
        onOpenChange(false);
      }, 3000);
    } catch (err: any) {
      setError(err.message || 'Transaction failed');
      toast.error('Transaction failed', {
        description: err.message
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Get explorer URL
  const getExplorerUrl = () => {
    if (!txHash || !networkName) return '#';
    
    const explorers: { [key: string]: string } = {
      'Ethereum': `https://etherscan.io/tx/${txHash}`,
      'Polygon': `https://polygonscan.com/tx/${txHash}`,
      'Sepolia': `https://sepolia.etherscan.io/tx/${txHash}`
    };
    
    return explorers[networkName] || '#';
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-2xl">
            {type === 'buy' ? '🛒 Buy' : '💰 Sell'} {coinName}
          </DialogTitle>
          <DialogDescription>
            {type === 'buy' 
              ? `Purchase ${coinSymbol} using your wallet` 
              : `Sell your ${coinSymbol} holdings`}
          </DialogDescription>
        </DialogHeader>

        {txHash ? (
          // Success State
          <div className="space-y-4 py-4">
            <div className="flex flex-col items-center justify-center text-center space-y-3">
              <CheckCircle2 className="h-16 w-16 text-green-600" />
              <h3 className="text-xl font-semibold">Transaction Submitted!</h3>
              <p className="text-sm text-muted-foreground">
                Your transaction has been sent to the blockchain
              </p>
              
              <Alert>
                <AlertDescription className="font-mono text-xs break-all">
                  {txHash}
                </AlertDescription>
              </Alert>

              <Button
                variant="outline"
                onClick={() => window.open(getExplorerUrl(), '_blank')}
                className="w-full"
              >
                View on Explorer →
              </Button>
            </div>
          </div>
        ) : (
          // Transaction Form
          <div className="space-y-4 py-4">
            {/* Current Price */}
            <div className="p-3 bg-secondary/30 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Current Price</span>
                <span className="text-lg font-bold">${currentPrice.toLocaleString()}</span>
              </div>
              {balance && (
                <div className="flex justify-between items-center mt-1">
                  <span className="text-xs text-muted-foreground">Your Balance</span>
                  <span className="text-sm font-medium">{parseFloat(balance).toFixed(4)} {networkName === 'Polygon' ? 'MATIC' : 'ETH'}</span>
                </div>
              )}
            </div>

            {/* Amount Input */}
            <div className="space-y-2">
              <Label htmlFor="amount">
                Amount ({networkName === 'Polygon' ? 'MATIC' : 'ETH'})
              </Label>
              <Input
                id="amount"
                type="number"
                step="0.0001"
                placeholder="0.0000"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                disabled={isProcessing}
              />
              {amount && (
                <p className="text-xs text-muted-foreground">
                  ≈ ${calculateTotal().toFixed(2)} USD
                </p>
              )}
            </div>

            {/* Recipient Address */}
            <div className="space-y-2">
              <Label htmlFor="recipient">Recipient Address</Label>
              <Input
                id="recipient"
                type="text"
                placeholder="0x..."
                value={recipientAddress}
                onChange={(e) => setRecipientAddress(e.target.value)}
                disabled={isProcessing}
                className="font-mono text-sm"
              />
            </div>

            {/* Gas Estimate */}
            {gasEstimate && gasPrice && (
              <div className="p-3 bg-secondary/30 rounded-lg space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Estimated Gas</span>
                  <span className="font-mono">{gasEstimate}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Gas Price</span>
                  <span className="font-mono">{gasPrice} Gwei</span>
                </div>
                <div className="flex justify-between font-semibold pt-1 border-t">
                  <span>Network Fee</span>
                  <span>
                    {((parseFloat(gasPrice) * parseFloat(gasEstimate)) / 1e9).toFixed(6)} {networkName === 'Polygon' ? 'MATIC' : 'ETH'}
                  </span>
                </div>
              </div>
            )}

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Warning for Buy */}
            {type === 'buy' && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  This is a simulated buy. In production, this would interact with a DEX or exchange contract.
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        <DialogFooter>
          {!txHash && (
            <>
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isProcessing}
              >
                Cancel
              </Button>
              <Button
                onClick={handleTransaction}
                disabled={isProcessing || !amount || !recipientAddress}
                className={type === 'buy' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    {type === 'buy' ? 'Buy Now' : 'Sell Now'}
                  </>
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
