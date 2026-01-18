/**
 * Yup validation schemas for campaign forms
 */
import * as yup from 'yup';
import { CampaignType, BiddingStrategy } from '../types/campaign';
import { CAMPAIGN_TYPE_CONFIGS } from '../config/campaignTypeConfig';

/**
 * Validate Performance Max short description requirement.
 * At least one description must be 60 characters or fewer.
 */
export function validatePMaxShortDescription(descriptions: string[] | null | undefined): string[] {
  if (!descriptions?.length) return [];

  const shortMaxLength = 60;
  const hasShort = descriptions.some(d => d.length <= shortMaxLength);

  if (!hasShort) {
    return [`At least one description must be ${shortMaxLength} characters or fewer`];
  }

  return [];
}

/**
 * Check if PMax has a valid short description.
 */
export function hasPMaxShortDescription(descriptions: string[] | null | undefined): boolean {
  if (!descriptions?.length) return false;
  return descriptions.some(d => d.length <= 60);
}

/**
 * Validate keyword uniqueness within an ad group.
 * Returns list of duplicate keyword errors.
 */
export function validateKeywordUniqueness(keywords: string[] | null | undefined): string[] {
  if (!keywords?.length) return [];

  const errors: string[] = [];
  const seen = new Set<string>();

  for (const keyword of keywords) {
    const normalized = keyword.trim().toLowerCase();
    if (seen.has(normalized)) {
      errors.push(`Duplicate keyword: "${keyword}"`);
    } else {
      seen.add(normalized);
    }
  }

  return errors;
}

/**
 * Get list of duplicate keywords.
 */
export function getDuplicateKeywords(keywords: string[] | null | undefined): string[] {
  if (!keywords?.length) return [];

  const duplicates: string[] = [];
  const seen = new Set<string>();

  for (const keyword of keywords) {
    const normalized = keyword.trim().toLowerCase();
    if (seen.has(normalized)) {
      duplicates.push(keyword);
    } else {
      seen.add(normalized);
    }
  }

  return duplicates;
}

/**
 * Check if VIDEO campaigns can be created via API.
 */
export function canCreateViaApi(campaignType: CampaignType): boolean {
  const config = CAMPAIGN_TYPE_CONFIGS[campaignType];
  return config.apiCreationSupported !== false;
}

/**
 * Get warning message for campaigns that can't be created via API.
 */
export function getApiCreationWarning(campaignType: CampaignType): string | null {
  const config = CAMPAIGN_TYPE_CONFIGS[campaignType];
  if (config.apiCreationSupported === false) {
    return config.creationWarning || `${campaignType} campaigns cannot be created via the Google Ads API.`;
  }
  return null;
}

// All valid bidding strategies
const ALL_BIDDING_STRATEGIES: BiddingStrategy[] = [
  'maximize_conversions', 'maximize_conversion_value', 'maximize_clicks',
  'target_cpa', 'target_roas', 'target_cpc', 'manual_cpc', 'manual_cpm', 'target_cpm'
];

// Image assets schema
const imageAssetsSchema = yup.object({
  landscape_url: yup.string().nullable().url('Landscape image URL must be a valid URL'),
  square_url: yup.string().nullable().url('Square image URL must be a valid URL'),
  logo_url: yup.string().nullable().url('Logo URL must be a valid URL'),
}).nullable();

/**
 * Base campaign form validation schema (common fields)
 */
