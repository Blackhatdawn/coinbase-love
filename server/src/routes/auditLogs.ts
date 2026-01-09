import { Router, Response } from 'express';
import { authMiddleware, AuthRequest } from '@/middleware/auth';
import {
  getUserAuditLogs,
  getAuditLogSummary,
  exportAuditLogsCSV,
  AuditAction,
} from '@/utils/auditLog';
import { asyncHandler } from '@/middleware/security';

const router = Router();

// ============================================================================
// GET AUDIT LOGS - Retrieve user's audit log history
// ============================================================================
router.get(
  '/',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const limit = Math.min(parseInt(req.query.limit as string) || 50, 500);
    const offset = parseInt(req.query.offset as string) || 0;
    const action = req.query.action as string | undefined;

    const logs = await getUserAuditLogs(req.user.id, limit, offset, action as AuditAction);

    res.json({
      logs,
      limit,
      offset,
      message: `Retrieved ${logs.length} audit log entries`,
    });
  })
);

// ============================================================================
// GET AUDIT SUMMARY - Get counts of different actions
// ============================================================================
router.get(
  '/summary',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const days = Math.min(parseInt(req.query.days as string) || 30, 365);
    const summary = await getAuditLogSummary(req.user.id, days);

    // Format response
    const actionCounts: Record<string, any> = {};
    summary.forEach((row: any) => {
      const key = `${row.action}_${row.status}`;
      actionCounts[key] = row.count;
    });

    res.json({
      summary: actionCounts,
      days,
      message: `Audit log summary for last ${days} days`,
    });
  })
);

// ============================================================================
// EXPORT AUDIT LOGS - Export audit logs as CSV
// ============================================================================
router.get(
  '/export',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const days = Math.min(parseInt(req.query.days as string) || 90, 365);

    const csvContent = await exportAuditLogsCSV(req.user.id, days);

    // Set response headers for CSV download
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename="audit_logs_${new Date().toISOString().slice(0, 10)}.csv"`
    );

    res.send(csvContent);
  })
);

// ============================================================================
// GET AUDIT LOG DETAIL - Get a specific audit log entry
// ============================================================================
router.get(
  '/:id',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { id } = req.params;

    // TODO: Implement get single log endpoint
    // Verify user owns this log entry before returning

    res.json({
      message: 'Audit log detail endpoint',
      id,
    });
  })
);

export default router;
