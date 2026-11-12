import React from 'react';
import { Card } from './Card';
import { Badge, BadgeTone } from './Badge';

interface StatTileProps {
  label: string;
  value: string | number;
  detail?: string;
  badge?: string;
  badgeTone?: BadgeTone;
  accent?: 'none' | 'forest' | 'cobalt' | 'lime' | 'mint' | 'sand' | 'champagne';
  icon?: React.ReactNode;
}

const iconStyles: Record<NonNullable<StatTileProps['accent']>, string> = {
  none: 'bg-[#F6F8FC] text-[#3867E9] border-[#E2E8F4]',
  forest: 'bg-[#EAF0FE] text-[#3867E9] border-[#C5D5FA]',
  cobalt: 'bg-[#EAF0FE] text-[#3867E9] border-[#C5D5FA]',
  lime: 'bg-[#E6F6F3] text-[#22A995] border-[#99DDD2]',
  mint: 'bg-[#E6F6F3] text-[#22A995] border-[#99DDD2]',
  sand: 'bg-[#FBF4E7] text-[#D69B42] border-[#EBD09F]',
  champagne: 'bg-[#FBF4E7] text-[#D69B42] border-[#EBD09F]',
};

export const StatTile: React.FC<StatTileProps> = ({
  label,
  value,
  detail,
  badge,
  badgeTone = 'cobalt',
  accent = 'none',
  icon,
}) => {
  return (
    <Card accent={accent} className="space-y-3 transition-shadow duration-300 hover:shadow-elevated">
      <div className="flex items-start justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[#4E5D78]">{label}</span>
        {icon ? (
          <span className={`w-8 h-8 rounded-xl border flex items-center justify-center shrink-0 ${iconStyles[accent]}`}>
            {icon}
          </span>
        ) : badge ? (
          <Badge tone={badgeTone}>{badge}</Badge>
        ) : null}
      </div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-heading text-2xl sm:text-3xl font-bold text-[#202B43] tabular-nums">
          {value}
        </span>
        {icon && badge && <Badge tone={badgeTone}>{badge}</Badge>}
      </div>
      {detail && <p className="text-xs text-[#4E5D78] leading-snug">{detail}</p>}
    </Card>
  );
};
