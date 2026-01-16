/**
 * LivePriceDisplay Component
 * Displays animated cryptocurrency prices from WebSocket stream
 * Shows price changes with color animation (green up, red down)
 */

import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LivePriceDisplayProps {
  symbol: string;
  price: string | number;
  previousPrice?: string | number;
  showSymbol?: boolean;
  className?: string;
  animationDuration?: number;
}

export function LivePriceDisplay({
  symbol,
  price,
  previousPrice,
  showSymbol = true,
  className = '',
  animationDuration = 500,
}: LivePriceDisplayProps) {
  const [displayPrice, setDisplayPrice] = useState<string | number>(price);
  const [priceChange, setPriceChange] = useState<'up' | 'down' | null>(null);
  const [isFlashing, setIsFlashing] = useState(false);

  useEffect(() => {
    const currentPrice = parseFloat(String(price));
    const prevPrice = previousPrice ? parseFloat(String(previousPrice)) : null;

    // Determine if price went up or down
    if (prevPrice !== null && prevPrice !== currentPrice) {
      setPriceChange(currentPrice > prevPrice ? 'up' : 'down');
      setIsFlashing(true);

      // Reset animation state after duration
      const timeout = setTimeout(() => {
        setIsFlashing(false);
      }, animationDuration);

      return () => clearTimeout(timeout);
    }

    setDisplayPrice(price);
  }, [price, previousPrice, animationDuration]);

  const formatPrice = (value: string | number): string => {
    const num = parseFloat(String(value));

    if (num >= 1000) {
      return num.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    } else if (num >= 1) {
      return num.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 4,
      });
    } else {
      return num.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 4,
        maximumFractionDigits: 8,
      });
    }
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Price Display */}
      <span
        className={cn(
          'font-mono font-semibold transition-all duration-300',
          isFlashing && priceChange === 'up' && 'text-green-400 animate-pulse',
          isFlashing && priceChange === 'down' && 'text-red-400 animate-pulse'
        )}
      >
        {formatPrice(displayPrice)}
      </span>

      {/* Symbol Badge */}
      {showSymbol && (
        <span className="text-sm font-medium text-muted-foreground">
          {symbol.toUpperCase()}
        </span>
      )}

      {/* Change Indicator */}
      {isFlashing && priceChange && (
        <div
          className={cn(
            'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold transition-all',
            priceChange === 'up'
              ? 'text-green-400 bg-green-500/10 animate-bounce'
              : 'text-red-400 bg-red-500/10 animate-bounce'
          )}
        >
          {priceChange === 'up' ? (
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
}

export default LivePriceDisplay;
