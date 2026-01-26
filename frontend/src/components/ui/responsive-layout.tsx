/**
 * Enterprise Responsive Layout Components
 * 
 * Provides:
 * - Responsive container with proper breakpoints
 * - Bento grid for dashboard layouts
 * - Marketing grid for landing pages
 * - Mobile-first design patterns
 */

import React from 'react';
import { cn } from '@/lib/utils';

// ============================================
// RESPONSIVE CONTAINER
// ============================================

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  size?: 'default' | 'wide' | 'narrow' | 'full';
}

export function Container({ children, className, size = 'default' }: ContainerProps) {
  const sizeClasses = {
    default: 'max-w-7xl',
    wide: 'max-w-[1400px]',
    narrow: 'max-w-4xl',
    full: 'max-w-full',
  };

  return (
    <div
      className={cn(
        'mx-auto w-full px-4 sm:px-6 lg:px-8',
        sizeClasses[size],
        className
      )}
    >
      {children}
    </div>
  );
}

// ============================================
// BENTO GRID (Dashboard Layout)
// ============================================

interface BentoGridProps {
  children: React.ReactNode;
  className?: string;
  columns?: 2 | 3 | 4;
}

export function BentoGrid({ children, className, columns = 4 }: BentoGridProps) {
  const columnClasses = {
    2: 'md:grid-cols-2',
    3: 'md:grid-cols-2 lg:grid-cols-3',
    4: 'md:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div
      className={cn(
        'grid grid-cols-1 gap-4',
        columnClasses[columns],
        className
      )}
    >
      {children}
    </div>
  );
}

interface BentoCardProps {
  children: React.ReactNode;
  className?: string;
  span?: 1 | 2 | 3 | 4;
  rowSpan?: 1 | 2;
}

export function BentoCard({ children, className, span = 1, rowSpan = 1 }: BentoCardProps) {
  const spanClasses = {
    1: '',
    2: 'md:col-span-2',
    3: 'md:col-span-2 lg:col-span-3',
    4: 'md:col-span-2 lg:col-span-4',
  };

  const rowSpanClasses = {
    1: '',
    2: 'md:row-span-2',
  };

  return (
    <div
      className={cn(
        'bg-card border border-border/40 rounded-xl p-4 sm:p-6',
        'hover:border-primary/30 transition-colors duration-300',
        'min-h-[120px] sm:min-h-[180px]',
        spanClasses[span],
        rowSpanClasses[rowSpan],
        className
      )}
    >
      {children}
    </div>
  );
}

// ============================================
// STATS CARD
// ============================================

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
  className?: string;
}

