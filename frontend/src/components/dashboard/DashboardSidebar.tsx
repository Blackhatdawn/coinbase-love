/**
 * DashboardSidebar - Collapsible Navigation Sidebar
 * Bybit-inspired sleek sidebar with icons and tooltips
 */

import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  TrendingUp,
  Wallet,
  History,
  Bell,
  Users,
  Gift,
  Settings,
  ChevronLeft,
  ChevronRight,
  Percent,
  ArrowRightLeft,
  Shield,
  HelpCircle,
  PieChart
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface DashboardSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  isMobile?: boolean;
}

interface NavItem {
  path: string;
  icon: React.ElementType;
  label: string;
  badge?: string | number;
  isNew?: boolean;
}

const mainNavItems: NavItem[] = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/markets', icon: TrendingUp, label: 'Markets', isNew: true },
  { path: '/portfolio', icon: PieChart, label: 'Portfolio' },
  { path: '/trade', icon: ArrowRightLeft, label: 'Trade' },
  { path: '/earn', icon: Percent, label: 'Earn', badge: 'APY 12%' },
  { path: '/wallet/deposit', icon: Wallet, label: 'Wallet' },
];

const secondaryNavItems: NavItem[] = [
  { path: '/transactions', icon: History, label: 'Transactions' },
  { path: '/alerts', icon: Bell, label: 'Price Alerts' },
  { path: '/wallet/transfer', icon: Users, label: 'P2P Transfer', isNew: true },
  { path: '/referrals', icon: Gift, label: 'Referrals' },
];

const bottomNavItems: NavItem[] = [
  { path: '/security', icon: Shield, label: 'Security' },
  { path: '/settings', icon: Settings, label: 'Settings' },
  { path: '/help', icon: HelpCircle, label: 'Help Center' },
];

const DashboardSidebar = ({ collapsed, onToggle, isMobile = false }: DashboardSidebarProps) => {
  const location = useLocation();

  return (
    <aside
      className={cn(
        'fixed left-0 top-14 bottom-0 bg-[#0f0f17] border-r border-white/5 transition-all duration-300 z-40 flex flex-col',
        collapsed ? 'w-[72px]' : 'w-[240px]',
        isMobile && 'h-[calc(100vh-56px)] pb-20'
      )}
    >
      {/* Navigation Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        {/* Main Navigation */}
        <nav className="p-2 sm:p-3">
          <div className={cn('mb-2 px-3', collapsed && 'px-0 text-center')}>
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
              {collapsed ? '•' : 'Main'}
            </span>
          </div>
          <ul className="space-y-1">
            {mainNavItems.map((item) => (
              <NavItem
                key={item.path}
                item={item}
                isActive={location.pathname === item.path}
                collapsed={collapsed}
              />
            ))}
          </ul>
        </nav>

        {/* Secondary Navigation */}
        <nav className="p-2 sm:p-3 pt-0">
          <div className={cn('mb-2 px-3', collapsed && 'px-0 text-center')}>
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
              {collapsed ? '•' : 'Activity'}
            </span>
          </div>
          <ul className="space-y-1">
            {secondaryNavItems.map((item) => (
              <NavItem
                key={item.path}
                item={item}
                isActive={location.pathname === item.path}
                collapsed={collapsed}
              />
            ))}
          </ul>
        </nav>

        {/* Bottom Navigation */}
        <nav className="p-2 sm:p-3 pt-0 mt-auto">
          <div className={cn('mb-2 px-3', collapsed && 'px-0 text-center')}>
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
              {collapsed ? '•' : 'Account'}
            </span>
          </div>
          <ul className="space-y-1">
            {bottomNavItems.map((item) => (
              <NavItem
                key={item.path}
                item={item}
                isActive={location.pathname === item.path}
                collapsed={collapsed}
              />
            ))}
          </ul>
        </nav>
      </div>

      {/* Collapse Toggle Button (Desktop only) */}
      {!isMobile && (
        <div className="p-2 sm:p-3 border-t border-white/5">
          <button
            onClick={onToggle}
            className={cn(
              'w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg',
              'text-gray-400 hover:text-white hover:bg-white/5 transition-colors',
              collapsed && 'px-0'
            )}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span className="text-sm">Collapse</span>
              </>
            )}
          </button>
        </div>
      )}
    </aside>
  );
};

// Individual Navigation Item
const NavItem = ({
  item,
  isActive,
  collapsed
}: {
  item: NavItem;
  isActive: boolean;
  collapsed: boolean;
}) => {
  const Icon = item.icon;

  const content = (
    <Link
      to={item.path}
      className={cn(
        'relative flex items-center gap-3 px-3 py-2 sm:py-2.5 rounded-lg transition-all duration-200 group',
        isActive
          ? 'bg-gold-500/10 text-gold-400'
          : 'text-gray-400 hover:text-white hover:bg-white/5',
        collapsed && 'justify-center px-0'
      )}
      data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
    >
      {/* Active Indicator */}
      {isActive && (
        <motion.div
          layoutId="activeNav"
          className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-gold-400 rounded-r-full"
        />
      )}

      {/* Icon */}
      <Icon
        className={cn(
          'h-5 w-5 flex-shrink-0 transition-transform',
          isActive && 'drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]',
          'group-hover:scale-110'
        )}
      />

      {/* Label */}
      {!collapsed && (
        <span className="text-sm font-medium truncate">{item.label}</span>
      )}

      {/* Badge */}
      {item.badge && !collapsed && (
        <span className="ml-auto px-2 py-0.5 text-[10px] font-semibold bg-gold-500/20 text-gold-400 rounded-full">
          {item.badge}
        </span>
      )}

      {/* New Badge */}
      {item.isNew && !collapsed && (
        <span className="ml-auto px-1.5 py-0.5 text-[9px] font-bold bg-emerald-500 text-white rounded uppercase">
          New
        </span>
      )}
    </Link>
  );

  // Wrap in tooltip when collapsed
  if (collapsed) {
    return (
      <li>
        <Tooltip delayDuration={0}>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent side="right" className="bg-[#1a1a2e] border-white/10">
            <div className="flex items-center gap-2">
              <span>{item.label}</span>
              {item.badge && (
                <span className="px-1.5 py-0.5 text-[10px] bg-gold-500/20 text-gold-400 rounded">
                  {item.badge}
                </span>
              )}
              {item.isNew && (
                <span className="px-1 py-0.5 text-[9px] font-bold bg-emerald-500 text-white rounded uppercase">
                  New
                </span>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </li>
    );
  }

  return <li>{content}</li>;
};

export default DashboardSidebar;
