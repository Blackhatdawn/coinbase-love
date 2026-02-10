import React, { useState, useEffect, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  containerClassName?: string;
  priority?: boolean;
  placeholder?: 'blur' | 'empty' | 'color';
  placeholderColor?: string;
  onLoad?: () => void;
  onError?: () => void;
  sizes?: string;
  quality?: number;
  format?: 'auto' | 'webp' | 'avif' | 'jpeg' | 'png';
}

/**
 * OptimizedImage Component
 * 
 * Features:
 * - Lazy loading with Intersection Observer
 * - Modern format support (WebP, AVIF) with fallbacks
 * - Blur placeholder for smooth loading experience
 * - Responsive images with srcset
 * - Priority loading for above-the-fold images
 * - Error handling with fallback
 * 
 * @example
 * <OptimizedImage
 *   src="/hero-image.jpg"
 *   alt="Hero banner"
 *   width={1200}
 *   height={600}
 *   priority
 *   placeholder="blur"
 * />
 */
export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  className,
  containerClassName,
  priority = false,
  placeholder = 'blur',
  placeholderColor = '#0a0a0f',
  onLoad,
  onError,
  sizes = '100vw',
  quality = 80,
  format = 'auto',
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(priority);
  const [hasError, setHasError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState<string>('');
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Generate optimized image URLs with format support
  const generateOptimizedSrc = useCallback((originalSrc: string, targetFormat?: string): string => {
    // If using an image optimization service (like Cloudinary, Imgix, etc.)
    // you would transform the URL here
    
    // For local images, we'll append query parameters that could be
    // used by a server-side image optimization middleware
    if (originalSrc.startsWith('http') || originalSrc.startsWith('/')) {
      const params = new URLSearchParams();
      
      if (width) params.set('w', width.toString());
      if (height) params.set('h', height.toString());
      if (quality) params.set('q', quality.toString());
      if (targetFormat && targetFormat !== 'auto') params.set('fm', targetFormat);
      
      const queryString = params.toString();
      return queryString ? `${originalSrc}?${queryString}` : originalSrc;
    }
    
    return originalSrc;
  }, [width, height, quality]);

  // Generate srcset for responsive images
  const generateSrcSet = useCallback((): string | undefined => {
    if (!width || !src) return undefined;
    
    const widths = [320, 640, 960, 1280, 1920];
    const relevantWidths = widths.filter(w => w <= width * 2);
    
    return relevantWidths
      .map(w => {
        const optimized = generateOptimizedSrc(src, format === 'auto' ? 'webp' : format);
        const url = new URL(optimized, window.location.origin);
        url.searchParams.set('w', w.toString());
        return `${url.toString()} ${w}w`;
      })
      .join(', ');
  }, [src, width, format, generateOptimizedSrc]);

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (priority || !containerRef.current) {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        rootMargin: '50px', // Start loading 50px before image enters viewport
        threshold: 0.01,
      }
    );

    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, [priority]);

  // Set image source when in view
  useEffect(() => {
    if (isInView && !currentSrc) {
      // Try modern formats first
      const supportsWebP = document.createElement('canvas')
        .toDataURL('image/webp')
        .indexOf('data:image/webp') === 0;
      
      const targetFormat = format === 'auto' 
        ? (supportsWebP ? 'webp' : undefined)
        : format;
      
      setCurrentSrc(generateOptimizedSrc(src, targetFormat));
    }
  }, [isInView, src, format, currentSrc, generateOptimizedSrc]);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    onError?.();
  };

  // Generate blur placeholder (simplified - in production, use actual blur hash)
  const blurPlaceholder = placeholder === 'blur' 
    ? `data:image/svg+xml;base64,${btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width || 100} ${height || 100}">
        <rect width="100%" height="100%" fill="${placeholderColor}"/>
      </svg>
    `)}`
    : undefined;

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative overflow-hidden',
        containerClassName
      )}
      style={{
        width: width ? `${width}px` : '100%',
        height: height ? `${height}px` : 'auto',
        aspectRatio: width && height ? `${width}/${height}` : undefined,
        backgroundColor: placeholderColor,
      }}
    >
      {/* Placeholder */}
      {!isLoaded && placeholder !== 'empty' && (
        <div
          className={cn(
            'absolute inset-0 transition-opacity duration-300',
            isLoaded ? 'opacity-0' : 'opacity-100'
          )}
          style={{
            backgroundColor: placeholder === 'color' ? placeholderColor : undefined,
            backgroundImage: placeholder === 'blur' && blurPlaceholder ? `url(${blurPlaceholder})` : undefined,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: placeholder === 'blur' ? 'blur(20px)' : undefined,
          }}
        />
      )}

      {/* Loading spinner */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-gold-500/20 rounded-full animate-spin border-t-gold-500" />
        </div>
      )}

      {/* Error state */}
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-destructive/10">
          <span className="text-xs text-destructive">Failed to load image</span>
        </div>
      )}

      {/* Actual image */}
      {isInView && !hasError && (
        <picture>
          {/* AVIF format - best compression */}
          <source
            srcSet={generateSrcSet()?.replace(/\.webp/g, '.avif')}
            sizes={sizes}
            type="image/avif"
          />
          
          {/* WebP format - good compression, wide support */}
          <source
            srcSet={generateSrcSet()}
            sizes={sizes}
            type="image/webp"
          />
          
          {/* Fallback to original format */}
          <img
            ref={imgRef}
            src={currentSrc}
            alt={alt}
            width={width}
            height={height}
            className={cn(
              'w-full h-full object-cover transition-opacity duration-300',
              isLoaded ? 'opacity-100' : 'opacity-0',
              className
            )}
            loading={priority ? 'eager' : 'lazy'}
            decoding={priority ? 'sync' : 'async'}
            onLoad={handleLoad}
            onError={handleError}
          />
        </picture>
      )}
    </div>
  );
};

/**
 * Hook for tracking image loading performance
 */
export const useImagePerformance = () => {
  const trackImageLoad = useCallback((src: string, loadTime: number) => {
    // Send to analytics
    if (window.gtag) {
      window.gtag('event', 'image_load', {
        src,
        load_time: loadTime,
      });
    }

    // Log to console in development
    if (import.meta.env.DEV) {
      console.log(`[Image Performance] ${src} loaded in ${loadTime.toFixed(0)}ms`);
    }
  }, []);

  return { trackImageLoad };
};

/**
 * Preload critical images
 */
export const preloadImage = (src: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve();
    img.onerror = reject;
    img.src = src;
  });
};

/**
 * Preload multiple images
 */
export const preloadImages = async (srcs: string[]): Promise<void> => {
  await Promise.all(srcs.map(src => preloadImage(src).catch(() => {
    // Silently fail individual image preloads
    console.warn(`Failed to preload image: ${src}`);
  })));
};

export default OptimizedImage;
