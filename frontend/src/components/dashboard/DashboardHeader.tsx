/**
 * DashboardHeader - Slim Top Navigation Bar
 * Bybit-inspired compact header for authenticated dashboard
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu,
  Bell,
  Shield,
  Settings,
  LogOut,
  User,
  ChevronDown,
  Moon,
  Sun,
  Wallet,
  HelpCircle
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface DashboardHeaderProps {
  onMenuToggle: () => void;
  isSidebarCollapsed: boolean;
}

const DashboardHeader = ({ onMenuToggle, isSidebarCollapsed }: DashboardHeaderProps) => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [notificationCount] = useState(3); // Mock notification count
  const [isDarkMode, setIsDarkMode] = useState(true);

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-[#0f0f17]/95 backdrop-blur-xl border-b border-white/5 z-50">
      <div className="h-full px-3 sm:px-4 flex items-center justify-between">
        {/* Left Section: Menu + Logo */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Menu Toggle Button */}
          <button
            onClick={onMenuToggle}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
            aria-label="Toggle sidebar"
            data-testid="sidebar-toggle"
          >
            <Menu className="h-5 w-5 text-gray-400" />
          </button>

          {/* Logo */}
          <Link to="/dashboard" className="flex items-center gap-2 group">
            <div className="relative">
              <div className="absolute inset-0 bg-gold-400/20 blur-lg rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
              <img
                src="/logo.svg"
                alt="CryptoVault"
                className="h-7 w-7 sm:h-8 sm:w-8 object-contain relative z-10"
              />
            </div>
            <span className="font-display text-base sm:text-lg font-bold hidden sm:block">
              Crypto<span className="text-gold-400">Vault</span>
            </span>
          </Link>

          {/* Security Badge */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 rounded-full border border-emerald-500/20">
            <Shield className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider">
              Secured
            </span>
          </div>
        </div>

        {/* Center Section: Quick Actions (Desktop) */}
        <div className="hidden lg:flex items-center gap-1">
          <QuickActionButton href="/wallet/deposit" label="Deposit" />
          <QuickActionButton href="/wallet/withdraw" label="Withdraw" />
          <QuickActionButton href="/trade" label="Trade" highlight />
        </div>

        {/* Right Section: Actions */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Theme Toggle */}
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors hidden sm:flex"
            aria-label="Toggle theme"
          >
            {isDarkMode ? (
              <Moon className="h-4.5 w-4.5 text-gray-400" />
            ) : (
              <Sun className="h-4.5 w-4.5 text-gray-400" />
            )}
          </button>

          {/* Help */}
          <Link
            to="/help"
            className="p-2 hover:bg-white/5 rounded-lg transition-colors hidden sm:flex"
            aria-label="Help center"
          >
            <HelpCircle className="h-4.5 w-4.5 text-gray-400" />
          </Link>

          {/* Notifications */}
          <NotificationButton count={notificationCount} />

          {/* User Menu */}
          <UserMenu user={user} onSignOut={handleSignOut} />
        </div>
      </div>
    </header>
  );
};

// Quick Action Button Component
const QuickActionButton = ({
  href,
  label,
  highlight = false
}: {
  href: string;
  label: string;
  highlight?: boolean;
}) => (
  <Link
    to={href}
    className={cn(
      'px-4 py-1.5 text-sm font-medium rounded-lg transition-all',
      highlight
        ? 'bg-gradient-to-r from-gold-500 to-gold-600 text-black hover:from-gold-400 hover:to-gold-500 shadow-lg shadow-gold-500/20'
        : 'text-gray-400 hover:text-white hover:bg-white/5'
    )}
  >
    {label}
  </Link>
);

