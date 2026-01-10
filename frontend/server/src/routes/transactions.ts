import { Router, Response } from 'express';
import { query } from '@/config/database';
import { authMiddleware, AuthRequest } from '@/middleware/auth';

const router = Router();

// Get all transactions for user
router.get('/', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const limit = Math.min(parseInt(req.query.limit as string) || 50, 100);
    const offset = parseInt(req.query.offset as string) || 0;

    const result = await query(
      `SELECT id, transaction_type, amount, symbol, description, status, created_at
       FROM transactions
       WHERE user_id = $1
       ORDER BY created_at DESC
       LIMIT $2 OFFSET $3`,
      [req.user?.id, limit, offset]
    );

    const countResult = await query(
      'SELECT COUNT(*) as count FROM transactions WHERE user_id = $1',
      [req.user?.id]
    );

    const transactions = result.rows.map((t: any) => ({
      id: t.id,
      type: t.transaction_type,
      amount: parseFloat(t.amount),
      symbol: t.symbol,
      description: t.description,
      status: t.status,
      createdAt: t.created_at,
    }));

    res.json({
      transactions,
      count: transactions.length,
      total: parseInt(countResult.rows[0].count),
    });
  } catch (error) {
    console.error('Error fetching transactions:', error);
    res.status(500).json({ error: 'Failed to fetch transactions' });
  }
});

// Get specific transaction
router.get('/:id', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const result = await query(
      `SELECT id, transaction_type, amount, symbol, description, status, created_at
       FROM transactions
       WHERE id = $1 AND user_id = $2`,
      [id, req.user?.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Transaction not found' });
    }

    const transaction = result.rows[0];
    res.json({
      transaction: {
        id: transaction.id,
        type: transaction.transaction_type,
        amount: parseFloat(transaction.amount),
        symbol: transaction.symbol,
        description: transaction.description,
        status: transaction.status,
        createdAt: transaction.created_at,
      },
    });
  } catch (error) {
    console.error('Error fetching transaction:', error);
    res.status(500).json({ error: 'Failed to fetch transaction' });
  }
});

// Create transaction (internal use)
router.post('/', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const { type, amount, symbol, description } = req.body;

    if (!type || !amount) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const result = await query(
      `INSERT INTO transactions (user_id, transaction_type, amount, symbol, description, status)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING id, transaction_type, amount, symbol, description, status, created_at`,
      [req.user?.id, type, amount, symbol || null, description || null, 'completed']
    );

    const transaction = result.rows[0];
    res.status(201).json({
      transaction: {
        id: transaction.id,
        type: transaction.transaction_type,
        amount: parseFloat(transaction.amount),
        symbol: transaction.symbol,
        description: transaction.description,
        status: transaction.status,
        createdAt: transaction.created_at,
      },
    });
  } catch (error) {
    console.error('Error creating transaction:', error);
    res.status(500).json({ error: 'Failed to create transaction' });
  }
});

// Get transaction statistics
router.get('/stats/overview', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
    const result = await query(
      `SELECT 
        transaction_type,
        COUNT(*) as count,
        SUM(amount) as total_amount
       FROM transactions
       WHERE user_id = $1
       GROUP BY transaction_type`,
      [req.user?.id]
    );

    const stats: { [key: string]: any } = {};
    result.rows.forEach((row: any) => {
      stats[row.transaction_type] = {
        count: parseInt(row.count),
        totalAmount: parseFloat(row.total_amount || 0),
      };
    });

    res.json({ stats });
  } catch (error) {
    console.error('Error fetching transaction stats:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

export default router;
