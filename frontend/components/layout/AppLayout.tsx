'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { useAppStore } from '@/stores/appStore';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { ToastContainer } from '@/components/ui/Toast';
import type { ToastData } from '@/components/ui/Toast';

function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const notifications = useAppStore((s) => s.notifications);
  const removeNotification = useAppStore((s) => s.removeNotification);

  const isLoginPage = pathname === '/login';

  if (isLoginPage) {
    return <>{children}</>;
  }

  const toasts: ToastData[] = notifications.map((n) => ({
    id: n.id,
    type: n.type,
    message: n.message || n.title,
    duration: n.duration,
  }));

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div
        className={`
          transition-all duration-slow
          ${!sidebarOpen ? 'ml-[var(--sidebar-collapsed-width)]' : 'ml-[var(--sidebar-width)]'}
        `}
      >
        <TopBar />
        <main className="p-6">{children}</main>
      </div>
      <ToastContainer toasts={toasts} onRemove={removeNotification} />
    </div>
  );
}

export { AppLayout };
