import axios from 'axios';

const COINGECKO_BASE = 'https://api.coingecko.com/api/v3';

const cryptoSymbolMap: { [key: string]: string } = {
  'BTC': 'bitcoin',
  'ETH': 'ethereum',
  'SOL': 'solana',
  'XRP': 'ripple',
  'ADA': 'cardano',
  'DOGE': 'dogecoin',
  'AVAX': 'avalanche-2',
  'DOT': 'polkadot',
  'LINK': 'chainlink',
  'MATIC': 'matic-network',
  'UNI': 'uniswap',
  'ATOM': 'cosmos',
};

export interface CryptoData {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  marketCap: string;
  volume24h: string;
  icon?: string;
}

export const getCryptoPrice = async (symbol: string): Promise<CryptoData | null> => {
  try {
    const coinId = cryptoSymbolMap[symbol.toUpperCase()];
    if (!coinId) return null;

    const response = await axios.get(`${COINGECKO_BASE}/simple/price`, {
      params: {
        ids: coinId,
        vs_currencies: 'usd',
        include_market_cap: true,
        include_24hr_vol: true,
        include_24hr_change: true,
      },
    });

    const data = response.data[coinId];
    if (!data) return null;

    return {
      symbol: symbol.toUpperCase(),
      name: symbol.toUpperCase(),
      price: data.usd,
      change24h: data.usd_24h_change || 0,
      marketCap: formatMarketCap(data.usd_market_cap),
      volume24h: formatVolume(data.usd_24h_vol),
    };
  } catch (error) {
    console.error(`Error fetching price for ${symbol}:`, error);
    return null;
  }
};

export const getAllCryptoPrices = async (): Promise<CryptoData[]> => {
  try {
    const symbols = Object.keys(cryptoSymbolMap);
    const coinIds = symbols.map(s => cryptoSymbolMap[s]).join(',');

    const response = await axios.get(`${COINGECKO_BASE}/simple/price`, {
      params: {
        ids: coinIds,
        vs_currencies: 'usd',
        include_market_cap: true,
        include_24hr_vol: true,
        include_24hr_change: true,
      },
    });

    const results: CryptoData[] = [];
    symbols.forEach((symbol) => {
      const coinId = cryptoSymbolMap[symbol];
      const data = response.data[coinId];
      
      if (data) {
        results.push({
          symbol: symbol.toUpperCase(),
          name: symbol.toUpperCase(),
          price: data.usd,
          change24h: data.usd_24h_change || 0,
          marketCap: formatMarketCap(data.usd_market_cap),
          volume24h: formatVolume(data.usd_24h_vol),
        });
      }
    });

    return results;
  } catch (error) {
    console.error('Error fetching all crypto prices:', error);
    return [];
  }
};

const formatMarketCap = (value: number | null): string => {
  if (!value) return '$0';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
};

const formatVolume = (value: number | null): string => {
  if (!value) return '$0';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toLocaleString()}`;
};

// Default fallback market data (same as frontend)
export const getDefaultMarketData = (): CryptoData[] => [
  { symbol: 'BTC', name: 'Bitcoin', price: 97423.50, change24h: 2.34, marketCap: '$1.9T', volume24h: '$42B', icon: '₿' },
  { symbol: 'ETH', name: 'Ethereum', price: 3456.78, change24h: -1.23, marketCap: '$415B', volume24h: '$18B', icon: 'Ξ' },
  { symbol: 'SOL', name: 'Solana', price: 189.45, change24h: 5.67, marketCap: '$82B', volume24h: '$4.2B', icon: '◎' },
  { symbol: 'XRP', name: 'Ripple', price: 2.34, change24h: 3.21, marketCap: '$134B', volume24h: '$8.1B', icon: '✕' },
  { symbol: 'ADA', name: 'Cardano', price: 0.89, change24h: -0.45, marketCap: '$31B', volume24h: '$890M', icon: '₳' },
  { symbol: 'DOGE', name: 'Dogecoin', price: 0.31, change24h: 4.56, marketCap: '$45B', volume24h: '$2.1B', icon: '🐕' },
  { symbol: 'AVAX', name: 'Avalanche', price: 38.67, change24h: 1.56, marketCap: '$15B', volume24h: '$512M', icon: '🔺' },
  { symbol: 'DOT', name: 'Polkadot', price: 7.23, change24h: -2.34, marketCap: '$10B', volume24h: '$312M', icon: '●' },
  { symbol: 'LINK', name: 'Chainlink', price: 14.89, change24h: 4.12, marketCap: '$8.7B', volume24h: '$623M', icon: '⬡' },
  { symbol: 'MATIC', name: 'Polygon', price: 0.42, change24h: 2.15, marketCap: '$4.2B', volume24h: '$287M', icon: '▲' },
  { symbol: 'UNI', name: 'Uniswap', price: 6.78, change24h: -0.89, marketCap: '$5.1B', volume24h: '$145M', icon: '⬢' },
  { symbol: 'ATOM', name: 'Cosmos', price: 11.34, change24h: 3.45, marketCap: '$3.4B', volume24h: '$89M', icon: '⚛' },
];
