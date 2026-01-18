import {
  validatePMaxShortDescription,
  hasPMaxShortDescription,
  validateKeywordUniqueness,
  getDuplicateKeywords,
  canCreateViaApi,
  getApiCreationWarning,
  getCampaignFormSchema,
  validateBiddingStrategyForType,
  getHeadlineMaxLength,
  getDescriptionMaxLength,
  campaignFormSchema,
} from './validation';

describe('validatePMaxShortDescription', () => {
  it('returns empty array for null descriptions', () => {
    expect(validatePMaxShortDescription(null)).toEqual([]);
  });

  it('returns empty array for undefined descriptions', () => {
    expect(validatePMaxShortDescription(undefined)).toEqual([]);
  });

  it('returns empty array for empty descriptions array', () => {
    expect(validatePMaxShortDescription([])).toEqual([]);
  });

  it('returns empty array when at least one short description exists', () => {
    const descriptions = ['Short', 'This is a much longer description that exceeds sixty characters'];
    expect(validatePMaxShortDescription(descriptions)).toEqual([]);
  });

  it('returns error when all descriptions are too long', () => {
    const descriptions = [
      'This is a very long description that definitely exceeds the sixty character limit',
      'Another long description that also exceeds the maximum allowed length for short descriptions',
    ];
    const errors = validatePMaxShortDescription(descriptions);
    expect(errors).toHaveLength(1);
    expect(errors[0]).toContain('60 characters');
  });
});

describe('hasPMaxShortDescription', () => {
  it('returns false for null', () => {
    expect(hasPMaxShortDescription(null)).toBe(false);
  });

  it('returns false for undefined', () => {
    expect(hasPMaxShortDescription(undefined)).toBe(false);
  });

  it('returns false for empty array', () => {
    expect(hasPMaxShortDescription([])).toBe(false);
  });

  it('returns true when short description exists', () => {
    expect(hasPMaxShortDescription(['Short desc'])).toBe(true);
  });

  it('returns true when at least one is short', () => {
    const descriptions = ['Short', 'This is way too long to be considered a short description'];
    expect(hasPMaxShortDescription(descriptions)).toBe(true);
  });

  it('returns false when all descriptions exceed 60 chars', () => {
    const descriptions = [
      'This description is definitely longer than sixty characters allowed',
      'Another description that is also too long for the short requirement',
    ];
    expect(hasPMaxShortDescription(descriptions)).toBe(false);
  });
});

describe('validateKeywordUniqueness', () => {
  it('returns empty array for null', () => {
    expect(validateKeywordUniqueness(null)).toEqual([]);
  });

  it('returns empty array for undefined', () => {
    expect(validateKeywordUniqueness(undefined)).toEqual([]);
  });

  it('returns empty array for empty keywords', () => {
    expect(validateKeywordUniqueness([])).toEqual([]);
  });

  it('returns empty array for unique keywords', () => {
    expect(validateKeywordUniqueness(['one', 'two', 'three'])).toEqual([]);
  });

  it('returns errors for duplicate keywords', () => {
    const errors = validateKeywordUniqueness(['test', 'TEST', 'test']);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0]).toContain('Duplicate keyword');
  });

  it('handles case-insensitive duplicates', () => {
    const errors = validateKeywordUniqueness(['Hello', 'HELLO']);
    expect(errors.length).toBe(1);
  });

  it('handles whitespace in keywords', () => {
    const errors = validateKeywordUniqueness(['test', ' test ']);
    expect(errors.length).toBe(1);
  });
});

describe('getDuplicateKeywords', () => {
  it('returns empty array for null', () => {
    expect(getDuplicateKeywords(null)).toEqual([]);
  });

  it('returns empty array for unique keywords', () => {
    expect(getDuplicateKeywords(['one', 'two'])).toEqual([]);
  });

  it('returns duplicate keywords', () => {
    const duplicates = getDuplicateKeywords(['test', 'TEST', 'unique']);
    expect(duplicates).toContain('TEST');
  });
});

describe('canCreateViaApi', () => {
  it('returns true for DEMAND_GEN', () => {
    expect(canCreateViaApi('DEMAND_GEN')).toBe(true);
  });

  it('returns true for SEARCH', () => {
    expect(canCreateViaApi('SEARCH')).toBe(true);
  });

  it('returns true for DISPLAY', () => {
    expect(canCreateViaApi('DISPLAY')).toBe(true);
  });

  it('returns true for SHOPPING', () => {
    expect(canCreateViaApi('SHOPPING')).toBe(true);
  });

  it('returns true for PERFORMANCE_MAX', () => {
    expect(canCreateViaApi('PERFORMANCE_MAX')).toBe(true);
  });

  it('returns false for VIDEO', () => {
    expect(canCreateViaApi('VIDEO')).toBe(false);
  });
});

describe('getApiCreationWarning', () => {
  it('returns null for DEMAND_GEN', () => {
    expect(getApiCreationWarning('DEMAND_GEN')).toBeNull();
  });

  it('returns null for SEARCH', () => {
    expect(getApiCreationWarning('SEARCH')).toBeNull();
  });

  it('returns warning message for VIDEO', () => {
    const warning = getApiCreationWarning('VIDEO');
    expect(warning).not.toBeNull();
    expect(warning).toContain('VIDEO');
  });
});

