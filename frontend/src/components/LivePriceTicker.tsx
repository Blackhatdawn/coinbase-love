/**
 * Enhanced Live Price Ticker Component
 * Features: Real-time WebSocket updates, flash animations, mobile-optimized swipe
 * Now uses usePriceWebSocket for zero-latency price updates
 */
import { useEffect, useState, memo } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { usePriceWebSocket } from '@/hooks/usePriceWebSocket';
import { cn } from '@/lib/utils';

interface CryptoItem {
  symbol: string;
  name: string;
  price: number;
  image?: string;
}

interface PriceItemProps {
  crypto: CryptoItem;
  currentPrice: string | number;
  prevPrice?: string | number;
}

// Memoized price item to prevent unnecessary re-renders
const PriceItem = memo(({ crypto, currentPrice, prevPrice }: PriceItemProps) => {
  const [flash, setFlash] = useState<'up' | 'down' | null>(null);

  useEffect(() => {
    if (prevPrice !== undefined && prevPrice !== currentPrice) {
      const curr = parseFloat(String(currentPrice));
      const prev = parseFloat(String(prevPrice));
      const direction = curr > prev ? 'up' : 'down';
      setFlash(direction);
      const timer = setTimeout(() => setFlash(null), 500);
      return () => clearTimeout(timer);
    }
  }, [currentPrice, prevPrice]);

  const formatPrice = (price: string | number): string => {
    const num = parseFloat(String(price));
    if (num >= 1000) {
      return num.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    } else if (num >= 1) {
      return num.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 4
      });
    } else {
      return num.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 4,
        maximumFractionDigits: 8
      });
    }
  };

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
        {formatPrice(currentPrice)}
      </span>

      {/* Live indicator */}
      {flash && (
        <div className={cn(
          'flex items-center gap-0.5 text-xs font-bold uppercase tracking-wider px-1.5 py-0.5 rounded',
          flash === 'up'
            ? 'text-emerald-400 bg-emerald-500/20'
            : 'text-red-400 bg-red-500/20'
        )}>
          {flash === 'up' ? (
            <>
              <TrendingUp className="h-3 w-3" />
              <span>↑</span>
            </>
          ) : (
            <>
              <TrendingDown className="h-3 w-3" />
              <span>↓</span>
            </>
          )}
        </div>
      )}
    </div>
  );
});

PriceItem.displayName = 'PriceItem';

interface TopCryptoData {
  symbol: string;
  name: string;
  image?: string;
}

const TOP_CRYPTOS: TopCryptoData[] = [
  { symbol: 'bitcoin', name: 'Bitcoin', image: '/assets/placeholder.svg' },
  { symbol: 'ethereum', name: 'Ethereum', image: '/assets/placeholder.svg' },
  { symbol: 'cardano', name: 'Cardano', image: '/assets/placeholder.svg' },
  { symbol: 'dogecoin', name: 'Dogecoin', image: '/assets/placeholder.svg' },
  { symbol: 'ripple', name: 'Ripple', image: '/assets/placeholder.svg' },
  { symbol: 'litecoin', name: 'Litecoin', image: '/assets/placeholder.svg' },
];

const LivePriceTicker = () => {
  const { prices, status } = usePriceWebSocket();
  const [prevPrices, setPrevPrices] = useState<Record<string, string | number>>({});

  // Track previous prices for animation effect
  useEffect(() => {
    const timer = setTimeout(() => {
      setPrevPrices(prices);
    }, 600);
    return () => clearTimeout(timer);
  }, [prices]);

  // Loading skeleton
  if (!status.isConnected && Object.keys(prices).length === 0) {
    return (
      <div className="bg-background/90 border-y border-gold-500/10 backdrop-blur-sm overflow-hidden">
        <div className="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-5 py-2.5 whitespace-nowrap animate-pulse">
              <div className="h-6 w-6 rounded-full bg-gold-500/10" />
              <div className="h-4 w-12 bg-gold-500/10 rounded" />
              <div className="h-4 w-20 bg-gold-500/10 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-background/90 border-y border-gold-500/10 backdrop-blur-sm overflow-hidden relative">
      {/* Live indicator badge */}
      {status.isConnected && (
        <div className="absolute top-1 right-3 z-20 flex items-center gap-1.5">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-bold text-green-400 uppercase">Live</span>
        </div>
      )}

      {/* Gradient fade edges */}
      <div className="absolute left-0 top-0 bottom-0 w-6 sm:w-12 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-6 sm:w-12 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none" />

      {/* Mobile: Horizontal swipeable */}
      <div className="md:hidden flex overflow-x-auto snap-x snap-mandatory scrollbar-hide scroll-smooth">
        {TOP_CRYPTOS.slice(0, 6).map((crypto) => {
          const currentPrice = prices[crypto.symbol] || '0';
          const prevPrice = prevPrices[crypto.symbol];
          return (
            <PriceItem
              key={crypto.symbol}
              crypto={crypto}
              currentPrice={currentPrice}
              prevPrice={prevPrice}
            />
          );
        })}
      </div>

      {/* Desktop: Scrolling animation */}
      <div className="hidden md:flex animate-ticker">
        {[...TOP_CRYPTOS, ...TOP_CRYPTOS].map((crypto, index) => {
          const currentPrice = prices[crypto.symbol] || '0';
          const prevPrice = prevPrices[crypto.symbol];
          return (
            <PriceItem
              key={`${crypto.symbol}-${index}`}
              crypto={crypto}
              currentPrice={currentPrice}
              prevPrice={prevPrice}
            />
          );
        })}
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