const baseSchemaFields = {
  name: yup
    .string()
    .required('Campaign name is required')
    .min(1, 'Campaign name is required')
    .max(255, 'Campaign name must be at most 255 characters'),

  objective: yup
    .string()
    .required('Objective is required')
    .oneOf(['SALES', 'LEADS', 'WEBSITE_TRAFFIC'], 'Invalid objective'),

  campaign_type: yup
    .string()
    .required('Campaign type is required')
    .oneOf(
      ['DEMAND_GEN', 'SEARCH', 'DISPLAY', 'VIDEO', 'SHOPPING', 'PERFORMANCE_MAX'],
      'Invalid campaign type'
    ),

  daily_budget: yup
    .number()
    .required('Daily budget is required')
    .positive('Daily budget must be positive')
    .min(1, 'Daily budget must be at least $1'),

  start_date: yup
    .string()
    .required('Start date is required')
    .test('is-future', 'Start date cannot be in the past', (value) => {
      if (!value) return false;
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return new Date(value) >= today;
    }),

  end_date: yup
    .string()
    .nullable()
    .test('is-after-start', 'End date must be after start date', function (value) {
      const { start_date } = this.parent;
      if (!value || !start_date) return true;
      return new Date(value) >= new Date(start_date);
    }),

  // Bidding strategy (validated dynamically based on campaign type)
  bidding_strategy: yup
    .string()
    .nullable()
    .oneOf([...ALL_BIDDING_STRATEGIES, null, ''] as const, 'Invalid bidding strategy'),

  target_cpa: yup
    .number()
    .nullable()
    .positive('Target CPA must be positive')
    .when('bidding_strategy', {
      is: 'target_cpa',
      then: (schema) => schema.required('Target CPA is required for this bidding strategy'),
    }),

  target_roas: yup
    .number()
    .nullable()
    .positive('Target ROAS must be positive')
    .when('bidding_strategy', {
      is: 'target_roas',
      then: (schema) => schema.required('Target ROAS is required for this bidding strategy'),
    }),

  // Legacy fields (kept for backwards compatibility)
  ad_group_name: yup
    .string()
    .nullable()
    .max(255, 'Ad group name must be at most 255 characters'),

  ad_headline: yup.string().nullable().max(255, 'Ad headline must be at most 255 characters'),
  ad_description: yup.string().nullable().max(1000, 'Ad description must be at most 1000 characters'),
  asset_url: yup.string().nullable().url('Asset URL must be a valid URL'),
  final_url: yup.string().nullable().url('Final URL must be a valid URL'),

  // New dynamic fields
  headlines: yup.array().of(yup.string().required()).nullable(),
  long_headline: yup.string().nullable().max(90, 'Long headline must be at most 90 characters'),
  descriptions: yup.array().of(yup.string().required()).nullable(),
  business_name: yup.string().nullable().max(25, 'Business name must be at most 25 characters'),
  images: imageAssetsSchema,
  keywords: yup.array().of(yup.string().max(80, 'Keyword must be at most 80 characters')).nullable(),
  video_url: yup.string().nullable().url('Video URL must be a valid URL'),
  merchant_center_id: yup.string().nullable().max(100, 'Merchant Center ID must be at most 100 characters'),
};

/**
 * Default campaign form validation schema (for backwards compatibility)
 */
export const campaignFormSchema = yup.object(baseSchemaFields);

/**
 * Create a dynamic validation schema based on campaign type
 * @param campaignType - The selected campaign type
 * @returns Yup validation schema customized for the campaign type
 */
