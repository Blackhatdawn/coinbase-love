/**
 * Enhanced Live Price Ticker Component
 * Features: Real-time updates, flash animations, mobile-optimized swipe
 */
import { useEffect, useState, memo } from 'react';
import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { useCryptoData, formatPrice, formatPercentage } from '@/hooks/useCryptoData';
import { cn } from '@/lib/utils';

interface CryptoItem {
  id: string;
  symbol: string;
  name: string;
  price: number;
  change_24h: number;
  image?: string;
}

interface PriceItemProps {
  crypto: CryptoItem;
  prevPrice?: number;
}

// Memoized price item to prevent unnecessary re-renders
const PriceItem = memo(({ crypto, prevPrice }: PriceItemProps) => {
  const [flash, setFlash] = useState<'up' | 'down' | null>(null);
  
  useEffect(() => {
    if (prevPrice !== undefined && prevPrice !== crypto.price) {
      const direction = crypto.price > prevPrice ? 'up' : 'down';
      setFlash(direction);
      const timer = setTimeout(() => setFlash(null), 500);
      return () => clearTimeout(timer);
    }
  }, [crypto.price, prevPrice]);

  return (
    <div
      className={cn(
        'flex items-center gap-2 sm:gap-3 px-3 sm:px-5 py-2.5 whitespace-nowrap',
        'snap-start scroll-ml-4 flex-shrink-0',
        'transition-all duration-500',
        flash === 'up' && 'bg-emerald-500/20',
        flash === 'down' && 'bg-red-500/20'
      )}
      data-testid={`ticker-item-${crypto.symbol}`}
    >
      {/* Coin Icon */}
      {crypto.image && (
        <img 
          src={crypto.image} 
          alt={crypto.name}
          className="h-5 w-5 sm:h-6 sm:w-6 rounded-full"
          loading="lazy"
        />
      )}
      
      {/* Symbol */}
      <span className="font-semibold text-gold-400 text-sm sm:text-base">
        {crypto.symbol}
      </span>
      
      {/* Price with flash effect */}
      <span className={cn(
        'text-xs sm:text-sm font-mono transition-colors duration-300',
        flash === 'up' && 'text-emerald-400',
        flash === 'down' && 'text-red-400',
        !flash && 'text-muted-foreground'
      )}>
        {formatPrice(crypto.price)}
      </span>
      
      {/* Change percentage with arrow */}
      <span className={cn(
        'flex items-center gap-0.5 text-xs sm:text-sm font-medium',
        crypto.change_24h >= 0 ? 'text-emerald-400' : 'text-red-400'
      )}>
        {crypto.change_24h >= 0 ? (
          <TrendingUp className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
        ) : (
          <TrendingDown className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
        )}
        <span className={cn(
          'px-1 py-0.5 rounded text-[10px] sm:text-xs',
          crypto.change_24h >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10'
        )}>
          {formatPercentage(crypto.change_24h)}
        </span>
      </span>
    </div>
  );
});

PriceItem.displayName = 'PriceItem';

const LivePriceTicker = () => {
  const { data, isLoading, error, isRefreshing } = useCryptoData({
    refreshInterval: 15000, // 15 seconds for real-time feel
    autoRefresh: true,
  });

  const [prevPrices, setPrevPrices] = useState<Record<string, number>>({});

  // Track previous prices for flash effect
  useEffect(() => {
    if (data.length > 0) {
      const newPrevPrices: Record<string, number> = {};
      data.forEach(crypto => {
        newPrevPrices[crypto.symbol] = crypto.price;
      });
      
      // Only update after first render
      if (Object.keys(prevPrices).length > 0) {
        setPrevPrices(prev => {
          const updated = { ...prev };
          data.forEach(crypto => {
            updated[crypto.symbol] = prev[crypto.symbol] || crypto.price;
          });
          return updated;
        });
      } else {
        setPrevPrices(newPrevPrices);
      }
    }
  }, [data]);

  // Update previous prices after animation
  useEffect(() => {
    const timer = setTimeout(() => {
      if (data.length > 0) {
        const newPrevPrices: Record<string, number> = {};
        data.forEach(crypto => {
          newPrevPrices[crypto.symbol] = crypto.price;
        });
        setPrevPrices(newPrevPrices);
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [data]);

  // Loading skeleton
  if (isLoading && data.length === 0) {
    return (
      <div className="bg-background/90 border-y border-gold-500/10 backdrop-blur-sm overflow-hidden">
        <div className="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-5 py-2.5 whitespace-nowrap animate-pulse">
              <div className="h-6 w-6 rounded-full bg-gold-500/10" />
              <div className="h-4 w-12 bg-gold-500/10 rounded" />
              <div className="h-4 w-20 bg-gold-500/10 rounded" />
              <div className="h-4 w-14 bg-gold-500/10 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error && data.length === 0) {
    return (
      <div className="bg-red-500/10 border-y border-red-500/20 py-2.5">
        <div className="container mx-auto px-4 flex items-center justify-center gap-3 text-sm">
          <span className="text-red-400">Failed to load prices</span>
          <button
            onClick={() => window.location.reload()}
            className="text-gold-400 hover:text-gold-300 flex items-center gap-1"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-background/90 border-y border-gold-500/10 backdrop-blur-sm overflow-hidden relative">
      {/* Refresh indicator */}
      {isRefreshing && (
        <div className="absolute top-1 right-2 z-20">
          <RefreshCw className="h-3 w-3 animate-spin text-gold-400" />
        </div>
      )}

      {/* Gradient fade edges */}
      <div className="absolute left-0 top-0 bottom-0 w-6 sm:w-12 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-6 sm:w-12 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none" />

      {/* Mobile: Horizontal swipeable */}
      <div className="md:hidden flex overflow-x-auto snap-x snap-mandatory scrollbar-hide scroll-smooth">
        {data.slice(0, 6).map((crypto) => (
          <PriceItem 
            key={crypto.symbol}
            crypto={crypto}
            prevPrice={prevPrices[crypto.symbol]}
          />
        ))}
      </div>

      {/* Desktop: Scrolling animation */}
      <div className="hidden md:flex animate-ticker">
        {[...data, ...data].map((crypto, index) => (
          <PriceItem 
            key={`${crypto.symbol}-${index}`}
            crypto={crypto}
            prevPrice={prevPrices[crypto.symbol]}
          />
        ))}
      </div>

      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-ticker {
          animation: ticker 40s linear infinite;
        }
        .animate-ticker:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};

export default LivePriceTicker;
