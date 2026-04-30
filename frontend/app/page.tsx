'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import apiClient from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { Card, CardContent, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import {
  MessageSquare,
  Bot,
  DollarSign,
  Zap,
  Plus,
  Settings,
  ListTodo,
  Activity,
  CheckCircle,
  AlertTriangle,
  Wrench,
} from 'lucide-react';

import { AuditLog } from '@/lib/types';

interface DashboardStats {
  activeSessions: number;
  totalAgents: number;
  todayCost: string;
  tokensUsed: string;
}

const statItems = [
  { key: 'activeSessions' as const, title: '活跃会话', icon: <MessageSquare className="w-5 h-5" />, color: 'text-accent' },
  { key: 'totalAgents' as const, title: '智能体总数', icon: <Bot className="w-5 h-5" />, color: 'text-primary' },
  { key: 'todayCost' as const, title: '今日费用', icon: <DollarSign className="w-5 h-5" />, color: 'text-warning' },
  { key: 'tokensUsed' as const, title: 'Token 用量', icon: <Zap className="w-5 h-5" />, color: 'text-success' },
];

const quickActions = [
  { label: '新建对话', icon: <Plus className="w-4 h-4" />, href: '/chat' },
  { label: '管理智能体', icon: <Bot className="w-4 h-4" />, href: '/agents' },
  { label: '查看会话', icon: <Activity className="w-4 h-4" />, href: '/sessions' },
  { label: '任务管理', icon: <ListTodo className="w-4 h-4" />, href: '/tasks' },
];

function getActivityIcon(log: AuditLog) {
  if (log.status_code && log.status_code < 400) return <CheckCircle className="w-4 h-4 text-success" />;
  if (log.action.includes('deny')) return <AlertTriangle className="w-4 h-4 text-warning" />;
  return <Wrench className="w-4 h-4 text-text-tertiary" />;
}

export default function HomePage() {
  const [stats, setStats] = useState<DashboardStats>({
    activeSessions: 0,
    totalAgents: 0,
    todayCost: '-',
    tokensUsed: '-',
  });
  const [activities, setActivities] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiClient.get<{ data: { id: string; status: string }[]; total: number }>('/sessions').catch(() => ({ data: [], total: 0 })),
      apiClient.get<{ data: { id: string }[]; total: number }>('/agents').catch(() => ({ data: [], total: 0 })),
      apiClient.get<{ data: AuditLog[]; total: number }>('/audit?per_page=5').catch(() => ({ data: [], total: 0 })),
    ]).then(([sessionsRes, agentsRes, auditRes]) => {
      const activeCount = (sessionsRes.data || []).filter((s: { status: string }) => s.status === 'active').length;
      setStats({
        activeSessions: activeCount,
        totalAgents: agentsRes.total || (agentsRes.data || []).length,
        todayCost: '-',
        tokensUsed: '-',
      });
      setActivities(auditRes.data || []);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statItems.map((item) => (
          <Card key={item.key} hover>
            <div className="flex items-start justify-between mb-3">
              <p className="text-sm text-text-secondary">{item.title}</p>
              <span className={item.color}>{item.icon}</span>
            </div>
            <span className="text-2xl font-bold text-text-primary">
              {stats[item.key]}
            </span>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardTitle>最近活动</CardTitle>
          {activities.length === 0 ? (
            <EmptyState
              icon={<Activity className="w-8 h-8" />}
              title="暂无活动记录"
              description="系统操作将在此处显示"
            />
          ) : (
            <div className="space-y-1 mt-3">
              {activities.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-raised transition-colors"
                >
                  <span className="mt-0.5 shrink-0">{getActivityIcon(log)}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary">
                      {log.action} <Badge size="sm" variant="default">{log.resource_type}</Badge>
                    </p>
                    <p className="text-xs text-text-tertiary truncate mt-0.5">
                      {log.resource_id || log.details || ''}
                    </p>
                  </div>
                  <span className="text-xs text-text-tertiary whitespace-nowrap">
                    {formatDate(log.created_at)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <CardTitle>快捷操作</CardTitle>
          <div className="space-y-2 mt-3">
            {quickActions.map((action) => (
              <Link
                key={action.href}
                href={action.href}
                className="flex items-center gap-3 px-4 py-2.5 rounded-lg border border-border hover:border-border-hover hover:bg-surface-raised transition-all text-sm text-text-secondary hover:text-text-primary"
              >
                {action.icon}
                <span>{action.label}</span>
              </Link>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
