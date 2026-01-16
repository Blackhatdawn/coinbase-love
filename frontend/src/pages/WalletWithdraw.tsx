import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/apiClient";
import { toast } from "sonner";
import { ArrowLeft, AlertTriangle, CheckCircle2, Clock, Wallet, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

interface WithdrawalHistory {
  id: string;
  amount: number;
  currency: string;
  address: string;
  status: string;
  fee: number;
  totalAmount: number;
  transactionHash?: string;
  createdAt: string;
  processedAt?: string;
  completedAt?: string;
}

interface WalletBalance {
  balances: Record<string, number>;
  updated_at: string;
}

const WalletWithdraw = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [address, setAddress] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [withdrawalHistory, setWithdrawalHistory] = useState<WithdrawalHistory[]>([]);
  const [wallet, setWallet] = useState<WalletBalance | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  
  // Fee calculation
  const withdrawalFee = amount ? Math.max(parseFloat(amount) * 0.01, 1) : 0;
  const totalAmount = amount ? parseFloat(amount) + withdrawalFee : 0;
  const availableBalance = wallet?.balances[currency] || 0;

  useEffect(() => {
    if (!user) {
      navigate("/auth");
      return;
    }
    
    fetchWallet();
    fetchWithdrawalHistory();
  }, [user, navigate]);

  const fetchWallet = async () => {
    try {
      const response = await api.wallet.getBalance();
      setWallet(response.wallet);
    } catch (error: any) {
      toast.error(error.message || "Failed to load wallet");
    }
  };

  const fetchWithdrawalHistory = async () => {
    try {
      setIsLoadingHistory(true);
      const response = await api.wallet.getWithdrawals();
      setWithdrawalHistory(response.withdrawals || []);
    } catch (error: any) {
      console.error("Failed to load withdrawal history:", error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleWithdrawal = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!amount || parseFloat(amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }
    
    if (parseFloat(amount) < 10) {
      toast.error("Minimum withdrawal is $10");
      return;
    }
    
    if (parseFloat(amount) > 10000) {
      toast.error("Maximum withdrawal is $10,000 per transaction");
      return;
    }
    
    if (!address || address.trim().length < 10) {
      toast.error("Please enter a valid withdrawal address");
      return;
    }
    
    if (totalAmount > availableBalance) {
      toast.error(`Insufficient balance. Available: ${availableBalance.toFixed(2)} ${currency}`);
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await api.wallet.withdraw({
        amount: parseFloat(amount),
        currency,
        address: address.trim()
      });

      toast.success(response.message || "Withdrawal request submitted successfully");
      
      // Reset form
      setAmount("");
      setAddress("");
      
      // Refresh data
      await Promise.all([fetchWallet(), fetchWithdrawalHistory()]);
      
    } catch (error: any) {
      toast.error(error.message || "Failed to submit withdrawal request");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
      case "processing":
        return <Clock className="h-5 w-5 text-cyan-500 animate-pulse" />;
      case "pending":
        return <Clock className="h-5 w-5 text-gold-400" />;
      case "cancelled":
      case "failed":
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-emerald-500";
      case "processing":
        return "text-cyan-500";
      case "pending":
        return "text-gold-400";
      case "cancelled":
      case "failed":
        return "text-red-500";
      default:
        return "text-muted-foreground";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/dashboard")}
              className="min-h-[44px]"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold mb-2">Withdraw Funds</h1>
          <p className="text-muted-foreground">
            Withdraw your funds to an external wallet or bank account
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Withdrawal Form */}
          <div className="lg:col-span-2">
            <Card className="glass-card border-gold-500/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wallet className="h-5 w-5 text-gold-400" />
                  New Withdrawal
                </CardTitle>
                <CardDescription>
                  Submit a withdrawal request. Processing time: 1-3 business days
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleWithdrawal} className="space-y-6">
                  {/* Currency Selection */}
                  <div className="space-y-2">
                    <Label htmlFor="currency">Currency</Label>
                    <Select value={currency} onValueChange={setCurrency}>
                      <SelectTrigger id="currency" className="h-12">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="BTC">BTC</SelectItem>
                        <SelectItem value="ETH">ETH</SelectItem>
                        <SelectItem value="USDT">USDT</SelectItem>
                        <SelectItem value="USDC">USDC</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-sm text-muted-foreground">
                      Available: {availableBalance.toFixed(2)} {currency}
                    </p>
                  </div>

                  {/* Amount Input */}
                  <div className="space-y-2">
                    <Label htmlFor="amount">Amount</Label>
                    <Input
                      id="amount"
                      type="number"
                      step="0.01"
                      min="10"
                      max="10000"
                      placeholder="Enter amount"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="h-12 text-lg"
                      required
                    />
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>Minimum: $10</span>
                      <span>Maximum: $10,000</span>
                    </div>
                  </div>

                  {/* Address Input */}
                  <div className="space-y-2">
                    <Label htmlFor="address">Withdrawal Address</Label>
                    <Input
                      id="address"
                      type="text"
                      placeholder={currency === "USD" ? "Bank account or routing number" : "Wallet address"}
                      value={address}
                      onChange={(e) => setAddress(e.target.value)}
                      className="h-12 font-mono text-sm"
                      required
                    />
                    <p className="text-sm text-muted-foreground">
                      Double-check the address. Withdrawals cannot be reversed.
                    </p>
                  </div>

                  {/* Fee Summary */}
                  {amount && parseFloat(amount) > 0 && (
                    <div className="rounded-lg bg-muted/50 p-4 space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Withdrawal Amount:</span>
                        <span className="font-semibold">{parseFloat(amount).toFixed(2)} {currency}</span>
                      </div>
                      <div className="flex justify-between text-sm text-muted-foreground">
                        <span>Network Fee (1%):</span>
                        <span>{withdrawalFee.toFixed(2)} {currency}</span>
                      </div>
                      <div className="border-t border-border/50 pt-2 flex justify-between font-semibold">
                        <span>Total Deduction:</span>
                        <span className={cn(
                          "text-lg",
                          totalAmount > availableBalance ? "text-red-500" : "text-gold-400"
                        )}>
                          {totalAmount.toFixed(2)} {currency}
                        </span>
                      </div>
                      {totalAmount > availableBalance && (
                        <div className="flex items-center gap-2 text-sm text-red-500 pt-2">
                          <AlertTriangle className="h-4 w-4" />
                          <span>Insufficient balance</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Security Notice */}
                  <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 p-4">
                    <div className="flex items-start gap-3">
                      <Shield className="h-5 w-5 text-cyan-400 mt-0.5 flex-shrink-0" />
                      <div className="text-sm">
                        <p className="font-semibold text-cyan-400 mb-1">Security Notice</p>
                        <ul className="space-y-1 text-cyan-300/80">
                          <li>• Withdrawals are reviewed for security</li>
                          <li>• You will receive email confirmation</li>
                          <li>• Processing takes 1-3 business days</li>
                          <li>• Contact support for urgent requests</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    className="w-full h-12 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold text-lg"
                    disabled={isSubmitting || !amount || !address || totalAmount > availableBalance}
                  >
                    {isSubmitting ? "Processing..." : "Submit Withdrawal Request"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Withdrawal History */}
          <div>
            <Card className="glass-card border-gold-500/10">
              <CardHeader>
                <CardTitle className="text-lg">Recent Withdrawals</CardTitle>
                <CardDescription>Your withdrawal history</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingHistory ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="animate-pulse space-y-2">
                        <div className="h-4 bg-gold-500/10 rounded w-3/4" />
                        <div className="h-3 bg-gold-500/10 rounded w-1/2" />
                      </div>
                    ))}
                  </div>
                ) : withdrawalHistory.length > 0 ? (
                  <div className="space-y-3">
                    {withdrawalHistory.slice(0, 5).map((withdrawal) => (
                      <div
                        key={withdrawal.id}
                        className="p-3 rounded-lg border border-border/50 hover:bg-gold-500/5 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(withdrawal.status)}
                            <span className={cn("font-semibold text-sm", getStatusColor(withdrawal.status))}>
                              {withdrawal.status.charAt(0).toUpperCase() + withdrawal.status.slice(1)}
                            </span>
                          </div>
                          <span className="font-semibold text-sm">
                            {withdrawal.amount} {withdrawal.currency}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground font-mono truncate">
                          {withdrawal.address}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(withdrawal.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Wallet className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p className="text-sm">No withdrawals yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default WalletWithdraw;
