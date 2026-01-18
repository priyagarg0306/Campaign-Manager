/**
 * InfoTooltip Component
 * Reusable info icon with hover tooltip for providing contextual help.
 */
import React, { memo } from 'react';
import './InfoTooltip.css';

export interface TooltipLine {
  label: string;
  description: string;
}

export interface InfoTooltipProps {
  /** Simple text content */
  text?: string;
  /** Structured content with label-description pairs (renders as list) */
  items?: TooltipLine[];
  position?: 'top' | 'bottom' | 'left' | 'right';
}

const InfoTooltipComponent: React.FC<InfoTooltipProps> = ({
  text,
  items,
  position = 'top',
}) => {
  return (
    <span className={`info-tooltip info-tooltip--${position}`}>
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle
          cx="8"
          cy="8"
          r="7"
          stroke="currentColor"
          strokeWidth="1.5"
          fill="none"
        />
        <path
          d="M8 7V11"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        <circle cx="8" cy="4.5" r="0.75" fill="currentColor" />
      </svg>
      <span className="tooltip-text" role="tooltip">
        {items ? (
          <ul className="tooltip-list">
            {items.map((item, index) => (
              <li key={index}>
                <strong>{item.label}:</strong> {item.description}
              </li>
            ))}
          </ul>
        ) : (
          text
        )}
      </span>
    </span>
  );
};

export const InfoTooltip = memo(InfoTooltipComponent);

export default InfoTooltip;
