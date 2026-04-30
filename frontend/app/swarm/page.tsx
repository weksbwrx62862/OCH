'use client';

import { useState } from 'react';
import { Card, CardTitle, Badge, Button, Avatar, Spinner, EmptyState, Modal, ConfirmModal, Input } from '@/components/ui';
import { Plus, Users, Bot, ListTodo, Trash2 } from 'lucide-react';
import apiClient from '@/lib/api';
import { useApi } from '@/lib/hooks/useApi';

interface Team {
  id: string;
  name: string;
  description?: string;
  status: string;
  member_count?: number;
  created_at?: string;
}

interface AgentDef {
  id: string;
  name: string;
  description: string;
}

export default function SwarmPage() {
  const { data: teamsRes, loading: teamsLoading, refetch: refetchTeams } = useApi<{ data: Team[]; total: number }>('/coordinator/teams');
  const { data: agentsRes, loading: agentsLoading } = useApi<{ agents: AgentDef[]; total_builtin: number; total_custom: number }>('/coordinator/agents');
  const { data: tasksRes } = useApi<{ tasks: { id: string }[]; total: number }>('/coordinator/tasks');
  const loading = teamsLoading || agentsLoading;
  const teams = teamsRes?.data || [];
  const agents = agentsRes?.agents || [];
  const taskCount = tasksRes?.total || 0;

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDesc, setNewTeamDesc] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return;
    try {
      await apiClient.post('/coordinator/teams', { name: newTeamName.trim(), description: newTeamDesc.trim() || undefined });
      setShowCreateModal(false);
      setNewTeamName('');
      setNewTeamDesc('');
      refetchTeams();
    } catch (e) { console.error(e); }
  };

  const handleDeleteTeam = async () => {
    if (!deleteTarget) return;
    try {
      await apiClient.delete(`/coordinator/teams/${deleteTarget.id}`);
      setDeleteTarget(null);
      refetchTeams();
    } catch (e) { console.error(e); }
  };

  const statusBadgeVariant = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    if (status === 'active') return 'success';
    if (status === 'pending') return 'warning';
    if (status === 'failed' || status === 'error') return 'error';
    return 'default';
  };

  const statusLabel = (status: string): string => {
    const labels: Record<string, string> = { active: '活跃', completed: '已完成', running: '运行中', pending: '等待中', failed: '失败', paused: '暂停', stopped: '停止' };
    return labels[status] || status;
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold gradient-text">多智能体协作</h2>
          <p className="text-sm text-text-tertiary mt-1">Swarm 团队管理与协作</p>
        </div>
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>创建团队</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card><div className="flex items-center gap-3"><Avatar icon={<Users className="w-4 h-4" />} size="md" /><div><p className="text-xs text-text-tertiary">活跃团队</p><p className="text-2xl font-bold text-success">{teams.filter((t) => t.status === 'active').length}</p></div></div></Card>
        <Card><div className="flex items-center gap-3"><Avatar icon={<Bot className="w-4 h-4" />} size="md" /><div><p className="text-xs text-text-tertiary">可用智能体</p><p className="text-2xl font-bold text-info">{agents.length}</p></div></div></Card>
        <Card><div className="flex items-center gap-3"><Avatar icon={<Bot className="w-4 h-4" />} size="md" /><div><p className="text-xs text-text-tertiary">内置智能体</p><p className="text-2xl font-bold text-primary">{agentsRes?.total_builtin || 0}</p></div></div></Card>
        <Card><div className="flex items-center gap-3"><Avatar icon={<ListTodo className="w-4 h-4" />} size="md" /><div><p className="text-xs text-text-tertiary">总任务数</p><p className="text-2xl font-bold text-info">{taskCount}</p></div></div></Card>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : teams.length === 0 ? (
        <EmptyState icon={<Users className="w-10 h-10" />} title="暂无团队" description="创建第一个团队，开始多智能体协作" action={{ label: '创建团队', onClick: () => setShowCreateModal(true) }} />
      ) : (
        <div className="space-y-3">
          {teams.map((team) => (
            <Card key={team.id} hover>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Avatar name={team.name} size="md" />
                  <div>
                    <CardTitle>{team.name}</CardTitle>
                    <p className="text-xs text-text-tertiary mt-0.5">{team.description || '无描述'} · {team.member_count || 0} 成员</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={statusBadgeVariant(team.status)}>{statusLabel(team.status)}</Badge>
                  <span className="text-xs text-text-tertiary">{team.created_at?.slice(0, 10)}</span>
                  <Button variant="ghost" size="sm" icon={<Trash2 className="w-3.5 h-3.5" />} onClick={() => setDeleteTarget({ id: team.id, name: team.name })}>解散</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <div className="mt-12">
        <h3 className="text-lg font-semibold mb-4">可用子智能体</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {agents.map((agent) => {
            const isBuiltin = ['code-reviewer', 'debugger', 'planner'].includes(agent.id);
            return (
              <Card key={agent.id} hover>
                <div className="flex items-start gap-3">
                  <Avatar icon={<Bot className="w-4 h-4" />} size="sm" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-sm">{agent.name}</p>
                    <p className="text-xs text-text-tertiary mt-1 line-clamp-2">{agent.description}</p>
                    <Badge variant={isBuiltin ? 'primary' : 'info'} size="sm" className="mt-2">{isBuiltin ? '内置' : '自定义'}</Badge>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      <Modal open={showCreateModal} onClose={() => { setShowCreateModal(false); setNewTeamName(''); setNewTeamDesc(''); }} title="创建团队" footer={<><Button variant="secondary" onClick={() => { setShowCreateModal(false); setNewTeamName(''); setNewTeamDesc(''); }}>取消</Button><Button onClick={handleCreateTeam} disabled={!newTeamName.trim()}>创建</Button></>}>
        <div className="space-y-4">
          <div><label className="text-sm text-text-secondary mb-1.5 block">团队名称</label><Input placeholder="输入团队名称" value={newTeamName} onChange={(e) => setNewTeamName(e.target.value)} /></div>
          <div><label className="text-sm text-text-secondary mb-1.5 block">团队描述（可选）</label><Input placeholder="输入团队描述" value={newTeamDesc} onChange={(e) => setNewTeamDesc(e.target.value)} /></div>
        </div>
      </Modal>

      <ConfirmModal open={deleteTarget !== null} onClose={() => setDeleteTarget(null)} onConfirm={handleDeleteTeam} title="解散团队" description={`确定解散团队「${deleteTarget?.name}」？此操作不可恢复。`} confirmText="解散" variant="danger" />
    </div>
  );
}