describe('validateBiddingStrategyForType', () => {
  it('returns true for null bidding strategy', () => {
    expect(validateBiddingStrategyForType(null, 'DEMAND_GEN')).toBe(true);
  });

  it('returns true for undefined bidding strategy', () => {
    expect(validateBiddingStrategyForType(undefined, 'DEMAND_GEN')).toBe(true);
  });

  it('returns true for valid DEMAND_GEN bidding strategy', () => {
    expect(validateBiddingStrategyForType('maximize_conversions', 'DEMAND_GEN')).toBe(true);
  });

  it('returns true for valid SEARCH bidding strategy', () => {
    expect(validateBiddingStrategyForType('maximize_clicks', 'SEARCH')).toBe(true);
  });

  it('returns false for invalid bidding strategy for campaign type', () => {
    // target_cpm is not valid for SEARCH campaigns
    expect(validateBiddingStrategyForType('target_cpm', 'SEARCH')).toBe(false);
  });
});

describe('getHeadlineMaxLength', () => {
  it('returns correct max length for DEMAND_GEN', () => {
    expect(getHeadlineMaxLength('DEMAND_GEN')).toBe(40);
  });

  it('returns correct max length for SEARCH', () => {
    expect(getHeadlineMaxLength('SEARCH')).toBe(30);
  });

  it('returns correct max length for PERFORMANCE_MAX', () => {
    expect(getHeadlineMaxLength('PERFORMANCE_MAX')).toBe(30);
  });
});

describe('getDescriptionMaxLength', () => {
  it('returns correct max length for DEMAND_GEN', () => {
    expect(getDescriptionMaxLength('DEMAND_GEN')).toBe(90);
  });

  it('returns correct max length for SEARCH', () => {
    expect(getDescriptionMaxLength('SEARCH')).toBe(90);
  });
});

describe('campaignFormSchema', () => {
  it('validates required name field', async () => {
    const data = {
      objective: 'SALES',
      campaign_type: 'DEMAND_GEN',
      daily_budget: 100,
      start_date: '2030-01-01',
    };

    await expect(campaignFormSchema.validate(data)).rejects.toThrow('Campaign name is required');
  });

  it('validates name max length', async () => {
    const data = {
      name: 'a'.repeat(256),
      objective: 'SALES',
      campaign_type: 'DEMAND_GEN',
      daily_budget: 100,
      start_date: '2030-01-01',
    };

    await expect(campaignFormSchema.validate(data)).rejects.toThrow('255 characters');
  });

  it('validates objective values', async () => {
    const data = {
      name: 'Test',
      objective: 'INVALID',
      campaign_type: 'DEMAND_GEN',
      daily_budget: 100,
      start_date: '2030-01-01',
    };

    await expect(campaignFormSchema.validate(data)).rejects.toThrow('Invalid objective');
  });

  it('validates positive daily budget', async () => {
    const data = {
      name: 'Test',
      objective: 'SALES',
      campaign_type: 'DEMAND_GEN',
      daily_budget: -100,
      start_date: '2030-01-01',
    };

    await expect(campaignFormSchema.validate(data)).rejects.toThrow('at least $1');
  });

  it('accepts valid campaign data', async () => {
    const data = {
      name: 'Test Campaign',
      objective: 'SALES',
      campaign_type: 'DEMAND_GEN',
      daily_budget: 100,
      start_date: '2030-01-01',
    };

    const result = await campaignFormSchema.validate(data);
    expect(result.name).toBe('Test Campaign');
  });
});

describe('getCampaignFormSchema', () => {
  it('returns schema for DEMAND_GEN', () => {
    const schema = getCampaignFormSchema('DEMAND_GEN');
    expect(schema).toBeDefined();
  });

  it('returns schema for SEARCH', () => {
    const schema = getCampaignFormSchema('SEARCH');
    expect(schema).toBeDefined();
  });

  it('returns schema for DISPLAY', () => {
    const schema = getCampaignFormSchema('DISPLAY');
    expect(schema).toBeDefined();
  });

  it('returns schema for VIDEO', () => {
    const schema = getCampaignFormSchema('VIDEO');
    expect(schema).toBeDefined();
  });

  it('returns schema for SHOPPING', () => {
    const schema = getCampaignFormSchema('SHOPPING');
    expect(schema).toBeDefined();
  });

  it('returns schema for PERFORMANCE_MAX', () => {
    const schema = getCampaignFormSchema('PERFORMANCE_MAX');
    expect(schema).toBeDefined();
  });

  it('validates headline max length for DEMAND_GEN', async () => {
    const schema = getCampaignFormSchema('DEMAND_GEN');
    const data = {
      name: 'Test',
      objective: 'SALES',
      campaign_type: 'DEMAND_GEN',
      daily_budget: 100,
      start_date: '2030-01-01',
      headlines: ['a'.repeat(50)], // Exceeds 40 char limit
    };

    await expect(schema.validate(data)).rejects.toThrow('40 characters');
  });

  it('validates headline max length for SEARCH', async () => {
    const schema = getCampaignFormSchema('SEARCH');
    const data = {
      name: 'Test',
      objective: 'SALES',
      campaign_type: 'SEARCH',
      daily_budget: 100,
      start_date: '2030-01-01',
      headlines: ['a'.repeat(35)], // Exceeds 30 char limit
    };

    await expect(schema.validate(data)).rejects.toThrow('30 characters');
  });

  it('validates bidding strategy for campaign type', async () => {
    const schema = getCampaignFormSchema('SEARCH');
    const data = {
      name: 'Test',
      objective: 'SALES',
      campaign_type: 'SEARCH',
      daily_budget: 100,
      start_date: '2030-01-01',
      bidding_strategy: 'target_cpm', // Invalid for SEARCH
    };

    await expect(schema.validate(data)).rejects.toThrow('Invalid bidding strategy');
  });
});
