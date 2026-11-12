import React from 'react';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  accent?: 'none' | 'forest' | 'cobalt' | 'lime' | 'mint' | 'sand' | 'champagne';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  interactive?: boolean;
}

const accentBorders: Record<NonNullable<CardProps['accent']>, string> = {
  none: '',
  forest: 'border-t-[3px] border-t-[#3867E9]',
  cobalt: 'border-t-[3px] border-t-[#3867E9]',
  lime: 'border-t-[3px] border-t-[#22A995]',
  mint: 'border-t-[3px] border-t-[#22A995]',
  sand: 'border-t-[3px] border-t-[#D69B42]',
  champagne: 'border-t-[3px] border-t-[#D69B42]',
};

const padMap: Record<NonNullable<CardProps['padding']>, string> = {
  none: 'p-0',
  sm: 'p-4',
  md: 'p-5 sm:p-6',
  lg: 'p-6 sm:p-8',
};

export const Card: React.FC<CardProps> = ({
  accent = 'none',
  padding = 'md',
  interactive = false,
  className,
  children,
  ...rest
}) => {
  return (
    <div
      className={twMerge(
        'bg-white border border-[#E2E8F4] rounded-2xl shadow-card',
        accentBorders[accent],
        padMap[padding],
        interactive &&
          'transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-0.5 hover:shadow-elevated hover:border-[#C5D5FA]',
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
};
