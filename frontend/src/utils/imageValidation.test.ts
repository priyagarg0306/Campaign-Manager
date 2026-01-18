import {
  IMAGE_REQUIREMENTS,
  validateAspectRatio,
  validateImageDimensions,
  suggestImageType,
  getImageRequirementsDescription,
} from './imageValidation';

describe('IMAGE_REQUIREMENTS', () => {
  it('has landscape requirements', () => {
    expect(IMAGE_REQUIREMENTS.landscape).toBeDefined();
    expect(IMAGE_REQUIREMENTS.landscape.ratio).toBe(1.91);
    expect(IMAGE_REQUIREMENTS.landscape.minWidth).toBe(600);
    expect(IMAGE_REQUIREMENTS.landscape.minHeight).toBe(314);
  });

  it('has square requirements', () => {
    expect(IMAGE_REQUIREMENTS.square).toBeDefined();
    expect(IMAGE_REQUIREMENTS.square.ratio).toBe(1.0);
    expect(IMAGE_REQUIREMENTS.square.minWidth).toBe(300);
    expect(IMAGE_REQUIREMENTS.square.minHeight).toBe(300);
  });

  it('has logo requirements', () => {
    expect(IMAGE_REQUIREMENTS.logo).toBeDefined();
    expect(IMAGE_REQUIREMENTS.logo.ratio).toBe(1.0);
    expect(IMAGE_REQUIREMENTS.logo.minWidth).toBe(128);
    expect(IMAGE_REQUIREMENTS.logo.minHeight).toBe(128);
  });

  it('has logo_landscape requirements', () => {
    expect(IMAGE_REQUIREMENTS.logo_landscape).toBeDefined();
    expect(IMAGE_REQUIREMENTS.logo_landscape.ratio).toBe(4.0);
    expect(IMAGE_REQUIREMENTS.logo_landscape.minWidth).toBe(512);
    expect(IMAGE_REQUIREMENTS.logo_landscape.minHeight).toBe(128);
  });
});

