import { Router, Response } from 'express';
import { query } from '@/config/database';
import { authMiddleware, AuthRequest } from '@/middleware/auth';
import { addHoldingSchema } from '@/utils/validation';
import { getCryptoPrice } from '@/utils/cryptoApi';

const router = Router();

// Get user portfolio
router.get('/', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    // Get portfolio
    const portfolioResult = await query(
      'SELECT id, total_balance FROM portfolios WHERE user_id = $1',
      [req.user?.id]
    );

    if (portfolioResult.rows.length === 0) {
      return res.status(404).json({ error: 'Portfolio not found' });
    }

    const portfolio = portfolioResult.rows[0];

    // Get holdings
    const holdingsResult = await query(
      'SELECT symbol, name, amount, value FROM holdings WHERE portfolio_id = $1 ORDER BY value DESC',
      [portfolio.id]
    );

    // Calculate allocation percentages
    const holdings = holdingsResult.rows.map((h: any) => ({
      symbol: h.symbol,
      name: h.name,
      amount: parseFloat(h.amount),
      value: parseFloat(h.value),
      allocation: portfolio.total_balance > 0 ? (parseFloat(h.value) / parseFloat(portfolio.total_balance)) * 100 : 0,
    }));

    res.json({
      portfolio: {
        id: portfolio.id,
        totalBalance: parseFloat(portfolio.total_balance),
        holdings,
      },
    });
  } catch (error) {
    console.error('Error fetching portfolio:', error);
    res.status(500).json({ error: 'Failed to fetch portfolio' });
  }
});

// Get specific holding
router.get('/holding/:symbol', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const { symbol } = req.params;

    const result = await query(
      `SELECT h.* FROM holdings h
       JOIN portfolios p ON h.portfolio_id = p.id
       WHERE p.user_id = $1 AND h.symbol = $2`,
      [req.user?.id, symbol.toUpperCase()]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Holding not found' });
    }

    const holding = result.rows[0];
    res.json({
      holding: {
        symbol: holding.symbol,
        name: holding.name,
        amount: parseFloat(holding.amount),
        value: parseFloat(holding.value),
      },
    });
  } catch (error) {
    console.error('Error fetching holding:', error);
    res.status(500).json({ error: 'Failed to fetch holding' });
  }
});

// Add or update holding
router.post('/holding', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const { symbol, name, amount } = addHoldingSchema.parse(req.body);

    // Get user's portfolio
    const portfolioResult = await query(
      'SELECT id, total_balance FROM portfolios WHERE user_id = $1',
      [req.user?.id]
    );

    if (portfolioResult.rows.length === 0) {
      return res.status(404).json({ error: 'Portfolio not found' });
    }

    const portfolio = portfolioResult.rows[0];

    // Check if holding exists
    const existingResult = await query(
      'SELECT id FROM holdings WHERE portfolio_id = $1 AND symbol = $2',
      [portfolio.id, symbol.toUpperCase()]
    );

    // Fetch live price from CoinGecko API
    const priceData = await getCryptoPrice(symbol.toUpperCase());
    if (!priceData) {
      return res.status(400).json({ error: 'Cryptocurrency price not found. Please use a valid symbol (BTC, ETH, SOL, etc.)' });
    }
    const price = priceData.price;
    const value = amount * price;

    if (existingResult.rows.length > 0) {
      // Update existing holding
      await query(
        'UPDATE holdings SET amount = $1, value = $2, updated_at = CURRENT_TIMESTAMP WHERE portfolio_id = $3 AND symbol = $4',
        [amount, value, portfolio.id, symbol.toUpperCase()]
      );
    } else {
      // Create new holding
      await query(
        'INSERT INTO holdings (portfolio_id, symbol, name, amount, value) VALUES ($1, $2, $3, $4, $5)',
        [portfolio.id, symbol.toUpperCase(), name, amount, value]
      );
    }

    // Update portfolio balance
    const balanceResult = await query(
      'SELECT SUM(value) as total FROM holdings WHERE portfolio_id = $1',
      [portfolio.id]
    );

    const newBalance = parseFloat(balanceResult.rows[0]?.total || 0);
    await query(
      'UPDATE portfolios SET total_balance = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
      [newBalance, portfolio.id]
    );

    res.json({
      message: 'Holding updated successfully',
      holding: {
        symbol: symbol.toUpperCase(),
        name,
        amount,
        value,
      },
    });
  } catch (error: any) {
    if (error.name === 'ZodError') {
      return res.status(400).json({ error: error.errors[0].message });
    }
    console.error('Error updating holding:', error);
    res.status(500).json({ error: 'Failed to update holding' });
  }
});

// Delete holding
router.delete('/holding/:symbol', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const { symbol } = req.params;

    const portfolioResult = await query(
      'SELECT id FROM portfolios WHERE user_id = $1',
      [req.user?.id]
    );

    if (portfolioResult.rows.length === 0) {
      return res.status(404).json({ error: 'Portfolio not found' });
    }

    await query(
      'DELETE FROM holdings WHERE portfolio_id = $1 AND symbol = $2',
      [portfolioResult.rows[0].id, symbol.toUpperCase()]
    );

    res.json({ message: 'Holding deleted successfully' });
  } catch (error) {
    console.error('Error deleting holding:', error);
    res.status(500).json({ error: 'Failed to delete holding' });
  }
});

export default router;
