import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import {
  TrendingUp,
  TrendingDown,
  PieChart,
  Activity,
  Settings,
  User,
  Shield,
  Bell,
  Wallet,
  LogOut,
  History,
  Menu,
  X,
  Home,
  LineChart,
  RefreshCw
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import { usePriceWebSocket } from "@/hooks/usePriceWebSocket";
import { PriceStreamStatus } from "@/components/PriceStreamStatus";

interface Holding {
  symbol: string;
  name: string;
  amount: number;
  value: number;
  allocation: number;
  change?: number;
}

const Dashboard = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const user = auth?.user;
  const signOut = auth?.signOut ?? (() => {});
  const { prices, status } = usePriceWebSocket();

  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [totalValue, setTotalValue] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [originalTotalValue, setOriginalTotalValue] = useState(0);

  const fetchPortfolio = async (isBackground = false) => {
    try {
      if (!isBackground) {
        setIsLoading(true);
        setError(null);
      } else {
        setIsRefreshing(true);
      }
      const response = await api.portfolio.get();
      const portfolio = response.portfolio;

      setTotalValue(portfolio.totalBalance);
      setOriginalTotalValue(portfolio.totalBalance);
      setHoldings(portfolio.holdings || []);
    } catch (error: any) {
      console.error("Failed to fetch portfolio:", error);
      const errorMessage = error?.message || 'Failed to load portfolio data';
      setError(errorMessage);
      setTotalValue(0);
      setOriginalTotalValue(0);
      setHoldings([]);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchPortfolio();
    }
  }, [user]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => fetchPortfolio(true), 30000);
    return () => clearInterval(interval);
  }, [user]);

  // Update portfolio value in real-time based on WebSocket prices
  useEffect(() => {
    if (holdings.length === 0 || Object.keys(prices).length === 0) return;

    const updatedValue = holdings.reduce((sum, holding) => {
      const wsPrice = prices[holding.symbol.toLowerCase()];
      if (wsPrice) {
        return sum + (parseFloat(wsPrice) * holding.amount);
      }
      return sum + holding.value;
    }, 0);

    setTotalValue(updatedValue);
  }, [prices, holdings]);

  const handleSignOut = () => {
    signOut();
    navigate("/");
  };

  // Calculate total change based on original value
  const portfolioChange = originalTotalValue > 0
    ? ((totalValue - originalTotalValue) / originalTotalValue) * 100
    : 0;

  // Calculate total change using holding allocation
  const totalChange = holdings.reduce((acc, h) => acc + (h.change || 0) * (h.allocation / 100), 0);

  return (
    <div className="min-h-screen bg-background">
      {/* Dashboard Header */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 sm:gap-3">
              <img 
                src="/logo.svg" 
                alt="CryptoVault" 
                className="h-9 w-9 sm:h-10 sm:w-10 object-contain"
              />
              <span className="font-display text-lg sm:text-xl font-bold">
                Crypto<span className="text-gold-400">Vault</span>
              </span>
            </Link>
            
            {/* Desktop Actions */}
            <div className="hidden sm:flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                Welcome, {user?.name}
              </span>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleSignOut}
                className="min-h-[44px]"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>

            {/* Mobile Menu Toggle */}
            <button
              className="sm:hidden p-2 text-muted-foreground hover:text-foreground min-h-[44px] min-w-[44px] flex items-center justify-center"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="sm:hidden border-t border-border/50 bg-background/95 backdrop-blur-xl">
            <div className="container mx-auto px-4 py-4 space-y-2">
              <div className="text-sm text-muted-foreground mb-4">
                Welcome, {user?.name}
              </div>
              <Link 
                to="/" 
                className="flex items-center gap-3 p-3 hover:bg-gold-500/10 rounded-lg min-h-[48px]"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Home className="h-5 w-5" />
                Home
              </Link>
              <Link 
                to="/markets" 
                className="flex items-center gap-3 p-3 hover:bg-gold-500/10 rounded-lg min-h-[48px]"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <LineChart className="h-5 w-5" />
                Markets
              </Link>
              <Link 
                to="/trade" 
                className="flex items-center gap-3 p-3 hover:bg-gold-500/10 rounded-lg min-h-[48px]"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Activity className="h-5 w-5" />
                Trade
              </Link>
              <button 
                onClick={() => { handleSignOut(); setIsMobileMenuOpen(false); }}
                className="flex items-center gap-3 p-3 hover:bg-red-500/10 text-red-500 rounded-lg w-full min-h-[48px]"
              >
                <LogOut className="h-5 w-5" />
                Sign Out
              </button>
            </div>
          </div>
        )}
      </header>

      <main className="container mx-auto px-4 py-6 sm:py-8">
        {/* Page Title */}
        <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl sm:text-3xl font-bold mb-1 sm:mb-2">Dashboard</h1>
            <p className="text-sm sm:text-base text-muted-foreground">
              Manage your portfolio and account settings
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Price Stream Status */}
            <PriceStreamStatus status={status} />

            {/* Refresh Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchPortfolio(true)}
              disabled={isRefreshing}
              className="min-h-[44px]"
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 sm:p-6 rounded-xl border border-red-500/30 bg-red-500/10">
            <div className="flex items-start gap-3">
              <div className="text-red-500 text-lg">⚠</div>
              <div className="flex-1">
                <p className="font-semibold text-red-400 text-base sm:text-lg">{error}</p>
                <button
                  onClick={() => fetchPortfolio()}
                  className="mt-2 text-red-400 hover:text-red-300 hover:underline text-sm min-h-[44px]"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-4 sm:space-y-6 mb-6">
            {Array.from({ length: 2 }).map((_, i) => (
              <Card key={i} className="glass-card border-gold-500/10">
                <CardHeader>
                  <CardTitle className="h-6 bg-gold-500/10 rounded w-1/3 animate-pulse" />
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="h-10 bg-gold-500/10 rounded animate-pulse" />
                  <div className="h-20 bg-gold-500/10 rounded animate-pulse" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!isLoading && (
        <div className="grid lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Portfolio Section */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            {/* Portfolio Summary Card */}
            <Card className="glass-card border-gold-500/10">
              <CardHeader className="flex flex-row items-center justify-between pb-2 sm:pb-4">
                <div>
                  <CardTitle className="text-base sm:text-lg">Total Balance</CardTitle>
                  <CardDescription className="text-xs sm:text-sm">Your portfolio value</CardDescription>
                </div>
                <PieChart className="h-5 w-5 text-gold-400" />
              </CardHeader>
              <CardContent>
                <div className="mb-4 sm:mb-6">
                  <div className={cn(
                    "font-display text-3xl sm:text-4xl font-bold mb-2 transition-colors duration-300",
                    status.isConnected && totalValue !== originalTotalValue && "text-gold-400"
                  )}>
                    ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                  <div className={cn(
                    "flex items-center gap-2 text-sm",
                    portfolioChange >= 0 ? "text-emerald-500" : "text-red-500"
                  )}>
                    {portfolioChange >= 0 ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <TrendingDown className="h-4 w-4" />
                    )}
                    <span className="font-medium">
                      {portfolioChange >= 0 ? '+' : ''}{portfolioChange.toFixed(2)}% from initial value
                    </span>
                  </div>
                  {status.isConnected && totalValue !== originalTotalValue && (
                    <div className="mt-2 text-xs text-gold-400 flex items-center gap-1">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-gold-400 animate-pulse" />
                      Real-time prices updating
                    </div>
                  )}
                </div>

                {/* Allocation Chart */}
                {holdings.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex gap-1 h-2 sm:h-3 rounded-full overflow-hidden bg-secondary">
                      {holdings.map((h, i) => (
                        <div 
                          key={h.symbol}
                          className="h-full transition-all duration-500"
                          style={{ 
                            width: `${h.allocation}%`,
                            backgroundColor: i === 0 ? '#F59E0B' : 
                                            i === 1 ? '#8B5CF6' : 
                                            i === 2 ? '#10B981' : 
                                            '#6B7280'
                          }}
                        />
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-2 sm:gap-3">
                      {holdings.map((h, i) => (
                        <div key={h.symbol} className="flex items-center gap-1.5 sm:gap-2 text-xs">
                          <div 
                            className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{ 
                              backgroundColor: i === 0 ? '#F59E0B' : 
                                              i === 1 ? '#8B5CF6' : 
                                              i === 2 ? '#10B981' : 
                                              '#6B7280'
                            }}
                          />
                          <span className="text-muted-foreground">{h.symbol} {h.allocation}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3 mt-4 sm:mt-6">
                  <Link to="/wallet/deposit" className="flex-1">
                    <Button className="w-full h-11 sm:h-12 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold">
                      Deposit
                    </Button>
                  </Link>
                  <Link to="/wallet/withdraw" className="flex-1">
                    <Button variant="outline" className="w-full h-11 sm:h-12 border-gold-500/30 hover:bg-gold-500/10">
                      Withdraw
                    </Button>
                  </Link>
                </div>
                <Link to="/wallet/transfer" className="block mt-3">
                  <Button variant="ghost" className="w-full h-11 hover:bg-purple-500/10 text-purple-400">
                    <Users className="h-4 w-4 mr-2" />
                    Send to User (P2P)
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Holdings List */}
            <Card className="glass-card border-gold-500/10 overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between border-b border-border/50 py-3 sm:py-4">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-gold-400" />
                  <CardTitle className="text-base sm:text-lg">Your Holdings</CardTitle>
                </div>
                <Link to="/transactions">
                  <Button variant="ghost" size="sm" className="min-h-[44px]">
                    <History className="h-4 w-4 mr-1" />
                    <span className="hidden sm:inline">History</span>
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="p-0">
                {isLoading ? (
                  <div className="p-4 sm:p-6 space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex items-center gap-4 animate-pulse">
                        <div className="w-10 h-10 rounded-full bg-gold-500/10" />
                        <div className="flex-1 space-y-2">
                          <div className="h-4 w-20 bg-gold-500/10 rounded" />
                          <div className="h-3 w-16 bg-gold-500/10 rounded" />
                        </div>
                        <div className="text-right space-y-2">
                          <div className="h-4 w-16 bg-gold-500/10 rounded ml-auto" />
                          <div className="h-3 w-12 bg-gold-500/10 rounded ml-auto" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : holdings.length > 0 ? (
                  <div className="divide-y divide-border/50">
                    {holdings.map((holding) => {
                      const wsPrice = prices[holding.symbol.toLowerCase()];
                      const currentValue = wsPrice ? parseFloat(wsPrice) * holding.amount : holding.value;
                      return (
                        <div
                          key={holding.symbol}
                          className={cn(
                            "p-4 hover:bg-gold-500/5 transition-colors",
                            wsPrice && "bg-gold-500/5"
                          )}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div className="flex items-center gap-3 sm:gap-4 min-w-0">
                              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gold-500/20 flex items-center justify-center font-bold text-gold-400 flex-shrink-0">
                                {holding.symbol.charAt(0)}
                              </div>
                              <div className="min-w-0">
                                <div className="font-semibold text-sm sm:text-base truncate">{holding.symbol}</div>
                                <div className="text-xs sm:text-sm text-muted-foreground">
                                  {holding.amount.toFixed(4)} {holding.symbol}
                                </div>
                              </div>
                            </div>
                            <div className="text-right flex-shrink-0">
                              <div className={cn(
                                "font-semibold text-sm sm:text-base transition-colors duration-300",
                                wsPrice && "text-gold-400"
                              )}>
                                ${currentValue.toLocaleString()}
                              </div>
                              {holding.change !== undefined && (
                                <div className={cn(
                                  "text-xs sm:text-sm font-medium",
                                  holding.change >= 0 ? "text-emerald-500" : "text-red-500"
                                )}>
                                  {holding.change >= 0 ? '+' : ''}{holding.change}%
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-6 sm:p-8 text-center text-muted-foreground">
                    <Wallet className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-sm sm:text-base">No holdings yet.</p>
                    <Link to="/trade">
                      <Button variant="link" className="mt-2 text-gold-400">
                        Start trading →
                      </Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Settings Sidebar */}
          <div className="space-y-4 sm:space-y-6">
            {/* Account Info Card */}
            <Card className="glass-card border-gold-500/10">
              <CardHeader className="pb-2 sm:pb-4">
                <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                  <User className="h-5 w-5 text-gold-400" />
                  Account
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 sm:space-y-4">
                <div>
                  <label className="text-xs text-muted-foreground uppercase tracking-wide">Name</label>
                  <p className="font-medium text-sm sm:text-base truncate">{user?.name}</p>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground uppercase tracking-wide">Email</label>
                  <p className="font-medium text-sm sm:text-base truncate">{user?.email}</p>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground uppercase tracking-wide">Member Since</label>
                  <p className="font-medium text-sm sm:text-base">
                    {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Quick Settings */}
            <Card className="glass-card border-gold-500/10">
              <CardHeader className="pb-2 sm:pb-4">
                <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                  <Settings className="h-5 w-5 text-gold-400" />
                  Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 sm:space-y-2">
                <Button 
                  variant="ghost" 
                  className="w-full justify-start min-h-[48px]" 
                  size="sm"
                >
                  <Shield className="h-4 w-4 mr-3" />
                  Security
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start min-h-[48px]" 
                  size="sm"
                >
                  <Bell className="h-4 w-4 mr-3" />
                  Notifications
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start min-h-[48px]" 
                  size="sm"
                >
                  <User className="h-4 w-4 mr-3" />
                  Edit Profile
                </Button>
              </CardContent>
            </Card>

            {/* Quick Actions - Mobile Only */}
            <Card className="glass-card border-gold-500/10 lg:hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-5 w-5 text-gold-400" />
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-2">
                <Link to="/trade">
                  <Button 
                    variant="outline" 
                    className="w-full h-12 border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10"
                  >
                    Trade
                  </Button>
                </Link>
                <Link to="/markets">
                  <Button 
                    variant="outline" 
                    className="w-full h-12 border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10"
                  >
                    Markets
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
