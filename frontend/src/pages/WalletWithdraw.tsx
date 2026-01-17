/**
 * Wallet Withdraw Page - Dashboard Version
 * Premium Bybit-style withdrawal interface
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  ArrowLeft, 
  Loader2, 
  Shield, 
  AlertTriangle,
  CheckCircle2,
  Wallet,
  Send,
  Info
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/apiClient';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import DashboardCard from '@/components/dashboard/DashboardCard';

const CRYPTO_OPTIONS = [
  { value: 'btc', label: 'Bitcoin', symbol: 'BTC', icon: '₿', fee: 0.0001 },
  { value: 'eth', label: 'Ethereum', symbol: 'ETH', icon: 'Ξ', fee: 0.005 },
  { value: 'usdt', label: 'Tether', symbol: 'USDT', icon: '₮', fee: 1 },
  { value: 'usdc', label: 'USD Coin', symbol: 'USDC', icon: '$', fee: 1 },
];

const WalletWithdraw = () => {
  const { user } = useAuth();
  
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('btc');
  const [address, setAddress] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const selectedCrypto = CRYPTO_OPTIONS.find(c => c.value === currency);

  // Fetch wallet balance
  const { data: balanceData } = useQuery({
    queryKey: ['walletBalance'],
    queryFn: () => api.wallet.getBalance(),
  });

  const handleWithdraw = async (e: React.FormEvent) => {
    e.preventDefault();

    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    if (!address || address.length < 20) {
      toast.error('Please enter a valid wallet address');
      return;
    }

    setIsLoading(true);

    try {
      await api.wallet.withdraw({
        amount: numAmount,
        currency: currency,
        address: address,
      });
      
      setSuccess(true);
      toast.success('Withdrawal request submitted!');
    } catch (error: any) {
      toast.error(error.message || 'Failed to process withdrawal');
    } finally {
      setIsLoading(false);
    }
  };

  // Success state
  if (success) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link
            to="/dashboard"
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-display font-bold text-white">Withdrawal Submitted</h1>
            <p className="text-gray-400 text-sm">Your request is being processed</p>
          </div>
        </div>

        <div className="max-w-lg mx-auto">
          <DashboardCard glowColor="emerald">
            <div className="text-center space-y-6 py-6">
              <div className="mx-auto w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center">
                <CheckCircle2 className="h-8 w-8 text-emerald-400" />
              </div>
              
              <div>
                <h2 className="text-xl font-semibold text-white">Request Submitted</h2>
                <p className="text-gray-400 mt-2">Your withdrawal is being processed and will be sent shortly.</p>
              </div>

              <div className="p-4 bg-white/5 rounded-xl text-left space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Amount</span>
                  <span className="text-white font-mono">{amount} {selectedCrypto?.symbol}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Network Fee</span>
                  <span className="text-white font-mono">{selectedCrypto?.fee} {selectedCrypto?.symbol}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">To Address</span>
                  <span className="text-gold-400 font-mono text-xs truncate max-w-[200px]">{address}</span>
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1 border-white/10 hover:bg-white/5"
                  onClick={() => {
                    setSuccess(false);
                    setAmount('');
                    setAddress('');
                  }}
                >
                  New Withdrawal
                </Button>
                <Link to="/transactions" className="flex-1">
                  <Button className="w-full bg-gold-500 hover:bg-gold-400 text-black">
                    View Transactions
                  </Button>
                </Link>
              </div>
            </div>
          </DashboardCard>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/dashboard"
          className="p-2 hover:bg-white/5 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-400" />
        </Link>
        <div>
          <h1 className="text-2xl font-display font-bold text-white">Withdraw Funds</h1>
          <p className="text-gray-400 text-sm">Send cryptocurrency to external wallet</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Withdraw Form */}
        <div className="lg:col-span-2">
          <DashboardCard>
            <form onSubmit={handleWithdraw} className="space-y-6">
              {/* Currency Select */}
              <div className="space-y-3">
                <Label className="text-gray-300">Select Asset</Label>
                <Select value={currency} onValueChange={setCurrency}>
                  <SelectTrigger className="h-14 bg-white/5 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1a1a2e] border-white/10">
                    {CRYPTO_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{option.icon}</span>
                          <div>
                            <span className="font-medium">{option.label}</span>
                            <span className="text-gray-500 ml-2">{option.symbol}</span>
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Amount Input */}
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label className="text-gray-300">Amount</Label>
                  <span className="text-sm text-gray-500">
                    Available: <span className="text-gold-400">0.00 {selectedCrypto?.symbol}</span>
                  </span>
                </div>
                <div className="relative">
                  <Input
                    type="number"
                    placeholder="0.00"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="h-14 text-xl font-mono bg-white/5 border-white/10 focus:border-gold-500/50 pr-20"
                    step="0.00000001"
                    required
                    data-testid="withdraw-amount-input"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">
                    {selectedCrypto?.symbol}
                  </span>
                </div>
                <button
                  type="button"
                  className="text-sm text-gold-400 hover:text-gold-300"
                  onClick={() => setAmount('0')}
                >
                  Max
                </button>
              </div>

              {/* Address Input */}
              <div className="space-y-3">
                <Label className="text-gray-300">Withdrawal Address</Label>
                <Input
                  type="text"
                  placeholder={`Enter ${selectedCrypto?.symbol} address`}
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="h-14 font-mono bg-white/5 border-white/10 focus:border-gold-500/50"
                  required
                  data-testid="withdraw-address-input"
                />
              </div>

              {/* Fee Info */}
              <div className="p-4 bg-white/5 rounded-xl space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Network Fee</span>
                  <span className="text-white">{selectedCrypto?.fee} {selectedCrypto?.symbol}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">You will receive</span>
                  <span className="text-white font-semibold">
                    {amount ? (parseFloat(amount) - (selectedCrypto?.fee || 0)).toFixed(8) : '0.00'} {selectedCrypto?.symbol}
                  </span>
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full h-14 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold text-lg"
                disabled={isLoading || !amount || !address}
                data-testid="withdraw-submit-button"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    Withdraw {selectedCrypto?.symbol}
                  </>
                )}
              </Button>
            </form>
          </DashboardCard>
        </div>

        {/* Info Sidebar */}
        <div className="space-y-4">
          <DashboardCard glowColor="gold">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-gold-500/10 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-gold-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Important</h3>
                <p className="text-sm text-gray-400 mt-1">
                  Double-check the withdrawal address. Transactions cannot be reversed once confirmed.
                </p>
              </div>
            </div>
          </DashboardCard>

          <DashboardCard>
            <div className="space-y-4">
              <h3 className="font-semibold text-white">Withdrawal Limits</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Min withdrawal</span>
                  <span className="text-white">0.001 BTC</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Max withdrawal</span>
                  <span className="text-white">10 BTC / day</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Processing time</span>
                  <span className="text-white">10-30 mins</span>
                </div>
              </div>
            </div>
          </DashboardCard>

          <DashboardCard glowColor="emerald">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-emerald-500/10 rounded-lg">
                <Shield className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Secure Withdrawals</h3>
                <p className="text-sm text-gray-400 mt-1">
                  All withdrawals are reviewed for security. Large withdrawals may require additional verification.
                </p>
              </div>
            </div>
          </DashboardCard>
        </div>
      </div>
    </div>
  );
};

export default WalletWithdraw;
