import React from 'react';
import { twMerge } from 'tailwind-merge';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'lime' | 'mint' | 'champagne' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantClasses: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary:
    'bg-[#3867E9] text-white hover:bg-[#2952C8] border border-[#3867E9] shadow-sm',
  lime:
    'bg-[#E6F6F3] text-[#127466] hover:bg-[#D2EFE9] border border-[#22A995] shadow-sm font-semibold',
  mint:
    'bg-[#E6F6F3] text-[#127466] hover:bg-[#D2EFE9] border border-[#22A995] shadow-sm font-semibold',
  champagne:
    'bg-[#FBF4E7] text-[#8A5B14] hover:bg-[#F5E7CE] border border-[#D69B42] shadow-sm font-semibold',
  secondary:
    'bg-white text-[#202B43] hover:bg-[#F6F8FC] border border-[#E2E8F4] shadow-sm',
  ghost:
    'bg-transparent text-[#202B43] hover:bg-[#EEF2FA] border border-transparent',
  danger:
    'bg-[#991B1B] text-white hover:bg-[#7F1D1D] border border-[#991B1B] shadow-sm',
};

const sizeClasses: Record<NonNullable<ButtonProps['size']>, string> = {
  sm: 'min-h-[36px] px-3.5 py-1.5 text-xs rounded-xl gap-1.5',
  md: 'min-h-[42px] px-5 py-2.5 text-sm rounded-xl gap-2',
  lg: 'min-h-[48px] px-6 py-3 text-sm rounded-2xl gap-2.5',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      leftIcon,
      rightIcon,
      className,
      disabled,
      children,
      ...rest
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={twMerge(
          'inline-flex items-center justify-center font-semibold transition-all duration-150 disabled:opacity-55 disabled:cursor-not-allowed cursor-pointer active:scale-[0.99]',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...rest}
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin shrink-0" /> : leftIcon}
        <span className="inline-flex items-center justify-center gap-1.5">{children}</span>
        {!loading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
