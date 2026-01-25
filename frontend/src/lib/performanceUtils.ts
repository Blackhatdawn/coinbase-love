/**
 * Frontend Performance Optimization Utilities
 * 
 * Provides:
 * 1. Image lazy loading with blur-up effect
 * 2. Virtual scrolling for large lists
 * 3. Request deduplication
 * 4. Memory management
 * 5. Performance monitoring
 */

// ============================================
// IMAGE OPTIMIZATION
// ============================================

/**
 * Create a low-quality image placeholder (LQIP) blur hash
 */
export function createBlurDataURL(width = 10, height = 10): string {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, width, height);
  }
  return canvas.toDataURL('image/jpeg', 0.1);
}

/**
 * Preload critical images
 */
export function preloadImages(urls: string[]): Promise<void[]> {
  return Promise.all(
    urls.map((url) => {
      return new Promise<void>((resolve) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = () => resolve();
        img.src = url;
      });
    })
  );
}

// ============================================
// REQUEST DEDUPLICATION
// ============================================

type PendingRequest = {
  promise: Promise<unknown>;
  timestamp: number;
};

const pendingRequests = new Map<string, PendingRequest>();

/**
 * Deduplicate identical requests within a time window
 */
export async function deduplicatedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  dedupeWindow = 100 // ms
): Promise<T> {
  const existing = pendingRequests.get(key);
  const now = Date.now();

  // Return existing promise if within deduplication window
  if (existing && now - existing.timestamp < dedupeWindow) {
    return existing.promise as Promise<T>;
  }

  // Create new request
  const promise = fetcher().finally(() => {
    // Clean up after request completes
    setTimeout(() => pendingRequests.delete(key), dedupeWindow);
  });

  pendingRequests.set(key, { promise, timestamp: now });
  return promise;
}

// ============================================
// VIRTUAL SCROLLING UTILITIES
// ============================================

export interface VirtualScrollConfig {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

export interface VirtualScrollResult {
  startIndex: number;
  endIndex: number;
  offsetY: number;
  visibleCount: number;
}

/**
 * Calculate virtual scroll indices
 */
export function calculateVirtualScroll(
  scrollTop: number,
  totalItems: number,
  config: VirtualScrollConfig
): VirtualScrollResult {
  const { itemHeight, containerHeight, overscan = 3 } = config;

  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    totalItems - 1,
    startIndex + visibleCount + overscan * 2
  );

  return {
    startIndex,
    endIndex,
    offsetY: startIndex * itemHeight,
    visibleCount,
  };
}

// ============================================
// MEMORY MANAGEMENT
// ============================================

/**
 * Create a cache with automatic eviction
 */
export class LRUCache<K, V> {
  private cache: Map<K, V>;
  private readonly maxSize: number;

  constructor(maxSize = 100) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  get(key: K): V | undefined {
    const value = this.cache.get(key);
    if (value !== undefined) {
      // Move to end (most recently used)
      this.cache.delete(key);
      this.cache.set(key, value);
    }
    return value;
  }

  set(key: K, value: V): void {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.maxSize) {
      // Evict oldest (first) entry
      const firstKey = this.cache.keys().next().value;
      if (firstKey !== undefined) {
        this.cache.delete(firstKey);
      }
    }
    this.cache.set(key, value);
  }

  has(key: K): boolean {
    return this.cache.has(key);
  }

  delete(key: K): boolean {
    return this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  get size(): number {
    return this.cache.size;
  }
}

/**
 * Cleanup event listeners on unmount
 */
export function createCleanupManager() {
  const cleanupFns: (() => void)[] = [];

  return {
    add(cleanup: () => void) {
      cleanupFns.push(cleanup);
    },
    cleanup() {
      cleanupFns.forEach((fn) => fn());
      cleanupFns.length = 0;
    },
  };
}

