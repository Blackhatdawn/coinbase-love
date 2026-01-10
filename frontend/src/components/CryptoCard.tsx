import { TrendingUp, TrendingDown } from "lucide-react";

interface CryptoCardProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  marketCap: string;
  volume: string;
  icon: string;
  index: number;
}

const CryptoCard = ({ symbol, name, price, change, marketCap, volume, icon, index }: CryptoCardProps) => {
  const isPositive = change >= 0;

  return (
    <div 
      className="glass-card p-5 hover:border-primary/50 transition-all duration-300 cursor-pointer group animate-slide-up"
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-3xl">{icon}</div>
          <div>
            <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
              {symbol}
            </h3>
            <p className="text-sm text-muted-foreground">{name}</p>
          </div>
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-md text-sm font-medium ${
          isPositive 
            ? 'bg-success/10 text-success' 
            : 'bg-destructive/10 text-destructive'
        }`}>
          {isPositive ? (
            <TrendingUp className="h-3 w-3" />
          ) : (
            <TrendingDown className="h-3 w-3" />
          )}
          {isPositive ? '+' : ''}{change.toFixed(2)}%
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-baseline gap-2">
          <span className="font-display text-2xl font-bold">
            ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>MCap: {marketCap}</span>
          <span>Vol: {volume}</span>
        </div>
      </div>

      {/* Mini Chart Placeholder */}
      <div className="mt-4 h-12 flex items-end gap-0.5">
        {Array.from({ length: 20 }).map((_, i) => {
          const height = Math.random() * 100;
          return (
            <div
              key={i}
              className={`flex-1 rounded-t transition-all duration-300 ${
                isPositive ? 'bg-success/40 group-hover:bg-success' : 'bg-destructive/40 group-hover:bg-destructive'
              }`}
              style={{ height: `${height}%` }}
            />
          );
        })}
      </div>
    </div>
  );
};

export default CryptoCard;
