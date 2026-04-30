'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAppStore } from '@/stores/appStore';
import {
  LayoutDashboard,
  MessageSquare,
  Bot,
  MessagesSquare,
  Wrench,
  BookOpen,
  ListTodo,
  Network,
  ShieldCheck,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
} from 'lucide-react';
import { Tooltip } from '@/components/ui/Tooltip';

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { href: '/', label: '仪表盘', icon: <LayoutDashboard className="w-4 h-4" /> },
  { href: '/chat', label: '对话', icon: <MessageSquare className="w-4 h-4" /> },
  { href: '/agents', label: '智能体', icon: <Bot className="w-4 h-4" /> },
  { href: '/sessions', label: '会话', icon: <MessagesSquare className="w-4 h-4" /> },
  { href: '/tasks', label: '任务', icon: <ListTodo className="w-4 h-4" /> },
  { href: '/tools', label: '工具库', icon: <Wrench className="w-4 h-4" /> },
  { href: '/skills', label: '技能库', icon: <BookOpen className="w-4 h-4" /> },
  { href: '/swarm', label: 'Swarm', icon: <Network className="w-4 h-4" /> },
  { href: '/audit', label: '审计日志', icon: <ShieldCheck className="w-4 h-4" /> },
  { href: '/settings', label: '设置', icon: <Settings className="w-4 h-4" /> },
];

function Sidebar() {
  const pathname = usePathname();
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);
  const collapsed = !sidebarOpen;

  return (
    <aside
      className={`
        fixed left-0 top-0 h-full z-sticky
        flex flex-col
        bg-surface border-r border-border
        transition-all duration-slow
        ${collapsed ? 'w-[var(--sidebar-collapsed-width)]' : 'w-[var(--sidebar-width)]'}
      `}
    >
      <div className="flex items-center h-[var(--topbar-height)] px-4 border-b border-border shrink-0">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg gradient-bg flex items-center justify-center shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <span className="text-sm font-bold gradient-text whitespace-nowrap">
              OCH
            </span>
          )}
        </Link>
      </div>

      <nav className="flex-1 py-2 px-2 overflow-y-auto">
        <div className="flex flex-col gap-0.5">
          {navItems.map((item) => {
            const isActive =
              item.href === '/'
                ? pathname === '/'
                : pathname.startsWith(item.href);

            const linkContent = (
              <Link
                href={item.href}
                className={`
                  flex items-center gap-3 px-3 py-2 rounded-lg
                  text-sm font-medium transition-all duration-fast
                  ${
                    isActive
                      ? 'bg-primary-muted text-primary'
                      : 'text-text-tertiary hover:text-text-secondary hover:bg-surface-raised'
                  }
                  ${collapsed ? 'justify-center' : ''}
                `}
              >
                <span className="shrink-0">{item.icon}</span>
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );

            if (collapsed) {
              return (
                <Tooltip key={item.href} content={item.label} position="right">
                  {linkContent}
                </Tooltip>
              );
            }

            return <React.Fragment key={item.href}>{linkContent}</React.Fragment>;
          })}
        </div>
      </nav>

      <div className="px-2 py-3 border-t border-border shrink-0">
        <Tooltip content={collapsed ? '展开侧边栏' : '收起侧边栏'} position="right">
          <button
            onClick={toggleSidebar}
            className={`
              flex items-center gap-3 px-3 py-2 rounded-lg w-full
              text-sm text-text-tertiary hover:text-text-secondary
              hover:bg-surface-raised transition-all duration-fast
              ${collapsed ? 'justify-center' : ''}
            `}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4 shrink-0" />
            ) : (
              <>
                <ChevronLeft className="w-4 h-4 shrink-0" />
                <span>收起</span>
              </>
            )}
          </button>
        </Tooltip>
      </div>
    </aside>
  );
}

export { Sidebar };
