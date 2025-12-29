"use client";

import { useState, useCallback, useEffect } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Image as ImageIcon,
  X,
  Expand,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageCarouselProps {
  images: string[];
  alt: string;
  className?: string;
  enableFullscreen?: boolean;
}

/**
 * Upgrade image URL to higher resolution.
 * Realtor.com CDN (rdcpix.com) supports size modifications:
 * - Replace dimension parameters (w480_h360 -> w1024_h768)
 * - Replace size suffixes at end of filename (s, m -> l for large, o for original)
 * URL formats:
 *   - ...abc123-w480_h360.jpg
 *   - ...abc123l-m821058964s.jpg (s=small, m=medium, l=large, o=original)
 */
function getHighResUrl(url: string): string {
  if (!url) return url;

  // Handle rdcpix.com URLs
  if (url.includes("rdcpix.com")) {
    let upgraded = url;

    // Pattern 1: dimension parameters (w480_h360 -> w1024_h768)
    upgraded = upgraded.replace(/-w\d+_h\d+/g, "-w1024_h768");
    upgraded = upgraded.replace(/-m\d+x\d*w/g, "-m1024x768w");

    // Pattern 2: size suffix at end of filename before extension
    // e.g., ...l-m821058964s.jpg -> ...l-m821058964o.jpg (s/m -> o for original)
    upgraded = upgraded.replace(/([a-z0-9])s\.(jpg|jpeg|png|webp)$/i, "$1o.$2");
    upgraded = upgraded.replace(/([a-z0-9])m\.(jpg|jpeg|png|webp)$/i, "$1o.$2");

    // Pattern 3: standalone size suffix
    upgraded = upgraded.replace(/-s\.(jpg|jpeg|png|webp)$/i, "-o.$1");
    upgraded = upgraded.replace(/-m\.(jpg|jpeg|png|webp)$/i, "-o.$1");

    return upgraded;
  }

  // Handle other CDNs that use query params
  if (url.includes("?")) {
    try {
      const urlObj = new URL(url);
      // Try to upgrade common size parameters
      if (urlObj.searchParams.has("w")) {
        urlObj.searchParams.set("w", "1024");
      }
      if (urlObj.searchParams.has("h")) {
        urlObj.searchParams.set("h", "768");
      }
      return urlObj.toString();
    } catch {
      return url;
    }
  }

  return url;
}

/**
 * Get maximum resolution URL for fullscreen viewing.
 */
function getMaxResUrl(url: string): string {
  if (!url) return url;

  // Handle rdcpix.com URLs - get original/largest size
  if (url.includes("rdcpix.com")) {
    let upgraded = url;

    // Use larger dimensions for fullscreen
    upgraded = upgraded.replace(/-w\d+_h\d+/g, "-w1920_h1440");
    upgraded = upgraded.replace(/-m\d+x\d*w/g, "-m1920x1440w");

    // Always use 'o' for original quality
    upgraded = upgraded.replace(/([a-z0-9])[smlo]\.(jpg|jpeg|png|webp)$/i, "$1o.$2");
    upgraded = upgraded.replace(/-[smlo]\.(jpg|jpeg|png|webp)$/i, "-o.$1");

    return upgraded;
  }

  // For other CDNs, try larger dimensions
  if (url.includes("?")) {
    try {
      const urlObj = new URL(url);
      if (urlObj.searchParams.has("w")) {
        urlObj.searchParams.set("w", "1920");
      }
      if (urlObj.searchParams.has("h")) {
        urlObj.searchParams.set("h", "1440");
      }
      return urlObj.toString();
    } catch {
      return url;
    }
  }

  return url;
}

interface FullscreenViewerProps {
  images: string[];
  alt: string;
  initialIndex: number;
  onClose: () => void;
}

function FullscreenViewer({
  images,
  alt,
  initialIndex,
  onClose,
}: FullscreenViewerProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [imageError, setImageError] = useState<Set<number>>(new Set());

  const goToPrevious = useCallback(() => {
    setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  }, [images.length]);

  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  }, [images.length]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "ArrowLeft") {
        goToPrevious();
      } else if (e.key === "ArrowRight") {
        goToNext();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    // Prevent body scroll when fullscreen is open
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [onClose, goToPrevious, goToNext]);

  const handleImageError = useCallback((index: number) => {
    setImageError((prev) => new Set(prev).add(index));
  }, []);

  const currentImage = images[currentIndex];
  const maxResUrl = getMaxResUrl(currentImage);
  const hasError = imageError.has(currentIndex);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors z-10"
        aria-label="Close fullscreen"
      >
        <X className="h-6 w-6" />
      </button>

      {/* Image counter */}
      <div className="absolute top-4 left-4 px-3 py-1.5 bg-white/10 text-white text-sm rounded-full">
        {currentIndex + 1} / {images.length}
      </div>

      {/* Previous button */}
      {images.length > 1 && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            goToPrevious();
          }}
          className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
          aria-label="Previous image"
        >
          <ChevronLeft className="h-8 w-8" />
        </button>
      )}

      {/* Main image */}
      <div
        className="max-w-[90vw] max-h-[90vh] flex items-center justify-center"
        onClick={(e) => e.stopPropagation()}
      >
        {hasError ? (
          <div className="w-96 h-64 flex items-center justify-center bg-gray-800 text-gray-400 rounded-lg">
            <ImageIcon className="h-16 w-16" />
          </div>
        ) : (
          <img
            src={maxResUrl}
            alt={`${alt} - Photo ${currentIndex + 1}`}
            className="max-w-full max-h-[90vh] object-contain rounded-lg"
            onError={() => handleImageError(currentIndex)}
          />
        )}
      </div>

      {/* Next button */}
      {images.length > 1 && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            goToNext();
          }}
          className="absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
          aria-label="Next image"
        >
          <ChevronRight className="h-8 w-8" />
        </button>
      )}

      {/* Thumbnail strip */}
      {images.length > 1 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 p-2 bg-black/50 rounded-lg max-w-[90vw] overflow-x-auto">
          {images.map((img, index) => (
            <button
              key={index}
              onClick={(e) => {
                e.stopPropagation();
                setCurrentIndex(index);
              }}
              className={cn(
                "flex-shrink-0 w-16 h-12 rounded overflow-hidden transition-all",
                index === currentIndex
                  ? "ring-2 ring-white opacity-100"
                  : "opacity-50 hover:opacity-75"
              )}
            >
              <img
                src={getHighResUrl(img)}
                alt={`Thumbnail ${index + 1}`}
                className="w-full h-full object-cover"
              />
            </button>
          ))}
        </div>
      )}

      {/* Keyboard hints */}
      <div className="absolute bottom-4 right-4 text-white/50 text-xs hidden sm:block">
        Use ← → to navigate, ESC to close
      </div>
    </div>
  );
}