describe('validateAspectRatio', () => {
  describe('landscape images', () => {
    it('validates correct landscape ratio', () => {
      const result = validateAspectRatio(1910, 1000, 'landscape');
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('rejects incorrect landscape ratio', () => {
      const result = validateAspectRatio(1000, 1000, 'landscape');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('aspect ratio');
    });

    it('accepts landscape with tolerance', () => {
      // 1.91 with 2% tolerance = 1.8718 to 1.9482
      const result = validateAspectRatio(955, 500, 'landscape'); // ratio = 1.91
      expect(result.valid).toBe(true);
    });
  });

  describe('square images', () => {
    it('validates correct square ratio', () => {
      const result = validateAspectRatio(500, 500, 'square');
      expect(result.valid).toBe(true);
    });

    it('rejects non-square ratio', () => {
      const result = validateAspectRatio(500, 300, 'square');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('aspect ratio');
    });
  });

  describe('logo images', () => {
    it('validates correct logo ratio', () => {
      const result = validateAspectRatio(256, 256, 'logo');
      expect(result.valid).toBe(true);
    });

    it('rejects non-square logo', () => {
      const result = validateAspectRatio(256, 128, 'logo');
      expect(result.valid).toBe(false);
    });
  });

  describe('landscape logo images', () => {
    it('validates correct landscape logo ratio (4:1)', () => {
      const result = validateAspectRatio(512, 128, 'logo_landscape');
      expect(result.valid).toBe(true);
    });

    it('rejects non-4:1 landscape logo', () => {
      const result = validateAspectRatio(256, 128, 'logo_landscape');
      expect(result.valid).toBe(false);
    });
  });

  describe('error handling', () => {
    it('rejects unknown image type', () => {
      const result = validateAspectRatio(500, 500, 'unknown_type');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Unknown image type');
    });

    it('rejects zero width', () => {
      const result = validateAspectRatio(0, 500, 'square');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid image dimensions');
    });

    it('rejects zero height', () => {
      const result = validateAspectRatio(500, 0, 'square');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid image dimensions');
    });

    it('rejects negative dimensions', () => {
      const result = validateAspectRatio(-100, 100, 'square');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid image dimensions');
    });
  });
});

describe('validateImageDimensions', () => {
  describe('landscape images', () => {
    it('validates dimensions meeting minimums', () => {
      const result = validateImageDimensions(600, 314, 'landscape');
      expect(result.valid).toBe(true);
    });

    it('validates dimensions exceeding minimums', () => {
      const result = validateImageDimensions(1200, 628, 'landscape');
      expect(result.valid).toBe(true);
    });

    it('rejects width below minimum', () => {
      const result = validateImageDimensions(599, 314, 'landscape');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('width');
      expect(result.error).toContain('600');
    });

    it('rejects height below minimum', () => {
      const result = validateImageDimensions(600, 313, 'landscape');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('height');
      expect(result.error).toContain('314');
    });
  });

  describe('square images', () => {
    it('validates dimensions meeting minimums', () => {
      const result = validateImageDimensions(300, 300, 'square');
      expect(result.valid).toBe(true);
    });

    it('rejects dimensions below minimum', () => {
      const result = validateImageDimensions(299, 299, 'square');
      expect(result.valid).toBe(false);
    });
  });

  describe('logo images', () => {
    it('validates logo dimensions meeting minimums', () => {
      const result = validateImageDimensions(128, 128, 'logo');
      expect(result.valid).toBe(true);
    });

    it('rejects logo dimensions below minimum', () => {
      const result = validateImageDimensions(127, 127, 'logo');
      expect(result.valid).toBe(false);
    });
  });

  describe('landscape logo images', () => {
    it('validates landscape logo dimensions', () => {
      const result = validateImageDimensions(512, 128, 'logo_landscape');
      expect(result.valid).toBe(true);
    });

    it('rejects landscape logo with insufficient width', () => {
      const result = validateImageDimensions(511, 128, 'logo_landscape');
      expect(result.valid).toBe(false);
    });
  });

  describe('error handling', () => {
    it('rejects unknown image type', () => {
      const result = validateImageDimensions(500, 500, 'invalid_type');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Unknown image type');
    });
  });
});

describe('suggestImageType', () => {
  it('suggests landscape for 1.91:1 ratio images', () => {
    const result = suggestImageType(1910, 1000);
    expect(result).toBe('landscape');
  });

  it('suggests square for 1:1 ratio images with large dimensions', () => {
    const result = suggestImageType(500, 500);
    expect(result).toBe('square');
  });

  it('suggests logo for 1:1 ratio images with small dimensions', () => {
    const result = suggestImageType(150, 150);
    expect(result).toBe('logo');
  });

  it('suggests logo_landscape for 4:1 ratio images', () => {
    const result = suggestImageType(512, 128);
    expect(result).toBe('logo_landscape');
  });

  it('returns null for invalid dimensions', () => {
    expect(suggestImageType(0, 0)).toBeNull();
    expect(suggestImageType(-100, 100)).toBeNull();
    expect(suggestImageType(100, -100)).toBeNull();
  });

  it('returns null when no type matches', () => {
    // 3:1 ratio doesn't match any requirement
    const result = suggestImageType(900, 300);
    expect(result).toBeNull();
  });

  it('returns null when dimensions are too small', () => {
    // Square ratio but dimensions too small for any type
    const result = suggestImageType(50, 50);
    expect(result).toBeNull();
  });

  it('prefers exact match over tolerance match', () => {
    // Exact 1:1 ratio with sufficient dimensions for square
    const result = suggestImageType(300, 300);
    expect(result).toBe('square');
  });
});

describe('getImageRequirementsDescription', () => {
  it('returns description for landscape', () => {
    const description = getImageRequirementsDescription('landscape');
    expect(description).toBe('Landscape marketing image (1.91:1) - minimum 600x314 pixels');
  });

  it('returns description for square', () => {
    const description = getImageRequirementsDescription('square');
    expect(description).toBe('Square marketing image (1:1) - minimum 300x300 pixels');
  });

  it('returns description for logo', () => {
    const description = getImageRequirementsDescription('logo');
    expect(description).toBe('Square logo (1:1) - minimum 128x128 pixels');
  });

  it('returns description for logo_landscape', () => {
    const description = getImageRequirementsDescription('logo_landscape');
    expect(description).toBe('Landscape logo (4:1) - minimum 512x128 pixels');
  });

  it('returns null for unknown image type', () => {
    const description = getImageRequirementsDescription('unknown');
    expect(description).toBeNull();
  });

  it('returns null for empty string', () => {
    const description = getImageRequirementsDescription('');
    expect(description).toBeNull();
  });
});
