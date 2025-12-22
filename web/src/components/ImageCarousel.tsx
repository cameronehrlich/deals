"use client";

import { useState, useCallback } from "react";
import { ChevronLeft, ChevronRight, Image as ImageIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageCarouselProps {
  images: string[];
  alt: string;
  className?: string;
}

/**
 * Upgrade image URL to higher resolution.
 * Realtor.com CDN (rdcpix.com) supports size modifications:
 * - Replace dimension parameters (w480_h360 -> w1024_h768)
 * - Replace size suffixes (-s, -m, -l, -o)
 */
function getHighResUrl(url: string): string {
  if (!url) return url;

  // Handle rdcpix.com URLs with dimension parameters
  // e.g., ...abc123-w480_h360.jpg -> ...abc123-w1024_h768.jpg
  if (url.includes("rdcpix.com")) {
    // Replace common thumbnail sizes with larger versions
    return url
      .replace(/-w\d+_h\d+/g, "-w1024_h768")
      .replace(/-m\d+x\d*w/g, "-m1024x768w")
      .replace(/-s\.jpg/g, "-l.jpg")
      .replace(/-m\.jpg/g, "-l.jpg");
  }

  // Handle other CDNs that use query params
  if (url.includes("?")) {
    const urlObj = new URL(url);
    // Try to upgrade common size parameters
    if (urlObj.searchParams.has("w")) {
      urlObj.searchParams.set("w", "1024");
    }
    if (urlObj.searchParams.has("h")) {
      urlObj.searchParams.set("h", "768");
    }
    return urlObj.toString();
  }

  return url;
}

export function ImageCarousel({ images, alt, className }: ImageCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [imageError, setImageError] = useState<Set<number>>(new Set());

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
          className="w-full h-full object-cover"
          onError={() => handleImageError(currentIndex)}
        />
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
  );
}