export function StatsCard({ title, value, change, icon, className }: StatsCardProps) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <div
      className={cn(
        'bg-card border border-border/40 rounded-xl p-4 sm:p-6',
        'hover:border-primary/30 transition-all duration-300',
        'group',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-xs sm:text-sm font-medium text-muted-foreground uppercase tracking-wider">
            {title}
          </p>
          <p className="text-xl sm:text-2xl lg:text-3xl font-bold font-heading tracking-tight">
            {value}
          </p>
          {change !== undefined && (
            <p
              className={cn(
                'text-xs sm:text-sm font-medium flex items-center gap-1',
                isPositive && 'text-success',
                isNegative && 'text-destructive',
                !isPositive && !isNegative && 'text-muted-foreground'
              )}
            >
              {isPositive && '↑'}
              {isNegative && '↓'}
              {Math.abs(change).toFixed(2)}%
            </p>
          )}
        </div>
        {icon && (
          <div className="p-2 sm:p-3 rounded-lg bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================
// RESPONSIVE TABLE WRAPPER
// ============================================

interface ResponsiveTableProps {
  children: React.ReactNode;
  className?: string;
}

export function ResponsiveTable({ children, className }: ResponsiveTableProps) {
  return (
    <div className={cn('w-full overflow-x-auto -mx-4 sm:mx-0', className)}>
      <div className="inline-block min-w-full align-middle px-4 sm:px-0">
        {children}
      </div>
    </div>
  );
}

// ============================================
// MOBILE NAVIGATION DRAWER
// ============================================

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

export function MobileDrawer({ isOpen, onClose, children }: MobileDrawerProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        onClick={onClose}
        data-testid="mobile-drawer-backdrop"
      />
      {/* Drawer */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-[280px] bg-card border-r border-border',
          'transform transition-transform duration-300 ease-out lg:hidden',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        data-testid="mobile-drawer"
      >
        {children}
      </div>
    </>
  );
}

// ============================================
// RESPONSIVE SECTION
// ============================================

interface SectionProps {
  children: React.ReactNode;
  className?: string;
  spacing?: 'sm' | 'md' | 'lg';
}

export function Section({ children, className, spacing = 'md' }: SectionProps) {
  const spacingClasses = {
    sm: 'py-8 sm:py-12',
    md: 'py-12 sm:py-16 lg:py-24',
    lg: 'py-16 sm:py-24 lg:py-32',
  };

  return (
    <section className={cn(spacingClasses[spacing], className)}>
      {children}
    </section>
  );
}

// ============================================
// PAGE HEADER
// ============================================

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between',
        'pb-6 sm:pb-8 border-b border-border/40',
        className
      )}
    >
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-bold font-heading tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="text-sm sm:text-base text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 sm:gap-3">
          {actions}
        </div>
      )}
    </div>
  );
}

// ============================================
// RESPONSIVE GRID
// ============================================

interface ResponsiveGridProps {
  children: React.ReactNode;
  className?: string;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: 'sm' | 'md' | 'lg';
}

export function ResponsiveGrid({
  children,
  className,
  cols = { default: 1, sm: 2, lg: 3 },
  gap = 'md',
}: ResponsiveGridProps) {
  const gapClasses = {
    sm: 'gap-2 sm:gap-3',
    md: 'gap-4 sm:gap-6',
    lg: 'gap-6 sm:gap-8',
  };

  const colClasses = [
    cols.default && `grid-cols-${cols.default}`,
    cols.sm && `sm:grid-cols-${cols.sm}`,
    cols.md && `md:grid-cols-${cols.md}`,
    cols.lg && `lg:grid-cols-${cols.lg}`,
    cols.xl && `xl:grid-cols-${cols.xl}`,
  ].filter(Boolean).join(' ');

  return (
    <div className={cn('grid', gapClasses[gap], colClasses, className)}>
      {children}
    </div>
  );
}

// ============================================
// EMPTY STATE
// ============================================

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center',
        'py-12 sm:py-16 px-4',
        className
      )}
    >
      {icon && (
        <div className="p-4 rounded-full bg-muted/50 text-muted-foreground mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg sm:text-xl font-semibold font-heading mb-2">
        {title}
      </h3>
      {description && (
        <p className="text-sm sm:text-base text-muted-foreground max-w-sm mb-6">
          {description}
        </p>
      )}
      {action}
    </div>
  );
}

// ============================================
// LOADING SKELETON
// ============================================

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'card' | 'avatar' | 'button';
}

export function Skeleton({ className, variant = 'text' }: SkeletonProps) {
  const variantClasses = {
    text: 'h-4 w-full rounded',
    card: 'h-32 w-full rounded-xl',
    avatar: 'h-10 w-10 rounded-full',
    button: 'h-10 w-24 rounded-md',
  };

  return (
    <div
      className={cn(
        'animate-pulse bg-muted/50',
        variantClasses[variant],
        className
      )}
    />
  );
}

// ============================================
// EXPORTS
// ============================================

export {
  Container,
  BentoGrid,
  BentoCard,
  StatsCard,
  ResponsiveTable,
  MobileDrawer,
  Section,
  PageHeader,
  ResponsiveGrid,
  EmptyState,
  Skeleton,
};
