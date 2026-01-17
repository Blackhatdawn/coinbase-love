/**
 * Socket.IO Service for Real-time Communication
 * Features:
 * - Auto-reconnection with exponential backoff
 * - Heartbeat/ping-pong for connection health
 * - Event-based messaging
 * - Room subscriptions
 */

import { io, Socket } from 'socket.io-client';

// Get backend URL from environment
const getSocketURL = () => {
  const apiUrl = import.meta.env.VITE_API_BASE_URL || '';
  
  // In development, use proxy
  if (!apiUrl || apiUrl === '') {
    return window.location.origin;
  }
  
  return apiUrl;
};

class SocketService {
  private socket: Socket | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private eventHandlers: Map<string, Set<Function>> = new Map();
  
  /**
   * Initialize Socket.IO connection
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
    
    const socketURL = getSocketURL();
    console.log(`[Socket] Connecting to ${socketURL}/socket.io/`);
    
    this.socket = io(socketURL, {
      path: '/socket.io/',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
      timeout: 20000,
      autoConnect: true,
      auth: token ? { token } : undefined,
    });
    
    this.setupEventHandlers();
    
    return this.socket;
  }
  
  /**
   * Setup Socket.IO event handlers
   */
  private setupEventHandlers() {
    if (!this.socket) return;
    
    // Connection events
    this.socket.on('connect', () => {
      console.log('[Socket] ✅ Connected successfully');
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.emit('connection', { status: 'connected' });
    });
    
    this.socket.on('disconnect', (reason) => {
      console.log(`[Socket] 🔴 Disconnected: ${reason}`);
      this.isConnecting = false;
      this.emit('connection', { status: 'disconnected', reason });
    });
    
    this.socket.on('connect_error', (error) => {
      console.error('[Socket] ❌ Connection error:', error.message);
      this.reconnectAttempts++;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.log('[Socket] Max reconnection attempts reached');
        this.emit('connection', { status: 'failed', error: error.message });
      }
    });
    
    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`[Socket] 🔄 Reconnected after ${attemptNumber} attempts`);
      this.reconnectAttempts = 0;
      this.emit('connection', { status: 'reconnected' });
    });
    
    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[Socket] 🔄 Reconnection attempt ${attemptNumber}`);
    });
    
    this.socket.on('reconnect_error', (error) => {
      console.error('[Socket] ❌ Reconnection error:', error.message);
    });
    
    this.socket.on('reconnect_failed', () => {
      console.error('[Socket] ❌ Reconnection failed');
      this.emit('connection', { status: 'failed', error: 'Reconnection failed' });
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
}

// Export singleton instance
export const socketService = new SocketService();
