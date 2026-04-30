'use client';

import { useEffect, useMemo, useState } from 'react';
import { Card, Badge, Button, Spinner, EmptyState, ConfirmModal } from '@/components/ui';
import { Download, Trash2, Plus, Pencil, ShieldBan, Zap, ClipboardList, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import apiClient from '@/lib/api';
import { formatDate } from '@/lib/utils';

import { AuditLog } from '@/lib/types';

interface AuditStats {
  total: number;
  by_action: Record<string, number>;
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'success' | 'denied' | 'error'>('all');
  const [showPurgeConfirm, setShowPurgeConfirm] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [logsRes, statsRes] = await Promise.all([
        apiClient.get<{ data: AuditLog[]; total: number }>('/audit?per_page=50'),
        apiClient.get<AuditStats>('/audit/stats'),
      ]);
      setLogs(logsRes.data || []);
      setStats(statsRes);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const handlePurge = async () => {
    try { await apiClient.post('/audit/purge'); loadData(); } catch (e) { console.error(e); }
    setShowPurgeConfirm(false);
  };

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('och_token');
      const response = await fetch('/api/v1/audit/export', { headers: { 'Authorization': `Bearer ${token}` } });
      if (!response.ok) throw new Error('导出失败');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'audit_export.csv';
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) { console.error(e); }
  };

  const filtered = useMemo(() => logs.filter((l) => {
    if (filter === 'all') return true;
    if (filter === 'success') return !l.action.includes('deny') && (!l.status_code || l.status_code < 400);
    if (filter === 'denied') return l.action.includes('deny');
    if (filter === 'error') return l.status_code != null && l.status_code >= 400;
    return true;
  }), [logs, filter]);

  const actionIcon = (action: string) => {
    if (action.includes('create')) return <Plus className="w-4 h-4 text-success" />;
    if (action.includes('delete')) return <Trash2 className="w-4 h-4 text-error" />;
    if (action.includes('update')) return <Pencil className="w-4 h-4 text-info" />;
    if (action.includes('deny') || action.includes('block')) return <ShieldBan className="w-4 h-4 text-error" />;
    if (action.includes('execute') || action.includes('run')) return <Zap className="w-4 h-4 text-warning" />;
    return <ClipboardList className="w-4 h-4 text-text-tertiary" />;
  };

  const logStatusBadge = (log: AuditLog): { variant: 'success' | 'error' | 'warning'; label: string } => {
    if (log.action.includes('deny')) return { variant: 'error', label: '拒绝' };
    if (log.status_code && log.status_code >= 400) return { variant: 'warning', label: '错误' };
    return { variant: 'success', label: '成功' };
  };

  const filterItems: { key: typeof filter; label: string; icon: React.ReactNode }[] = [
    { key: 'all', label: '全部', icon: <ClipboardList className="w-3.5 h-3.5" /> },
    { key: 'success', label: '成功', icon: <CheckCircle className="w-3.5 h-3.5" /> },
    { key: 'denied', label: '拒绝', icon: <XCircle className="w-3.5 h-3.5" /> },
    { key: 'error', label: '错误', icon: <AlertTriangle className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold gradient-text">审计日志</h2>
          <p className="text-sm text-text-tertiary mt-1">操作记录与安全审计</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" icon={<Download className="w-4 h-4" />} onClick={handleExport}>导出</Button>
          <Button variant="danger" size="sm" icon={<Trash2 className="w-4 h-4" />} onClick={() => setShowPurgeConfirm(true)}>清理过期</Button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card><p className="text-xs text-text-tertiary">总记录</p><p className="text-2xl font-bold mt-1">{stats.total}</p></Card>
          <Card><p className="text-xs text-text-tertiary">工具调用</p><p className="text-2xl font-bold mt-1 text-success">{stats.by_action?.tool_use || 0}</p></Card>
          <Card><p className="text-xs text-text-tertiary">权限拒绝</p><p className="text-2xl font-bold mt-1 text-error">{stats.by_action?.tool_denied || 0}</p></Card>
          <Card><p className="text-xs text-text-tertiary">操作类型</p><p className="text-2xl font-bold mt-1 text-warning">{Object.keys(stats.by_action || {}).length}</p></Card>
        </div>
      )}

      <div className="flex gap-2 mb-4">
        {filterItems.map((f) => (
          <Button key={f.key} variant={filter === f.key ? 'primary' : 'secondary'} size="sm" icon={f.icon} onClick={() => setFilter(f.key)}>{f.label}</Button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={<ClipboardList className="w-10 h-10" />} title="暂无审计记录" description="当前没有匹配的审计日志" />
      ) : (
        <div className="space-y-2">
          {filtered.map((log) => {
            const statusInfo = logStatusBadge(log);
            return (
              <Card key={log.id} hover padding="sm">
                <div className="flex items-center gap-4">
                  <span className="shrink-0">{actionIcon(log.action)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{log.action}</span>
                      <Badge variant="default" size="sm">{log.resource_type}</Badge>
                    </div>
                    <p className="text-xs text-text-tertiary mt-0.5 truncate">{log.resource_id}{log.agent_id && ` · Agent: ${log.agent_id}`}{log.details && ` · ${log.details}`}</p>
                  </div>
                  <Badge variant={statusInfo.variant} size="sm">{statusInfo.label}</Badge>
                  <span className="text-xs text-text-tertiary whitespace-nowrap">{formatDate(log.created_at)}</span>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <ConfirmModal open={showPurgeConfirm} onClose={() => setShowPurgeConfirm(false)} onConfirm={handlePurge} title="清理过期审计日志" description="确定清理过期审计日志？此操作不可恢复。" confirmText="清理" variant="danger" />
    </div>
  );
}
