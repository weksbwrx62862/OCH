'use client';

import { useState } from 'react';
import { Card, CardTitle, Badge, Button, Avatar, Spinner, EmptyState, Modal, ConfirmModal, Input } from '@/components/ui';
import { Plus, Bot, Pencil, Trash2 } from 'lucide-react';
import apiClient from '@/lib/api';
import { useApi } from '@/lib/hooks/useApi';
import { formatDate } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';

interface Agent {
  id: string;
  name: string;
  description?: string;
  model: string;
  is_active: boolean;
  created_at?: string;
}

export default function AgentsPage() {
  const { data: agentsRes, loading, refetch } = useApi<{ data: Agent[]; total: number }>('/agents');
  const agents = agentsRes?.data || [];
  const addToast = useAppStore((s) => s.addToast);

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', description: '', model: 'claude-sonnet-4-20250514' });
  const [creating, setCreating] = useState(false);

  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [editForm, setEditForm] = useState({ name: '', description: '', model: '' });
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<Agent | null>(null);

  const handleCreate = async () => {
    if (!createForm.name.trim()) return;
    setCreating(true);
    try {
      await apiClient.post('/agents', createForm);
      setShowCreate(false);
      setCreateForm({ name: '', description: '', model: 'claude-sonnet-4-20250514' });
      addToast('success', '智能体创建成功');
      refetch();
    } catch (e) {
      addToast('error', '创建失败');
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (agent: Agent) => {
    setEditingAgent(agent);
    setEditForm({ name: agent.name, description: agent.description || '', model: agent.model });
  };

  const saveEdit = async () => {
    if (!editingAgent) return;
    setSaving(true);
    try {
      await apiClient.put(`/agents/${editingAgent.id}`, editForm);
      setEditingAgent(null);
      addToast('success', '智能体更新成功');
      refetch();
    } catch (e) {
      addToast('error', '更新失败');
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await apiClient.delete(`/agents/${deleteTarget.id}`);
      setDeleteTarget(null);
      addToast('success', '智能体已删除');
      refetch();
    } catch (e) {
      addToast('error', '删除失败');
      console.error(e);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-text-primary">智能体管理</h2>
          <p className="text-sm text-text-tertiary mt-1">创建和管理 AI 智能体</p>
        </div>
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreate(true)}>
          创建智能体
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : agents.length === 0 ? (
        <EmptyState
          icon={<Bot className="w-12 h-12" />}
          title="暂无智能体"
          description="创建第一个智能体来开始使用"
          action={{ label: '创建智能体', onClick: () => setShowCreate(true) }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <Card key={agent.id} hover>
              <div className="flex items-start gap-4">
                <Avatar name={agent.name} size="lg" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <CardTitle>{agent.name}</CardTitle>
                    <Badge variant={agent.is_active ? 'success' : 'default'} size="sm">
                      {agent.is_active ? '活跃' : '停用'}
                    </Badge>
                  </div>
                  <p className="text-xs text-text-tertiary mt-0.5">{agent.model}</p>
                </div>
              </div>
              {agent.description && (
                <p className="text-sm text-text-secondary mt-3 line-clamp-2">{agent.description}</p>
              )}
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
                <span className="text-xs text-text-tertiary">{formatDate(agent.created_at)}</span>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" icon={<Pencil className="w-3.5 h-3.5" />} onClick={() => startEdit(agent)}>
                    编辑
                  </Button>
                  <Button variant="ghost" size="sm" icon={<Trash2 className="w-3.5 h-3.5" />} onClick={() => setDeleteTarget(agent)}>
                    删除
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="创建智能体"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCreate(false)}>取消</Button>
            <Button loading={creating} onClick={handleCreate}>创建</Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm text-text-secondary mb-1 block">名称</label>
            <Input
              placeholder="输入智能体名称"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            />
          </div>
          <div>
            <label className="text-sm text-text-secondary mb-1 block">描述</label>
            <textarea
              placeholder="输入智能体描述（可选）"
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              rows={3}
              className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-border-focus resize-none"
            />
          </div>
          <div>
            <label className="text-sm text-text-secondary mb-1 block">模型</label>
            <select
              value={createForm.model}
              onChange={(e) => setCreateForm({ ...createForm, model: e.target.value })}
              className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-border-focus"
            >
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
              <option value="claude-opus-4-20250514">Claude Opus 4</option>
              <option value="gpt-4o">GPT-4o</option>
            </select>
          </div>
        </div>
      </Modal>

      <Modal
        open={!!editingAgent}
        onClose={() => setEditingAgent(null)}
        title="编辑智能体"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditingAgent(null)}>取消</Button>
            <Button loading={saving} onClick={saveEdit}>保存</Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm text-text-secondary mb-1 block">名称</label>
            <Input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
          </div>
          <div>
            <label className="text-sm text-text-secondary mb-1 block">描述</label>
            <textarea
              value={editForm.description}
              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              rows={3}
              className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-border-focus resize-none"
            />
          </div>
          <div>
            <label className="text-sm text-text-secondary mb-1 block">模型</label>
            <select
              value={editForm.model}
              onChange={(e) => setEditForm({ ...editForm, model: e.target.value })}
              className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-border-focus"
            >
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
              <option value="claude-opus-4-20250514">Claude Opus 4</option>
              <option value="gpt-4o">GPT-4o</option>
            </select>
          </div>
        </div>
      </Modal>

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="删除智能体"
        description={`确定删除智能体「${deleteTarget?.name}」？此操作不可撤销。`}
        confirmText="删除"
        variant="danger"
      />
    </div>
  );
}
