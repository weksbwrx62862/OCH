'use client';

import React, { forwardRef, useState } from 'react';
import { X, Search } from 'lucide-react';

type InputVariant = 'default' | 'search';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: InputVariant;
  error?: string;
  icon?: React.ReactNode;
  onClear?: () => void;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      variant = 'default',
      error,
      icon,
      onClear,
      className = '',
      value,
      onChange,
      ...props
    },
    ref
  ) => {
    const [focused, setFocused] = useState(false);
    const hasValue = value !== undefined && value !== '';
    const isSearch = variant === 'search';

    return (
      <div className="w-full">
        <div
          className={`
            flex items-center gap-2 h-9 px-3 rounded-lg
            bg-surface-raised border transition-all duration-normal
            ${focused ? 'border-border-focus shadow-[0_0_0_1px_var(--border-focus)]' : 'border-border'}
            ${error ? 'border-error shadow-[0_0_0_1px_var(--error)]' : ''}
            ${className}
          `}
        >
          {icon && <span className="shrink-0 text-text-tertiary">{icon}</span>}
          {isSearch && !icon && (
            <Search className="w-4 h-4 shrink-0 text-text-tertiary" />
          )}
          <input
            ref={ref}
            value={value}
            onChange={onChange}
            onFocus={(e) => {
              setFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setFocused(false);
              props.onBlur?.(e);
            }}
            className={`
              flex-1 bg-transparent outline-none text-sm text-text-primary
              placeholder:text-text-tertiary
              ${isSearch ? 'placeholder:text-text-tertiary' : ''}
            `}
            {...props}
          />
          {(hasValue && onClear) && (
            <button
              type="button"
              onClick={onClear}
              className="shrink-0 text-text-tertiary hover:text-text-secondary transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        {error && (
          <p className="mt-1 text-xs text-error">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
export type { InputProps, InputVariant };
