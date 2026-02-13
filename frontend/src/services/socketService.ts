/**
 * Socket.IO Service for Real-time Communication
 * 
 * Enterprise Features:
 * - Auto-reconnection with exponential backoff
 * - Heartbeat/ping-pong for connection health
 * - Event-based messaging with type safety
 * - Room subscriptions for targeted updates
 * - Credential-based authentication
 * - Transport fallback (WebSocket → Polling)
 * 
 * @version 2.0.0
 */

import { io, Socket, ManagerOptions, SocketOptions } from 'socket.io-client';
import { resolveApiBaseUrl, resolveSocketIoPath, resolveWsBaseUrl } from '@/lib/runtimeConfig';

// Connection configuration constants
const CONNECTION_CONFIG = {
  maxReconnectAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 10000,
  timeout: 30000,
  pingInterval: 25000,
  pingTimeout: 60000,
} as const;

/**
 * Resolve Socket.IO server URL
 * Handles development proxy and production direct connections
 */
const normalizeSocketOrigin = (url: string): string => {
  if (!url) {
    return '';
  }

  // Socket.IO client expects an HTTP(S) origin URL. Convert ws schemes safely.
  if (url.startsWith('wss://')) {
    return `https://${url.slice('wss://'.length)}`;
  }
  if (url.startsWith('ws://')) {
    return `http://${url.slice('ws://'.length)}`;
  }

  return url.replace(/\/+$/, '');
};

const getSocketURL = (): string => {
  const wsBaseUrl = normalizeSocketOrigin(resolveWsBaseUrl());
  const apiUrl = normalizeSocketOrigin(resolveApiBaseUrl());

  // In development with proxy, use current origin.
  if (!wsBaseUrl && !apiUrl) {
    if (typeof window !== 'undefined') {
      return window.location.origin;
    }
    return '';
  }

  // Prefer explicit WS base URL when provided by backend runtime config.
  return wsBaseUrl || apiUrl;
};

/**
 * Connection state for external monitoring
 */
export interface ConnectionStatus {
  connected: boolean;
  authenticated: boolean;
  transport: 'websocket' | 'polling' | null;
  reconnectAttempts: number;
  lastPing: Date | null;
}

class SocketService {
  private socket: Socket | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private currentToken: string | null = null;
  private eventHandlers: Map<string, Set<Function>> = new Map();
  private lastPing: Date | null = null;
  private connectionStatus: ConnectionStatus = {
    connected: false,
    authenticated: false,
    transport: null,
    reconnectAttempts: 0,
    lastPing: null,
  };
  
  /**
   * Initialize Socket.IO connection with optional authentication token
   * 
   * @param token - JWT token for authenticated connections
   * @returns Socket instance
   */
  connect(token?: string): Socket {
    if (this.socket?.connected) {
      console.log('[Socket] Already connected');
      return this.socket;
    }
    
    if (this.isConnecting) {
      console.log('[Socket] Connection in progress...');
      return this.socket!;
    }
    
    this.isConnecting = true;
    this.currentToken = token || null;
    
    const socketURL = getSocketURL();
    const socketPath = resolveSocketIoPath();
    
    console.log(`[Socket] Connecting to ${socketURL}${socketPath}`);
    
    // Socket.IO client options optimized for production
    const socketOptions: Partial<ManagerOptions & SocketOptions> = {
      // Connection path
      path: socketPath,
      
      // Transport configuration - WebSocket preferred, polling fallback
      transports: ['websocket', 'polling'],
      upgrade: true,  // Allow transport upgrades
      
      // Reconnection settings with exponential backoff
      reconnection: true,
      reconnectionDelay: CONNECTION_CONFIG.reconnectionDelay,
      reconnectionDelayMax: CONNECTION_CONFIG.reconnectionDelayMax,
      reconnectionAttempts: CONNECTION_CONFIG.maxReconnectAttempts,
      
      // Timeout settings
      timeout: CONNECTION_CONFIG.timeout,
      
      // CRITICAL: Enable credentials for cross-origin cookie auth
      withCredentials: true,
      
      // Auto connect on creation
      autoConnect: true,
      
      // Force new connection on reconnect (prevents stale connections)
      forceNew: false,
      
      // Authentication token (if provided)
      auth: token ? { token } : undefined,
      
      // Extra headers for CORS
      extraHeaders: {
        'X-Client-Version': '2.0.0',
      },
    };
    
    this.socket = io(socketURL, socketOptions);
    
    this.setupEventHandlers();
    
    return this.socket;
  }
  
