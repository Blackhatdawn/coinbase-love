import { Router, Response } from 'express';
import { query, getClient } from '@/config/database';
import { authMiddleware, AuthRequest } from '@/middleware/auth';
import { createOrderSchema } from '@/utils/validation';

const router = Router();

// Get all orders for user
router.get('/', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const result = await query(
      `SELECT id, trading_pair, order_type, side, amount, price, total, status, created_at
       FROM orders
       WHERE user_id = $1
       ORDER BY created_at DESC`,
      [req.user?.id]
    );

    const orders = result.rows.map((o: any) => ({
      id: o.id,
      tradingPair: o.trading_pair,
      orderType: o.order_type,
      side: o.side,
      amount: parseFloat(o.amount),
      price: parseFloat(o.price),
      total: parseFloat(o.total),
      status: o.status,
      createdAt: o.created_at,
    }));

    res.json({ orders, count: orders.length });
  } catch (error) {
    console.error('Error fetching orders:', error);
    res.status(500).json({ error: 'Failed to fetch orders' });
  }
});

// Create new order
router.post('/', authMiddleware, async (req: AuthRequest, res: Response) => {
  let client;
  try {
    const { trading_pair, order_type, side, amount, price } = createOrderSchema.parse(req.body);

    const total = amount * price;

    // Get database client for transaction
    client = await getClient();

    try {
      // Start transaction
      await client.query('BEGIN');

      // Get user's portfolio to check balance (with row lock)
      const portfolioResult = await client.query(
        'SELECT id, total_balance FROM portfolios WHERE user_id = $1 FOR UPDATE',
        [req.user?.id]
      );

      if (portfolioResult.rows.length === 0) {
        await client.query('ROLLBACK');
        return res.status(404).json({ error: 'Portfolio not found' });
      }

      const portfolio = portfolioResult.rows[0];

      // Check if user has enough balance for buy orders
      if (side === 'buy' && parseFloat(portfolio.total_balance) < total) {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Insufficient balance' });
      }

      // Insert order with 'pending' status
      const orderResult = await client.query(
        `INSERT INTO orders (user_id, trading_pair, order_type, side, amount, price, total, status)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
         RETURNING id, trading_pair, order_type, side, amount, price, total, status, created_at`,
        [req.user?.id, trading_pair, order_type, side, amount, price, total, 'pending']
      );

      const order = orderResult.rows[0];

      // Update portfolio balance for buy orders
      if (side === 'buy') {
        const newBalance = parseFloat(portfolio.total_balance) - total;
        await client.query(
          'UPDATE portfolios SET total_balance = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
          [newBalance, portfolio.id]
        );
      } else if (side === 'sell') {
        // For sell orders, add balance back
        const newBalance = parseFloat(portfolio.total_balance) + total;
        await client.query(
          'UPDATE portfolios SET total_balance = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
          [newBalance, portfolio.id]
        );
      }

      // Commit transaction
      await client.query('COMMIT');

      res.status(201).json({
        message: 'Order created successfully',
        order: {
          id: order.id,
          tradingPair: order.trading_pair,
          orderType: order.order_type,
          side: order.side,
          amount: parseFloat(order.amount),
          price: parseFloat(order.price),
          total: parseFloat(order.total),
          status: order.status,
          createdAt: order.created_at,
        },
      });
    } catch (txError) {
      // Rollback on transaction error
      await client.query('ROLLBACK');
      throw txError;
    }
  } catch (error: any) {
    if (error.name === 'ZodError') {
      return res.status(400).json({ error: error.errors[0].message });
    }
    console.error('Error creating order:', error);
    res.status(500).json({ error: 'Failed to create order' });
  } finally {
    // Release client back to pool
    if (client) {
      client.release();
    }
  }
});

// Get specific order
router.get('/:id', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const result = await query(
      `SELECT id, trading_pair, order_type, side, amount, price, total, status, created_at
       FROM orders
       WHERE id = $1 AND user_id = $2`,
      [id, req.user?.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Order not found' });
    }

    const order = result.rows[0];
    res.json({
      order: {
        id: order.id,
        tradingPair: order.trading_pair,
        orderType: order.order_type,
        side: order.side,
        amount: parseFloat(order.amount),
        price: parseFloat(order.price),
        total: parseFloat(order.total),
        status: order.status,
        createdAt: order.created_at,
      },
    });
  } catch (error) {
    console.error('Error fetching order:', error);
    res.status(500).json({ error: 'Failed to fetch order' });
  }
});

// Cancel order
router.post('/:id/cancel', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const result = await query(
      `UPDATE orders
       SET status = 'cancelled'
       WHERE id = $1 AND user_id = $2 AND status = 'pending'
       RETURNING id, status`,
      [id, req.user?.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Order not found or cannot be cancelled' });
    }

    res.json({ message: 'Order cancelled successfully' });
  } catch (error) {
    console.error('Error cancelling order:', error);
    res.status(500).json({ error: 'Failed to cancel order' });
  }
});

export default router;
