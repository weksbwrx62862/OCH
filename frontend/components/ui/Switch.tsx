'use client';

import React from 'react';

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label?: string;
  className?: string;
}

function Switch({
  checked,
  onChange,
  disabled = false,
  label,
  className = '',
}: SwitchProps) {
  return (
    <label
      className={`
        inline-flex items-center gap-2 cursor-pointer
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={`
          relative inline-flex h-5 w-9 shrink-0 rounded-full
          transition-colors duration-normal focus-ring
          ${checked ? 'bg-primary' : 'bg-surface-overlay border border-border'}
        `}
      >
        <span
          className={`
            pointer-events-none inline-block h-4 w-4 rounded-full
            bg-white shadow-sm transition-transform duration-normal
            ${checked ? 'translate-x-[18px]' : 'translate-x-[2px]'}
            mt-[2px]
          `}
        />
      </button>
      {label && (
        <span className="text-sm text-text-secondary">{label}</span>
      )}
    </label>
  );
}

export { Switch };
export type { SwitchProps };
