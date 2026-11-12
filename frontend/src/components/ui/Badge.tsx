import React from 'react';
import { twMerge } from 'tailwind-merge';

export type BadgeTone = 'forest' | 'cobalt' | 'lime' | 'mint' | 'champagne' | 'neutral' | 'warning' | 'danger' | 'info';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

const toneMap: Record<BadgeTone, string> = {
  forest: 'bg-[#EAF0FE] text-[#2952C8] border-[#C5D5FA]',
  cobalt: 'bg-[#EAF0FE] text-[#2952C8] border-[#C5D5FA]',
  lime: 'bg-[#E6F6F3] text-[#127466] border-[#99DDD2]',
  mint: 'bg-[#E6F6F3] text-[#127466] border-[#99DDD2]',
  champagne: 'bg-[#FBF4E7] text-[#8A5B14] border-[#EBD09F]',
  neutral: 'bg-[#EEF2FA] text-[#4E5D78] border-[#E2E8F4]',
  warning: 'bg-[#FEF3C7] text-[#92400E] border-[#FDE68A]',
  danger: 'bg-[#FEE2E2] text-[#991B1B] border-[#FECACA]',
  info: 'bg-[#EAF0FE] text-[#2952C8] border-[#C5D5FA]',
};

export const Badge: React.FC<BadgeProps> = ({ tone = 'neutral', className, children, ...rest }) => {
  return (
    <span
      className={twMerge(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wide border',
        toneMap[tone],
        className
      )}
      {...rest}
    >
      {children}
    </span>
  );
};