// Notification Button Component
const NotificationButton = ({ count }: { count: number }) => (
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <button
        className="relative p-2 hover:bg-white/5 rounded-lg transition-colors"
        aria-label="Notifications"
        data-testid="notifications-button"
      >
        <Bell className="h-4.5 w-4.5 text-gray-400" />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 h-4 min-w-4 px-1 flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" className="w-80 bg-[#1a1a2e] border-white/10">
      <div className="px-4 py-3 border-b border-white/10">
        <h3 className="font-semibold text-sm">Notifications</h3>
      </div>
      <div className="max-h-[300px] overflow-y-auto">
        <NotificationItem
          title="Deposit Confirmed"
          message="Your deposit of 0.5 BTC has been confirmed"
          time="2 min ago"
          type="success"
        />
        <NotificationItem
          title="Price Alert"
          message="BTC has reached your target price of $68,000"
          time="1 hour ago"
          type="info"
        />
        <NotificationItem
          title="Security Notice"
          message="New login detected from Chrome on Windows"
          time="3 hours ago"
          type="warning"
        />
      </div>
      <div className="p-2 border-t border-white/10">
        <Link
          to="/notifications"
          className="block text-center text-sm text-gold-400 hover:text-gold-300 py-2"
        >
          View all notifications
        </Link>
      </div>
    </DropdownMenuContent>
  </DropdownMenu>
);

// Notification Item Component
const NotificationItem = ({
  title,
  message,
  time,
  type
}: {
  title: string;
  message: string;
  time: string;
  type: 'success' | 'info' | 'warning';
}) => {
  const typeColors = {
    success: 'bg-emerald-500',
    info: 'bg-blue-500',
    warning: 'bg-amber-500',
  };

  return (
    <div className="px-4 py-3 hover:bg-white/5 cursor-pointer border-b border-white/5 last:border-b-0">
      <div className="flex items-start gap-3">
        <div className={cn('w-2 h-2 rounded-full mt-2', typeColors[type])} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{title}</p>
          <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{message}</p>
          <p className="text-[10px] text-gray-500 mt-1">{time}</p>
        </div>
      </div>
    </div>
  );
};

// User Menu Component
const UserMenu = ({
  user,
  onSignOut
}: {
  user: any;
  onSignOut: () => void;
}) => (
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <button
        className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded-lg transition-colors"
        data-testid="user-menu-button"
      >
        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-black font-bold text-sm">
          {user?.name?.charAt(0)?.toUpperCase() || 'U'}
        </div>
        <div className="hidden md:block text-left">
          <p className="text-sm font-medium text-white truncate max-w-[100px]">
            {user?.name || 'User'}
          </p>
          <p className="text-[10px] text-gray-500 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Verified
          </p>
        </div>
        <ChevronDown className="h-4 w-4 text-gray-400 hidden md:block" />
      </button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" className="w-56 bg-[#1a1a2e] border-white/10">
      <div className="px-3 py-2 border-b border-white/10">
        <p className="text-sm font-medium text-white">{user?.name}</p>
        <p className="text-xs text-gray-400 truncate">{user?.email}</p>
      </div>
      <div className="py-1">
        <DropdownMenuItem asChild>
          <Link to="/dashboard" className="flex items-center gap-3 cursor-pointer">
            <User className="h-4 w-4" />
            <span>My Profile</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/wallet/deposit" className="flex items-center gap-3 cursor-pointer">
            <Wallet className="h-4 w-4" />
            <span>Wallet</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/security" className="flex items-center gap-3 cursor-pointer">
            <Shield className="h-4 w-4" />
            <span>Security</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/settings" className="flex items-center gap-3 cursor-pointer">
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </Link>
        </DropdownMenuItem>
      </div>
      <DropdownMenuSeparator className="bg-white/10" />
      <div className="py-1">
        <DropdownMenuItem
          onClick={onSignOut}
          className="flex items-center gap-3 cursor-pointer text-red-400 focus:text-red-400"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign Out</span>
        </DropdownMenuItem>
      </div>
    </DropdownMenuContent>
  </DropdownMenu>
);

export default DashboardHeader;
