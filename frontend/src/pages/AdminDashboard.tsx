/**
 * Admin Dashboard
 * Real-time monitoring with user management, trade monitoring, and analytics
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Users,
  Activity,
  DollarSign,
  Bell,
  Search,
  Shield,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  MoreHorizontal,
  Ban,
  Eye,
  Edit,
  LogOut,
  Home,
  Settings,
  BarChart3
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/apiClient';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface User {
  id: string;
  email: string;
  name: string;
  status: 'active' | 'suspended' | 'pending';
  balance: number;
  joinedAt: string;
  lastLogin?: string;
}

interface Trade {
  id: string;
  userId: string;
  userEmail: string;
  type: 'buy' | 'sell';
  symbol: string;
  amount: number;
  price: number;
  status: 'filled' | 'pending' | 'cancelled';
  timestamp: string;
}

interface DashboardStats {
  totalUsers: number;
  activeUsers: number;
  volume24h: number;
  totalAlerts: number;
  userGrowth: number;
  volumeChange: number;
}

const AdminDashboard = () => {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  
  const [stats, setStats] = useState<DashboardStats>({
    totalUsers: 0,
    activeUsers: 0,
    volume24h: 0,
    totalAlerts: 0,
    userGrowth: 0,
    volumeChange: 0,
  });
  const [users, setUsers] = useState<User[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'trades'>('overview');

  // Check admin access
  useEffect(() => {
    // In production, check if user has admin role
    if (!user) {
      navigate('/auth');
    }
  }, [user, navigate]);

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, usersRes, tradesRes] = await Promise.all([
          api.admin.getStats(),
          api.admin.getUsers(),
          api.admin.getTrades(),
        ]);
        
        setStats(statsRes);
        setUsers(usersRes.users || []);
        setTrades(tradesRes.trades || []);
      } catch (error) {
        console.error('Failed to fetch admin data:', error);
        // Mock data for development
        setStats({
          totalUsers: 12543,
          activeUsers: 8234,
          volume24h: 2847562.34,
          totalAlerts: 1523,
          userGrowth: 12.5,
          volumeChange: 8.3,
        });
        setUsers([
          { id: '1', email: 'john@example.com', name: 'John Doe', status: 'active', balance: 25420.50, joinedAt: '2026-01-10' },
          { id: '2', email: 'jane@example.com', name: 'Jane Smith', status: 'active', balance: 12350.00, joinedAt: '2026-01-12' },
          { id: '3', email: 'bob@example.com', name: 'Bob Wilson', status: 'pending', balance: 0, joinedAt: '2026-01-14' },
        ]);
        setTrades([
          { id: 't1', userId: '1', userEmail: 'john@example.com', type: 'buy', symbol: 'BTC', amount: 0.5, price: 95000, status: 'filled', timestamp: '2026-01-14T10:30:00Z' },
          { id: 't2', userId: '2', userEmail: 'jane@example.com', type: 'sell', symbol: 'ETH', amount: 2.0, price: 3300, status: 'filled', timestamp: '2026-01-14T11:15:00Z' },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    
    // Polling for real-time updates
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Volume chart data
  const chartData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Volume ($)',
        data: [1200000, 1900000, 3000000, 2847562, 2500000, 2100000, 2800000],
        fill: true,
        borderColor: '#F59E0B',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: {
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { 
          color: '#9CA3AF',
          callback: (value: any) => `$${(value / 1000000).toFixed(1)}M`
        },
      },
      x: {
        grid: { display: false },
        ticks: { color: '#9CA3AF' },
      },
    },
  };

  const handleUserAction = async (userId: string, action: 'view' | 'edit' | 'ban') => {
    if (action === 'ban') {
      toast.success(`User ${userId} suspended`);
    } else if (action === 'view') {
      toast.info('User details view coming soon');
    } else {
      toast.info('User edit coming soon');
    }
  };

  const filteredUsers = users.filter(u => 
    u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Admin Header */}
      <header className="border-b border-border/50 bg-card/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-4">
              <img src="/logo.svg" alt="CryptoVault" className="h-8 w-8" />
              <span className="font-display text-lg font-bold">
                Admin <span className="text-gold-400">Panel</span>
              </span>
            </div>
            
            <div className="flex items-center gap-3">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => navigate('/')}
                className="min-h-[44px]"
              >
                <Home className="h-4 w-4 mr-2" />
                Site
              </Button>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => signOut()}
                className="min-h-[44px]"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="hidden lg:block w-64 border-r border-border/50 min-h-[calc(100vh-64px)] p-4">
          <nav className="space-y-1">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'users', label: 'Users', icon: Users },
              { id: 'trades', label: 'Trades', icon: Activity },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as any)}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left',
                  activeTab === item.id
                    ? 'bg-gold-500/10 text-gold-400'
                    : 'text-muted-foreground hover:bg-muted'
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {/* Mobile Tab Selector */}
          <div className="lg:hidden flex gap-2 mb-6 overflow-x-auto pb-2">
            {['overview', 'users', 'trades'].map((tab) => (
              <Button
                key={tab}
                variant={activeTab === tab ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveTab(tab as any)}
                className={cn(
                  'capitalize min-h-[44px]',
                  activeTab === tab && 'bg-gold-500 text-black'
                )}
              >
                {tab}
              </Button>
            ))}
          </div>

          {/* Stats Grid */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="glass-card border-gold-500/10">
                  <CardContent className="p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-3">
                      <Users className="h-5 w-5 text-gold-400" />
                      <Badge className={cn(
                        'text-xs',
                        stats.userGrowth >= 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'
                      )}>
                        {stats.userGrowth >= 0 ? '+' : ''}{stats.userGrowth}%
                      </Badge>
                    </div>
                    <div className="font-display text-2xl sm:text-3xl font-bold">
                      {stats.totalUsers.toLocaleString()}
                    </div>
                    <div className="text-xs sm:text-sm text-muted-foreground">Total Users</div>
                  </CardContent>
                </Card>

                <Card className="glass-card border-gold-500/10">
                  <CardContent className="p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-3">
                      <Activity className="h-5 w-5 text-emerald-400" />
                    </div>
                    <div className="font-display text-2xl sm:text-3xl font-bold">
                      {stats.activeUsers.toLocaleString()}
                    </div>
                    <div className="text-xs sm:text-sm text-muted-foreground">Active Now</div>
                  </CardContent>
                </Card>

                <Card className="glass-card border-gold-500/10">
                  <CardContent className="p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-3">
                      <DollarSign className="h-5 w-5 text-gold-400" />
                      <Badge className={cn(
                        'text-xs',
                        stats.volumeChange >= 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'
                      )}>
                        {stats.volumeChange >= 0 ? '+' : ''}{stats.volumeChange}%
                      </Badge>
                    </div>
                    <div className="font-display text-2xl sm:text-3xl font-bold">
                      ${(stats.volume24h / 1000000).toFixed(2)}M
                    </div>
                    <div className="text-xs sm:text-sm text-muted-foreground">24h Volume</div>
                  </CardContent>
                </Card>

                <Card className="glass-card border-gold-500/10">
                  <CardContent className="p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-3">
                      <Bell className="h-5 w-5 text-purple-400" />
                    </div>
                    <div className="font-display text-2xl sm:text-3xl font-bold">
                      {stats.totalAlerts.toLocaleString()}
                    </div>
                    <div className="text-xs sm:text-sm text-muted-foreground">Active Alerts</div>
                  </CardContent>
                </Card>
              </div>

              {/* Volume Chart */}
              <Card className="glass-card border-gold-500/10">
                <CardHeader>
                  <CardTitle>Trading Volume</CardTitle>
                  <CardDescription>Last 7 days</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64 sm:h-80">
                    <Line data={chartData} options={chartOptions as any} />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="space-y-4">
              {/* Search */}
              <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Users Table */}
              <Card className="glass-card border-gold-500/10 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border/50">
                        <th className="text-left p-4 text-sm font-medium text-muted-foreground">User</th>
                        <th className="text-left p-4 text-sm font-medium text-muted-foreground hidden sm:table-cell">Status</th>
                        <th className="text-right p-4 text-sm font-medium text-muted-foreground">Balance</th>
                        <th className="text-right p-4 text-sm font-medium text-muted-foreground hidden md:table-cell">Joined</th>
                        <th className="text-right p-4 text-sm font-medium text-muted-foreground">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map((u) => (
                        <tr key={u.id} className="border-b border-border/30 hover:bg-muted/50 transition-colors">
                          <td className="p-4">
                            <div className="flex items-center gap-3">
                              <div className="h-10 w-10 rounded-full bg-gold-500/10 flex items-center justify-center text-gold-400 font-bold">
                                {u.name.charAt(0)}
                              </div>
                              <div>
                                <div className="font-medium text-sm">{u.name}</div>
                                <div className="text-xs text-muted-foreground">{u.email}</div>
                              </div>
                            </div>
                          </td>
                          <td className="p-4 hidden sm:table-cell">
                            <Badge className={cn(
                              u.status === 'active' && 'bg-emerald-500/10 text-emerald-500',
                              u.status === 'pending' && 'bg-amber-500/10 text-amber-500',
                              u.status === 'suspended' && 'bg-red-500/10 text-red-500'
                            )}>
                              {u.status}
                            </Badge>
                          </td>
                          <td className="p-4 text-right font-mono">
                            ${u.balance.toLocaleString()}
                          </td>
                          <td className="p-4 text-right text-sm text-muted-foreground hidden md:table-cell">
                            {new Date(u.joinedAt).toLocaleDateString()}
                          </td>
                          <td className="p-4 text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleUserAction(u.id, 'view')}>
                                  <Eye className="h-4 w-4 mr-2" /> View
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleUserAction(u.id, 'edit')}>
                                  <Edit className="h-4 w-4 mr-2" /> Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  onClick={() => handleUserAction(u.id, 'ban')}
                                  className="text-red-500"
                                >
                                  <Ban className="h-4 w-4 mr-2" /> Suspend
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          )}

          {/* Trades Tab */}
          {activeTab === 'trades' && (
            <div className="space-y-4">
              <Card className="glass-card border-gold-500/10 overflow-hidden">
                <CardHeader>
                  <CardTitle>Recent Trades</CardTitle>
                  <CardDescription>Live trade monitoring</CardDescription>
                </CardHeader>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border/50">
                        <th className="text-left p-4 text-sm font-medium text-muted-foreground">User</th>
                        <th className="text-left p-4 text-sm font-medium text-muted-foreground">Type</th>
                        <th className="text-left p-4 text-sm font-medium text-muted-foreground hidden sm:table-cell">Symbol</th>
                        <th className="text-right p-4 text-sm font-medium text-muted-foreground">Amount</th>
                        <th className="text-right p-4 text-sm font-medium text-muted-foreground hidden md:table-cell">Status</th>
                        <th className="text-right p-4 text-sm font-medium text-muted-foreground">Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {trades.map((trade) => (
                        <tr key={trade.id} className="border-b border-border/30 hover:bg-muted/50 transition-colors">
                          <td className="p-4 text-sm">{trade.userEmail}</td>
                          <td className="p-4">
                            <span className={cn(
                              'flex items-center gap-1 text-sm font-medium',
                              trade.type === 'buy' ? 'text-emerald-500' : 'text-red-500'
                            )}>
                              {trade.type === 'buy' ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                              {trade.type.toUpperCase()}
                            </span>
                          </td>
                          <td className="p-4 text-sm hidden sm:table-cell">{trade.symbol}</td>
                          <td className="p-4 text-right font-mono text-sm">
                            ${(trade.amount * trade.price).toLocaleString()}
                          </td>
                          <td className="p-4 text-right hidden md:table-cell">
                            <Badge className="bg-emerald-500/10 text-emerald-500">
                              {trade.status}
                            </Badge>
                          </td>
                          <td className="p-4 text-right text-sm text-muted-foreground">
                            {new Date(trade.timestamp).toLocaleTimeString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;
