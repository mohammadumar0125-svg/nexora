import React from 'react';
import { Card } from './Card';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action }) => {
  return (
    <Card className="text-center py-12 px-6 bg-white/95 border-dashed border-[#CBD5E6]">
      {icon && (
        <div className="w-12 h-12 mx-auto rounded-2xl bg-[#EEF2FA] border border-[#E2E8F4] flex items-center justify-center text-[#3867E9] mb-4">
          {icon}
        </div>
      )}
      <h3 className="font-heading text-base font-bold text-[#202B43]">{title}</h3>
      <p className="text-sm text-[#4E5D78] max-w-md mx-auto mt-1.5 leading-relaxed">{description}</p>
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </Card>
  );
};