export function getCampaignFormSchema(campaignType: CampaignType): yup.ObjectSchema<any> {
  const config = CAMPAIGN_TYPE_CONFIGS[campaignType];

  // Build type-specific validations
  const typeSpecificFields: Record<string, yup.Schema<any>> = { ...baseSchemaFields };

  // Headlines validation based on campaign type
  if (config.headlines.max > 0) {
    const headlineMaxLength = config.headlines.maxLength;
    typeSpecificFields.headlines = yup
      .array()
      .of(
        yup.string()
          .required('Headline cannot be empty')
          .max(headlineMaxLength, `Headline must be at most ${headlineMaxLength} characters`)
      )
      .nullable()
      .when('$isPublishing', {
        is: true,
        then: (schema) => config.headlines.required
          ? schema
              .required(`${campaignType} campaigns require headlines`)
              .min(config.headlines.min, `${campaignType} campaigns require at least ${config.headlines.min} headline(s)`)
              .max(config.headlines.max, `${campaignType} campaigns allow at most ${config.headlines.max} headlines`)
          : schema,
      });
  }

  // Long headline validation
  if (config.longHeadline && config.longHeadline.max > 0) {
    typeSpecificFields.long_headline = yup
      .string()
      .nullable()
      .max(config.longHeadline.maxLength, `Long headline must be at most ${config.longHeadline.maxLength} characters`)
      .when('$isPublishing', {
        is: true,
        then: (schema) => config.longHeadline?.required
          ? schema.required(`${campaignType} campaigns require a long headline`)
          : schema,
      });
  }

  // Descriptions validation based on campaign type
  if (config.descriptions.max > 0) {
    const descMaxLength = config.descriptions.maxLength;
    let descriptionSchema = yup
      .array()
      .of(
        yup.string()
          .required('Description cannot be empty')
          .max(descMaxLength, `Description must be at most ${descMaxLength} characters`)
      )
      .nullable()
      .when('$isPublishing', {
        is: true,
        then: (schema) => config.descriptions.required
          ? schema
              .required(`${campaignType} campaigns require descriptions`)
              .min(config.descriptions.min, `${campaignType} campaigns require at least ${config.descriptions.min} description(s)`)
              .max(config.descriptions.max, `${campaignType} campaigns allow at most ${config.descriptions.max} descriptions`)
          : schema,
      });

    // Add short description validation for PERFORMANCE_MAX
    if (config.descriptions.shortRequired && config.descriptions.shortMaxLength) {
      const shortMaxLength = config.descriptions.shortMaxLength;
      descriptionSchema = descriptionSchema.test(
        'has-short-description',
        `At least one description must be ${shortMaxLength} characters or fewer`,
        (descriptions) => {
          if (!descriptions?.length) return true;  // Let required validation handle empty
          return descriptions.some((d: string | undefined) => d && d.length <= shortMaxLength);
        }
      );
    }

    typeSpecificFields.descriptions = descriptionSchema;
  }

  // Business name validation
  if (config.businessName.required) {
    typeSpecificFields.business_name = yup
      .string()
      .nullable()
      .max(config.businessName.maxLength, `Business name must be at most ${config.businessName.maxLength} characters`)
      .when('$isPublishing', {
        is: true,
        then: (schema) => schema.required(`${campaignType} campaigns require a business name`),
      });
  }

  // Images validation
  if (config.images.landscape || config.images.square || config.images.logo) {
    typeSpecificFields.images = imageAssetsSchema.when('$isPublishing', {
      is: true,
      then: (schema) => schema.test(
        'has-at-least-one-image',
        `${campaignType} campaigns require at least one image`,
        (value) => {
          if (!value) return false;
          return !!(value.landscape_url || value.square_url || value.logo_url);
        }
      ),
    });
  }

  // Final URL validation
  if (config.finalUrl.required) {
    typeSpecificFields.final_url = yup
      .string()
      .nullable()
      .url('Final URL must be a valid URL')
      .when('$isPublishing', {
        is: true,
        then: (schema) => schema.required(`${campaignType} campaigns require a final URL`),
      });
  }

  // Keywords validation (SEARCH campaigns)
  if (config.keywords.required) {
    let keywordSchema = yup
      .array()
      .of(yup.string().max(80, 'Keyword must be at most 80 characters'))
      .nullable()
      .when('$isPublishing', {
        is: true,
        then: (schema) => schema
          .required(`${campaignType} campaigns require keywords`)
          .min(1, `${campaignType} campaigns require at least one keyword`),
      });

    // Add keyword uniqueness validation
    if (config.keywords.unique) {
      keywordSchema = keywordSchema.test(
        'unique-keywords',
        'Keywords must be unique',
        (keywords) => {
          if (!keywords?.length) return true;
          const seen = new Set<string>();
          for (const keyword of keywords) {
            if (!keyword) continue;
            const normalized = keyword.trim().toLowerCase();
            if (seen.has(normalized)) {
              return false;
            }
            seen.add(normalized);
          }
          return true;
        }
      );
    }

    typeSpecificFields.keywords = keywordSchema;
  }

  // Video URL validation (VIDEO campaigns)
  if (config.videoUrl.required) {
    typeSpecificFields.video_url = yup
      .string()
      .nullable()
      .url('Video URL must be a valid URL')
      .when('$isPublishing', {
        is: true,
        then: (schema) => schema.required(`${campaignType} campaigns require a video URL`),
      });
  }

  // Merchant Center ID validation (SHOPPING campaigns)
  if (config.merchantCenterId.required) {
    typeSpecificFields.merchant_center_id = yup
      .string()
      .nullable()
      .max(100, 'Merchant Center ID must be at most 100 characters')
      .when('$isPublishing', {
        is: true,
        then: (schema) => schema.required(`${campaignType} campaigns require a Merchant Center ID`),
      });
  }

  // Bidding strategy validation - check it's valid for this campaign type
  const validBiddingStrategies = config.biddingOptions.map(opt => opt.value);
  typeSpecificFields.bidding_strategy = yup
    .string()
    .nullable()
    .test(
      'valid-for-campaign-type',
      `Invalid bidding strategy for ${campaignType} campaigns`,
      (value) => {
        if (!value) return true; // Optional
        return validBiddingStrategies.includes(value as any);
      }
    );

  return yup.object(typeSpecificFields);
}

/**
 * Validate bidding strategy is appropriate for campaign type
 */
export function validateBiddingStrategyForType(
  biddingStrategy: BiddingStrategy | null | undefined,
  campaignType: CampaignType
): boolean {
  if (!biddingStrategy) return true;
  const config = CAMPAIGN_TYPE_CONFIGS[campaignType];
  return config.biddingOptions.some(opt => opt.value === biddingStrategy);
}

/**
 * Get character limit for headlines based on campaign type
 */
export function getHeadlineMaxLength(campaignType: CampaignType): number {
  return CAMPAIGN_TYPE_CONFIGS[campaignType].headlines.maxLength;
}

/**
 * Get character limit for descriptions based on campaign type
 */
export function getDescriptionMaxLength(campaignType: CampaignType): number {
  return CAMPAIGN_TYPE_CONFIGS[campaignType].descriptions.maxLength;
}

export type CampaignFormValues = yup.InferType<typeof campaignFormSchema>;
