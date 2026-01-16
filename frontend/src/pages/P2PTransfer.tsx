import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import { ArrowLeft, Send, ArrowDownLeft, ArrowUpRight, Users, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface Transfer {
  id: string;
  amount: number;
  currency: string;
  direction: "sent" | "received";
  otherParty: {
    email: string;
    name: string;
  };
  note?: string;
  status: string;
  createdAt: string;
  completedAt?: string;
}

interface WalletBalance {
  balances: Record<string, number>;
}

const P2PTransfer = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [recipientEmail, setRecipientEmail] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [note, setNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [wallet, setWallet] = useState<WalletBalance | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  
  const availableBalance = wallet?.balances[currency] || 0;

  useEffect(() => {
    if (!user) {
      navigate("/auth");
      return;
    }
    
    fetchWallet();
    fetchTransferHistory();
  }, [user, navigate]);

  const fetchWallet = async () => {
    try {
      const response = await api.wallet.getBalance();
      setWallet(response.wallet);
    } catch (error: any) {
      toast.error(error.message || "Failed to load wallet");
    }
  };

  const fetchTransferHistory = async () => {
    try {
      setIsLoadingHistory(true);
      const response = await api.wallet.getTransfers();
      setTransfers(response.transfers || []);
    } catch (error: any) {
      console.error("Failed to load transfer history:", error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!recipientEmail || !recipientEmail.includes("@")) {
      toast.error("Please enter a valid email address");
      return;
    }
    
    if (!amount || parseFloat(amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }
    
    if (parseFloat(amount) < 1) {
      toast.error("Minimum transfer is $1");
      return;
    }
    
    if (parseFloat(amount) > 50000) {
      toast.error("Maximum transfer is $50,000 per transaction");
      return;
    }
    
    if (parseFloat(amount) > availableBalance) {
      toast.error(`Insufficient balance. Available: ${availableBalance.toFixed(2)} ${currency}`);
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await api.wallet.transfer({
        recipient_email: recipientEmail.toLowerCase().trim(),
        amount: parseFloat(amount),
        currency,
        note: note.trim() || undefined
      });

      toast.success(response.message || "Transfer completed successfully");
      
      // Reset form
      setRecipientEmail("");
      setAmount("");
      setNote("");
      
      // Refresh data
      await Promise.all([fetchWallet(), fetchTransferHistory()]);
      
    } catch (error: any) {
      toast.error(error.message || "Failed to complete transfer");
    } finally {
      setIsSubmitting(false);
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
          <h1 className="font-display text-3xl font-bold mb-2 flex items-center gap-3">
            <Users className="h-8 w-8 text-gold-400" />
            P2P Transfer
          </h1>
          <p className="text-muted-foreground">
            Send funds instantly to other CryptoVault users - free and instant
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Transfer Form */}
          <div className="lg:col-span-2">
            <Card className="glass-card border-gold-500/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Send className="h-5 w-5 text-gold-400" />
                  Send Money
                </CardTitle>
                <CardDescription>
                  Transfer funds instantly to another user's account
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleTransfer} className="space-y-6">
                  {/* Recipient Email */}
                  <div className="space-y-2">
                    <Label htmlFor="recipientEmail">Recipient Email</Label>
                    <Input
                      id="recipientEmail"
                      type="email"
                      placeholder="recipient@example.com"
                      value={recipientEmail}
                      onChange={(e) => setRecipientEmail(e.target.value)}
                      className="h-12"
                      required
                    />
                    <p className="text-sm text-muted-foreground">
                      The recipient must have a verified CryptoVault account
                    </p>
                  </div>

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
                      min="1"
                      max="50000"
                      placeholder="Enter amount"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="h-12 text-lg"
                      required
                    />
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>Minimum: $1</span>
                      <span>Maximum: $50,000</span>
                    </div>
                  </div>

                  {/* Note */}
                  <div className="space-y-2">
                    <Label htmlFor="note">Note (Optional)</Label>
                    <Textarea
                      id="note"
                      placeholder="Add a note for the recipient..."
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      className="min-h-[80px] resize-none"
                      maxLength={200}
                    />
                    <p className="text-sm text-muted-foreground text-right">
                      {note.length}/200 characters
                    </p>
                  </div>

                  {/* Transfer Summary */}
                  {amount && parseFloat(amount) > 0 && (
                    <div className="rounded-lg bg-gradient-to-r from-gold-500/10 to-gold-600/10 border border-gold-500/30 p-4 space-y-2">
                      <div className="flex items-center gap-2 mb-3">
                        <Zap className="h-5 w-5 text-gold-400" />
                        <span className="font-semibold text-gold-400">Transfer Summary</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Transfer Amount:</span>
                        <span className="font-semibold">{parseFloat(amount).toFixed(2)} {currency}</span>
                      </div>
                      <div className="flex justify-between text-sm text-emerald-500">
                        <span>Transfer Fee:</span>
                        <span className="font-semibold">FREE</span>
                      </div>
                      <div className="border-t border-gold-500/30 pt-2 flex justify-between font-semibold">
                        <span>Total Amount:</span>
                        <span className={cn(
                          "text-lg",
                          parseFloat(amount) > availableBalance ? "text-red-500" : "text-gold-400"
                        )}>
                          {parseFloat(amount).toFixed(2)} {currency}
                        </span>
                      </div>
                      {parseFloat(amount) > availableBalance && (
                        <div className="text-sm text-red-500 pt-2">
                          ⚠️ Insufficient balance
                        </div>
                      )}
                    </div>
                  )}

                  {/* Benefits */}
                  <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 p-4">
                    <div className="grid sm:grid-cols-3 gap-4 text-sm text-cyan-300">
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4 text-cyan-400" />
                        <span>Instant</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4 text-cyan-400" />
                        <span>Free</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4 text-cyan-400" />
                        <span>Secure</span>
                      </div>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    className="w-full h-12 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold text-lg"
                    disabled={isSubmitting || !amount || !recipientEmail || parseFloat(amount) > availableBalance}
                  >
                    {isSubmitting ? "Processing..." : "Send Transfer"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Transfer History */}
          <div>
            <Card className="glass-card border-gold-500/10">
              <CardHeader>
                <CardTitle className="text-lg">Transfer History</CardTitle>
                <CardDescription>Recent sent & received transfers</CardDescription>
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
                ) : transfers.length > 0 ? (
                  <div className="space-y-3">
                    {transfers.slice(0, 8).map((transfer) => (
                      <div
                        key={transfer.id}
                        className="p-3 rounded-lg border border-border/50 hover:bg-gold-500/5 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            {transfer.direction === "sent" ? (
                              <ArrowUpRight className="h-4 w-4 text-red-400" />
                            ) : (
                              <ArrowDownLeft className="h-4 w-4 text-emerald-400" />
                            )}
                            <div className="min-w-0">
                              <p className="text-sm font-medium truncate">
                                {transfer.otherParty.name}
                              </p>
                              <p className="text-xs text-muted-foreground truncate">
                                {transfer.otherParty.email}
                              </p>
                            </div>
                          </div>
                          <span className={cn(
                            "font-semibold text-sm whitespace-nowrap",
                            transfer.direction === "sent" ? "text-red-400" : "text-emerald-400"
                          )}>
                            {transfer.direction === "sent" ? "-" : "+"}
                            {transfer.amount} {transfer.currency}
                          </span>
                        </div>
                        {transfer.note && (
                          <p className="text-xs text-muted-foreground italic mb-1">
                            "{transfer.note}"
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground">
                          {new Date(transfer.createdAt).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Send className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p className="text-sm">No transfers yet</p>
                    <p className="text-xs mt-1">Start sending money to other users</p>
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

export default P2PTransfer;
