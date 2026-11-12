import React from 'react';
import { clsx } from 'clsx';

interface NexoraLogoProps {
  compact?: boolean;
  className?: string;
}

export const NexoraLogo: React.FC<NexoraLogoProps> = ({ compact = false, className }) => {
  return (
    <span className={clsx('inline-flex items-center gap-2.5 select-none', className)}>
      <span
        className="w-9 h-9 rounded-xl bg-[#3867E9] flex items-center justify-center shadow-sm shrink-0 border border-[#2952C8]"
        aria-hidden="true"
      >
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none">
          <path
            d="M6.5 18.5V5.5L17.5 18.5V5.5"
            stroke="#FFFFFF"
            strokeWidth="2.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      {!compact && (
        <span className="flex flex-col leading-none">
          <span className="font-heading text-lg font-extrabold tracking-tight text-[#202B43]">
            NEXORA
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#4E5D78] mt-0.5">
            Business OS
          </span>
        </span>
      )}
    </span>
  );
};