// ============================================
// PERFORMANCE MONITORING
// ============================================

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private readonly maxMetrics = 1000;

  /**
   * Measure execution time of a function
   */
  async measure<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    try {
      return await fn();
    } finally {
      const duration = performance.now() - start;
      this.record(name, duration);
    }
  }

  /**
   * Record a metric
   */
  record(name: string, value: number): void {
    this.metrics.push({
      name,
      value,
      timestamp: Date.now(),
    });

    // Trim old metrics
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(-this.maxMetrics);
    }
  }

  /**
   * Get average for a metric
   */
  getAverage(name: string): number {
    const relevant = this.metrics.filter((m) => m.name === name);
    if (relevant.length === 0) return 0;
    return relevant.reduce((sum, m) => sum + m.value, 0) / relevant.length;
  }

  /**
   * Get all metrics summary
   */
  getSummary(): Record<string, { avg: number; count: number; min: number; max: number }> {
    const summary: Record<string, { sum: number; count: number; min: number; max: number }> = {};

    for (const metric of this.metrics) {
      if (!summary[metric.name]) {
        summary[metric.name] = { sum: 0, count: 0, min: Infinity, max: -Infinity };
      }
      summary[metric.name].sum += metric.value;
      summary[metric.name].count++;
      summary[metric.name].min = Math.min(summary[metric.name].min, metric.value);
      summary[metric.name].max = Math.max(summary[metric.name].max, metric.value);
    }

    const result: Record<string, { avg: number; count: number; min: number; max: number }> = {};
    for (const [name, data] of Object.entries(summary)) {
      result[name] = {
        avg: Math.round(data.sum / data.count * 100) / 100,
        count: data.count,
        min: Math.round(data.min * 100) / 100,
        max: Math.round(data.max * 100) / 100,
      };
    }

    return result;
  }

  /**
   * Report Web Vitals
   */
  reportWebVitals(): void {
    if (typeof window === 'undefined') return;

    // First Contentful Paint
    const paintEntries = performance.getEntriesByType('paint');
    const fcp = paintEntries.find((e) => e.name === 'first-contentful-paint');
    if (fcp) {
      this.record('FCP', fcp.startTime);
    }

    // Largest Contentful Paint
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          if (lastEntry) {
            this.record('LCP', lastEntry.startTime);
          }
        });
        lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
      } catch {
        // LCP not supported
      }

      // Cumulative Layout Shift
      try {
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries() as PerformanceEntry[]) {
            if (!(entry as unknown as { hadRecentInput: boolean }).hadRecentInput) {
              clsValue += (entry as unknown as { value: number }).value;
            }
          }
          this.record('CLS', clsValue);
        });
        clsObserver.observe({ type: 'layout-shift', buffered: true });
      } catch {
        // CLS not supported
      }

      // First Input Delay
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const firstInput = list.getEntries()[0] as PerformanceEventTiming;
          if (firstInput) {
            this.record('FID', firstInput.processingStart - firstInput.startTime);
          }
        });
        fidObserver.observe({ type: 'first-input', buffered: true });
      } catch {
        // FID not supported
      }
    }
  }
}

export const performanceMonitor = new PerformanceMonitor();

// ============================================
// DEBOUNCE & THROTTLE
// ============================================

/**
 * Debounce function with leading/trailing options
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  wait: number,
  options: { leading?: boolean; trailing?: boolean } = {}
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  let lastArgs: Parameters<T> | null = null;
  const { leading = false, trailing = true } = options;

  return function (this: unknown, ...args: Parameters<T>) {
    const shouldCallNow = leading && !timeout;

    lastArgs = args;

    if (timeout) {
      clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
      timeout = null;
      if (trailing && lastArgs) {
        fn.apply(this, lastArgs);
      }
    }, wait);

    if (shouldCallNow) {
      fn.apply(this, args);
    }
  };
}

/**
 * Throttle function
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  fn: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false;

  return function (this: unknown, ...args: Parameters<T>) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

// ============================================
// RESOURCE HINTS
// ============================================

/**
 * Add DNS prefetch for external domains
 */
export function addDnsPrefetch(domain: string): void {
  if (typeof document === 'undefined') return;

  const link = document.createElement('link');
  link.rel = 'dns-prefetch';
  link.href = domain;
  document.head.appendChild(link);
}

/**
 * Preconnect to external origin
 */
export function preconnect(origin: string, crossOrigin = true): void {
  if (typeof document === 'undefined') return;

  const link = document.createElement('link');
  link.rel = 'preconnect';
  link.href = origin;
  if (crossOrigin) {
    link.crossOrigin = 'anonymous';
  }
  document.head.appendChild(link);
}

/**
 * Prefetch a resource for future navigation
 */
export function prefetch(url: string): void {
  if (typeof document === 'undefined') return;

  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.href = url;
  link.as = 'document';
  document.head.appendChild(link);
}

// ============================================
// INTERSECTION OBSERVER UTILITY
// ============================================

/**
 * Create an intersection observer for lazy loading
 */
export function createLazyLoadObserver(
  callback: (entry: IntersectionObserverEntry) => void,
  options: IntersectionObserverInit = {}
): IntersectionObserver | null {
  if (typeof IntersectionObserver === 'undefined') {
    return null;
  }

  const defaultOptions: IntersectionObserverInit = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1,
    ...options,
  };

  return new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        callback(entry);
      }
    });
  }, defaultOptions);
}

// ============================================
// BUNDLE SIZE HELPERS
// ============================================

/**
 * Dynamic import with retry
 */
export async function dynamicImportWithRetry<T>(
  importFn: () => Promise<T>,
  retries = 3
): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await importFn();
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise((r) => setTimeout(r, 1000 * (i + 1)));
    }
  }
  throw new Error('Import failed after retries');
}
