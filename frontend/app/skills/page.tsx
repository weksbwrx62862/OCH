'use client';

import { useMemo, useState } from 'react';
import { Plus, RefreshCw, BookOpen, Trash2 } from 'lucide-react';
import { Card, CardTitle, Badge, Button, Input, Spinner, EmptyState, Modal, ConfirmModal, Switch } from '@/components/ui';
import apiClient from '@/lib/api';
import { useApi } from '@/lib/hooks/useApi';
import { truncate } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';

interface Skill {
  id?: string;
  name: string;
  description: string;
  category: string;
  version?: string;
  source: string;
  enabled: boolean;
  triggers?: string[];
  usage_count?: number;
}

function getSourceBadgeVariant(source: string) {
  if (source === 'builtin') return 'primary' as const;
  if (source === 'file') return 'info' as const;
  return 'default' as const;
}

export default function SkillsPage() {
  const { data: skillsRes, loading, refetch } = useApi<{ data: Skill[]; total: number }>('/skills');
  const skills = skillsRes?.data || [];
  const addNotification = useAppStore((s) => s.addNotification);
  const [filter, setFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [showInstall, setShowInstall] = useState(false);
  const [installForm, setInstallForm] = useState({ source: '', name: '' });
  const [uninstallTarget, setUninstallTarget] = useState<string | null>(null);

  const filtered = useMemo(() => skills.filter((s) => {
    if (filter === 'enabled') return s.enabled;
    if (filter === 'disabled') return !s.enabled;
    return true;
  }), [skills, filter]);

  const toggleSkill = async (name: string, enable: boolean) => {
    try {
      await apiClient.put(`/skills/${name}${enable ? '/enable' : '/disable'}`, {});
      refetch();
    } catch (e) { console.error(e); addNotification({ type: 'error', title: '切换失败', message: '无法切换技能状态' }); }
  };

  const installSkill = async () => {
    try {
      await apiClient.post('/skills/install', { source: installForm.source, name: installForm.name || undefined });
      setShowInstall(false);
      setInstallForm({ source: '', name: '' });
      refetch();
    } catch (e) { console.error(e); }
  };

  const uninstallSkill = async () => {
    if (!uninstallTarget) return;
    try {
      await apiClient.delete(`/skills/${uninstallTarget}`);
      setUninstallTarget(null);
      refetch();
    } catch (e) { console.error(e); }
  };

  const scanSkills = async () => {
    try {
      await apiClient.post('/skills/scan');
      refetch();
    } catch (e) { console.error(e); }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold gradient-text">技能库</h2>
          <p className="text-sm text-text-tertiary mt-1">知识库技能管理</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" icon={<RefreshCw className="w-3.5 h-3.5" />} onClick={scanSkills}>扫描</Button>
          <Button size="sm" icon={<Plus className="w-3.5 h-3.5" />} onClick={() => setShowInstall(true)}>安装技能</Button>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        {([{ key: 'all' as const, label: '全部' }, { key: 'enabled' as const, label: '已启用' }, { key: 'disabled' as const, label: '已禁用' }]).map(({ key, label }) => (
          <button key={key} onClick={() => setFilter(key)} className={`px-3 py-2 text-xs rounded-lg border transition-colors ${filter === key ? 'bg-primary-muted border-primary text-primary' : 'border-border text-text-secondary hover:border-border-hover'}`}>{label}</button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={<BookOpen className="w-10 h-10" />} title="暂无技能" description="安装或扫描技能文件以开始使用" action={{ label: '安装技能', onClick: () => setShowInstall(true) }} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((skill) => (
            <Card key={skill.id || skill.name} hover>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2 min-w-0">
                  <BookOpen className="w-4 h-4 text-text-tertiary shrink-0" />
                  <CardTitle className="text-sm truncate">{skill.name}</CardTitle>
                </div>
                <Switch checked={skill.enabled} onChange={(checked) => toggleSkill(skill.name, checked)} />
              </div>
              <div className="flex items-center gap-2 mb-3">
                {skill.version && <Badge variant="default" size="sm">v{skill.version}</Badge>}
                <Badge variant={getSourceBadgeVariant(skill.source)} size="sm">{skill.source}</Badge>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed mb-4 line-clamp-2">{truncate(skill.description || '无描述')}</p>
              {skill.triggers && skill.triggers.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-1">
                  {skill.triggers.slice(0, 3).map((t) => (
                    <Badge key={t} variant="primary" size="sm" className="font-mono">/{t}</Badge>
                  ))}
                </div>
              )}
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <Badge variant="default" size="sm">{skill.category}</Badge>
                <div className="flex items-center gap-2">
                  {skill.usage_count !== undefined && skill.usage_count > 0 && <span className="text-xs text-text-tertiary">{skill.usage_count} 次使用</span>}
                  {skill.source !== 'builtin' && (
                    <Button variant="ghost" size="sm" icon={<Trash2 className="w-3.5 h-3.5" />} onClick={() => setUninstallTarget(skill.name)}>卸载</Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showInstall} onClose={() => setShowInstall(false)} title="安装技能" footer={<><Button variant="secondary" onClick={() => setShowInstall(false)}>取消</Button><Button onClick={installSkill}>安装</Button></>}>
        <div className="space-y-4">
          <div><label className="text-sm text-text-secondary mb-1 block">来源（URL 或文件路径）</label><Input placeholder="https://github.com/... 或 /path/to/skill.md" value={installForm.source} onChange={(e) => setInstallForm({ ...installForm, source: e.target.value })} /></div>
          <div><label className="text-sm text-text-secondary mb-1 block">名称（可选）</label><Input placeholder="自定义技能名称" value={installForm.name} onChange={(e) => setInstallForm({ ...installForm, name: e.target.value })} /></div>
        </div>
      </Modal>

      <ConfirmModal open={uninstallTarget !== null} onClose={() => setUninstallTarget(null)} onConfirm={uninstallSkill} title="确认卸载" description={`确定卸载技能「${uninstallTarget || ''}」？此操作不可撤销。`} confirmText="卸载" variant="danger" />
    </div>
  );
}
