import { Button } from "@/components/ui/button";
import { TrendingUp, ArrowUpRight, PieChart, Activity } from "lucide-react";

const holdings = [
  { symbol: "BTC", name: "Bitcoin", amount: 0.5234, value: 50987.23, allocation: 45, change: 2.34 },
  { symbol: "ETH", name: "Ethereum", amount: 8.234, value: 28456.78, allocation: 25, change: -1.23 },
  { symbol: "SOL", name: "Solana", amount: 120.5, value: 22829.22, allocation: 20, change: 5.67 },
  { symbol: "XRP", name: "Ripple", amount: 4500, value: 10530.00, allocation: 10, change: 3.21 },
];

const PortfolioSection = () => {
  const totalValue = holdings.reduce((acc, h) => acc + h.value, 0);

  return (
    <section className="py-14 sm:py-16 lg:py-20 relative">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
      </div>

      <div className="container mx-auto px-4">
        <div className="text-center mb-8 sm:mb-10">
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-bold mb-3">
            Your <span className="text-gradient">Portfolio</span>
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground max-w-xl mx-auto">
            Track your investments in real-time. Manage your crypto portfolio with powerful analytics and insights.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Portfolio Summary */}
          <div className="lg:col-span-1">
            <div className="glass-card p-4 sm:p-6 h-full">
              <div className="flex items-center justify-between mb-5 sm:mb-6">
                <h3 className="text-sm sm:text-base font-semibold text-muted-foreground">Total Balance</h3>
                <PieChart className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
              </div>
              
              <div className="mb-5 sm:mb-6">
                <div className="font-display text-3xl sm:text-4xl font-bold mb-2">
                  ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className="flex items-center gap-2 text-success">
                  <TrendingUp className="h-4 w-4" />
                  <span className="text-xs sm:text-sm font-medium">+$4,523.45 (4.12%) today</span>
                </div>
              </div>

              {/* Allocation Chart */}
              <div className="space-y-3">
                <div className="flex gap-1 h-3 rounded-full overflow-hidden bg-secondary">
                  {holdings.map((h, i) => (
                    <div 
                      key={h.symbol}
                      className="h-full transition-all duration-500"
                      style={{ 
                        width: `${h.allocation}%`,
                        backgroundColor: i === 0 ? 'hsl(var(--primary))' : 
                                        i === 1 ? 'hsl(var(--accent))' : 
                                        i === 2 ? 'hsl(var(--success))' : 
                                        'hsl(var(--muted-foreground))'
                      }}
                    />
                  ))}
                </div>
                <div className="flex flex-wrap gap-3">
                  {holdings.map((h, i) => (
                    <div key={h.symbol} className="flex items-center gap-2 text-xs">
                      <div 
                        className="w-2 h-2 rounded-full"
                        style={{ 
                          backgroundColor: i === 0 ? 'hsl(var(--primary))' : 
                                          i === 1 ? 'hsl(var(--accent))' : 
                                          i === 2 ? 'hsl(var(--success))' : 
                                          'hsl(var(--muted-foreground))'
                        }}
                      />
                      <span className="text-muted-foreground">{h.symbol} {h.allocation}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <Button variant="gradient" className="w-full mt-5 sm:mt-6">
                Deposit Funds
              </Button>
            </div>
          </div>

          {/* Holdings List */}
          <div className="lg:col-span-2">
            <div className="glass-card overflow-hidden">
              <div className="p-3 sm:p-4 border-b border-border/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
                  <h3 className="text-sm sm:text-base font-semibold">Holdings</h3>
                </div>
                <Button variant="ghost" size="sm">
                  View All
                  <ArrowUpRight className="h-4 w-4" />
                </Button>
              </div>

              <div className="divide-y divide-border/50">
                {holdings.map((holding) => (
                  <div key={holding.symbol} className="p-3 sm:p-4 hover:bg-secondary/50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-secondary flex items-center justify-center font-bold text-primary">
                          {holding.symbol.charAt(0)}
                        </div>
                        <div>
                          <div className="text-sm sm:text-base font-semibold">{holding.symbol}</div>
                          <div className="text-xs sm:text-sm text-muted-foreground">{holding.amount} {holding.symbol}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm sm:text-base font-semibold">${holding.value.toLocaleString()}</div>
                        <div className={`text-xs sm:text-sm ${holding.change >= 0 ? 'text-success' : 'text-destructive'}`}>
                          {holding.change >= 0 ? '+' : ''}{holding.change}%
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PortfolioSection;
