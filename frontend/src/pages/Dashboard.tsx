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
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  ChevronRight,
  Zap,
  Lock,
  CreditCard,
  BarChart3,
  Sparkles,
  Crown,
  Gift,
  ExternalLink
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/lib/apiClient";
import { cn } from "@/lib/utils";

interface Holding {
  symbol: string;
  name: string;
  amount: number;
  value: number;
  allocation: number;
  change?: number;
}

interface WalletBalance {
  balances: Record<string, number>;
  updated_at: string;
}

const Dashboard = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const user = auth?.user;
  const signOut = auth?.signOut ?? (() => {});

  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [totalValue, setTotalValue] = useState(0);
  const [walletBalance, setWalletBalance] = useState<WalletBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchPortfolio = async (isBackground = false) => {
    try {
      if (!isBackground) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }
      
      // Fetch portfolio and wallet balance in parallel
      const [portfolioRes, walletRes] = await Promise.allSettled([
        api.portfolio.get(),
        api.wallet.getBalance()
      ]);

      if (portfolioRes.status === 'fulfilled') {
        const portfolio = portfolioRes.value.portfolio;
        setTotalValue(portfolio.totalBalance);
        setHoldings(portfolio.holdings || []);
      }

      if (walletRes.status === 'fulfilled') {
        setWalletBalance(walletRes.value.wallet);
      }
    } catch (error) {
      console.error("Failed to fetch portfolio:", error);
      setTotalValue(0);
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

  const handleSignOut = () => {
    signOut();
    navigate("/");
  };

  // Calculate total change
  const totalChange = holdings.reduce((acc, h) => acc + (h.change || 0) * (h.allocation / 100), 0);
  const cashBalance = walletBalance?.balances?.USD || 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-gold-950/5">
      {/* Premium Dashboard Header */}
      <header className="border-b border-gold-500/10 bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 sm:gap-3 group">
              <div className="relative">
                <img 
                  src="/logo.svg" 
                  alt="CryptoVault" 
                  className="h-9 w-9 sm:h-10 sm:w-10 object-contain transition-transform group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gold-500/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <span className="font-display text-lg sm:text-xl font-bold">
                Crypto<span className="text-gold-400">Vault</span>
              </span>
            </Link>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              <Link to="/markets">
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                  <LineChart className="h-4 w-4 mr-2" />
                  Markets
                </Button>
              </Link>
              <Link to="/trade">
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                  <Activity className="h-4 w-4 mr-2" />
                  Trade
                </Button>
              </Link>
              <Link to="/alerts">
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                  <Bell className="h-4 w-4 mr-2" />
                  Alerts
                </Button>
              </Link>
            </nav>
            
            {/* Desktop Actions */}
            <div className="hidden sm:flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-500/10 border border-gold-500/20">
                <Crown className="h-4 w-4 text-gold-400" />
                <span className="text-sm font-medium text-gold-400">Premium</span>
              </div>
              <div className="h-8 w-px bg-border/50" />
              <span className="text-sm text-muted-foreground">
                {user?.name}
              </span>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleSignOut}
                className="text-muted-foreground hover:text-red-400"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>

            {/* Mobile Menu Toggle */}
            <button
              className="md:hidden p-2 text-muted-foreground hover:text-foreground min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg hover:bg-gold-500/10 transition-colors"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-gold-500/10 bg-background/95 backdrop-blur-xl">
            <div className="container mx-auto px-4 py-4 space-y-1">
              <div className="flex items-center gap-2 px-3 py-2 mb-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-black font-bold">
                  {user?.name?.charAt(0)}
                </div>
                <div>
                  <div className="font-medium text-sm">{user?.name}</div>
                  <div className="text-xs text-muted-foreground">{user?.email}</div>
                </div>
              </div>
              <Link 
                to="/" 
                className="flex items-center gap-3 p-3 hover:bg-gold-500/10 rounded-xl min-h-[48px] transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Home className="h-5 w-5 text-gold-400" />
                Home
              </Link>
              <Link 
                to="/markets" 
                className="flex items-center gap-3 p-3 hover:bg-gold-500/10 rounded-xl min-h-[48px] transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <LineChart className="h-5 w-5 text-gold-400" />
                Markets
              </Link>
              <Link 
                to="/trade" 
                className="flex items-center gap-3 p-3 hover:bg-gold-500/10 rounded-xl min-h-[48px] transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Activity className="h-5 w-5 text-gold-400" />
                Trade
              </Link>
              <Link 
                to="/alerts" 
                className="flex items-center gap-3 p-3 hover:bg-gold-500/10 rounded-xl min-h-[48px] transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Bell className="h-5 w-5 text-gold-400" />
                Alerts
              </Link>
              <div className="pt-2 border-t border-gold-500/10 mt-2">
                <button 
                  onClick={() => { handleSignOut(); setIsMobileMenuOpen(false); }}
                  className="flex items-center gap-3 p-3 hover:bg-red-500/10 text-red-400 rounded-xl w-full min-h-[48px] transition-colors"
                >
                  <LogOut className="h-5 w-5" />
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        )}
      </header>

      <main className="container mx-auto px-4 py-6 sm:py-8" data-testid="patient-dashboard">
        {/* Page Header with Actions */}
        <div className="mb-6 sm:mb-8 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl font-bold mb-1 sm:mb-2 flex items-center gap-3">
              Dashboard
              <Sparkles className="h-6 w-6 text-gold-400 animate-pulse" />
            </h1>
            <p className="text-sm sm:text-base text-muted-foreground">
              Welcome back! Here's your portfolio overview.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 sm:gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchPortfolio(true)}
              disabled={isRefreshing}
              className="min-h-[44px] border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10"
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
              Refresh
            </Button>
            <Link to="/wallet/deposit">
              <Button 
                size="sm"
                className="min-h-[44px] bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold shadow-lg shadow-gold-500/25"
                data-testid="deposit-btn"
              >
                <Wallet className="h-4 w-4 mr-2" />
                Deposit
              </Button>
            </Link>
          </div>
        </div>

        {/* Premium Stats Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
          {/* Total Portfolio */}
          <Card className="glass-card border-gold-500/20 bg-gradient-to-br from-gold-500/10 to-transparent overflow-hidden relative group hover:border-gold-400/40 transition-all duration-300">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gold-500/10 rounded-full blur-2xl group-hover:bg-gold-500/20 transition-colors" />
            <CardContent className="p-4 sm:p-6 relative">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <PieChart className="h-4 w-4 text-gold-400" />
                <span className="text-xs sm:text-sm font-medium">Total Value</span>
              </div>
              <div className="font-display text-xl sm:text-2xl lg:text-3xl font-bold text-gold-400">
                ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className={cn(
                "flex items-center gap-1 text-xs sm:text-sm mt-1",
                totalChange >= 0 ? "text-emerald-400" : "text-red-400"
              )}>
                {totalChange >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                <span>{totalChange >= 0 ? '+' : ''}{totalChange.toFixed(2)}%</span>
              </div>
            </CardContent>
          </Card>

          {/* Cash Balance */}
          <Card className="glass-card border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 to-transparent overflow-hidden relative group hover:border-emerald-400/40 transition-all duration-300">
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-colors" />
            <CardContent className="p-4 sm:p-6 relative">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <CreditCard className="h-4 w-4 text-emerald-400" />
                <span className="text-xs sm:text-sm font-medium">Cash Balance</span>
              </div>
              <div className="font-display text-xl sm:text-2xl lg:text-3xl font-bold text-emerald-400">
                ${cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="text-xs sm:text-sm text-muted-foreground mt-1">
                Available to trade
              </div>
            </CardContent>
          </Card>

          {/* Assets Count */}
          <Card className="glass-card border-purple-500/20 bg-gradient-to-br from-purple-500/10 to-transparent overflow-hidden relative group hover:border-purple-400/40 transition-all duration-300">
            <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/10 rounded-full blur-2xl group-hover:bg-purple-500/20 transition-colors" />
            <CardContent className="p-4 sm:p-6 relative">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <BarChart3 className="h-4 w-4 text-purple-400" />
                <span className="text-xs sm:text-sm font-medium">Assets</span>
              </div>
              <div className="font-display text-xl sm:text-2xl lg:text-3xl font-bold text-purple-400">
                {holdings.length}
              </div>
              <div className="text-xs sm:text-sm text-muted-foreground mt-1">
                Cryptocurrencies
              </div>
            </CardContent>
          </Card>

          {/* Account Status */}
          <Card className="glass-card border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 to-transparent overflow-hidden relative group hover:border-cyan-400/40 transition-all duration-300">
            <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/10 rounded-full blur-2xl group-hover:bg-cyan-500/20 transition-colors" />
            <CardContent className="p-4 sm:p-6 relative">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <Shield className="h-4 w-4 text-cyan-400" />
                <span className="text-xs sm:text-sm font-medium">Security</span>
              </div>
              <div className="font-display text-xl sm:text-2xl font-bold text-cyan-400 flex items-center gap-2">
                Verified
                <Lock className="h-4 w-4" />
              </div>
              <div className="text-xs sm:text-sm text-muted-foreground mt-1">
                Account protected
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Portfolio Section */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            {/* Portfolio Allocation Card */}
            <Card className="glass-card border-gold-500/10 overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between pb-2 sm:pb-4 border-b border-gold-500/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
                    <PieChart className="h-5 w-5 text-black" />
                  </div>
                  <div>
                    <CardTitle className="text-base sm:text-lg">Portfolio Allocation</CardTitle>
                    <CardDescription className="text-xs sm:text-sm">Asset distribution</CardDescription>
                  </div>
                </div>
                <Link to="/trade">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="text-gold-400 hover:text-gold-300 hover:bg-gold-500/10"
                  >
                    Trade
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="p-4 sm:p-6">
                {/* Allocation Chart */}
                {holdings.length > 0 ? (
                  <div className="space-y-4">
                    <div className="flex gap-1 h-3 sm:h-4 rounded-full overflow-hidden bg-secondary/50">
                      {holdings.map((h, i) => (
                        <div 
                          key={h.symbol}
                          className="h-full transition-all duration-700 hover:opacity-80"
                          style={{ 
                            width: `${h.allocation}%`,
                            backgroundColor: i === 0 ? '#F59E0B' : 
                                            i === 1 ? '#8B5CF6' : 
                                            i === 2 ? '#10B981' :
                                            i === 3 ? '#3B82F6' : 
                                            '#6B7280'
                          }}
                        />
                      ))}
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {holdings.map((h, i) => (
                        <div key={h.symbol} className="flex items-center gap-2 p-2 rounded-lg bg-secondary/30">
                          <div 
                            className="w-3 h-3 rounded-full flex-shrink-0"
                            style={{ 
                              backgroundColor: i === 0 ? '#F59E0B' : 
                                              i === 1 ? '#8B5CF6' : 
                                              i === 2 ? '#10B981' :
                                              i === 3 ? '#3B82F6' : 
                                              '#6B7280'
                            }}
                          />
                          <div className="min-w-0">
                            <div className="font-medium text-xs sm:text-sm truncate">{h.symbol}</div>
                            <div className="text-xs text-muted-foreground">{h.allocation}%</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 rounded-full bg-gold-500/10 flex items-center justify-center mx-auto mb-4">
                      <Wallet className="h-8 w-8 text-gold-400" />
                    </div>
                    <p className="text-muted-foreground mb-4">No assets in portfolio yet</p>
                    <Link to="/trade">
                      <Button className="bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold">
                        Start Trading
                        <ArrowUpRight className="h-4 w-4 ml-2" />
                      </Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Holdings List */}
            <Card className="glass-card border-gold-500/10 overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between border-b border-gold-500/10 py-3 sm:py-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-400 to-purple-600 flex items-center justify-center">
                    <Activity className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-base sm:text-lg">Holdings</CardTitle>
                    <CardDescription className="text-xs sm:text-sm">Your cryptocurrency assets</CardDescription>
                  </div>
                </div>
                <Link to="/transactions">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="text-muted-foreground hover:text-foreground hover:bg-gold-500/10"
                  >
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
                        <div className="w-12 h-12 rounded-xl bg-gold-500/10" />
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
                  <div className="divide-y divide-gold-500/10">
                    {holdings.map((holding, index) => (
                      <div 
                        key={holding.symbol} 
                        className="p-4 hover:bg-gold-500/5 transition-colors group cursor-pointer"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3 sm:gap-4 min-w-0">
                            <div 
                              className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center font-bold text-white flex-shrink-0 group-hover:scale-105 transition-transform"
                              style={{
                                background: `linear-gradient(135deg, ${
                                  index === 0 ? '#F59E0B, #D97706' : 
                                  index === 1 ? '#8B5CF6, #7C3AED' : 
                                  index === 2 ? '#10B981, #059669' :
                                  index === 3 ? '#3B82F6, #2563EB' : 
                                  '#6B7280, #4B5563'
                                })`
                              }}
                            >
                              {holding.symbol.charAt(0)}
                            </div>
                            <div className="min-w-0">
                              <div className="font-semibold text-sm sm:text-base flex items-center gap-2">
                                {holding.symbol}
                                <span className="text-xs text-muted-foreground font-normal hidden sm:inline">
                                  {holding.name}
                                </span>
                              </div>
                              <div className="text-xs sm:text-sm text-muted-foreground">
                                {holding.amount.toFixed(6)} {holding.symbol}
                              </div>
                            </div>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <div className="font-semibold text-sm sm:text-base">
                              ${holding.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </div>
                            {holding.change !== undefined && (
                              <div className={cn(
                                "text-xs sm:text-sm font-medium flex items-center justify-end gap-1",
                                holding.change >= 0 ? "text-emerald-400" : "text-red-400"
                              )}>
                                {holding.change >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                                {holding.change >= 0 ? '+' : ''}{holding.change.toFixed(2)}%
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 sm:p-8 text-center text-muted-foreground">
                    <div className="w-16 h-16 rounded-full bg-gold-500/10 flex items-center justify-center mx-auto mb-4">
                      <Wallet className="h-8 w-8 text-gold-400" />
                    </div>
                    <p className="text-sm sm:text-base mb-2">No holdings yet</p>
                    <p className="text-xs text-muted-foreground mb-4">Start building your portfolio</p>
                    <Link to="/trade">
                      <Button variant="outline" className="border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 text-gold-400">
                        Start Trading
                        <ArrowUpRight className="h-4 w-4 ml-2" />
                      </Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-4 sm:space-y-6">
            {/* Quick Actions */}
            <Card className="glass-card border-gold-500/10 overflow-hidden">
              <CardHeader className="pb-3">
                <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                  <Zap className="h-5 w-5 text-gold-400" />
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Link to="/wallet/deposit" className="block">
                  <Button 
                    className="w-full h-12 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold justify-start shadow-lg shadow-gold-500/20"
                    data-testid="quick-deposit-btn"
                  >
                    <Wallet className="h-5 w-5 mr-3" />
                    Deposit Funds
                    <ChevronRight className="h-4 w-4 ml-auto" />
                  </Button>
                </Link>
                <Link to="/trade" className="block">
                  <Button 
                    variant="outline"
                    className="w-full h-12 border-purple-500/30 hover:border-purple-400 hover:bg-purple-500/10 justify-start group"
                  >
                    <Activity className="h-5 w-5 mr-3 text-purple-400" />
                    Trade Now
                    <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Button>
                </Link>
                <Link to="/alerts" className="block">
                  <Button 
                    variant="outline"
                    className="w-full h-12 border-cyan-500/30 hover:border-cyan-400 hover:bg-cyan-500/10 justify-start group"
                  >
                    <Bell className="h-5 w-5 mr-3 text-cyan-400" />
                    Price Alerts
                    <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Button>
                </Link>
                <Link to="/transactions" className="block">
                  <Button 
                    variant="outline"
                    className="w-full h-12 border-emerald-500/30 hover:border-emerald-400 hover:bg-emerald-500/10 justify-start group"
                  >
                    <History className="h-5 w-5 mr-3 text-emerald-400" />
                    Transaction History
                    <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Account Card */}
            <Card className="glass-card border-gold-500/10">
              <CardHeader className="pb-3">
                <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                  <User className="h-5 w-5 text-gold-400" />
                  Account
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-black font-bold text-lg">
                    {user?.name?.charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <div className="font-semibold truncate">{user?.name}</div>
                    <div className="text-sm text-muted-foreground truncate">{user?.email}</div>
                  </div>
                </div>
                <div className="pt-3 border-t border-gold-500/10 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Member Since</span>
                    <span className="font-medium">
                      {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Account Type</span>
                    <span className="font-medium text-gold-400 flex items-center gap-1">
                      <Crown className="h-3 w-3" />
                      Premium
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Settings Card */}
            <Card className="glass-card border-gold-500/10">
              <CardHeader className="pb-3">
                <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                  <Settings className="h-5 w-5 text-gold-400" />
                  Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                <Button 
                  variant="ghost" 
                  className="w-full justify-start h-11 hover:bg-gold-500/10 group" 
                  size="sm"
                >
                  <Shield className="h-4 w-4 mr-3 text-muted-foreground group-hover:text-gold-400 transition-colors" />
                  Security Settings
                  <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start h-11 hover:bg-gold-500/10 group" 
                  size="sm"
                >
                  <Bell className="h-4 w-4 mr-3 text-muted-foreground group-hover:text-gold-400 transition-colors" />
                  Notifications
                  <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start h-11 hover:bg-gold-500/10 group" 
                  size="sm"
                >
                  <User className="h-4 w-4 mr-3 text-muted-foreground group-hover:text-gold-400 transition-colors" />
                  Edit Profile
                  <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </Button>
              </CardContent>
            </Card>

            {/* Promo Card */}
            <Card className="overflow-hidden border-0 bg-gradient-to-br from-gold-500/20 via-gold-600/10 to-purple-500/20 relative">
              <div className="absolute top-0 right-0 w-32 h-32 bg-gold-500/20 rounded-full blur-3xl" />
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-purple-500/20 rounded-full blur-2xl" />
              <CardContent className="p-5 relative">
                <div className="flex items-center gap-2 mb-3">
                  <Gift className="h-5 w-5 text-gold-400" />
                  <span className="font-semibold text-gold-400">Referral Program</span>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  Invite friends and earn up to $100 in crypto rewards!
                </p>
                <Button 
                  variant="outline"
                  size="sm"
                  className="w-full border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 text-gold-400"
                >
                  Learn More
                  <ExternalLink className="h-3 w-3 ml-2" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
