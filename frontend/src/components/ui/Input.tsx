import React from 'react';
import { twMerge } from 'tailwind-merge';

interface BaseFieldProps {
  label?: string;
  error?: string;
  hint?: string;
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement>, BaseFieldProps {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, className, ...rest }, ref) => {
    const fieldId = id || (label ? `field-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}` : undefined);
    return (
      <div className="space-y-1.5 w-full">
        {label && (
          <label htmlFor={fieldId} className="block text-xs font-semibold text-[#202B43]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={fieldId}
          className={twMerge(
            'w-full min-h-[42px] px-3.5 py-2 rounded-xl bg-white border border-[#E2E8F4] text-sm text-[#202B43] placeholder:text-[#5E6D87] focus:border-[#3867E9] focus:outline-none focus:ring-2 focus:ring-[#3867E9]/15 transition-colors disabled:bg-[#EEF2FA] disabled:cursor-not-allowed',
            error && 'border-[#991B1B] focus:border-[#991B1B] focus:ring-[#991B1B]/15',
            className
          )}
          {...rest}
        />
        {error ? (
          <p className="text-xs font-medium text-[#991B1B]">{error}</p>
        ) : hint ? (
          <p className="text-xs text-[#4E5D78]">{hint}</p>
        ) : null}
      </div>
    );
  }
);
Input.displayName = 'Input';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement>, BaseFieldProps {}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, hint, id, className, children, ...rest }, ref) => {
    const fieldId = id || (label ? `field-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}` : undefined);
    return (
      <div className="space-y-1.5 w-full">
        {label && (
          <label htmlFor={fieldId} className="block text-xs font-semibold text-[#202B43]">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={fieldId}
          className={twMerge(
            'w-full min-h-[42px] px-3.5 py-2 rounded-xl bg-white border border-[#E2E8F4] text-sm text-[#202B43] focus:border-[#3867E9] focus:outline-none focus:ring-2 focus:ring-[#3867E9]/15 transition-colors',
            error && 'border-[#991B1B]',
            className
          )}
          {...rest}
        >
          {children}
        </select>
        {error ? (
          <p className="text-xs font-medium text-[#991B1B]">{error}</p>
        ) : hint ? (
          <p className="text-xs text-[#4E5D78]">{hint}</p>
        ) : null}
      </div>
    );
  }
);
Select.displayName = 'Select';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement>, BaseFieldProps {}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, id, className, ...rest }, ref) => {
    const fieldId = id || (label ? `field-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}` : undefined);
    return (
      <div className="space-y-1.5 w-full">
        {label && (
          <label htmlFor={fieldId} className="block text-xs font-semibold text-[#202B43]">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={fieldId}
          className={twMerge(
            'w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E2E8F4] text-sm text-[#202B43] placeholder:text-[#5E6D87] focus:border-[#3867E9] focus:outline-none focus:ring-2 focus:ring-[#3867E9]/15 transition-colors',
            error && 'border-[#991B1B]',
            className
          )}
          {...rest}
        />
        {error ? (
          <p className="text-xs font-medium text-[#991B1B]">{error}</p>
        ) : hint ? (
          <p className="text-xs text-[#4E5D78]">{hint}</p>
        ) : null}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';
