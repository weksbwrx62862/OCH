'use client';

import { useEffect, useState } from 'react';
import { Card, CardTitle, Badge, Button, Input, Spinner, Tabs, ConfirmModal, Switch, Avatar } from '@/components/ui';
import { Settings, Bot, Shield, Plug, Info, Plus } from 'lucide-react';
import apiClient from '@/lib/api';
import { useApi } from '@/lib/hooks/useApi';

interface Config {
  app: { name: string; env: string; debug: boolean; version: string };
  openharness: { default_model: string; max_turns: number; max_tokens: number };
  security: { rate_limit_requests: number };
}

interface Provider {
  id: string;
  type: string;
  models: string[];
  key_configured?: boolean;
}

interface PermissionMode {
  id: string;
  name: string;
  description: string;
}

interface McpServer {
  id: string;
  name: string;
  type: string;
  status: string;
  tool_count?: number;
}

export default function SettingsPage() {
  const { data: config, loading } = useApi<Config>('/config');
  const [activeTab, setActiveTab] = useState('general');
  const { data: providersRes } = useApi<{ providers: Provider[]; total: number }>('/config/providers', { skip: activeTab !== 'providers' });
  const { data: mcpServersRes, refetch: refetchMcpServers } = useApi<{ data: McpServer[]; total: number }>('/mcp/servers', { skip: activeTab !== 'mcp' });

  const providers = providersRes?.providers || [];
  const mcpServers = mcpServersRes?.data || [];
  const [currentPermMode, setCurrentPermMode] = useState('default');
  const [showAddMcp, setShowAddMcp] = useState(false);
  const [mcpForm, setMcpForm] = useState({ name: '', type: 'stdio', command: '' });
  const [removeMcpTarget, setRemoveMcpTarget] = useState<{ id: string; name: string } | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const userStr = localStorage.getItem('och_user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setIsAdmin(user?.role === 'admin');
      } catch {}
    }
  }, []);

  useEffect(() => {
    apiClient.get<{ modes: PermissionMode[]; current_mode: string }>('/permissions/modes').then((res) => {
      if (res.current_mode) setCurrentPermMode(res.current_mode);
    }).catch(() => {});
  }, []);

  const handlePermModeChange = async (modeId: string) => {
    const prevMode = currentPermMode;
    setCurrentPermMode(modeId);
    try {
      await apiClient.put(`/permissions/modes/${modeId}`);
    } catch (e) {
      console.error(e);
      setCurrentPermMode(prevMode);
    }
  };

  const handleAddMcp = async () => {
    try {
      await apiClient.post('/mcp/servers', mcpForm);
      setShowAddMcp(false);
      setMcpForm({ name: '', type: 'stdio', command: '' });
      refetchMcpServers();
    } catch (e) { console.error(e); }
  };

  const handleRemoveMcp = async () => {
    if (!removeMcpTarget) return;
    try { await apiClient.delete(`/mcp/servers/${removeMcpTarget.id}`); refetchMcpServers(); } catch (e) { console.error(e); }
    setRemoveMcpTarget(null);
  };

  if (loading) return <div className="max-w-4xl mx-auto flex justify-center py-24"><Spinner size="lg" /></div>;

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-xl font-bold gradient-text mb-8">设置</h2>

      <Tabs
        activeTab={activeTab}
        onChange={setActiveTab}
        items={[
          {
            id: 'general', label: '通用', icon: <Settings className="w-4 h-4" />,
            content: config ? (
              <div>
                <CardTitle className="mb-6">通用设置</CardTitle>
                <div className="space-y-0">
                  {[
                    { label: '应用名称', value: config.app.name },
                    { label: '环境', value: config.app.env },
                    { label: '调试模式', value: config.app.debug ? '开启' : '关闭' },
                    { label: '默认模型', value: config.openharness.default_model },
                    { label: '最大轮次', value: String(config.openharness.max_turns) },
                    { label: '最大 Token', value: String(config.openharness.max_tokens) },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                      <label className="text-sm text-text-secondary">{item.label}</label>
                      <span className="text-sm font-mono bg-surface-raised px-3 py-1.5 rounded-md">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null,
          },
          {
            id: 'providers', label: '模型提供商', icon: <Bot className="w-4 h-4" />,
            content: (
              <div>
                <CardTitle className="mb-2">LLM 提供商配置</CardTitle>
                <p className="text-sm text-text-tertiary mb-4">API Key 通过环境变量配置，此处显示连接状态</p>
                <div className="space-y-3">
                  {providers.map((p) => (
                    <Card key={p.id} className="bg-surface-raised">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Avatar icon={<Bot className="w-4 h-4" />} size="sm" />
                          <div>
                            <p className="text-sm font-medium">{p.type === 'anthropic' ? 'Anthropic' : p.type === 'openai' ? 'OpenAI' : p.type}</p>
                            <p className="text-xs text-text-tertiary">{(p.models || []).join(', ')}</p>
                          </div>
                        </div>
                        <Badge variant={p.key_configured ? 'success' : 'default'}>{p.key_configured ? '已配置' : '未配置'}</Badge>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ),
          },
          {
            id: 'permissions', label: '权限', icon: <Shield className="w-4 h-4" />,
            content: (
              <div>
                <CardTitle className="mb-4">权限模式</CardTitle>
                <div className="space-y-3">
                  {[
                    { id: 'default', name: '默认模式', description: '写入/执行操作前询问确认' },
                    { id: 'auto', name: '自动模式', description: '允许所有操作（沙箱内执行）' },
                    { id: 'plan', name: '计划模式', description: '禁止所有写入，仅允许读取' },
                  ].map((m) => (
                    <Card key={m.id} clickable onClick={() => handlePermModeChange(m.id)} className={`bg-surface-raised ${currentPermMode === m.id ? 'border-primary ring-1 ring-primary' : ''}`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">{m.name}{m.id === 'default' && <Badge variant="primary" size="sm" className="ml-2">推荐</Badge>}</p>
                          <p className="text-xs text-text-tertiary mt-1">{m.description}</p>
                        </div>
                        <Switch checked={currentPermMode === m.id} onChange={() => handlePermModeChange(m.id)} />
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ),
          },
          {
            id: 'mcp', label: 'MCP 服务', icon: <Plug className="w-4 h-4" />,
            content: (
              <div>
                <CardTitle className="mb-2">MCP 服务器</CardTitle>
                <p className="text-sm text-text-tertiary mb-4">管理 Model Context Protocol 外部工具服务</p>
                {mcpServers.length > 0 && (
                  <div className="space-y-3 mb-4">
                    {mcpServers.map((srv) => (
                      <Card key={srv.id} className="bg-surface-raised">
                        <div className="flex items-center justify-between">
                          <div><p className="text-sm font-medium">{srv.name}</p><p className="text-xs text-text-tertiary">{srv.type} · {srv.tool_count || 0} 个工具</p></div>
                          <div className="flex items-center gap-2">
                            <Badge variant={srv.status === 'connected' ? 'success' : 'default'}>{srv.status === 'connected' ? '已连接' : srv.status}</Badge>
                            {isAdmin && (<Button variant="ghost" size="sm" onClick={() => setRemoveMcpTarget({ id: srv.id, name: srv.name })}>移除</Button>)}
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
                {showAddMcp ? (
                  <Card className="border-dashed">
                    <div className="space-y-3">
                      <Input placeholder="服务器名称" value={mcpForm.name} onChange={(e) => setMcpForm({ ...mcpForm, name: e.target.value })} />
                      <Input placeholder="命令" value={mcpForm.command} onChange={(e) => setMcpForm({ ...mcpForm, command: e.target.value })} />
                      <div className="flex justify-end gap-2">
                        <Button variant="secondary" size="sm" onClick={() => setShowAddMcp(false)}>取消</Button>
                        <Button size="sm" onClick={handleAddMcp}>添加</Button>
                      </div>
                    </div>
                  </Card>
                ) : (
                  isAdmin ? (
                    <Button variant="secondary" className="w-full border-dashed" icon={<Plus className="w-4 h-4" />} onClick={() => setShowAddMcp(true)}>添加 MCP 服务器</Button>
                  ) : (
                    <p className="text-sm text-text-tertiary">需要管理员权限才能添加 MCP 服务器</p>
                  )
                )}
              </div>
            ),
          },
          {
            id: 'about', label: '关于', icon: <Info className="w-4 h-4" />,
            content: config ? (
              <div>
                <CardTitle className="mb-6">关于 OpenClaw-Harness</CardTitle>
                <div className="text-center py-8">
                  <Avatar name="OCH" size="lg" className="mx-auto mb-4" />
                  <h3 className="font-semibold text-lg">OpenClaw-Harness</h3>
                  <p className="text-sm text-text-tertiary mt-1">v{config.app.version} · 基于 OpenHarness 核心</p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <Card className="bg-surface-raised"><p className="text-text-tertiary">API 路由</p><p className="font-mono mt-1">126 个</p></Card>
                  <Card className="bg-surface-raised"><p className="text-text-tertiary">数据模型</p><p className="font-mono mt-1">14 个</p></Card>
                  <Card className="bg-surface-raised"><p className="text-text-tertiary">内置工具</p><p className="font-mono mt-1">43+</p></Card>
                  <Card className="bg-surface-raised"><p className="text-text-tertiary">内置技能</p><p className="font-mono mt-1">9 个</p></Card>
                </div>
              </div>
            ) : null,
          },
        ]}
      />

      <ConfirmModal open={removeMcpTarget !== null} onClose={() => setRemoveMcpTarget(null)} onConfirm={handleRemoveMcp} title="移除 MCP 服务器" description={`确定移除 MCP 服务器「${removeMcpTarget?.name}」？`} confirmText="移除" variant="danger" />
    </div>
  );
}