/**
 * Deduplicate images by normalizing URLs (protocol, size params).
 * Handles cases where same image appears with http/https or different sizes.
 */
function deduplicateImages(images: string[]): string[] {
  if (!images || images.length === 0) return images;

  const seen = new Set<string>();
  const result: string[] = [];

  for (const url of images) {
    // Normalize: use https, remove size params for comparison
    let normalized = url.replace(/^http:\/\//, "https://");
    // Remove size suffixes for dedup check
    normalized = normalized.replace(/-w\d+_h\d+/g, "");
    normalized = normalized.replace(/-m\d+x\d*w/g, "");
    normalized = normalized.replace(/[smlo]\.(jpg|jpeg|png|webp)$/i, ".$1");

    if (!seen.has(normalized)) {
      seen.add(normalized);
      // Store the https version
      result.push(url.replace(/^http:\/\//, "https://"));
    }
  }

  return result;
}

export function ImageCarousel({
  images: rawImages,
  alt,
  className,
  enableFullscreen = false,
}: ImageCarouselProps) {
  // Deduplicate images on the frontend as a safety net
  const images = deduplicateImages(rawImages);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [imageError, setImageError] = useState<Set<number>>(new Set());
  const [isFullscreen, setIsFullscreen] = useState(false);

  const hasImages = images && images.length > 0;
  const hasMultiple = hasImages && images.length > 1;

  const goToPrevious = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
    },
    [images.length]
  );

  const goToNext = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
    },
    [images.length]
  );

  const handleImageError = useCallback((index: number) => {
    setImageError((prev) => new Set(prev).add(index));
  }, []);

  const openFullscreen = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsFullscreen(true);
  }, []);

  if (!hasImages) {
    return (
      <div
        className={cn(
          "w-full h-full flex items-center justify-center bg-gray-100 text-gray-400",
          className
        )}
      >
        <ImageIcon className="h-12 w-12" />
      </div>
    );
  }

  const currentImage = images[currentIndex];
  const highResUrl = getHighResUrl(currentImage);
  const hasError = imageError.has(currentIndex);

  return (
    <>
      <div className={cn("relative w-full h-full group", className)}>
        {/* Main Image */}
        {hasError ? (
          <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
            <ImageIcon className="h-12 w-12" />
          </div>
        ) : (
          <img
            src={highResUrl}
            alt={`${alt} - Photo ${currentIndex + 1}`}
            className={cn(
              "w-full h-full object-cover",
              enableFullscreen && "cursor-pointer"
            )}
            onError={() => handleImageError(currentIndex)}
            onClick={enableFullscreen ? openFullscreen : undefined}
          />
        )}

        {/* Fullscreen button */}
        {enableFullscreen && !hasError && (
          <button
            onClick={openFullscreen}
            className="absolute top-2 left-2 p-1.5 rounded-full bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
            aria-label="View fullscreen"
          >
            <Expand className="h-4 w-4" />
          </button>
        )}

        {/* Navigation Arrows - only show if multiple images */}
        {hasMultiple && (
          <>
            <button
              onClick={goToPrevious}
              className="absolute left-2 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
              aria-label="Previous image"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={goToNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
              aria-label="Next image"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </>
        )}

        {/* Dot Indicators */}
        {hasMultiple && (
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
            {images.slice(0, 8).map((_, index) => (
              <button
                key={index}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setCurrentIndex(index);
                }}
                className={cn(
                  "w-1.5 h-1.5 rounded-full transition-all",
                  index === currentIndex
                    ? "bg-white w-3"
                    : "bg-white/60 hover:bg-white/80"
                )}
                aria-label={`Go to image ${index + 1}`}
              />
            ))}
            {images.length > 8 && (
              <span className="text-white text-xs ml-1">+{images.length - 8}</span>
            )}
          </div>
        )}

        {/* Image Counter */}
        {hasMultiple && (
          <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/50 text-white text-xs rounded">
            {currentIndex + 1}/{images.length}
          </div>
        )}
      </div>

      {/* Fullscreen viewer portal */}
      {isFullscreen && (
        <FullscreenViewer
          images={images}
          alt={alt}
          initialIndex={currentIndex}
          onClose={() => setIsFullscreen(false)}
        />
      )}
    </>
  );
}
