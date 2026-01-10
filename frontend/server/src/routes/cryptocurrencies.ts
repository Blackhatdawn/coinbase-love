import { Router } from 'express';
import { getAllCryptoPrices, getCryptoPrice, getDefaultMarketData } from '@/utils/cryptoApi';

const router = Router();

// Get all cryptocurrencies with market data
router.get('/', async (req, res) => {
  try {
    // Try to fetch live data from CoinGecko
    const cryptoData = await getAllCryptoPrices();

    // If we got data, return it; otherwise fallback to default data
    const data = cryptoData.length > 0 ? cryptoData : getDefaultMarketData();

    res.json({
      data,
      count: data.length,
      cached: cryptoData.length === 0,
    });
  } catch (error) {
    console.error('Error fetching cryptocurrencies:', error);
    
    // Fallback to default market data
    const data = getDefaultMarketData();
    res.json({
      data,
      count: data.length,
      cached: true,
    });
  }
});

// Get specific cryptocurrency
router.get('/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;

    // Try to fetch live data
    const cryptoData = await getCryptoPrice(symbol.toUpperCase());

    if (cryptoData) {
      return res.json({ data: cryptoData });
    }

    // Fallback to default data
    const defaultData = getDefaultMarketData();
    const crypto = defaultData.find((c) => c.symbol === symbol.toUpperCase());

    if (crypto) {
      return res.json({ data: crypto });
    }

    res.status(404).json({ error: 'Cryptocurrency not found' });
  } catch (error) {
    console.error(`Error fetching ${req.params.symbol}:`, error);
    res.status(500).json({ error: 'Failed to fetch cryptocurrency data' });
  }
});

export default router;
