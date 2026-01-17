/**
 * Dashboard Security Page
 * Dedicated security settings within the dashboard
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Shield,
  Lock,
  Smartphone,
  Key,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  Copy,
  RefreshCw,
  Loader2,
  Clock,
  MapPin,
  Monitor
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/apiClient';
import { cn } from '@/lib/utils';
import DashboardCard from '@/components/dashboard/DashboardCard';

// Mock login activity
const mockLoginActivity = [
  { id: '1', device: 'Chrome on Windows', ip: '192.168.1.1', location: 'New York, US', time: '2 hours ago', current: true },
  { id: '2', device: 'Safari on iPhone', ip: '192.168.1.2', location: 'New York, US', time: '1 day ago', current: false },
  { id: '3', device: 'Firefox on Mac', ip: '10.0.0.1', location: 'San Francisco, US', time: '3 days ago', current: false },
];

const DashboardSecurity = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);

  // Fetch 2FA status
  const { data: twoFAStatus } = useQuery({
    queryKey: ['2faStatus'],
    queryFn: () => api.auth.get2FAStatus(),
  });

  // Security items
  const securityItems = [
    {
      id: 'password',
      title: 'Password',
      description: 'Last changed 30 days ago',
      icon: Lock,
      status: 'secure',
      action: 'Change',
    },
    {
      id: '2fa',
      title: 'Two-Factor Authentication',
      description: is2FAEnabled ? 'Enabled via Authenticator App' : 'Add extra security to your account',
      icon: Smartphone,
      status: is2FAEnabled ? 'enabled' : 'disabled',
      action: is2FAEnabled ? 'Manage' : 'Enable',
    },
    {
      id: 'antiPhishing',
      title: 'Anti-Phishing Code',
      description: 'Not set - Set a code to identify official emails',
      icon: Shield,
      status: 'warning',
      action: 'Set up',
    },
    {
      id: 'withdrawalWhitelist',
      title: 'Withdrawal Whitelist',
      description: 'Restrict withdrawals to approved addresses only',
      icon: Key,
      status: 'disabled',
      action: 'Enable',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'secure':
      case 'enabled':
        return 'text-emerald-400 bg-emerald-500/10';
      case 'warning':
        return 'text-amber-400 bg-amber-500/10';
      case 'disabled':
        return 'text-gray-400 bg-gray-500/10';
      default:
        return 'text-gray-400 bg-gray-500/10';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-display font-bold text-white flex items-center gap-3">
          <Shield className="h-7 w-7 text-gold-400" />
          Security Center
        </h1>
        <p className="text-gray-400 mt-1">Manage your account security settings</p>
      </div>

      {/* Security Score */}
      <DashboardCard glowColor="emerald">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-20 h-20 rounded-full border-4 border-emerald-500/30 flex items-center justify-center">
                <span className="text-2xl font-bold text-emerald-400">75%</span>
              </div>
              <div className="absolute -bottom-1 -right-1 p-1.5 bg-emerald-500 rounded-full">
                <CheckCircle2 className="h-4 w-4 text-black" />
              </div>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Security Score: Good</h2>
              <p className="text-gray-400 text-sm">Enable 2FA to improve your security score</p>
            </div>
          </div>
          <Button className="bg-gold-500 hover:bg-gold-400 text-black">
            Improve Security
          </Button>
        </div>
      </DashboardCard>

      {/* Security Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DashboardCard title="Security Settings" icon={<Shield className="h-5 w-5" />}>
          <div className="space-y-3">
            {securityItems.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className={cn('p-2 rounded-lg', getStatusColor(item.status))}>
                    <item.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">{item.title}</h3>
                    <p className="text-sm text-gray-400">{item.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'px-2 py-0.5 text-xs font-medium rounded-full capitalize',
                    getStatusColor(item.status)
                  )}>
                    {item.status}
                  </span>
                  <Button variant="ghost" size="sm" className="text-gold-400 hover:text-gold-300">
                    {item.action}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </DashboardCard>

        {/* Login Activity */}
        <DashboardCard title="Recent Login Activity" icon={<Monitor className="h-5 w-5" />}>
          <div className="space-y-3">
            {mockLoginActivity.map((activity) => (
              <div
                key={activity.id}
                className={cn(
                  'p-4 rounded-xl transition-colors',
                  activity.current ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-white/5'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-white/10 rounded-lg">
                      <Monitor className="h-4 w-4 text-gray-400" />
                    </div>
                    <div>
                      <p className="font-medium text-white flex items-center gap-2">
                        {activity.device}
                        {activity.current && (
                          <span className="px-1.5 py-0.5 text-[10px] bg-emerald-500 text-white rounded font-bold">
                            CURRENT
                          </span>
                        )}
                      </p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {activity.location}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {activity.time}
                        </span>
                      </div>
                    </div>
                  </div>
                  {!activity.current && (
                    <button className="text-xs text-red-400 hover:text-red-300">
                      Revoke
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          <Button variant="outline" className="w-full mt-4 border-white/10 hover:bg-white/5">
            View All Activity
          </Button>
        </DashboardCard>
      </div>

      {/* Tips */}
      <DashboardCard title="Security Tips" icon={<AlertTriangle className="h-5 w-5" />}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-white/5 rounded-xl">
            <h4 className="font-medium text-white mb-2">Use a Strong Password</h4>
            <p className="text-sm text-gray-400">
              Create a unique password with at least 12 characters, including numbers and symbols.
            </p>
          </div>
          <div className="p-4 bg-white/5 rounded-xl">
            <h4 className="font-medium text-white mb-2">Enable 2FA</h4>
            <p className="text-sm text-gray-400">
              Two-factor authentication adds an extra layer of security to your account.
            </p>
          </div>
          <div className="p-4 bg-white/5 rounded-xl">
            <h4 className="font-medium text-white mb-2">Beware of Phishing</h4>
            <p className="text-sm text-gray-400">
              Always verify you're on the official CryptoVault website before entering credentials.
            </p>
          </div>
        </div>
      </DashboardCard>
    </div>
  );
};

export default DashboardSecurity;