  /**
   * Setup Socket.IO event handlers with enhanced logging and transport tracking
   */
  private setupEventHandlers() {
    if (!this.socket) return;
    
    // Connection events
    this.socket.on('connect', () => {
      const transport = this.socket?.io.engine?.transport?.name || 'unknown';
      console.log(`[Socket] ✅ Connected successfully via ${transport}`);
      
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.connectionStatus.connected = true;
      this.connectionStatus.transport = transport as 'websocket' | 'polling';
      this.connectionStatus.reconnectAttempts = 0;
      
      this.emit('connection', { 
        status: 'connected', 
        transport,
        socketId: this.socket?.id 
      });
    });
    
    // Track transport upgrades (polling → websocket)
    this.socket.io.engine?.on('upgrade', (transport) => {
      console.log(`[Socket] ⬆️ Transport upgraded to ${transport.name}`);
      this.connectionStatus.transport = transport.name as 'websocket' | 'polling';
      this.emit('transport_upgrade', { transport: transport.name });
    });
    
    this.socket.on('disconnect', (reason) => {
      console.log(`[Socket] 🔴 Disconnected: ${reason}`);
      this.isConnecting = false;
      this.connectionStatus.connected = false;
      this.connectionStatus.authenticated = false;
      this.connectionStatus.transport = null;
      
      // Handle specific disconnect reasons
      const shouldReconnect = reason !== 'io server disconnect' && reason !== 'io client disconnect';
      
      this.emit('connection', { 
        status: 'disconnected', 
        reason,
        willReconnect: shouldReconnect 
      });
    });
    
    this.socket.on('connect_error', (error) => {
      console.error('[Socket] ❌ Connection error:', error.message);
      this.reconnectAttempts++;
      this.connectionStatus.reconnectAttempts = this.reconnectAttempts;
      
      // Log transport fallback info
      const currentTransport = this.socket?.io.engine?.transport?.name;
      if (currentTransport === 'polling') {
        console.log('[Socket] ℹ️ Using HTTP polling (WebSocket may be blocked)');
      }
      
      if (this.reconnectAttempts >= CONNECTION_CONFIG.maxReconnectAttempts) {
        console.log('[Socket] Max reconnection attempts reached');
        this.emit('connection', { 
          status: 'failed', 
          error: error.message,
          attempts: this.reconnectAttempts 
        });
      }
    });
    
    this.socket.on('reconnect', (attemptNumber) => {
      const transport = this.socket?.io.engine?.transport?.name || 'unknown';
      console.log(`[Socket] 🔄 Reconnected after ${attemptNumber} attempts via ${transport}`);
      this.reconnectAttempts = 0;
      this.connectionStatus.connected = true;
      this.connectionStatus.transport = transport as 'websocket' | 'polling';
      this.connectionStatus.reconnectAttempts = 0;
      this.emit('connection', { status: 'reconnected', attempts: attemptNumber });
    });
    
    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[Socket] 🔄 Reconnection attempt ${attemptNumber}/${CONNECTION_CONFIG.maxReconnectAttempts}`);
      this.connectionStatus.reconnectAttempts = attemptNumber;
    });
    
    this.socket.on('reconnect_error', (error) => {
      console.error('[Socket] ❌ Reconnection error:', error.message);
    });
    
    this.socket.on('reconnect_failed', () => {
      console.error('[Socket] ❌ Reconnection failed after all attempts');
      this.connectionStatus.connected = false;
      this.emit('connection', { 
        status: 'failed', 
        error: 'Reconnection failed',
        attempts: this.reconnectAttempts 
      });
    });
    
    // Server events
    this.socket.on('connected', (data) => {
      console.log('[Socket] Server welcome:', data);
    });
    
    this.socket.on('authenticated', (data) => {
      console.log('[Socket] ✅ Authenticated:', data);
      this.emit('authenticated', data);
    });
    
    this.socket.on('auth_error', (data) => {
      console.error('[Socket] ❌ Authentication error:', data);
      this.emit('auth_error', data);
    });
    
    // Subscription events
    this.socket.on('subscribed', (data) => {
      console.log('[Socket] ✅ Subscribed to channels:', data.channels);
      this.emit('subscribed', data);
    });
    
    this.socket.on('unsubscribed', (data) => {
      console.log('[Socket] ✅ Unsubscribed from channels:', data.channels);
      this.emit('unsubscribed', data);
    });
    
    // Ping-pong for connection health
    this.socket.on('pong', (data) => {
      this.emit('pong', data);
    });
    
    // Application events
    this.socket.on('price_update', (data) => {
      this.emit('price_update', data);
    });
    
    this.socket.on('notification', (data) => {
      this.emit('notification', data);
    });
    
    this.socket.on('order_update', (data) => {
      this.emit('order_update', data);
    });
  }
  
  /**
   * Authenticate with user credentials
   */
  authenticate(userId: string, token: string) {
    if (!this.socket?.connected) {
      console.warn('[Socket] Not connected, cannot authenticate');
      return;
    }
    
    console.log(`[Socket] Authenticating user ${userId}...`);
    this.socket.emit('authenticate', { user_id: userId, token });
  }
  
  /**
   * Subscribe to channels
   */
  subscribe(channels: string[]) {
    if (!this.socket?.connected) {
      console.warn('[Socket] Not connected, cannot subscribe');
      return;
    }
    
    console.log('[Socket] Subscribing to channels:', channels);
    this.socket.emit('subscribe', { channels });
  }
  
  /**
   * Unsubscribe from channels
   */
  unsubscribe(channels: string[]) {
    if (!this.socket?.connected) {
      console.warn('[Socket] Not connected, cannot unsubscribe');
      return;
    }
    
    console.log('[Socket] Unsubscribing from channels:', channels);
    this.socket.emit('unsubscribe', { channels });
  }
  
  /**
   * Send ping to server
   */
  ping() {
    if (!this.socket?.connected) {
      return;
    }
    
    this.socket.emit('ping');
  }
  
  /**
   * Register event handler
   */
  on(event: string, handler: Function) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    
    this.eventHandlers.get(event)!.add(handler);
  }
  
  /**
   * Unregister event handler
   */
  off(event: string, handler: Function) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }
  
  /**
   * Emit event to local handlers
   */
  private emit(event: string, data: any) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`[Socket] Handler error for ${event}:`, error);
        }
      });
    }
  }
  
  /**
   * Disconnect socket
   */
  disconnect() {
    if (this.socket) {
      console.log('[Socket] Disconnecting...');
      this.socket.disconnect();
      this.socket = null;
      this.isConnecting = false;
    }
  }
  
  /**
   * Check if socket is connected
   */
  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
  
  /**
   * Get socket instance
   */
  getSocket(): Socket | null {
    return this.socket;
  }
  
  /**
   * Get current connection status
   */
  getConnectionStatus(): ConnectionStatus {
    return { ...this.connectionStatus };
  }
  
  /**
   * Get current transport type (websocket or polling)
   */
  getTransport(): 'websocket' | 'polling' | null {
    if (!this.socket?.connected) return null;
    return (this.socket.io.engine?.transport?.name || null) as 'websocket' | 'polling' | null;
  }
  
  /**
   * Update authentication token for existing connection
   */
  updateToken(token: string) {
    this.currentToken = token;
    if (this.socket) {
      this.socket.auth = { token };
    }
  }
}

// Export singleton instance
export const socketService = new SocketService();
