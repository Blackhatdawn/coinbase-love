import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { api } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

interface PriceData {
  symbol: string;
  price: number;
  change24h: number;
  previousPrice?: number;
}

export const LivePriceTicker = () => {
  const [prices, setPrices] = useState<PriceData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const response = await api.crypto.getAll(25);
        const cryptos = response?.cryptocurrencies || [];
        
        const priceData = cryptos.slice(0, 8).map((crypto: any) => ({
          symbol: crypto.symbol?.toUpperCase() || '',
          price: crypto.price || 0,
          change24h: crypto.change_24h || 0,
          previousPrice: prices.find(p => p.symbol === crypto.symbol?.toUpperCase())?.price
        }));
        
        setPrices(priceData);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to fetch prices:', error);
      }
    };

    // Initial fetch
    fetchPrices();
    
    // Update every 3 seconds
    const interval = setInterval(fetchPrices, 3000);
    
    return () => clearInterval(interval);
  }, []);

  if (isLoading || prices.length === 0) {
    return (
      <div className="bg-gradient-to-r from-gray-900/90 via-gray-800/90 to-gray-900/90 backdrop-blur-sm border-y border-gold-500/20 py-2 sm:py-3 overflow-hidden">
        <div className="animate-pulse flex gap-6 sm:gap-8 px-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-2 whitespace-nowrap">
              <div className="h-4 w-12 bg-gold-500/10 rounded" />
              <div className="h-4 w-16 bg-gold-500/10 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Duplicate prices for seamless scrolling
  const duplicatedPrices = [...prices, ...prices, ...prices];

  return (
    <div className="bg-gradient-to-r from-gray-900/90 via-gray-800/90 to-gray-900/90 backdrop-blur-sm border-y border-gold-500/20 py-2 sm:py-3 overflow-hidden relative group">
      <style>{`
        @keyframes scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-33.333%); }
        }
        .ticker-scroll {
          animation: scroll 30s linear infinite;
        }
        .ticker-scroll:hover {
          animation-play-state: paused;
        }
        @keyframes price-flash-up {
          0%, 100% { color: inherit; }
          50% { color: rgb(34, 197, 94); text-shadow: 0 0 8px rgba(34, 197, 94, 0.5); }
        }
        @keyframes price-flash-down {
          0%, 100% { color: inherit; }
          50% { color: rgb(239, 68, 68); text-shadow: 0 0 8px rgba(239, 68, 68, 0.5); }
        }
        .price-up {
          animation: price-flash-up 0.8s ease-in-out;
        }
        .price-down {
          animation: price-flash-down 0.8s ease-in-out;
        }
      `}</style>
      
      <div className="ticker-scroll flex gap-6 sm:gap-8">
        {duplicatedPrices.map((crypto, index) => {
          const isPriceUp = crypto.previousPrice !== undefined && crypto.price > crypto.previousPrice;
          const isPriceDown = crypto.previousPrice !== undefined && crypto.price < crypto.previousPrice;
          
          return (
            <div 
              key={`${crypto.symbol}-${index}`} 
              className="flex items-center gap-3 whitespace-nowrap text-sm font-mono group/item"
            >
              <span className="font-bold text-gold-400 group-hover/item:text-gold-300 transition-colors">
                {crypto.symbol}
              </span>
              <span 
                className={cn(
                  "font-semibold transition-all",
                  isPriceUp && "price-up",
                  isPriceDown && "price-down"
                )}
              >
                ${crypto.price >= 1 
                  ? crypto.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                  : crypto.price.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 6 })
                }
              </span>
              <span className={cn(
                "flex items-center gap-1 text-xs font-semibold",
                crypto.change24h >= 0 ? "text-green-500" : "text-red-500"
              )}>
                {crypto.change24h >= 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {crypto.change24h >= 0 ? '+' : ''}{crypto.change24h.toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>
      
      {/* Fade edges */}
      <div className="absolute inset-y-0 left-0 w-20 bg-gradient-to-r from-gray-900 to-transparent pointer-events-none" />
      <div className="absolute inset-y-0 right-0 w-20 bg-gradient-to-l from-gray-900 to-transparent pointer-events-none" />
    </div>
  );
};

export default LivePriceTicker;