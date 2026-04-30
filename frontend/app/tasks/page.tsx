'use client';

import { useEffect, useMemo, useState } from 'react';
import { Card, Badge, Button, Spinner, EmptyState, ConfirmModal } from '@/components/ui';
import { Circle, Play, CheckCircle, XCircle, Clock, Pause, Trash2 } from 'lucide-react';
import apiClient from '@/lib/api';
import { formatDate } from '@/lib/utils';

interface Task {
  id: string;
  name: string;
  description?: string;
  status: string;
  priority: string;
  progress?: number;
  created_at?: string;
  error?: string;
  depends_on?: string[];
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'running' | 'completed' | 'failed' | 'pending'>('all');
  const [confirmAction, setConfirmAction] = useState<{ type: 'stop' | 'delete'; taskId: string } | null>(null);

  useEffect(() => { loadTasks(); }, []);

  const loadTasks = async () => {
    try {
      const res = await apiClient.get<{ data: Task[]; total: number }>('/tasks');
      setTasks(res.data || []);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const handleConfirm = async () => {
    if (!confirmAction) return;
    try {
      if (confirmAction.type === 'stop') await apiClient.put(`/tasks/${confirmAction.taskId}/stop`);
      else await apiClient.delete(`/tasks/${confirmAction.taskId}`);
      loadTasks();
    } catch (e) { console.error(e); }
    setConfirmAction(null);
  };

  const filtered = useMemo(() => tasks.filter((t) => filter === 'all' || t.status === filter), [tasks, filter]);
  const statusCounts = useMemo(() => ({
    all: tasks.length, running: tasks.filter((t) => t.status === 'running').length,
    completed: tasks.filter((t) => t.status === 'completed').length,
    failed: tasks.filter((t) => t.status === 'failed').length,
    pending: tasks.filter((t) => t.status === 'pending').length,
  }), [tasks]);

  const statusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Play className="w-3.5 h-3.5 text-info" />;
      case 'completed': return <CheckCircle className="w-3.5 h-3.5 text-success" />;
      case 'failed': return <XCircle className="w-3.5 h-3.5 text-error" />;
      case 'pending': return <Clock className="w-3.5 h-3.5 text-warning" />;
      case 'paused': return <Pause className="w-3.5 h-3.5 text-warning" />;
      default: return <Circle className="w-3.5 h-3.5 text-text-tertiary" />;
    }
  };

  const statusBadgeVariant = (status: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
    if (status === 'completed') return 'success';
    if (status === 'running') return 'info';
    if (status === 'failed' || status === 'error') return 'error';
    if (status === 'pending' || status === 'paused') return 'warning';
    return 'default';
  };

  const statusLabel = (status: string): string => {
    const labels: Record<string, string> = { active: '活跃', completed: '已完成', running: '运行中', pending: '等待中', failed: '失败', paused: '暂停', stopped: '已停止' };
    return labels[status] || status;
  };

  const statItems: { key: keyof typeof statusCounts; label: string; icon: React.ReactNode }[] = [
    { key: 'all', label: '全部', icon: <Circle className="w-4 h-4" /> },
    { key: 'running', label: '运行中', icon: <Play className="w-4 h-4" /> },
    { key: 'completed', label: '已完成', icon: <CheckCircle className="w-4 h-4" /> },
    { key: 'failed', label: '失败', icon: <XCircle className="w-4 h-4" /> },
    { key: 'pending', label: '等待中', icon: <Clock className="w-4 h-4" /> },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h2 className="text-xl font-bold gradient-text">任务管理</h2>
        <p className="text-sm text-text-tertiary mt-1">后台任务执行与监控</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        {statItems.map((s) => (
          <Card key={s.key} clickable onClick={() => setFilter(s.key)} className={filter === s.key ? 'border-primary ring-1 ring-primary' : ''}>
            <div className="flex items-center gap-2 mb-1">{s.icon}<p className="text-xs text-text-tertiary">{s.label}</p></div>
            <p className="text-2xl font-bold">{statusCounts[s.key]}</p>
          </Card>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={<Clock className="w-10 h-10" />} title="暂无任务" description="当前没有匹配的任务记录" />
      ) : (
        <div className="space-y-3">
          {filtered.map((task) => (
            <Card key={task.id} hover>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  {statusIcon(task.status)}
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{task.name}</p>
                    {task.description && <p className="text-xs text-text-tertiary mt-0.5 truncate">{task.description}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {task.progress != null && task.status === 'running' && (
                    <div className="w-24 h-1.5 bg-surface-raised rounded-full overflow-hidden">
                      <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${task.progress}%` }} />
                    </div>
                  )}
                  <Badge variant={statusBadgeVariant(task.status)} size="sm">{statusLabel(task.status)}</Badge>
                  <span className="text-xs text-text-tertiary">{formatDate(task.created_at)}</span>
                  <div className="flex gap-1">
                    {task.status === 'running' && <Button variant="ghost" size="sm" icon={<Pause className="w-3.5 h-3.5" />} onClick={() => setConfirmAction({ type: 'stop', taskId: task.id })}>停止</Button>}
                    {(task.status === 'completed' || task.status === 'failed' || task.status === 'stopped') && <Button variant="ghost" size="sm" icon={<Trash2 className="w-3.5 h-3.5" />} onClick={() => setConfirmAction({ type: 'delete', taskId: task.id })}>删除</Button>}
                  </div>
                </div>
              </div>
              {task.error && <div className="mt-3 p-2 bg-error-muted border border-error/20 rounded-lg"><p className="text-xs text-error font-mono">{task.error}</p></div>}
              {task.depends_on && task.depends_on.length > 0 && (
                <div className="mt-2 flex items-center gap-1">
                  <span className="text-xs text-text-tertiary">依赖:</span>
                  {task.depends_on.map((dep) => <Badge key={dep} variant="default" size="sm" className="font-mono">{dep.slice(0, 8)}...</Badge>)}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      <ConfirmModal open={confirmAction !== null} onClose={() => setConfirmAction(null)} onConfirm={handleConfirm} title={confirmAction?.type === 'stop' ? '停止任务' : '删除任务'} description={confirmAction?.type === 'stop' ? '确定停止该任务？' : '确定删除该任务？此操作不可恢复。'} confirmText={confirmAction?.type === 'stop' ? '停止' : '删除'} variant="danger" />
    </div>
  );
}
