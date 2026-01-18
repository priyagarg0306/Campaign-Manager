/**
 * Campaign Form Component
 * Dynamic form for creating marketing campaigns with type-specific fields
 */
import React, { memo, useCallback, useEffect, useMemo } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Campaign, CampaignObjective, CampaignType, BiddingStrategy, ImageAssets } from '../types/campaign';
import {
  getCampaignTypeConfig,
  shouldShowField,
  getDefaultBiddingStrategy,
  BIDDING_STRATEGIES,
} from '../config/campaignTypeConfig';
import {
  hasPMaxShortDescription,
  getDuplicateKeywords,
  getApiCreationWarning,
} from '../utils/validation';
import { InfoTooltip } from './InfoTooltip';
import './CampaignForm.css';

// Form data interface with properly typed arrays
interface FormData {
  name: string;
  objective: CampaignObjective;
  campaign_type: CampaignType;
  daily_budget: number;
  start_date: string;
  end_date?: string;
  bidding_strategy?: BiddingStrategy;
  target_cpa?: number;
  target_roas?: number;
  ad_group_name?: string;
  ad_headline?: string;
  ad_description?: string;
  asset_url?: string;
  final_url?: string;
  headlines: { value: string }[];
  long_headline?: string;
  descriptions: { value: string }[];
  business_name?: string;
  images?: ImageAssets;
  keywords: { value: string }[];
  video_url?: string;
  merchant_center_id?: string;
}

interface CampaignFormProps {
  onSubmit: (data: any) => Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
  initialData?: Campaign | null;
  mode?: 'create' | 'edit';
}

const objectives: { value: CampaignObjective; label: string }[] = [
  { value: 'SALES', label: 'Sales' },
  { value: 'LEADS', label: 'Leads' },
  { value: 'WEBSITE_TRAFFIC', label: 'Website Traffic' },
];

const campaignTypes: { value: CampaignType; label: string; description: string }[] = [
  { value: 'DEMAND_GEN', label: 'Demand Gen', description: 'Drive demand across YouTube, Gmail, and Discover' },
  { value: 'SEARCH', label: 'Search', description: 'Text ads on Google Search results' },
  { value: 'DISPLAY', label: 'Display', description: 'Visual ads across the Google Display Network' },
  { value: 'VIDEO', label: 'Video', description: 'Video ads on YouTube and across the web' },
  { value: 'SHOPPING', label: 'Shopping', description: 'Product listings from Merchant Center' },
  { value: 'PERFORMANCE_MAX', label: 'Performance Max', description: 'Access all Google Ads inventory' },
];

// Base validation schema
const createValidationSchema = (campaignType: CampaignType) => {
  const config = getCampaignTypeConfig(campaignType);

  return yup.object({
    name: yup.string().required('Campaign name is required').min(1, 'Campaign name is required'),
    objective: yup.string().required('Objective is required'),
    campaign_type: yup.string().required('Campaign type is required'),
    daily_budget: yup
      .number()
      .typeError('Daily budget must be a number')
      .required('Daily budget is required')
      .positive('Daily budget must be positive')
      .min(1, 'Daily budget must be at least $1'),
    start_date: yup.string().required('Start date is required'),
    end_date: yup.string().nullable(),
    bidding_strategy: yup.string().nullable(),
    target_cpa: yup.number().nullable().when('bidding_strategy', {
      is: 'target_cpa',
      then: (schema) => schema.required('Target CPA is required').positive('Target CPA must be positive'),
    }),
    target_roas: yup.number().nullable().when('bidding_strategy', {
      is: 'target_roas',
      then: (schema) => schema.required('Target ROAS is required').positive('Target ROAS must be positive'),
    }),
    headlines: yup.array().of(
      yup.object({ value: yup.string() })
    ).test('min-headlines', `At least ${config.headlines.min} headline(s) required`, (value) => {
      if (!config.headlines.required || config.headlines.min === 0) return true;
      const filled = value?.filter(h => h.value?.trim()).length || 0;
      return filled >= config.headlines.min;
    }),
    descriptions: yup.array().of(
      yup.object({ value: yup.string() })
    ).test('min-descriptions', `At least ${config.descriptions.min} description(s) required`, (value) => {
      if (!config.descriptions.required || config.descriptions.min === 0) return true;
      const filled = value?.filter(d => d.value?.trim()).length || 0;
      return filled >= config.descriptions.min;
    }),
    final_url: config.finalUrl.required
      ? yup.string().required('Final URL is required').url('Must be a valid URL')
      : yup.string().nullable().url('Must be a valid URL'),
    keywords: config.keywords.required
      ? yup.array().of(yup.object({ value: yup.string() })).test('min-keywords', 'At least one keyword is required', (value) => {
          const filled = value?.filter(k => k.value?.trim()).length || 0;
          return filled >= 1;
        })
      : yup.array().nullable(),
    video_url: config.videoUrl.required
      ? yup.string().required('Video URL is required').url('Must be a valid URL')
      : yup.string().nullable(),
    merchant_center_id: config.merchantCenterId.required
      ? yup.string().required('Merchant Center ID is required')
      : yup.string().nullable(),
    business_name: config.businessName.required
      ? yup.string().required('Business name is required')
      : yup.string().nullable(),
    long_headline: yup.string().nullable(),
    ad_group_name: yup.string().nullable(),
    images: yup.object().nullable(),
  });
};

