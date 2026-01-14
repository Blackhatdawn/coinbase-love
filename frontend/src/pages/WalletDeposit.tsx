/**
 * Wallet Deposit Page
 * Crypto payment integration with NOWPayments
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  Bitcoin
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/apiClient';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

const CRYPTO_OPTIONS = [
  { value: 'btc', label: 'Bitcoin (BTC)', icon: '₿' },
  { value: 'eth', label: 'Ethereum (ETH)', icon: 'Ξ' },
  { value: 'usdt', label: 'Tether (USDT)', icon: '₮' },
  { value: 'usdc', label: 'USD Coin (USDC)', icon: '$' },
];

const PRESET_AMOUNTS = [100, 500, 1000, 5000];

interface DepositResponse {
  invoiceId: string;
  paymentUrl: string;
  address?: string;
  amount: number;
  currency: string;
  expiresAt: string;
}

const WalletDeposit = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('btc');
  const [isLoading, setIsLoading] = useState(false);
  const [depositInfo, setDepositInfo] = useState<DepositResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handlePresetAmount = (preset: number) => {
    setAmount(preset.toString());
  };

  const copyAddress = async () => {
    if (depositInfo?.address) {
      await navigator.clipboard.writeText(depositInfo.address);
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
      
      setDepositInfo(response);
      
      // If payment URL is returned, redirect to payment gateway
      if (response.paymentUrl) {
        toast.success('Redirecting to payment...');
        window.open(response.paymentUrl, '_blank');
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
      <div className="min-h-screen bg-background">
        <Header />
        <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
          <div className="container mx-auto px-4 sm:px-6 max-w-lg">
            <Card className="glass-card border-gold-500/10">
              <CardHeader className="text-center">
                <div className="mx-auto mb-4 h-14 w-14 rounded-full bg-gold-500/10 flex items-center justify-center">
                  <Clock className="h-7 w-7 text-gold-400" />
                </div>
                <CardTitle className="text-xl">Deposit Pending</CardTitle>
                <CardDescription>
                  Complete your payment within the time limit
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Amount Info */}
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-3xl font-bold font-mono">
                    ${depositInfo.amount.toFixed(2)}
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Pay in {depositInfo.currency.toUpperCase()}
                  </div>
                </div>

                {/* Payment Address */}
                {depositInfo.address && (
                  <div className="space-y-2">
                    <Label>Payment Address</Label>
                    <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
                      <code className="flex-1 text-xs font-mono break-all">
                        {depositInfo.address}
                      </code>
                      <button
                        onClick={copyAddress}
                        className="p-2 hover:bg-muted rounded transition-colors flex-shrink-0"
                      >
                        {copied ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <Copy className="h-4 w-4 text-muted-foreground" />
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Payment URL */}
                {depositInfo.paymentUrl && (
                  <Button
                    className="w-full h-12 bg-gold-500 hover:bg-gold-600 text-black"
                    onClick={() => window.open(depositInfo.paymentUrl, '_blank')}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open Payment Page
                  </Button>
                )}

                {/* Warning */}
                <div className="flex items-start gap-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg text-sm">
                  <AlertCircle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-amber-500">Important</p>
                    <p className="text-muted-foreground mt-1">
                      Send only {depositInfo.currency.toUpperCase()} to this address. 
                      Sending other cryptocurrencies may result in permanent loss.
                    </p>
                  </div>
                </div>

                {/* Back Button */}
                <Button
                  variant="outline"
                  className="w-full min-h-[44px]"
                  onClick={() => setDepositInfo(null)}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Create New Deposit
                </Button>
              </CardContent>
            </Card>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4 sm:px-6 max-w-lg">
          {/* Back Button */}
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 min-h-[44px]"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </button>

          <Card className="glass-card border-gold-500/10">
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="h-10 w-10 rounded-lg bg-gold-500/10 flex items-center justify-center">
                  <Wallet className="h-5 w-5 text-gold-400" />
                </div>
                <div>
                  <CardTitle>Deposit Funds</CardTitle>
                  <CardDescription>Add crypto to your wallet</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleDeposit} className="space-y-6">
                {/* Amount Input */}
                <div className="space-y-3">
                  <Label htmlFor="amount">Amount (USD)</Label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                    <Input
                      id="amount"
                      type="number"
                      placeholder="0.00"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="pl-8 h-12 text-lg font-mono"
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
                          'flex-1 py-2 text-sm rounded-lg transition-colors',
                          amount === preset.toString()
                            ? 'bg-gold-500 text-black'
                            : 'bg-muted hover:bg-muted/80'
                        )}
                      >
                        ${preset}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Currency Select */}
                <div className="space-y-2">
                  <Label>Pay With</Label>
                  <Select value={currency} onValueChange={setCurrency}>
                    <SelectTrigger className="h-12" data-testid="deposit-currency-select">
                      <SelectValue placeholder="Select cryptocurrency" />
                    </SelectTrigger>
                    <SelectContent>
                      {CRYPTO_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{option.icon}</span>
                            <span>{option.label}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Security Info */}
                <div className="flex items-start gap-3 p-4 bg-muted/50 rounded-lg text-sm">
                  <Shield className="h-5 w-5 text-gold-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Secure Payment</p>
                    <p className="text-muted-foreground mt-1">
                      All deposits are processed through secure payment gateways with instant confirmation.
                    </p>
                  </div>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full h-12 bg-gold-500 hover:bg-gold-600 text-black font-semibold"
                  disabled={isLoading || !amount}
                  data-testid="deposit-submit-button"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Wallet className="h-4 w-4 mr-2" />
                      Continue to Payment
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default WalletDeposit;
