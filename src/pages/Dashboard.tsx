import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import {
  TrendingUp,
  ArrowUpRight,
  PieChart,
  Activity,
  Settings,
  User,
  Shield,
  Bell,
  Wallet,
  LogOut,
  History
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";

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

  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [totalValue, setTotalValue] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        setIsLoading(true);
        const response = await api.portfolio.get();
        const portfolio = response.portfolio;

        setTotalValue(portfolio.totalBalance);
        setHoldings(portfolio.holdings || []);
      } catch (error) {
        console.error("Failed to fetch portfolio:", error);
        setTotalValue(0);
        setHoldings([]);
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      fetchPortfolio();
    }
  }, [user]);

  const handleSignOut = () => {
    signOut();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Dashboard Header */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent">
                <Wallet className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-display text-xl font-bold">CryptoVault</span>
            </Link>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground hidden sm:block">
                Welcome, {user?.name}
              </span>
              <Button variant="ghost" size="sm" onClick={handleSignOut}>
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-muted-foreground">
            Manage your portfolio and account settings
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Portfolio Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Portfolio Summary Card */}
            <Card className="glass-card border-border/50">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Total Balance</CardTitle>
                  <CardDescription>Your portfolio value</CardDescription>
                </div>
                <PieChart className="h-5 w-5 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="mb-6">
                  <div className="font-display text-4xl font-bold mb-2">
                    ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                  <div className="flex items-center gap-2 text-success">
                    <TrendingUp className="h-4 w-4" />
                    <span className="text-sm font-medium">+$4,523.45 (4.12%) today</span>
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

                <Button variant="gradient" className="w-full mt-6">
                  Deposit Funds
                </Button>
              </CardContent>
            </Card>

            {/* Holdings List */}
            <Card className="glass-card border-border/50 overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between border-b border-border/50">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">Your Holdings</CardTitle>
                </div>
                <Link to="/transactions">
                  <Button variant="ghost" size="sm">
                    <History className="h-4 w-4 mr-1" />
                    History
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border/50">
                  {holdings.map((holding) => (
                    <div key={holding.symbol} className="p-4 hover:bg-secondary/50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center font-bold text-primary">
                            {holding.symbol.charAt(0)}
                          </div>
                          <div>
                            <div className="font-semibold">{holding.symbol}</div>
                            <div className="text-sm text-muted-foreground">{holding.amount} {holding.symbol}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">${holding.value.toLocaleString()}</div>
                          <div className={`text-sm ${holding.change >= 0 ? 'text-success' : 'text-destructive'}`}>
                            {holding.change >= 0 ? '+' : ''}{holding.change}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Settings Sidebar */}
          <div className="space-y-6">
            {/* Account Info Card */}
            <Card className="glass-card border-border/50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="h-5 w-5 text-primary" />
                  Account
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs text-muted-foreground uppercase tracking-wide">Name</label>
                  <p className="font-medium">{user?.name}</p>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground uppercase tracking-wide">Email</label>
                  <p className="font-medium">{user?.email}</p>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground uppercase tracking-wide">Member Since</label>
                  <p className="font-medium">
                    {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Quick Settings */}
            <Card className="glass-card border-border/50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Settings className="h-5 w-5 text-primary" />
                  Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="ghost" className="w-full justify-start" size="sm">
                  <Shield className="h-4 w-4 mr-3" />
                  Security
                </Button>
                <Button variant="ghost" className="w-full justify-start" size="sm">
                  <Bell className="h-4 w-4 mr-3" />
                  Notifications
                </Button>
                <Button variant="ghost" className="w-full justify-start" size="sm">
                  <User className="h-4 w-4 mr-3" />
                  Edit Profile
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
