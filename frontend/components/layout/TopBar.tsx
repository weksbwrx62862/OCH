'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { useAppStore } from '@/stores/appStore';
import { Avatar } from '@/components/ui/Avatar';
import { Dropdown } from '@/components/ui/Dropdown';
import { Search, LogOut, User } from 'lucide-react';

const pageTitles: Record<string, string> = {
  '/': '仪表盘',
  '/chat': '对话',
  '/agents': '智能体管理',
  '/sessions': '会话管理',
  '/tasks': '任务管理',
  '/tools': '工具库',
  '/skills': '技能库',
  '/swarm': 'Swarm 多智能体',
  '/audit': '审计日志',
  '/settings': '系统设置',
  '/login': '登录',
};

function TopBar() {
  const pathname = usePathname();
  const { toggleCommandPalette, user } = useAppStore();
  const title = pageTitles[pathname] || '';

  return (
    <header className="h-[var(--topbar-height)] flex items-center justify-between px-6 border-b border-border bg-surface/80 backdrop-blur-sm shrink-0">
      <div className="flex items-center gap-4">
        <h1 className="text-base font-semibold text-text-primary">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={toggleCommandPalette}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-text-tertiary bg-surface-raised border border-border hover:border-border-hover transition-colors focus-ring"
        >
          <Search className="w-3.5 h-3.5" />
          <span>搜索...</span>
          <kbd className="px-1.5 py-0.5 rounded bg-surface-overlay text-[10px] font-mono">
            ⌘K
          </kbd>
        </button>

        <Dropdown
          trigger={
            <button className="focus-ring rounded-lg p-0.5">
              <Avatar
                name={user?.name || '用户'}
                size="sm"
              />
            </button>
          }
          items={[
            {
              id: 'profile',
              label: user?.name || '用户',
              icon: <User className="w-4 h-4" />,
              onClick: () => {},
            },
            {
              id: 'logout',
              label: '退出登录',
              icon: <LogOut className="w-4 h-4" />,
              onClick: () => {
                localStorage.removeItem('och_token');
                window.location.href = '/login';
              },
              danger: true,
            },
          ]}
        />
      </div>
    </header>
  );
}

export { TopBar };
