/**
 * AppLayout - Authenticated Dashboard Layout
 * Bybit-style professional trading platform layout
 * - Slim collapsible sidebar
 * - Compact top header
 * - No marketing elements (footer/promo banners)
 */

import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import DashboardHeader from '@/components/dashboard/DashboardHeader';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

interface AppLayoutProps {
  children?: React.ReactNode;
}

const AppLayout = ({ children }: AppLayoutProps) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { user } = useAuth();

  // Handle responsive behavior
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarCollapsed(true);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Background gradient effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-600/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-violet-600/5 rounded-full blur-[100px]" />
      </div>

      {/* Dashboard Header */}
      <DashboardHeader
        onMenuToggle={() => {
          if (isMobile) {
            setMobileMenuOpen(!mobileMenuOpen);
          } else {
            setSidebarCollapsed(!sidebarCollapsed);
          }
        }}
        isSidebarCollapsed={sidebarCollapsed}
      />

      {/* Main Layout Container */}
      <div className="flex pt-14">
        {/* Desktop Sidebar */}
        {!isMobile && (
          <DashboardSidebar
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        )}

        {/* Mobile Sidebar Overlay */}
        <AnimatePresence>
          {isMobile && mobileMenuOpen && (
            <>
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
                onClick={() => setMobileMenuOpen(false)}
              />
              {/* Mobile Sidebar */}
              <motion.div
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="fixed left-0 top-14 bottom-0 z-50 w-[280px]"
              >
                <DashboardSidebar
                  collapsed={false}
                  onToggle={() => setMobileMenuOpen(false)}
                  isMobile
                />
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <main
          className={cn(
            'flex-1 min-h-[calc(100vh-56px)] transition-all duration-300 relative z-10',
            !isMobile && !sidebarCollapsed && 'lg:ml-[240px]',
            !isMobile && sidebarCollapsed && 'lg:ml-[72px]'
          )}
        >
          <div className="p-4 md:p-6 lg:p-8">
            {children || <Outlet />}
          </div>
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      {isMobile && (
        <MobileBottomNav />
      )}
    </div>
  );
};

// Mobile Bottom Navigation Component
const MobileBottomNav = () => {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', icon: 'home', label: 'Home' },
    { path: '/earn', icon: 'percent', label: 'Earn' },
    { path: '/trade', icon: 'trending', label: 'Trade' },
    { path: '/transactions', icon: 'history', label: 'History' },
    { path: '/alerts', icon: 'bell', label: 'Alerts' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-[#0f0f17]/95 backdrop-blur-xl border-t border-white/5 z-50 safe-area-pb">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <a
              key={item.path}
              href={item.path}
              className={cn(
                'flex flex-col items-center justify-center gap-1 flex-1 h-full transition-colors',
                isActive ? 'text-gold-400' : 'text-gray-500 hover:text-gray-300'
              )}
            >
              <NavIcon name={item.icon} isActive={isActive} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </a>
          );
        })})
      </div>
    </nav>
  );
};

// Simple icon component for mobile nav
const NavIcon = ({ name, isActive }: { name: string; isActive: boolean }) => {
  const iconClass = cn('w-5 h-5', isActive && 'drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]');

  switch (name) {
    case 'home':
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      );
    case 'percent':
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
        </svg>
      );
    case 'trending':
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      );
    case 'history':
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'bell':
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      );
    default:
      return null;
  }
};

export default AppLayout;
