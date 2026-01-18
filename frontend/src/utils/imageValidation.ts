/**
 * Image validation utilities for Google Ads campaigns.
 * Client-side validation of image dimensions and aspect ratios.
 */

export interface ImageRequirements {
  ratio: number;
  tolerance: number;
  minWidth: number;
  minHeight: number;
  description: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  dimensions?: { width: number; height: number };
}

/**
 * Image requirements for different asset types.
 */
export const IMAGE_REQUIREMENTS: Record<string, ImageRequirements> = {
  landscape: {
    ratio: 1.91,
    tolerance: 0.02,
    minWidth: 600,
    minHeight: 314,
    description: 'Landscape marketing image (1.91:1) - minimum 600x314 pixels',
  },
  square: {
    ratio: 1.0,
    tolerance: 0.02,
    minWidth: 300,
    minHeight: 300,
    description: 'Square marketing image (1:1) - minimum 300x300 pixels',
  },
  logo: {
    ratio: 1.0,
    tolerance: 0.02,
    minWidth: 128,
    minHeight: 128,
    description: 'Square logo (1:1) - minimum 128x128 pixels',
  },
  logo_landscape: {
    ratio: 4.0,
    tolerance: 0.1,
    minWidth: 512,
    minHeight: 128,
    description: 'Landscape logo (4:1) - minimum 512x128 pixels',
  },
};

/**
 * Get image dimensions from a File object.
 */
export function getImageDimensions(file: File): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const objectUrl = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error('Failed to load image'));
    };

    img.src = objectUrl;
  });
}

/**
 * Get image dimensions from a URL.
 * Note: This only works for same-origin URLs or URLs with CORS enabled.
 */
export function getImageDimensionsFromUrl(url: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    };

    img.onerror = () => {
      reject(new Error('Failed to load image from URL'));
    };

    // Enable CORS
    img.crossOrigin = 'anonymous';
    img.src = url;
  });
}

/**
 * Validate aspect ratio.
 */
export function validateAspectRatio(
  width: number,
  height: number,
  expectedType: string
): { valid: boolean; error?: string } {
  const requirements = IMAGE_REQUIREMENTS[expectedType];
  if (!requirements) {
    return { valid: false, error: `Unknown image type: ${expectedType}` };
  }

  if (width <= 0 || height <= 0) {
    return { valid: false, error: 'Invalid image dimensions' };
  }

  const actualRatio = width / height;
  const expectedRatio = requirements.ratio;
  const tolerance = requirements.tolerance;

  const ratioDiff = Math.abs(actualRatio - expectedRatio) / expectedRatio;
  if (ratioDiff > tolerance) {
    return {
      valid: false,
      error: `Image aspect ratio ${actualRatio.toFixed(2)} does not match required ratio ${expectedRatio.toFixed(2)} (${requirements.description})`,
    };
  }

  return { valid: true };
}

/**
 * Validate image dimensions.
 */
export function validateImageDimensions(
  width: number,
  height: number,
  expectedType: string
): { valid: boolean; error?: string } {
  const requirements = IMAGE_REQUIREMENTS[expectedType];
  if (!requirements) {
    return { valid: false, error: `Unknown image type: ${expectedType}` };
  }

  if (width < requirements.minWidth) {
    return {
      valid: false,
      error: `Image width ${width}px is below minimum required ${requirements.minWidth}px for ${requirements.description}`,
    };
  }

  if (height < requirements.minHeight) {
    return {
      valid: false,
      error: `Image height ${height}px is below minimum required ${requirements.minHeight}px for ${requirements.description}`,
    };
  }

  return { valid: true };
}

/**
 * Validate an image file against expected type requirements.
 */
export async function validateImageFile(
  file: File,
  expectedType: string
): Promise<ValidationResult> {
  const errors: string[] = [];

  try {
    const dimensions = await getImageDimensions(file);

    // Validate dimensions
    const dimResult = validateImageDimensions(dimensions.width, dimensions.height, expectedType);
    if (!dimResult.valid && dimResult.error) {
      errors.push(dimResult.error);
    }

    // Validate aspect ratio
    const ratioResult = validateAspectRatio(dimensions.width, dimensions.height, expectedType);
    if (!ratioResult.valid && ratioResult.error) {
      errors.push(ratioResult.error);
    }

    return {
      valid: errors.length === 0,
      errors,
      dimensions,
    };
  } catch (error) {
    return {
      valid: false,
      errors: ['Failed to validate image'],
    };
  }
}

/**
 * Validate an image URL against expected type requirements.
 * Note: This only works for URLs with CORS enabled.
 */
export async function validateImageUrl(
  url: string,
  expectedType: string
): Promise<ValidationResult> {
  const errors: string[] = [];

  if (!url) {
    return { valid: false, errors: ['Image URL is required'] };
  }

  try {
    const dimensions = await getImageDimensionsFromUrl(url);

    // Validate dimensions
    const dimResult = validateImageDimensions(dimensions.width, dimensions.height, expectedType);
    if (!dimResult.valid && dimResult.error) {
      errors.push(dimResult.error);
    }

    // Validate aspect ratio
    const ratioResult = validateAspectRatio(dimensions.width, dimensions.height, expectedType);
    if (!ratioResult.valid && ratioResult.error) {
      errors.push(ratioResult.error);
    }

    return {
      valid: errors.length === 0,
      errors,
      dimensions,
    };
  } catch {
    // CORS issues or network errors - can't validate client-side
    return {
      valid: true,  // Allow it through - server will validate
      errors: [],
    };
  }
}

/**
 * Suggest the best image type based on dimensions.
 */
export function suggestImageType(width: number, height: number): string | null {
  if (width <= 0 || height <= 0) {
    return null;
  }

  const ratio = width / height;

  let bestMatch: string | null = null;
  let bestDiff = Infinity;

  for (const [imageType, requirements] of Object.entries(IMAGE_REQUIREMENTS)) {
    const expectedRatio = requirements.ratio;
    const tolerance = requirements.tolerance;
    const ratioDiff = Math.abs(ratio - expectedRatio) / expectedRatio;

    if (ratioDiff <= tolerance && ratioDiff < bestDiff) {
      // Also check minimum dimensions
      if (width >= requirements.minWidth && height >= requirements.minHeight) {
        bestMatch = imageType;
        bestDiff = ratioDiff;
      }
    }
  }

  return bestMatch;
}

/**
 * Get human-readable requirements for an image type.
 */
export function getImageRequirementsDescription(imageType: string): string | null {
  const requirements = IMAGE_REQUIREMENTS[imageType];
  return requirements?.description || null;
}
