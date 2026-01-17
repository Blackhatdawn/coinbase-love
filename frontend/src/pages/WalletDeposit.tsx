/**
 * Wallet Deposit Page - Dashboard Version
 * Premium Bybit-style deposit interface
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Wallet, 
  ArrowLeft, 
  Loader2, 
  Shield, 
  Clock, 
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Copy,
  QrCode,
  Info
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/apiClient';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import DashboardCard from '@/components/dashboard/DashboardCard';

const CRYPTO_OPTIONS = [
  { value: 'btc', label: 'Bitcoin', symbol: 'BTC', icon: '₿', color: 'orange' },
  { value: 'eth', label: 'Ethereum', symbol: 'ETH', icon: 'Ξ', color: 'violet' },
  { value: 'usdt', label: 'Tether', symbol: 'USDT', icon: '₮', color: 'emerald' },
  { value: 'usdc', label: 'USD Coin', symbol: 'USDC', icon: '$', color: 'blue' },
];

const PRESET_AMOUNTS = [100, 500, 1000, 5000];

interface DepositResponse {
  success: boolean;
  orderId?: string;
  invoiceId?: string;
  paymentUrl?: string;
  payAddress?: string;
  address?: string;
  payAmount?: number;
  amount: number;
  currency: string;
  expiresAt?: string;
  mock?: boolean;
}

const WalletDeposit = () => {
  const { user } = useAuth();
  
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('btc');
  const [isLoading, setIsLoading] = useState(false);
  const [depositInfo, setDepositInfo] = useState<DepositResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const selectedCrypto = CRYPTO_OPTIONS.find(c => c.value === currency);

  const handlePresetAmount = (preset: number) => {
    setAmount(preset.toString());
  };

  const copyAddress = async () => {
    const address = depositInfo?.address || depositInfo?.payAddress;
    if (address) {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      toast.success('Address copied!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();

    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount < 10) {
      toast.error('Minimum deposit is $10');
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.wallet.createDeposit({
        amount: numAmount,
        currency: currency,
      });
      
      setDepositInfo({
        ...response,
        address: response.payAddress,
        paymentUrl: response.paymentUrl,
      });
      
      if (response.paymentUrl) {
        toast.success('Payment invoice created!');
      } else if (response.payAddress) {
        toast.success('Deposit address generated!');
      }
      
      if (response.mock) {
        toast.info('Running in demo mode - this is a simulated deposit');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to create deposit');
    } finally {
      setIsLoading(false);
    }
  };

  // Show deposit info if we have it
  if (depositInfo) {
    return (
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setDepositInfo(null)}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-400" />
          </button>
          <div>
            <h1 className="text-2xl font-display font-bold text-white">Deposit Pending</h1>
            <p className="text-gray-400 text-sm">Complete your payment within the time limit</p>
          </div>
        </div>

        <div className="max-w-lg mx-auto">
          <DashboardCard glowColor="gold">
            <div className="space-y-6">
              {/* Status Icon */}
              <div className="flex justify-center">
                <div className="p-4 bg-gold-500/10 rounded-full">
                  <Clock className="h-10 w-10 text-gold-400" />
                </div>
              </div>

              {/* Mock Mode Warning */}
              {depositInfo.mock && (
                <div className="flex items-start gap-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl text-sm">
                  <Info className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-400">Demo Mode</p>
                    <p className="text-gray-400 mt-1">
                      This is a simulated deposit. In production, complete payment via the payment gateway.
                    </p>
                  </div>
                </div>
              )}
              
              {/* Amount Info */}
              <div className="text-center p-6 bg-white/5 rounded-xl border border-white/10">
                <div className="text-4xl font-bold font-mono text-white">
                  ${depositInfo.amount.toFixed(2)}
                </div>
                <div className="text-sm text-gray-400 mt-2">
                  Pay in {depositInfo.currency.toUpperCase()}
                </div>
              </div>

              {/* Payment Address */}
              {(depositInfo.address || depositInfo.payAddress) && (
                <div className="space-y-2">
                  <Label className="text-gray-400">Payment Address</Label>
                  <div className="flex items-center gap-2 p-4 bg-white/5 rounded-xl border border-white/10">
                    <code className="flex-1 text-xs font-mono break-all text-gold-400">
                      {depositInfo.address || depositInfo.payAddress}
                    </code>
                    <button
                      onClick={copyAddress}
                      className="p-2 hover:bg-white/10 rounded-lg transition-colors flex-shrink-0"
                    >
                      {copied ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                      ) : (
                        <Copy className="h-5 w-5 text-gray-400" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Payment URL */}
              {depositInfo.paymentUrl && (
                <Button
                  className="w-full h-12 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold"
                  onClick={() => window.open(depositInfo.paymentUrl, '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Open Payment Page
                </Button>
              )}

              {/* Warning */}
              <div className="flex items-start gap-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl text-sm">
                <AlertCircle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-amber-400">Important</p>
                  <p className="text-gray-400 mt-1">
                    Send only {depositInfo.currency.toUpperCase()} to this address. 
                    Sending other cryptocurrencies may result in permanent loss.
                  </p>
                </div>
              </div>

              {/* Back Button */}
              <Button
                variant="outline"
                className="w-full h-12 border-white/10 hover:bg-white/5"
                onClick={() => setDepositInfo(null)}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Create New Deposit
              </Button>
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
          <h1 className="text-2xl font-display font-bold text-white">Deposit Funds</h1>
          <p className="text-gray-400 text-sm">Add cryptocurrency to your wallet</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Deposit Form */}
        <div className="lg:col-span-2">
          <DashboardCard>
            <form onSubmit={handleDeposit} className="space-y-6">
              {/* Amount Input */}
              <div className="space-y-3">
                <Label className="text-gray-300">Amount (USD)</Label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-xl">$</span>
                  <Input
                    type="number"
                    placeholder="0.00"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="pl-10 h-14 text-2xl font-mono bg-white/5 border-white/10 focus:border-gold-500/50"
                    min="10"
                    step="0.01"
                    required
                    data-testid="deposit-amount-input"
                  />
                </div>
                
                {/* Preset Amounts */}
                <div className="flex gap-2">
                  {PRESET_AMOUNTS.map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => handlePresetAmount(preset)}
                      className={cn(
                        'flex-1 py-2.5 text-sm font-medium rounded-lg transition-all',
                        amount === preset.toString()
                          ? 'bg-gold-500 text-black'
                          : 'bg-white/5 hover:bg-white/10 text-gray-300'
                      )}
                    >
                      ${preset}
                    </button>
                  ))}
                </div>
              </div>

              {/* Currency Select */}
              <div className="space-y-3">
                <Label className="text-gray-300">Pay With</Label>
                <Select value={currency} onValueChange={setCurrency}>
                  <SelectTrigger className="h-14 bg-white/5 border-white/10" data-testid="deposit-currency-select">
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

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full h-14 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold text-lg"
                disabled={isLoading || !amount}
                data-testid="deposit-submit-button"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Wallet className="h-5 w-5 mr-2" />
                    Continue to Payment
                  </>
                )}
              </Button>
            </form>
          </DashboardCard>
        </div>

        {/* Info Sidebar */}
        <div className="space-y-4">
          <DashboardCard glowColor="emerald">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-emerald-500/10 rounded-lg">
                <Shield className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Secure Deposits</h3>
                <p className="text-sm text-gray-400 mt-1">
                  All deposits are processed through secure payment gateways with instant confirmation.
                </p>
              </div>
            </div>
          </DashboardCard>

          <DashboardCard>
            <div className="space-y-4">
              <h3 className="font-semibold text-white">How it works</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-gold-500/20 flex items-center justify-center text-gold-400 text-sm font-bold">1</div>
                  <p className="text-sm text-gray-400">Enter your deposit amount in USD</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-gold-500/20 flex items-center justify-center text-gold-400 text-sm font-bold">2</div>
                  <p className="text-sm text-gray-400">Select your preferred cryptocurrency</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-gold-500/20 flex items-center justify-center text-gold-400 text-sm font-bold">3</div>
                  <p className="text-sm text-gray-400">Complete payment to the generated address</p>
                </div>
              </div>
            </div>
          </DashboardCard>

          <DashboardCard>
            <div className="text-center">
              <p className="text-xs text-gray-500">Minimum deposit: <span className="text-gold-400">$10</span></p>
              <p className="text-xs text-gray-500 mt-1">Network confirmations: 1-6 depending on asset</p>
            </div>
          </DashboardCard>
        </div>
      </div>
    </div>
  );
};

export default WalletDeposit;
