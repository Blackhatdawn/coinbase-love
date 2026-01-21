/**
 * IndexedDB Database Management
 * Handles offline data persistence with TTL support
 */

interface StoredData<T> {
  data: T;
  timestamp: number;
  ttl?: number; // TTL in milliseconds
}

class CryptoVaultDB {
  private dbName = 'cryptovault-cache';
  private db: IDBDatabase | null = null;
  private readonly STORES = {
    QUERIES: 'query-cache',
    USER_DATA: 'user-data',
    PRICE_HISTORY: 'price-history',
    PENDING_MUTATIONS: 'pending-mutations',
    SETTINGS: 'settings',
  };

  /**
   * Initialize IndexedDB
   */
  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => {
        console.error('❌ Failed to open IndexedDB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('✅ IndexedDB initialized');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object stores
        Object.values(this.STORES).forEach((store) => {
          if (!db.objectStoreNames.contains(store)) {
            db.createObjectStore(store);
            console.log(`📦 Created store: ${store}`);
          }
        });
      };
    });
  }

  /**
   * Get item from cache
   */
  async get<T>(store: string, key: string): Promise<T | null> {
    if (!this.db) await this.init();

    return new Promise((resolve) => {
      try {
        const transaction = this.db!.transaction(store, 'readonly');
        const objectStore = transaction.objectStore(store);
        const request = objectStore.get(key);

        request.onsuccess = () => {
          const result = request.result as StoredData<T> | undefined;

          if (!result) {
            resolve(null);
            return;
          }

          // Check if expired
          const now = Date.now();
          const ttl = result.ttl || 24 * 60 * 60 * 1000; // Default 24h
          if (now - result.timestamp > ttl) {
            // Expired, delete and return null
            this.delete(store, key).catch(console.error);
            resolve(null);
            return;
          }

          resolve(result.data);
        };

        request.onerror = () => {
          console.error('❌ DB get failed:', request.error);
          resolve(null);
        };
      } catch (error) {
        console.error('❌ DB transaction failed:', error);
        resolve(null);
      }
    });
  }

  /**
   * Set item in cache
   */
  async set<T>(store: string, key: string, data: T, ttl?: number): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      try {
        const transaction = this.db!.transaction(store, 'readwrite');
        const objectStore = transaction.objectStore(store);
        const request = objectStore.put(
          {
            data,
            timestamp: Date.now(),
            ttl,
          } as StoredData<T>,
          key
        );

        request.onsuccess = () => {
          resolve();
        };

        request.onerror = () => {
          console.error('❌ DB set failed:', request.error);
          reject(request.error);
        };
      } catch (error) {
        console.error('❌ DB transaction failed:', error);
        reject(error);
      }
    });
  }

  /**
   * Delete item from cache
   */
  async delete(store: string, key: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve) => {
      try {
        const transaction = this.db!.transaction(store, 'readwrite');
        const objectStore = transaction.objectStore(store);
        const request = objectStore.delete(key);

        request.onsuccess = () => {
          resolve();
        };

        request.onerror = () => {
          console.error('❌ DB delete failed:', request.error);
          resolve();
        };
      } catch (error) {
        console.error('❌ DB transaction failed:', error);
        resolve();
      }
    });
  }

  /**
   * Get all items from a store
   */
  async getAll<T>(store: string): Promise<Array<{ key: string; value: T }>> {
    if (!this.db) await this.init();

    return new Promise((resolve) => {
      try {
        const transaction = this.db!.transaction(store, 'readonly');
        const objectStore = transaction.objectStore(store);
        const request = objectStore.getAll();

        request.onsuccess = () => {
          const results = request.result as StoredData<T>[];
          const now = Date.now();

          // Filter expired items
          const filtered = results.filter((result) => {
            const ttl = result.ttl || 24 * 60 * 60 * 1000;
            return now - result.timestamp <= ttl;
          });

          resolve(
            filtered.map((item, idx) => ({
              key: String(idx),
              value: item.data,
            }))
          );
        };

        request.onerror = () => {
          console.error('❌ DB getAll failed:', request.error);
          resolve([]);
        };
      } catch (error) {
        console.error('❌ DB transaction failed:', error);
        resolve([]);
      }
    });
  }

  /**
   * Clear all items from a store
   */
  async clear(store: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve) => {
      try {
        const transaction = this.db!.transaction(store, 'readwrite');
        const objectStore = transaction.objectStore(store);
        const request = objectStore.clear();

        request.onsuccess = () => {
          console.log(`📦 Cleared store: ${store}`);
          resolve();
        };

        request.onerror = () => {
          console.error('❌ DB clear failed:', request.error);
          resolve();
        };
      } catch (error) {
        console.error('❌ DB transaction failed:', error);
        resolve();
      }
    });
  }

  /**
   * Get storage usage stats
   */
  async getStats(): Promise<{ usage: number; quota: number; percentage: number }> {
    if (!navigator.storage?.estimate) {
      return { usage: 0, quota: 0, percentage: 0 };
    }

    const estimate = await navigator.storage.estimate();
    return {
      usage: estimate.usage || 0,
      quota: estimate.quota || 0,
      percentage: Math.round(((estimate.usage || 0) / (estimate.quota || 1)) * 100),
    };
  }

  /**
   * Public store names for external use
   */
  get stores() {
    return this.STORES;
  }
}

// Singleton instance
let instance: CryptoVaultDB | null = null;

export function getDB(): CryptoVaultDB {
  if (!instance) {
    instance = new CryptoVaultDB();
  }
  return instance;
}

/**
 * React hook for database access
 */
import { useEffect, useState } from 'react';

export function useDBStats() {
  const [stats, setStats] = useState({
    usage: 0,
    quota: 0,
    percentage: 0,
  });

  useEffect(() => {
    getDB().getStats().then(setStats).catch(console.error);
  }, []);

  return stats;
}
