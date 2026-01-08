import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { TrendingUp, BarChart3, Settings } from "lucide-react";

const Trade = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
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
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Select cryptocurrency pair" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="btcusdt">BTC/USDT</SelectItem>
                          <SelectItem value="ethusdt">ETH/USDT</SelectItem>
                          <SelectItem value="solusdt">SOL/USDT</SelectItem>
                          <SelectItem value="xrpusdt">XRP/USDT</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Order Type */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Order Type</label>
                        <Select>
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
                          <Button variant="outline" className="flex-1 text-success border-success/50">
                            Buy
                          </Button>
                          <Button variant="outline" className="flex-1 text-destructive border-destructive/50">
                            Sell
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Amount */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Amount</label>
                        <Input placeholder="0.00" type="number" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Price</label>
                        <Input placeholder="0.00" type="number" />
                      </div>
                    </div>

                    {/* Total */}
                    <div className="p-4 bg-secondary/50 rounded-lg border border-border/50">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Total</span>
                        <span className="font-display font-bold text-lg">0.00 USDT</span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4">
                      <Button variant="hero" size="lg" className="flex-1">
                        Place Order
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
                    <span className="font-medium">$10,000.00</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">In Orders</span>
                    <span className="font-medium">$0.00</span>
                  </div>
                  <div className="h-px bg-border/50 my-2" />
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Total</span>
                    <span className="font-display font-bold">$10,000.00</span>
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
