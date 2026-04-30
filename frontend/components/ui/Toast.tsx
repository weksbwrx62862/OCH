'use client';

import React, { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastData {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

const typeStyles: Record<ToastType, string> = {
  success: 'border-success/30 bg-success-muted',
  error: 'border-error/30 bg-error-muted',
  warning: 'border-warning/30 bg-warning-muted',
  info: 'border-info/30 bg-info-muted',
};

const typeIcons: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle className="w-4 h-4 text-success" />,
  error: <AlertCircle className="w-4 h-4 text-error" />,
  warning: <AlertTriangle className="w-4 h-4 text-warning" />,
  info: <Info className="w-4 h-4 text-info" />,
};

function Toast({ toast, onRemove }: { toast: ToastData; onRemove: (id: string) => void }) {
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const duration = toast.duration ?? 4000;
    const timer = setTimeout(() => {
      setExiting(true);
      setTimeout(() => onRemove(toast.id), 200);
    }, duration);
    return () => clearTimeout(timer);
  }, [toast, onRemove]);

  return (
    <div
      className={`
        flex items-center gap-3 px-4 py-3 rounded-lg
        border shadow-lg min-w-[280px] max-w-[400px]
        ${typeStyles[toast.type]}
        ${exiting ? 'animate-toast-exit' : 'animate-toast-enter'}
      `}
    >
      {typeIcons[toast.type]}
      <p className="flex-1 text-sm text-text-primary">{toast.message}</p>
      <button
        onClick={() => {
          setExiting(true);
          setTimeout(() => onRemove(toast.id), 200);
        }}
        className="shrink-0 text-text-tertiary hover:text-text-primary transition-colors"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: ToastData[];
  onRemove: (id: string) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-toast flex flex-col gap-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

export { Toast, ToastContainer };
export type { ToastType, ToastData };
