'use client';

import { useMemo, useState } from 'react';
import { Card, Badge, Button, Spinner, EmptyState, ConfirmModal } from '@/components/ui';
import { Plus, Circle, Pause, Play, Trash2, ChevronRight } from 'lucide-react';
import apiClient from '@/lib/api';
import { useApi } from '@/lib/hooks/useApi';
import { formatDate } from '@/lib/utils';
import Link from 'next/link';
import { useAppStore } from '@/stores/appStore';

interface Session {
  id: string;
  title: string;
  status: string;
  agent_id?: string;
  total_messages?: number;
  created_at?: string;
  updated_at?: string;
}

export default function SessionsPage() {
  const { data: sessionsRes, loading, refetch } = useApi<{ data: Session[]; total: number }>('/sessions');
  const sessions = sessionsRes?.data || [];
  const addNotification = useAppStore((s) => s.addNotification);
  const [deleteTarget, setDeleteTarget] = useState<Session | null>(null);

  const pauseSession = async (e: React.MouseEvent, sessionId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await apiClient.put(`/sessions/${sessionId}/pause`);
      refetch();
    } catch (err) { console.error(err); }
  };

  const resumeSession = async (e: React.MouseEvent, sessionId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await apiClient.put(`/sessions/${sessionId}/resume`);
      refetch();
    } catch (err) { console.error(err); addNotification({ type: 'error', title: '恢复失败', message: '无法恢复会话' }); }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await apiClient.delete(`/sessions/${deleteTarget.id}`);
      setDeleteTarget(null);
      refetch();
    } catch (err) { console.error(err); }
  };

  const statusBadgeVariant = (status: string): 'success' | 'warning' | 'info' | 'default' => {
    if (status === 'active') return 'success';
    if (status === 'paused') return 'warning';
    if (status === 'completed') return 'info';
    return 'default';
  };

  const statusLabel = (status: string): string => {
    const labels: Record<string, string> = { active: '活跃', completed: '已完成', paused: '暂停' };
    return labels[status] || status;
  };

  const stats = useMemo(() => [
    { label: '总会话', value: sessions.length },
    { label: '活跃', value: sessions.filter((s) => s.status === 'active').length },
    { label: '已暂停', value: sessions.filter((s) => s.status === 'paused').length },
    { label: '总消息', value: sessions.reduce((acc, s) => acc + (s.total_messages || 0), 0) },
  ], [sessions]);

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-text-primary">会话管理</h2>
          <p className="text-sm text-text-tertiary mt-1">所有聊天会话</p>
        </div>
        <Link href="/chat">
          <Button icon={<Plus className="w-4 h-4" />}>新建对话</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {stats.map((stat) => (
          <Card key={stat.label} padding="md">
            <p className="text-xs text-text-tertiary">{stat.label}</p>
            <p className="text-xl font-bold mt-1 text-text-primary">{stat.value}</p>
          </Card>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><Spinner size="lg" /></div>
      ) : sessions.length === 0 ? (
        <EmptyState
          icon={<Circle className="w-12 h-12" />}
          title="暂无会话"
          description="开始第一个对话来体验"
          action={{ label: '新建对话', onClick: () => { window.location.href = '/chat'; } }}
        />
      ) : (
        <div className="space-y-2">
          {sessions.map((session) => (
            <Link key={session.id} href={`/chat?sid=${session.id}`} className="group block">
              <Card hover clickable padding="md">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <Circle
                      className={`w-2.5 h-2.5 shrink-0 ${
                        session.status === 'active' ? 'text-success fill-success' :
                        session.status === 'paused' ? 'text-warning fill-warning' :
                        session.status === 'completed' ? 'text-info fill-info' :
                        'text-text-tertiary fill-text-tertiary'
                      }`}
                    />
                    <div className="min-w-0">
                      <p className="font-medium text-sm truncate text-text-primary group-hover:text-primary transition-colors">
                        {session.title || '未命名会话'}
                      </p>
                      <p className="text-xs text-text-tertiary mt-0.5">
                        {formatDate(session.created_at)} · {session.total_messages || 0} 条消息
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <Badge variant={statusBadgeVariant(session.status)} size="sm">
                      {statusLabel(session.status)}
                    </Badge>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {session.status === 'active' && (
                        <Button variant="ghost" size="sm" icon={<Pause className="w-3.5 h-3.5" />} onClick={(e) => pauseSession(e, session.id)}>暂停</Button>
                      )}
                      {session.status === 'paused' && (
                        <Button variant="ghost" size="sm" icon={<Play className="w-3.5 h-3.5" />} onClick={(e) => resumeSession(e, session.id)}>恢复</Button>
                      )}
                      <Button variant="ghost" size="sm" icon={<Trash2 className="w-3.5 h-3.5" />} onClick={(e) => { e.preventDefault(); e.stopPropagation(); setDeleteTarget(session); }}>删除</Button>
                    </div>
                    <ChevronRight className="w-4 h-4 text-text-tertiary group-hover:text-primary group-hover:translate-x-1 transition-all" />
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="删除会话"
        description={`确定删除会话「${deleteTarget?.title || '未命名会话'}」？此操作不可撤销。`}
        confirmText="删除"
        variant="danger"
      />
    </div>
  );
}
