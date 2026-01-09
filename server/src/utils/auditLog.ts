/**
 * Audit Logging Utility
 * Tracks all sensitive operations for compliance and security analysis
 */

import { query } from '@/config/database';
import { Request } from 'express';

/**
 * Audit log entry types
 */
export enum AuditAction {
  // Authentication
  LOGIN = 'login',
  LOGOUT = 'logout',
  SIGNUP = 'signup',
  LOGIN_FAILED = 'login_failed',
  LOGOUT_FAILED = 'logout_failed',

  // Email & Verification
  EMAIL_VERIFICATION_SENT = 'email_verification_sent',
  EMAIL_VERIFIED = 'email_verified',
  EMAIL_VERIFICATION_FAILED = 'email_verification_failed',
  EMAIL_RESENT = 'email_resent',

  // Two-Factor Authentication
  TWO_FA_ENABLED = 'two_fa_enabled',
  TWO_FA_DISABLED = 'two_fa_disabled',
  TWO_FA_VERIFICATION_FAILED = 'two_fa_verification_failed',
  BACKUP_CODES_GENERATED = 'backup_codes_generated',

  // Account Management
  PASSWORD_CHANGED = 'password_changed',
  PASSWORD_CHANGE_FAILED = 'password_change_failed',
  PROFILE_UPDATED = 'profile_updated',

  // Trading Operations
  ORDER_CREATED = 'order_created',
  ORDER_CANCELLED = 'order_cancelled',
  ORDER_FAILED = 'order_failed',

  // Portfolio Operations
  PORTFOLIO_MODIFIED = 'portfolio_modified',
  HOLDING_ADDED = 'holding_added',
  HOLDING_DELETED = 'holding_deleted',

  // Transaction Operations
  TRANSACTION_CREATED = 'transaction_created',
  TRANSACTION_FAILED = 'transaction_failed',

  // Admin Operations
  USER_SUSPENDED = 'user_suspended',
  USER_RESTORED = 'user_restored',
}

/**
 * Resource types being audited
 */
export enum AuditResource {
  USER = 'user',
  AUTH = 'auth',
  ORDER = 'order',
  PORTFOLIO = 'portfolio',
  HOLDING = 'holding',
  TRANSACTION = 'transaction',
  ACCOUNT = 'account',
}

/**
 * Audit log status
 */
export enum AuditStatus {
  SUCCESS = 'success',
  FAILURE = 'failure',
  PENDING = 'pending',
}

/**
 * Log an audit event
 * Call this function whenever a sensitive operation occurs
 */
export const logAuditEvent = async (
  userId: string | null,
  action: AuditAction,
  resource: AuditResource | null,
  resourceId: string | null,
  status: AuditStatus,
  ipAddress: string,
  userAgent: string,
  details: Record<string, any> = {}
): Promise<void> => {
  try {
    // Sanitize details to prevent logging sensitive data
    const sanitizedDetails = sanitizeAuditDetails(details);

    await query(
      `INSERT INTO audit_logs 
       (user_id, action, resource, resource_id, status, ip_address, user_agent, details)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
      [
        userId,
        action,
        resource,
        resourceId,
        status,
        ipAddress,
        userAgent,
        JSON.stringify(sanitizedDetails),
      ]
    );
  } catch (error) {
    // Log errors but don't throw - audit logging failures shouldn't crash the app
    console.error('Failed to log audit event:', error);
  }
};

/**
 * Sanitize audit details to remove sensitive data
 */
function sanitizeAuditDetails(details: Record<string, any>): Record<string, any> {
  const sanitized = { ...details };

  // Remove sensitive fields
  const sensitiveFields = ['password', 'token', 'secret', 'apiKey', 'privateKey', 'seed'];

  sensitiveFields.forEach((field) => {
    if (field in sanitized) {
      sanitized[field] = '[REDACTED]';
    }
  });

  return sanitized;
}

/**
 * Extract client info from request
 */
export const getClientInfo = (req: Request) => {
  const ipAddress = (
    req.headers['x-forwarded-for'] ||
    req.headers['x-real-ip'] ||
    req.socket.remoteAddress ||
    'unknown'
  ) as string;

  const userAgent = req.headers['user-agent'] || 'unknown';

  return { ipAddress, userAgent };
};

/**
 * Fetch audit logs for a user
 */
export const getUserAuditLogs = async (
  userId: string,
  limit: number = 50,
  offset: number = 0,
  action?: AuditAction
) => {
  try {
    let query_str = `
      SELECT id, action, resource, resource_id, status, created_at, details
      FROM audit_logs
      WHERE user_id = $1
    `;

    const params: any[] = [userId];

    if (action) {
      query_str += ` AND action = $${params.length + 1}`;
      params.push(action);
    }

    query_str += ` ORDER BY created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(limit, offset);

    const result = await query(query_str, params);

    return result.rows;
  } catch (error) {
    console.error('Error fetching audit logs:', error);
    return [];
  }
};

/**
 * Get audit log summary (counts by action)
 */
export const getAuditLogSummary = async (userId: string, days: number = 30) => {
  try {
    const result = await query(
      `
      SELECT 
        action,
        status,
        COUNT(*) as count
      FROM audit_logs
      WHERE user_id = $1 
        AND created_at > NOW() - INTERVAL '${days} days'
      GROUP BY action, status
      ORDER BY count DESC
      `,
      [userId]
    );

    return result.rows;
  } catch (error) {
    console.error('Error fetching audit summary:', error);
    return [];
  }
};

/**
 * Get failed login attempts for a user
 * Useful for detecting brute force attempts
 */
export const getFailedLoginAttempts = async (
  userId: string,
  minutesBack: number = 15
) => {
  try {
    const result = await query(
      `
      SELECT COUNT(*) as count
      FROM audit_logs
      WHERE user_id = $1
        AND action = $2
        AND status = $3
        AND created_at > NOW() - INTERVAL '${minutesBack} minutes'
      `,
      [userId, AuditAction.LOGIN_FAILED, AuditStatus.FAILURE]
    );

    return parseInt(result.rows[0]?.count || 0);
  } catch (error) {
    console.error('Error fetching failed login attempts:', error);
    return 0;
  }
};

/**
 * Export audit logs as CSV
 */
export const exportAuditLogsCSV = async (
  userId: string,
  days: number = 90
): Promise<string> => {
  try {
    const result = await query(
      `
      SELECT 
        created_at,
        action,
        resource,
        status,
        ip_address,
        details
      FROM audit_logs
      WHERE user_id = $1
        AND created_at > NOW() - INTERVAL '${days} days'
      ORDER BY created_at DESC
      `,
      [userId]
    );

    // Build CSV
    const headers = ['Timestamp', 'Action', 'Resource', 'Status', 'IP Address', 'Details'];
    const rows = result.rows.map((row: any) => [
      row.created_at,
      row.action,
      row.resource || '',
      row.status,
      row.ip_address,
      JSON.stringify(row.details || {}),
    ]);

    // CSV format
    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    return csvContent;
  } catch (error) {
    console.error('Error exporting audit logs:', error);
    throw error;
  }
};

/**
 * Clean up old audit logs (retention policy)
 * Run periodically (e.g., daily) to maintain database size
 */
export const cleanupOldAuditLogs = async (daysToKeep: number = 365): Promise<number> => {
  try {
    const result = await query(
      `
      DELETE FROM audit_logs
      WHERE created_at < NOW() - INTERVAL '${daysToKeep} days'
      `
    );

    return result.rowCount || 0;
  } catch (error) {
    console.error('Error cleaning up audit logs:', error);
    return 0;
  }
};