// Character counter component
const CharacterCounter: React.FC<{ current: number; max: number }> = ({ current, max }) => {
  const isOverLimit = current > max;
  return (
    <span className={`char-counter ${isOverLimit ? 'over-limit' : ''}`}>
      {current}/{max}
    </span>
  );
};

const CampaignFormComponent: React.FC<CampaignFormProps> = ({
  onSubmit,
  onCancel,
  loading = false,
  initialData = null,
  mode = 'create',
}) => {
  // Compute default values based on initialData for edit mode
  const computedDefaultValues = useMemo(() => {
    if (!initialData) {
      return {
        name: '',
        objective: 'SALES' as CampaignObjective,
        campaign_type: 'DEMAND_GEN' as CampaignType,
        daily_budget: 10,
        start_date: '',
        end_date: '',
        bidding_strategy: getDefaultBiddingStrategy('DEMAND_GEN'),
        target_cpa: undefined,
        target_roas: undefined,
        ad_group_name: '',
        ad_headline: '',
        ad_description: '',
        asset_url: '',
        final_url: '',
        headlines: [{ value: '' }],
        long_headline: '',
        descriptions: [{ value: '' }],
        business_name: '',
        images: { landscape_url: '', square_url: '', logo_url: '' },
        keywords: [{ value: '' }],
        video_url: '',
        merchant_center_id: '',
      };
    }

    // Convert data from Campaign format to form format for edit mode
    return {
      name: initialData.name,
      objective: initialData.objective,
      campaign_type: initialData.campaign_type,
      // Convert daily_budget from micros to USD
      daily_budget: initialData.daily_budget / 1_000_000,
      start_date: initialData.start_date || '',
      end_date: initialData.end_date || '',
      bidding_strategy: initialData.bidding_strategy || getDefaultBiddingStrategy(initialData.campaign_type),
      // Convert target_cpa from micros to USD
      target_cpa: initialData.target_cpa ? initialData.target_cpa / 1_000_000 : undefined,
      target_roas: initialData.target_roas || undefined,
      ad_group_name: initialData.ad_group_name || '',
      ad_headline: initialData.ad_headline || '',
      ad_description: initialData.ad_description || '',
      asset_url: initialData.asset_url || '',
      final_url: initialData.final_url || '',
      // Convert string arrays to field array format
      headlines: initialData.headlines?.length
        ? initialData.headlines.map(h => ({ value: h }))
        : [{ value: '' }],
      long_headline: initialData.long_headline || '',
      descriptions: initialData.descriptions?.length
        ? initialData.descriptions.map(d => ({ value: d }))
        : [{ value: '' }],
      business_name: initialData.business_name || '',
      images: {
        landscape_url: initialData.images?.landscape_url || '',
        square_url: initialData.images?.square_url || '',
        logo_url: initialData.images?.logo_url || '',
      },
      keywords: initialData.keywords?.length
        ? initialData.keywords.map(k => ({ value: k }))
        : [{ value: '' }],
      video_url: initialData.video_url || '',
      merchant_center_id: initialData.merchant_center_id || '',
    };
  }, [initialData]);

  const [campaignType, setCampaignType] = React.useState<CampaignType>(
    initialData?.campaign_type || 'DEMAND_GEN'
  );
  const config = useMemo(() => getCampaignTypeConfig(campaignType), [campaignType]);
  const validationSchema = useMemo(() => createValidationSchema(campaignType), [campaignType]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    watch,
    control,
    setValue,
    trigger,
  } = useForm<FormData>({
    resolver: yupResolver(validationSchema) as any,
    mode: 'onSubmit',
    defaultValues: computedDefaultValues,
  });

  // Field arrays for multiple headlines, descriptions, and keywords
  const {
    fields: headlineFields,
    append: appendHeadline,
    remove: removeHeadline,
  } = useFieldArray({ control, name: 'headlines' });

  const {
    fields: descriptionFields,
    append: appendDescription,
    remove: removeDescription,
  } = useFieldArray({ control, name: 'descriptions' });

  const {
    fields: keywordFields,
    append: appendKeyword,
    remove: removeKeyword,
  } = useFieldArray({ control, name: 'keywords' });

  // Reset form when initialData changes (switching between create/edit modes)
  useEffect(() => {
    reset(computedDefaultValues);
    setCampaignType(initialData?.campaign_type || 'DEMAND_GEN');
  }, [initialData, computedDefaultValues, reset]);

  // Watch campaign type changes
  const watchedCampaignType = watch('campaign_type') as CampaignType;
  const watchedBiddingStrategy = watch('bidding_strategy') as BiddingStrategy;

  // Update local state when campaign type changes
  useEffect(() => {
    if (watchedCampaignType && watchedCampaignType !== campaignType) {
      setCampaignType(watchedCampaignType);
      // Set default bidding strategy for new campaign type
      const defaultStrategy = getDefaultBiddingStrategy(watchedCampaignType);
      setValue('bidding_strategy', defaultStrategy);

      const newConfig = getCampaignTypeConfig(watchedCampaignType);
      const showHeadlinesField = shouldShowField(watchedCampaignType, 'headlines');
      const showDescriptionsField = shouldShowField(watchedCampaignType, 'descriptions');

      // Calculate target count for headlines - reset to minimum required for new type
      const targetHeadlines = (!showHeadlinesField || newConfig.headlines.max === 0)
        ? 1  // Keep 1 field even if not shown
        : Math.max(newConfig.headlines.min, 1);

      // Adjust headline fields to target count
      if (headlineFields.length > targetHeadlines) {
        // Remove excess fields from the end
        const indicesToRemove = Array.from(
          { length: headlineFields.length - targetHeadlines },
          (_, i) => targetHeadlines + i
        ).reverse();
        indicesToRemove.forEach(i => removeHeadline(i));
      } else if (headlineFields.length < targetHeadlines) {
        // Add fields to meet minimum
        const toAdd = targetHeadlines - headlineFields.length;
        for (let i = 0; i < toAdd; i++) {
          appendHeadline({ value: '' });
        }
      }

      // Calculate target count for descriptions - reset to minimum required for new type
      const targetDescriptions = (!showDescriptionsField || newConfig.descriptions.max === 0)
        ? 1  // Keep 1 field even if not shown
        : Math.max(newConfig.descriptions.min, 1);

      // Adjust description fields to target count
      if (descriptionFields.length > targetDescriptions) {
        // Remove excess fields from the end
        const indicesToRemove = Array.from(
          { length: descriptionFields.length - targetDescriptions },
          (_, i) => targetDescriptions + i
        ).reverse();
        indicesToRemove.forEach(i => removeDescription(i));
      } else if (descriptionFields.length < targetDescriptions) {
        // Add fields to meet minimum
        const toAdd = targetDescriptions - descriptionFields.length;
        for (let i = 0; i < toAdd; i++) {
          appendDescription({ value: '' });
        }
      }
    }
  }, [watchedCampaignType, campaignType, setValue, headlineFields.length, descriptionFields.length, appendHeadline, appendDescription, removeHeadline, removeDescription]);

  const handleFormSubmit = useCallback(async (data: FormData) => {
    try {
      // Extract values from object arrays and filter empty ones
      const headlineValues = data.headlines?.map(h => h.value).filter(v => v?.trim()) || [];
      const descriptionValues = data.descriptions?.map(d => d.value).filter(v => v?.trim()) || [];
      const keywordValues = data.keywords?.map(k => k.value).filter(v => v?.trim()) || [];

      // Build images object with only non-empty URLs
      const imagesData: { landscape_url?: string; square_url?: string; logo_url?: string } = {};
      if (data.images?.landscape_url?.trim()) {
        imagesData.landscape_url = data.images.landscape_url.trim();
      }
      if (data.images?.square_url?.trim()) {
        imagesData.square_url = data.images.square_url.trim();
      }
      if (data.images?.logo_url?.trim()) {
        imagesData.logo_url = data.images.logo_url.trim();
      }
      const hasImages = Object.keys(imagesData).length > 0;

      // Convert daily_budget from USD to micros
      const formattedData: any = {
        name: data.name,
        objective: data.objective,
        campaign_type: data.campaign_type,
        daily_budget: Math.round(data.daily_budget * 1_000_000),
        start_date: data.start_date,
        end_date: data.end_date || undefined,
        ad_group_name: data.ad_group_name || undefined,
        // Legacy fields
        ad_headline: data.ad_headline || undefined,
        ad_description: data.ad_description || undefined,
        asset_url: data.asset_url || undefined,
        final_url: data.final_url || undefined,
        // New fields
        bidding_strategy: data.bidding_strategy || undefined,
        target_cpa: data.target_cpa ? Math.round(data.target_cpa * 1_000_000) : undefined,
        target_roas: data.target_roas || undefined,
        headlines: headlineValues.length > 0 ? headlineValues : undefined,
        long_headline: data.long_headline || undefined,
        descriptions: descriptionValues.length > 0 ? descriptionValues : undefined,
        business_name: data.business_name || undefined,
        images: hasImages ? imagesData : undefined,
        keywords: keywordValues.length > 0 ? keywordValues : undefined,
        video_url: data.video_url || undefined,
        merchant_center_id: data.merchant_center_id || undefined,
      };
      await onSubmit(formattedData);
      reset();
    } catch (error) {
      // Error is handled by parent component
    }
  }, [onSubmit, reset]);

  const isLoading = loading || isSubmitting;

  // Determine which sections to show
  const showHeadlines = shouldShowField(campaignType, 'headlines');
  const showLongHeadline = shouldShowField(campaignType, 'longHeadline');
  const showDescriptions = shouldShowField(campaignType, 'descriptions');
  const showBusinessName = shouldShowField(campaignType, 'businessName');
  const showImages = shouldShowField(campaignType, 'images');
  const showKeywords = shouldShowField(campaignType, 'keywords');
  const showVideoUrl = shouldShowField(campaignType, 'videoUrl');
  const showMerchantCenterId = shouldShowField(campaignType, 'merchantCenterId');
  const showFinalUrl = shouldShowField(campaignType, 'finalUrl');

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="campaign-form">
      <h2>{mode === 'edit' ? 'Edit Campaign' : 'Create New Campaign'}</h2>

      {/* Campaign Name */}
      <div className="form-group">
        <label htmlFor="name">
          Campaign Name <span className="required">*</span>
        </label>
        <input
          id="name"
          type="text"
          {...register('name')}
          className={errors.name ? 'error' : ''}
          aria-required="true"
          aria-invalid={!!errors.name}
          disabled={isLoading}
          placeholder="Enter campaign name"
        />
        {errors.name && (
          <span className="error-message" role="alert">
            {errors.name.message}
          </span>
        )}
      </div>

      {/* Objective */}
      <div className="form-group">
        <label htmlFor="objective">
          Objective <span className="required">*</span>
          <InfoTooltip
            items={[
              { label: 'Sales', description: 'Drive purchases and transactions' },
              { label: 'Leads', description: 'Generate sign-ups and inquiries' },
              { label: 'Website Traffic', description: 'Increase visits to your website' },
            ]}
          />
        </label>
        <select
          id="objective"
          {...register('objective')}
          className={errors.objective ? 'error' : ''}
          aria-required="true"
          aria-invalid={!!errors.objective}
          disabled={isLoading}
        >
          {objectives.map((obj) => (
            <option key={obj.value} value={obj.value}>
              {obj.label}
            </option>
          ))}
        </select>
        {errors.objective && (
          <span className="error-message" role="alert">
            {errors.objective.message}
          </span>
        )}
      </div>

      {/* Campaign Type */}
      <div className="form-group">
        <label htmlFor="campaign_type">
          Campaign Type <span className="required">*</span>
          <InfoTooltip
            items={[
              { label: 'Demand Gen', description: 'Drive demand across YouTube, Gmail, and Discover feeds' },
              { label: 'Search', description: 'Text ads on Google Search results' },
              { label: 'Display', description: 'Visual ads across the Google Display Network' },
              { label: 'Video', description: 'Video ads on YouTube (requires Google Ads UI to publish)' },
              { label: 'Shopping', description: 'Product listings from Merchant Center' },
              { label: 'Performance Max', description: 'AI-powered ads across all Google channels' },
            ]}
          />
        </label>
        <select
          id="campaign_type"
          {...register('campaign_type')}
          className={errors.campaign_type ? 'error' : ''}
          aria-required="true"
          aria-invalid={!!errors.campaign_type}
          disabled={isLoading}
        >
          {campaignTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        <p className="field-description">{config.description}</p>
        {errors.campaign_type && (
          <span className="error-message" role="alert">
            {errors.campaign_type.message}
          </span>
        )}
      </div>

      {/* VIDEO Campaign Warning */}
      {watchedCampaignType === 'VIDEO' && (
        <div className="warning-banner" role="alert">
          <strong>Note:</strong> {getApiCreationWarning('VIDEO')}
        </div>
      )}

      {/* Daily Budget */}
      <div className="form-group">
        <label htmlFor="daily_budget">
          Daily Budget (USD) <span className="required">*</span>
        </label>
        <input
          id="daily_budget"
          type="number"
          step="0.01"
          min="1"
          {...register('daily_budget', { valueAsNumber: true })}
          className={errors.daily_budget ? 'error' : ''}
          aria-required="true"
          aria-invalid={!!errors.daily_budget}
          disabled={isLoading}
          placeholder="10.00"
        />
        {errors.daily_budget && (
          <span className="error-message" role="alert">
            {errors.daily_budget.message}
          </span>
        )}
      </div>

      {/* Start Date */}
      <div className="form-group">
        <label htmlFor="start_date">
          Start Date <span className="required">*</span>
        </label>
        <input
          id="start_date"
          type="date"
          {...register('start_date')}
          className={errors.start_date ? 'error' : ''}
          aria-required="true"
          aria-invalid={!!errors.start_date}
          disabled={isLoading}
        />
        {errors.start_date && (
          <span className="error-message" role="alert">
            {errors.start_date.message}
          </span>
        )}
      </div>

      {/* End Date */}
      <div className="form-group">
        <label htmlFor="end_date">End Date</label>
        <input
          id="end_date"
          type="date"
          {...register('end_date')}
          className={errors.end_date ? 'error' : ''}
          aria-invalid={!!errors.end_date}
          disabled={isLoading}
        />
        {errors.end_date && (
          <span className="error-message" role="alert">
            {errors.end_date.message}
          </span>
        )}
      </div>

      {/* Bidding Strategy Section */}
      <hr className="form-divider" />
      <h3>Bidding Strategy</h3>

      <div className="form-group">
        <label htmlFor="bidding_strategy">
          Bidding Strategy
          <InfoTooltip
            items={config.biddingOptions.map(option => ({
              label: option.label,
              description: option.description
            }))}
          />
        </label>
        <select
          id="bidding_strategy"
          {...register('bidding_strategy')}
          className={errors.bidding_strategy ? 'error' : ''}
          aria-invalid={!!errors.bidding_strategy}
          disabled={isLoading}
        >
          {config.biddingOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <p className="field-description">
          {config.biddingOptions.find(o => o.value === watchedBiddingStrategy)?.description}
        </p>
        {errors.bidding_strategy && (
          <span className="error-message" role="alert">
            {errors.bidding_strategy.message}
          </span>
        )}
      </div>

      {/* Target CPA */}
      {watchedBiddingStrategy === 'target_cpa' && (
        <div className="form-group">
          <label htmlFor="target_cpa">
            Target CPA (USD) <span className="required">*</span>
          </label>
          <input
            id="target_cpa"
            type="number"
            step="0.01"
            min="0.01"
            {...register('target_cpa', { valueAsNumber: true })}
            className={errors.target_cpa ? 'error' : ''}
            aria-required="true"
            aria-invalid={!!errors.target_cpa}
            disabled={isLoading}
            placeholder="10.00"
          />
          {errors.target_cpa && (
            <span className="error-message" role="alert">
              {errors.target_cpa.message}
            </span>
          )}
        </div>
      )}

      {/* Target ROAS */}
      {watchedBiddingStrategy === 'target_roas' && (
        <div className="form-group">
          <label htmlFor="target_roas">
            Target ROAS <span className="required">*</span>
          </label>
          <input
            id="target_roas"
            type="number"
            step="0.01"
            min="0.01"
            {...register('target_roas', { valueAsNumber: true })}
            className={errors.target_roas ? 'error' : ''}
            aria-required="true"
            aria-invalid={!!errors.target_roas}
            disabled={isLoading}
            placeholder="2.0 (200%)"
          />
          <p className="field-description">Enter as a multiplier (e.g., 2.0 for 200% ROAS)</p>
          {errors.target_roas && (
            <span className="error-message" role="alert">
              {errors.target_roas.message}
            </span>
          )}
        </div>
      )}

      {/* Ad Creative Section */}
      <hr className="form-divider" />
      <h3>Ad Creative</h3>

      {/* Ad Group Name */}
      <div className="form-group">
        <label htmlFor="ad_group_name">Ad Group Name</label>
        <input
          id="ad_group_name"
          type="text"
          {...register('ad_group_name')}
          disabled={isLoading}
          placeholder="Enter ad group name"
        />
        {errors.ad_group_name && (
          <span className="error-message" role="alert">
            {errors.ad_group_name.message}
          </span>
        )}
      </div>

      {/* Headlines - Multiple inputs */}
      {showHeadlines && (
        <div className="form-group">
          <label>
            Headlines {config.headlines.required && <span className="required">*</span>}
            <span className="field-hint">
              ({config.headlines.min}-{config.headlines.max}, max {config.headlines.maxLength} chars each)
            </span>
          </label>
          {headlineFields.map((field, index) => (
            <div key={field.id} className="array-field-row">
              <div className="input-with-counter">
                <input
                  type="text"
                  {...register(`headlines.${index}.value`)}
                  className={errors.headlines ? 'error' : ''}
                  aria-invalid={!!errors.headlines}
                  disabled={isLoading}
                  placeholder={`Headline ${index + 1}${index < config.headlines.min ? ' (required)' : ''}`}
                  maxLength={config.headlines.maxLength + 10}
                />
                <CharacterCounter
                  current={(watch(`headlines.${index}.value`) || '').length}
                  max={config.headlines.maxLength}
                />
              </div>
              {/* Only show delete button if above minimum required */}
              {headlineFields.length > config.headlines.min && (
                <button
                  type="button"
                  className="btn btn-icon btn-remove"
                  onClick={() => removeHeadline(index)}
                  disabled={isLoading}
                  aria-label="Remove headline"
                >
                  -
                </button>
              )}
            </div>
          ))}
          {headlineFields.length < config.headlines.max && (
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={() => appendHeadline({ value: '' })}
              disabled={isLoading}
            >
              + Add Headline
            </button>
          )}
          {errors.headlines && (
            <span className="error-message" role="alert">
              {(errors.headlines as any)?.message || 'Invalid headlines'}
            </span>
          )}
        </div>
      )}

      {/* Long Headline */}
      {showLongHeadline && (
        <div className="form-group">
          <label htmlFor="long_headline">
            Long Headline {config.longHeadline?.required && <span className="required">*</span>}
            <span className="field-hint">(max {config.longHeadline?.maxLength} chars)</span>
          </label>
          <div className="input-with-counter">
            <input
              id="long_headline"
              type="text"
              {...register('long_headline')}
              disabled={isLoading}
              placeholder="Enter long headline"
              maxLength={(config.longHeadline?.maxLength || 90) + 10}
            />
            <CharacterCounter
              current={(watch('long_headline') || '').length}
              max={config.longHeadline?.maxLength || 90}
            />
          </div>
          {errors.long_headline && (
            <span className="error-message" role="alert">
              {errors.long_headline.message}
            </span>
          )}
        </div>
      )}

      {/* Descriptions - Multiple inputs */}
      {showDescriptions && (
        <div className="form-group">
          <label>
            Descriptions {config.descriptions.required && <span className="required">*</span>}
            <span className="field-hint">
              ({config.descriptions.min}-{config.descriptions.max}, max {config.descriptions.maxLength} chars each)
            </span>
          </label>
          {/* PMax short description requirement indicator */}
          {campaignType === 'PERFORMANCE_MAX' && (
            <div className="field-requirement-note">
              At least one description must be 60 characters or fewer
              {hasPMaxShortDescription(
                descriptionFields.map((_, i) => watch(`descriptions.${i}.value`) || '')
              ) ? (
                <span className="success-indicator" aria-label="Requirement met"> &#10003;</span>
              ) : (
                <span className="warning-indicator" aria-label="Requirement not met"> (not met)</span>
              )}
            </div>
          )}
          {descriptionFields.map((field, index) => (
            <div key={field.id} className="array-field-row">
              <div className="input-with-counter textarea-container">
                <textarea
                  {...register(`descriptions.${index}.value`)}
                  className={errors.descriptions ? 'error' : ''}
                  aria-invalid={!!errors.descriptions}
                  disabled={isLoading}
                  placeholder={`Description ${index + 1}${index < config.descriptions.min ? ' (required)' : ''}`}
                  rows={2}
                  maxLength={config.descriptions.maxLength + 10}
                />
                <CharacterCounter
                  current={(watch(`descriptions.${index}.value`) || '').length}
                  max={config.descriptions.maxLength}
                />
                {/* Show indicator for short descriptions in PMax */}
                {campaignType === 'PERFORMANCE_MAX' && (watch(`descriptions.${index}.value`) || '').length <= 60 && (watch(`descriptions.${index}.value`) || '').length > 0 && (
                  <span className="short-desc-badge">Short</span>
                )}
              </div>
              {/* Only show delete button if above minimum required */}
              {descriptionFields.length > config.descriptions.min && (
                <button
                  type="button"
                  className="btn btn-icon btn-remove"
                  onClick={() => removeDescription(index)}
                  disabled={isLoading}
                  aria-label="Remove description"
                >
                  -
                </button>
              )}
            </div>
          ))}
          {descriptionFields.length < config.descriptions.max && (
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={() => appendDescription({ value: '' })}
              disabled={isLoading}
            >
              + Add Description
            </button>
          )}
          {errors.descriptions && (
            <span className="error-message" role="alert">
              {(errors.descriptions as any)?.message || 'Invalid descriptions'}
            </span>
          )}
        </div>
      )}

      {/* Business Name */}
      {showBusinessName && (
        <div className="form-group">
          <label htmlFor="business_name">
            Business Name {config.businessName.required && <span className="required">*</span>}
            <span className="field-hint">(max {config.businessName.maxLength} chars)</span>
          </label>
          <div className="input-with-counter">
            <input
              id="business_name"
              type="text"
              {...register('business_name')}
              className={errors.business_name ? 'error' : ''}
              aria-invalid={!!errors.business_name}
              disabled={isLoading}
              placeholder="Your business name"
              maxLength={config.businessName.maxLength + 5}
            />
            <CharacterCounter
              current={(watch('business_name') || '').length}
              max={config.businessName.maxLength}
            />
          </div>
          {errors.business_name && (
            <span className="error-message" role="alert">
              {errors.business_name.message}
            </span>
          )}
        </div>
      )}

      {/* Images Section */}
      {showImages && (
        <>
          <hr className="form-divider" />
          <h3>Images</h3>
          <p className="section-description">
            Provide URLs for your ad images. At least one marketing image (landscape OR square) is required.
          </p>

          {config.images.landscape && (
            <div className="form-group">
              <label htmlFor="images.landscape_url">Landscape Image URL (1.91:1 ratio)</label>
              <input
                id="images.landscape_url"
                type="url"
                {...register('images.landscape_url' as any)}
                disabled={isLoading}
                placeholder="https://example.com/landscape.jpg"
              />
            </div>
          )}

          {config.images.square && (
            <div className="form-group">
              <label htmlFor="images.square_url">Square Image URL (1:1 ratio)</label>
              <input
                id="images.square_url"
                type="url"
                {...register('images.square_url' as any)}
                disabled={isLoading}
                placeholder="https://example.com/square.jpg"
              />
            </div>
          )}

          {config.images.logo && (
            <div className="form-group">
              <label htmlFor="images.logo_url">Logo URL (1:1 or 4:1 ratio)</label>
              <input
                id="images.logo_url"
                type="url"
                {...register('images.logo_url' as any)}
                disabled={isLoading}
                placeholder="https://example.com/logo.png"
              />
            </div>
          )}

          {errors.images && (
            <span className="error-message" role="alert">
              {(errors.images as any)?.message || 'Image is required'}
            </span>
          )}
        </>
      )}

      {/* Final URL */}
      {showFinalUrl && (
        <div className="form-group">
          <label htmlFor="final_url">
            Final URL (Landing Page) {config.finalUrl.required && <span className="required">*</span>}
            <InfoTooltip text="The landing page users will visit after clicking your ad. Must be a valid URL on your website that is accessible and relevant to your ad content." />
          </label>
          <input
            id="final_url"
            type="url"
            {...register('final_url')}
            className={errors.final_url ? 'error' : ''}
            aria-invalid={!!errors.final_url}
            disabled={isLoading}
            placeholder="https://example.com/landing"
          />
          {errors.final_url && (
            <span className="error-message" role="alert">
              {errors.final_url.message}
            </span>
          )}
        </div>
      )}

      {/* Keywords Section (SEARCH campaigns) */}
      {showKeywords && (
        <>
          <hr className="form-divider" />
          <h3>Keywords</h3>
          <p className="section-description">
            Add keywords to target for your Search campaign. Keywords must be unique within an ad group.
          </p>

          <div className="form-group">
            <label>
              Keywords <span className="required">*</span>
              <span className="field-hint">(max 80 chars each, must be unique)</span>
            </label>
            {/* Show duplicate keyword warning */}
            {(() => {
              const currentKeywords = keywordFields.map((_, i) => watch(`keywords.${i}.value`) || '').filter(k => k.trim());
              const duplicates = getDuplicateKeywords(currentKeywords);
              return duplicates.length > 0 && (
                <div className="validation-warning" role="alert">
                  <strong>Duplicate keywords detected:</strong> {duplicates.join(', ')}
                </div>
              );
            })()}
            {keywordFields.map((field, index) => (
              <div key={field.id} className="array-field-row">
                <input
                  type="text"
                  {...register(`keywords.${index}.value`)}
                  className={errors.keywords ? 'error' : ''}
                  aria-invalid={!!errors.keywords}
                  disabled={isLoading}
                  placeholder={`Keyword ${index + 1}`}
                  maxLength={80}
                />
                {keywordFields.length > 1 && (
                  <button
                    type="button"
                    className="btn btn-icon btn-remove"
                    onClick={() => removeKeyword(index)}
                    disabled={isLoading}
                    aria-label="Remove keyword"
                  >
                    -
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={() => appendKeyword({ value: '' })}
              disabled={isLoading}
            >
              + Add Keyword
            </button>
            {errors.keywords && (
              <span className="error-message" role="alert">
                {(errors.keywords as any)?.message || 'Keywords are required'}
              </span>
            )}
          </div>
        </>
      )}

      {/* Video URL Section (VIDEO campaigns) */}
      {showVideoUrl && (
        <>
          <hr className="form-divider" />
          <h3>Video</h3>

          <div className="form-group">
            <label htmlFor="video_url">
              Video URL <span className="required">*</span>
            </label>
            <input
              id="video_url"
              type="url"
              {...register('video_url')}
              className={errors.video_url ? 'error' : ''}
              aria-required="true"
              aria-invalid={!!errors.video_url}
              disabled={isLoading}
              placeholder="https://www.youtube.com/watch?v=..."
            />
            <p className="field-description">Enter a YouTube video URL</p>
            {errors.video_url && (
              <span className="error-message" role="alert">
                {errors.video_url.message}
              </span>
            )}
          </div>
        </>
      )}

      {/* Merchant Center Section (SHOPPING campaigns) */}
      {showMerchantCenterId && (
        <>
          <hr className="form-divider" />
          <h3>Merchant Center</h3>

          <div className="form-group">
            <label htmlFor="merchant_center_id">
              Merchant Center ID <span className="required">*</span>
            </label>
            <input
              id="merchant_center_id"
              type="text"
              {...register('merchant_center_id')}
              className={errors.merchant_center_id ? 'error' : ''}
              aria-required="true"
              aria-invalid={!!errors.merchant_center_id}
              disabled={isLoading}
              placeholder="123456789"
            />
            <p className="field-description">
              Your Google Merchant Center account ID
            </p>
            {errors.merchant_center_id && (
              <span className="error-message" role="alert">
                {errors.merchant_center_id.message}
              </span>
            )}
          </div>
        </>
      )}

      {/* Form Actions */}
      <div className="form-actions">
        {onCancel && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading}
        >
          {isLoading ? 'Saving...' : (mode === 'edit' ? 'Update Campaign' : 'Save Campaign')}
        </button>
      </div>
    </form>
  );
};

// Export memoized component to prevent unnecessary re-renders
export const CampaignForm = memo(CampaignFormComponent);

export default CampaignForm;
