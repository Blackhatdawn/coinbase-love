import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { TrendingUp, BarChart3, Settings } from "lucide-react";
import { api } from "@/lib/apiClient";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";

const Trade = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [tradingPair, setTradingPair] = useState("");
  const [orderType, setOrderType] = useState("market");
  const [side, setSide] = useState("buy");
  const [amount, setAmount] = useState("");
  const [price, setPrice] = useState("");

  // Fetch account balance
  const { data: balanceData } = useQuery({
    queryKey: ["balance"],
    queryFn: () => api.wallet.balance(),
    enabled: !!user,
  });
  const accountBalance = balanceData?.balances?.USD || 0;

  // Fetch available trading pairs
  const { data: pairsData } = useQuery({
    queryKey: ["tradingPairs"],
    queryFn: () => api.crypto.getTradingPairs(),
  });
  const tradingPairs = pairsData?.pairs || [];

  const total = amount && price ? (parseFloat(amount) * parseFloat(price)).toFixed(2) : "0.00";

  const placeOrderMutation = useMutation({
    mutationFn: api.orders.create,
    onSuccess: () => {
      toast({
        title: "Order placed successfully",
        description: `${side.toUpperCase()} ${amount} ${tradingPair} at ${price}`,
      });
      // Invalidate queries to refetch data
      queryClient.invalidateQueries({ queryKey: ["balance"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      // Reset form
      setTradingPair("");
      setAmount("");
      setPrice("");
    },
    onError: (error: any) => {
      toast({
        title: "Failed to place order",
        description: error.message || "Something went wrong",
        variant: "destructive",
      });
    },
  });

  const handlePlaceOrder = () => {
    if (!user) {
      toast({
        title: "Not authenticated",
        description: "Please sign in to place orders",
        variant: "destructive",
      });
      return;
    }

    if (!tradingPair || !amount || !price) {
      toast({
        title: "Missing fields",
        description: "Please fill in all order details",
        variant: "destructive",
      });
      return;
    }

    placeOrderMutation.mutate({
      trading_pair: tradingPair,
      order_type: orderType,
      side: side,
      amount: parseFloat(amount),
      price: parseFloat(price)
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="mb-12 animate-fade-in">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-3">
              Advanced <span className="text-gradient">Trading</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Trade cryptocurrencies with powerful tools, real-time analytics, and institutional-grade features.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Trading Panel */}
            <div className="lg:col-span-2">
              <Card className="p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <div className="mb-6">
                  <h2 className="font-display text-xl font-bold mb-4">Create Order</h2>

                  <div className="space-y-4">
                    {/* Pair Selection */}
                    <div>
                      <label className="block text-sm font-medium mb-2">Trading Pair</label>
                      <Select value={tradingPair} onValueChange={setTradingPair}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select cryptocurrency pair" />
                        </SelectTrigger>
                        <SelectContent>
                          {tradingPairs.map((pair: string) => (
                            <SelectItem key={pair} value={pair}>{pair}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Order Type */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Order Type</label>
                        <Select value={orderType} onValueChange={setOrderType}>
                          <SelectTrigger>
                            <SelectValue placeholder="Market" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="market">Market</SelectItem>
                            <SelectItem value="limit">Limit</SelectItem>
                            <SelectItem value="stop">Stop Loss</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Side</label>
                        <div className="flex gap-2">
                          <Button
                            variant={side === "buy" ? "default" : "outline"}
                            className="flex-1"
                            onClick={() => setSide("buy")}
                          >
                            Buy
                          </Button>
                          <Button
                            variant={side === "sell" ? "default" : "outline"}
                            className="flex-1"
                            onClick={() => setSide("sell")}
                          >
                            Sell
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Amount */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Amount</label>
                        <Input
                          placeholder="0.00"
                          type="number"
                          value={amount}
                          onChange={(e) => setAmount(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Price</label>
                        <Input
                          placeholder="0.00"
                          type="number"
                          value={price}
                          onChange={(e) => setPrice(e.target.value)}
                        />
                      </div>
                    </div>

                    {/* Total */}
                    <div className="p-4 bg-secondary/50 rounded-lg border border-border/50">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Total</span>
                        <span className="font-display font-bold text-lg">{total} USDT</span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4">
                      <Button
                        variant="hero"
                        size="lg"
                        className="flex-1"
                        onClick={handlePlaceOrder}
                        disabled={placeOrderMutation.isPending || !user}
                      >
                        {placeOrderMutation.isPending ? "Placing..." : "Place Order"}
                      </Button>
                      <Button variant="outline" size="lg">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-4">
              {/* Trading Features */}
              <Card className="p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <h3 className="font-display font-bold mb-4">Trading Features</h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <TrendingUp className="h-5 w-5 text-primary mt-1 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-sm">Advanced Charts</p>
                      <p className="text-xs text-muted-foreground">Real-time price analysis</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <BarChart3 className="h-5 w-5 text-primary mt-1 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-sm">Multiple Orders</p>
                      <p className="text-xs text-muted-foreground">Manage multiple positions</p>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Account Balance */}
              <Card className="p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <h3 className="font-display font-bold mb-4">Account Balance</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Available</span>
                    <span className="font-medium">${accountBalance.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">In Orders</span>
                    <span className="font-medium">$0.00</span>
                  </div>
                  <div className="h-px bg-border/50 my-2" />
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Total</span>
                    <span className="font-display font-bold">${accountBalance.toLocaleString()}</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Trade;
