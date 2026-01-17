/**
 * DashboardCard - Reusable Card Component
 * Premium card with hover effects, glow, and animations
 */

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface DashboardCardProps {
  title?: string;
  icon?: React.ReactNode;
  badge?: string;
  action?: React.ReactNode;
  className?: string;
  glowColor?: 'gold' | 'emerald' | 'violet' | 'blue' | 'red';
  children: React.ReactNode;
  noPadding?: boolean;
}

const glowColors = {
  gold: 'hover:shadow-[0_0_40px_-10px_rgba(251,191,36,0.3)]',
  emerald: 'hover:shadow-[0_0_40px_-10px_rgba(52,211,153,0.3)]',
  violet: 'hover:shadow-[0_0_40px_-10px_rgba(139,92,246,0.3)]',
  blue: 'hover:shadow-[0_0_40px_-10px_rgba(59,130,246,0.3)]',
  red: 'hover:shadow-[0_0_40px_-10px_rgba(239,68,68,0.3)]',
};

const borderColors = {
  gold: 'hover:border-gold-500/30',
  emerald: 'hover:border-emerald-500/30',
  violet: 'hover:border-violet-500/30',
  blue: 'hover:border-blue-500/30',
  red: 'hover:border-red-500/30',
};

const iconColors = {
  gold: 'text-gold-400',
  emerald: 'text-emerald-400',
  violet: 'text-violet-400',
  blue: 'text-blue-400',
  red: 'text-red-400',
};

const DashboardCard = ({
  title,
  icon,
  badge,
  action,
  className,
  glowColor,
  children,
  noPadding = false
}: DashboardCardProps) => {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'relative bg-[#12121a] rounded-2xl border border-white/5 overflow-hidden transition-all duration-300',
        glowColor && glowColors[glowColor],
        glowColor && borderColors[glowColor],
        className
      )}
    >
      {/* Gradient overlay at top */}
      {glowColor && (
        <div className={cn(
          'absolute top-0 left-0 right-0 h-px',
          glowColor === 'gold' && 'bg-gradient-to-r from-transparent via-gold-500/50 to-transparent',
          glowColor === 'emerald' && 'bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent',
          glowColor === 'violet' && 'bg-gradient-to-r from-transparent via-violet-500/50 to-transparent',
          glowColor === 'blue' && 'bg-gradient-to-r from-transparent via-blue-500/50 to-transparent',
          glowColor === 'red' && 'bg-gradient-to-r from-transparent via-red-500/50 to-transparent',
        )} />
      )}

      {/* Card Content */}
      <div className={cn(!noPadding && 'p-5 sm:p-6')}>
        {/* Header */}
        {(title || icon || badge || action) && (
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {icon && (
                <div className={cn(
                  'flex-shrink-0',
                  glowColor ? iconColors[glowColor] : 'text-gray-400'
                )}>
                  {icon}
                </div>
              )}
              {title && (
                <h3 className="font-semibold text-white">{title}</h3>
              )}
              {badge && (
                <span className="px-2 py-0.5 text-[10px] font-semibold bg-gold-500/20 text-gold-400 rounded-full">
                  {badge}
                </span>
              )}
            </div>
            {action && (
              <div className="flex-shrink-0">
                {action}
              </div>
            )}
          </div>
        )}

        {/* Body */}
        {children}
      </div>
    </motion.div>
  );
};

export default DashboardCard;
