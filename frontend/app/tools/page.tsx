'use client';

import { useMemo, useState } from 'react';
import { Search, Wrench, Shield, ShieldAlert, ShieldCheck } from 'lucide-react';
import { Card, CardTitle, Badge, Input, Spinner, EmptyState } from '@/components/ui';
import { useApi } from '@/lib/hooks/useApi';
import { truncate } from '@/lib/utils';

interface ToolInfo {
  name: string;
  description: string;
  category: string;
  dangerous: boolean;
  requires_permission: boolean;
  danger_level: 'safe' | 'caution' | 'danger';
  input_schema?: Record<string, unknown>;
}

interface CategoryInfo {
  id: string;
  name: string;
  icon: string;
  count: number;
}

const CATEGORY_LABELS: Record<string, string> = {
  file_io: '文件系统', web: '网络', agent: '智能体', task: '任务',
  mcp: 'MCP', mode: '模式', schedule: '调度', meta: '元工具',
};

function getDangerLevel(tool: { dangerous?: boolean; requires_permission?: boolean }): 'safe' | 'caution' | 'danger' {
  if (tool.dangerous) return 'danger';
  if (tool.requires_permission) return 'caution';
  return 'safe';
}

function getDangerBadgeVariant(level: 'safe' | 'caution' | 'danger') {
  if (level === 'danger') return 'error' as const;
  if (level === 'caution') return 'warning' as const;
  return 'success' as const;
}

function getDangerIcon(level: 'safe' | 'caution' | 'danger') {
  if (level === 'danger') return ShieldAlert;
  if (level === 'caution') return Shield;
  return ShieldCheck;
}

export default function ToolsPage() {
  const { data: toolsRes, loading: toolsLoading } = useApi<{ total: number; categories: Record<string, ToolInfo[]> }>('/tools');
  const { data: catRes, loading: catLoading } = useApi<{ categories: CategoryInfo[] }>('/tools/categories');
  const loading = toolsLoading || catLoading;
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const tools = useMemo(() => {
    if (!toolsRes) return [];
    const allTools: ToolInfo[] = [];
    for (const [, catTools] of Object.entries(toolsRes.categories || {})) {
      for (const tool of catTools) {
        allTools.push({ ...tool, danger_level: getDangerLevel(tool) });
      }
    }
    return allTools;
  }, [toolsRes]);

  const categories = catRes?.categories || [];

  const filtered = tools.filter((t) => {
    if (selectedCategory !== 'all' && t.category !== selectedCategory) return false;
    if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase()) && !t.description.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h2 className="text-xl font-bold gradient-text">工具库</h2>
        <p className="text-sm text-text-tertiary mt-1">共 {tools.length} 个可用工具</p>
      </div>

      <div className="flex gap-4 mb-6">
        <Input variant="search" placeholder="搜索工具..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onClear={() => setSearchQuery('')} className="flex-1" />
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setSelectedCategory('all')} className={`px-3 py-2 text-xs rounded-lg border transition-colors ${selectedCategory === 'all' ? 'bg-primary-muted border-primary text-primary' : 'border-border text-text-secondary hover:border-border-hover'}`}>全部</button>
          {categories.map((cat) => (
            <button key={cat.id} onClick={() => setSelectedCategory(cat.id)} className={`px-3 py-2 text-xs rounded-lg border transition-colors ${selectedCategory === cat.id ? 'bg-primary-muted border-primary text-primary' : 'border-border text-text-secondary hover:border-border-hover'}`}>
              {CATEGORY_LABELS[cat.id] || cat.name} ({cat.count})
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={<Wrench className="w-10 h-10" />} title="未找到匹配的工具" description="尝试调整搜索关键词或选择其他分类" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((tool) => {
            const DangerIcon = getDangerIcon(tool.danger_level);
            return (
              <Card key={tool.name} hover>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Wrench className="w-4 h-4 text-text-tertiary shrink-0" />
                    <CardTitle className="text-sm font-mono">{tool.name}</CardTitle>
                  </div>
                  <Badge variant={getDangerBadgeVariant(tool.danger_level)} size="sm">
                    <DangerIcon className="w-3 h-3 mr-1" />
                    {tool.danger_level === 'danger' ? '危险' : tool.danger_level === 'caution' ? '警告' : '安全'}
                  </Badge>
                </div>
                <p className="text-sm text-text-secondary leading-relaxed">{truncate(tool.description)}</p>
                {tool.input_schema && tool.input_schema.properties && Object.keys(tool.input_schema.properties as Record<string, unknown>).length > 0 ? (
                  <div className="mt-3 pt-3 border-t border-border">
                    <p className="text-xs text-text-tertiary mb-1">参数</p>
                    <div className="flex flex-wrap gap-1">
                      {Object.keys(tool.input_schema.properties as Record<string, unknown>).slice(0, 4).map((param) => (
                        <Badge key={param} variant="default" size="sm" className="font-mono">{param}</Badge>
                      ))}
                      {Object.keys(tool.input_schema.properties as Record<string, unknown>).length > 4 && (
                        <span className="text-xs px-1.5 py-0.5 text-text-tertiary">+{Object.keys(tool.input_schema.properties as Record<string, unknown>).length - 4} 更多</span>
                      )}
                    </div>
                  </div>
                ) : null}
                <div className="mt-3 pt-3 border-t border-border">
                  <Badge variant="default" size="sm">{CATEGORY_LABELS[tool.category] || tool.category}</Badge>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
