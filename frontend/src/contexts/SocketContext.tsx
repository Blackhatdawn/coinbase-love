/**
 * Socket.IO Context Provider
 * Manages WebSocket connection state and provides hooks for components
 * 
 * Enterprise Features:
 * - Automatic connection with credential-based auth
 * - User authentication via JWT tokens
 * - Transport fallback handling (WebSocket → Polling)
 * - Connection health monitoring
 */

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { Socket } from 'socket.io-client';
import { socketService, ConnectionStatus } from '@/services/socketService';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  isAuthenticated: boolean;
  connectionStatus: ConnectionStatus | null;
  subscribe: (channels: string[]) => void;
  unsubscribe: (channels: string[]) => void;
  on: (event: string, handler: Function) => void;
  off: (event: string, handler: Function) => void;
  reconnect: () => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within SocketProvider');
  }
  return context;
};

interface SocketProviderProps {
  children: ReactNode;
}

export const SocketProvider: React.FC<SocketProviderProps> = ({ children }) => {
  const { user, token } = useAuth();
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  
  // Initialize socket connection
  useEffect(() => {
    console.log('[SocketProvider] Initializing Socket.IO connection...');
    
    const newSocket = socketService.connect(token);
    setSocket(newSocket);
    
    // Connection status handler with enhanced logging
    const handleConnection = (data: any) => {
      if (data.status === 'connected' || data.status === 'reconnected') {
        setIsConnected(true);
        setConnectionStatus(socketService.getConnectionStatus());
        
        const transport = data.transport || socketService.getTransport();
        console.log(`[SocketProvider] Connected via ${transport}`);
        
        // Notify if falling back to polling (might indicate firewall issues)
        if (transport === 'polling') {
          console.warn('[SocketProvider] Using HTTP polling - WebSocket may be blocked');
        }
      } else if (data.status === 'disconnected') {
        setIsConnected(false);
        setIsAuthenticated(false);
        setConnectionStatus(socketService.getConnectionStatus());
        console.log(`[SocketProvider] Disconnected: ${data.reason || 'unknown'}`);
      } else if (data.status === 'failed') {
        setIsConnected(false);
        setConnectionStatus(socketService.getConnectionStatus());
        console.error('[SocketProvider] Connection failed after retries');
      }
    };
    
    // Transport upgrade handler
    const handleTransportUpgrade = (data: any) => {
      console.log(`[SocketProvider] Transport upgraded to ${data.transport}`);
      setConnectionStatus(socketService.getConnectionStatus());
    };
    
    socketService.on('connection', handleConnection);
    socketService.on('transport_upgrade', handleTransportUpgrade);
    
    // Cleanup on unmount
    return () => {
      socketService.off('connection', handleConnection);
      socketService.off('transport_upgrade', handleTransportUpgrade);
      socketService.disconnect();
      setSocket(null);
      setIsConnected(false);
      setIsAuthenticated(false);
      setConnectionStatus(null);
    };
  }, [token]);
  
  // Authenticate when user logs in
  useEffect(() => {
    if (isConnected && user && token && !isAuthenticated) {
      console.log(`[SocketProvider] Authenticating user ${user.id}...`);
      socketService.authenticate(user.id, token);
      
      // Listen for authentication response
      const handleAuthenticated = (data: any) => {
        if (data.success) {
          setIsAuthenticated(true);
          console.log('[SocketProvider] ✅ Authenticated successfully');
          
          // Auto-subscribe to user-specific notifications
          socketService.subscribe(['prices', 'notifications']);
        }
      };
      
      const handleAuthError = (data: any) => {
        console.error('[SocketProvider] ❌ Authentication failed:', data.error);
        toast.error('WebSocket authentication failed');
        setIsAuthenticated(false);
      };
      
      socketService.on('authenticated', handleAuthenticated);
      socketService.on('auth_error', handleAuthError);
      
      return () => {
        socketService.off('authenticated', handleAuthenticated);
        socketService.off('auth_error', handleAuthError);
      };
    }
  }, [isConnected, user, token, isAuthenticated]);
  
  // Handle notifications
  useEffect(() => {
    const handleNotification = (data: any) => {
      console.log('[SocketProvider] 📬 Notification:', data);
      
      // Show toast notification
      if (data.message) {
        const type = data.type || 'info';
        
        switch (type) {
          case 'success':
            toast.success(data.message);
            break;
          case 'error':
            toast.error(data.message);
            break;
          case 'warning':
            toast(data.message, { icon: '⚠️' });
            break;
          default:
            toast(data.message);
        }
      }
    };
    
    socketService.on('notification', handleNotification);
    
    return () => {
      socketService.off('notification', handleNotification);
    };
  }, []);
  
  // Subscribe to channels
  const subscribe = useCallback((channels: string[]) => {
    if (isConnected && isAuthenticated) {
      socketService.subscribe(channels);
    } else {
      console.warn('[SocketProvider] Cannot subscribe: not connected or authenticated');
    }
  }, [isConnected, isAuthenticated]);
  
  // Unsubscribe from channels
  const unsubscribe = useCallback((channels: string[]) => {
    if (isConnected) {
      socketService.unsubscribe(channels);
    }
  }, [isConnected]);
  
  // Register event handler
  const on = useCallback((event: string, handler: Function) => {
    socketService.on(event, handler);
  }, []);
  
  // Unregister event handler
  const off = useCallback((event: string, handler: Function) => {
    socketService.off(event, handler);
  }, []);
  
  // Manual reconnect function
  const reconnect = useCallback(() => {
    console.log('[SocketProvider] Manual reconnect requested');
    socketService.disconnect();
    const newSocket = socketService.connect(token);
    setSocket(newSocket);
  }, [token]);
  
  const value: SocketContextType = {
    socket,
    isConnected,
    isAuthenticated,
    connectionStatus,
    subscribe,
    unsubscribe,
    on,
    off,
    reconnect,
  };
  
  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
};

/**
 * Hook for price updates
 */
export const usePriceUpdates = (callback: (data: any) => void) => {
  const { on, off, subscribe, unsubscribe } = useSocket();
  
  useEffect(() => {
    // Subscribe to price channel
    subscribe(['prices']);
    
    // Listen for price updates
    on('price_update', callback);
    
    return () => {
      off('price_update', callback);
      unsubscribe(['prices']);
    };
  }, [callback, on, off, subscribe, unsubscribe]);
};

/**
 * Hook for order updates
 */
export const useOrderUpdates = (callback: (data: any) => void) => {
  const { on, off } = useSocket();
  
  useEffect(() => {
    on('order_update', callback);
    
    return () => {
      off('order_update', callback);
    };
  }, [callback, on, off]);
};
