import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, BarChart3 } from "lucide-react";
import { api } from "@/lib/apiClient";
import { useAuth } from "@/contexts/AuthContext";
import AdvancedOrderForm from "@/components/AdvancedOrderForm";
import OrderManagement from "@/components/OrderManagement";

const AdvancedTradingPage = () => {
  const { user } = useAuth();
  const [tradingPair, setTradingPair] = useState("");

  // Fetch account balance
  const { data: balanceData } = useQuery({
    queryKey: ["balance"],
    queryFn: () => api.wallet.balance(),
    enabled: !!user,
  });
  const accountBalance = balanceData?.wallet?.balances?.USD || 0;

  // Fetch available trading pairs
  const { data: pairsData } = useQuery({
    queryKey: ["tradingPairs"],
    queryFn: () => api.crypto.getTradingPairs(),
  });
  const tradingPairs = pairsData?.pairs || [];

  // Fetch current price for selected pair
  const { data: priceData } = useQuery({
    queryKey: ["price", tradingPair],
    queryFn: () => {
      if (!tradingPair) return null;
      const symbol = tradingPair.split('/')[0].toLowerCase();
      return api.prices.getCurrentPrice(symbol);
    },
    enabled: !!tradingPair,
  });
  const currentPrice = priceData?.price || 0;

  return (
    <div className="min-h-screen">
      <main>
          {/* Header */}
          <div className="mb-12 animate-fade-in">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-3">
              Professional <span className="text-gradient">Trading</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Advanced order types including stop-loss, take-profit, and full order management.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Trading Panel */}
            <div className="lg:col-span-2 space-y-6">
              {/* Pair Selection */}
              <Card className="p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <label className="block text-sm font-medium mb-2">Select Trading Pair</label>
                <Select value={tradingPair} onValueChange={setTradingPair}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose cryptocurrency pair" />
                  </SelectTrigger>
                  <SelectContent>
                    {tradingPairs.map((pair: string) => (
                      <SelectItem key={pair} value={pair}>{pair}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {tradingPair && currentPrice > 0 && (
                  <div className="mt-4 p-4 bg-secondary/50 rounded-lg border border-border/50">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Current Price</span>
                      <span className="font-display font-bold text-xl">${currentPrice.toFixed(2)}</span>
                    </div>
                  </div>
                )}
              </Card>

              {/* Order Tabs */}
              <Tabs defaultValue="advanced" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="advanced">🆕 Advanced Orders</TabsTrigger>
                  <TabsTrigger value="management">Order Management</TabsTrigger>
                </TabsList>

                <TabsContent value="advanced" className="mt-6">
                  <AdvancedOrderForm
                    tradingPair={tradingPair}
                    currentPrice={currentPrice}
                  />
                </TabsContent>

                <TabsContent value="management" className="mt-6">
                  <OrderManagement />
                </TabsContent>
              </Tabs>
            </div>

            {/* Sidebar */}
            <div className="space-y-4">
              {/* Trading Features */}
              <Card className="p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <h3 className="font-display font-bold mb-4">New Features ✨</h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <TrendingUp className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">Advanced Orders</p>
                      <p className="text-xs text-muted-foreground">Stop-loss, take-profit, stop-limit</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <BarChart3 className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">Order Management</p>
                      <p className="text-xs text-muted-foreground">Cancel pending orders instantly</p>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Account Balance */}
              <Card className="p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <h3 className="font-display font-bold mb-4">Account Balance</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Available USD</span>
                    <span className="font-medium">${accountBalance.toLocaleString()}</span>
                  </div>
                  <div className="h-px bg-border/50 my-2" />
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Total</span>
                    <span className="font-display font-bold">${accountBalance.toLocaleString()}</span>
                  </div>
                </div>
              </Card>

              {/* Risk Management Info */}
              <Card className="p-6 border-border/50 bg-amber-500/5 border-amber-500/20">
                <h3 className="font-display font-bold mb-3 text-amber-200">Risk Management</h3>
                <div className="text-xs text-amber-200/80 space-y-2">
                  <p>• Stop-loss protects against downside risk</p>
                  <p>• Take-profit locks in gains automatically</p>
                  <p>• Always use risk management tools</p>
                  <p>• Never risk more than you can afford to lose</p>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdvancedTradingPage;
