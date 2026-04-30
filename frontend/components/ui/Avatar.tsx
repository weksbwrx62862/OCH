'use client';

import React from 'react';
import { getInitials } from '@/lib/utils';

type AvatarSize = 'sm' | 'md' | 'lg';

interface AvatarProps {
  src?: string;
  name?: string;
  icon?: React.ReactNode;
  size?: AvatarSize;
  className?: string;
}

const sizeStyles: Record<AvatarSize, string> = {
  sm: 'w-7 h-7 text-xs',
  md: 'w-9 h-9 text-sm',
  lg: 'w-12 h-12 text-base',
};

const iconSizeStyles: Record<AvatarSize, string> = {
  sm: 'w-3.5 h-3.5',
  md: 'w-4 h-4',
  lg: 'w-5 h-5',
};

function Avatar({
  src,
  name,
  icon,
  size = 'md',
  className = '',
}: AvatarProps) {
  const baseStyles = `
    inline-flex items-center justify-center rounded-lg shrink-0
    bg-primary-muted text-primary font-medium overflow-hidden
    ${sizeStyles[size]}
    ${className}
  `;

  if (src) {
    return (
      <div className={baseStyles}>
        <img src={src} alt={name || ''} className="w-full h-full object-cover" />
      </div>
    );
  }

  if (icon) {
    return <div className={baseStyles}>{icon}</div>;
  }

  if (name) {
    return <div className={baseStyles}>{getInitials(name)}</div>;
  }

  return (
    <div className={baseStyles}>
      <span className={iconSizeStyles[size]}>?</span>
    </div>
  );
}

export { Avatar };
export type { AvatarProps, AvatarSize };
