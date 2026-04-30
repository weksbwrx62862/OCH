'use client';

import React from 'react';

interface CardProps {
  children: React.ReactNode;
  hover?: boolean;
  clickable?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

function Card({
  children,
  hover = false,
  clickable = false,
  padding = 'md',
  className = '',
  onClick,
}: CardProps) {
  return (
    <div
      onClick={clickable ? onClick : undefined}
      className={`
        bg-surface border border-border rounded-xl
        transition-all duration-normal
        ${hover || clickable ? 'hover:border-border-hover hover:shadow-md' : ''}
        ${clickable ? 'cursor-pointer active:scale-[0.99]' : ''}
        ${paddingStyles[padding]}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

function CardHeader({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`mb-3 ${className}`}>
      {children}
    </div>
  );
}

function CardTitle({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h3 className={`text-base font-semibold text-text-primary ${className}`}>
      {children}
    </h3>
  );
}

function CardDescription({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p className={`text-sm text-text-secondary mt-1 ${className}`}>
      {children}
    </p>
  );
}

function CardContent({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={className}>{children}</div>;
}

function CardFooter({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`mt-4 pt-3 border-t border-border ${className}`}>
      {children}
    </div>
  );
}

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
export type { CardProps };
