'use client';

import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { Brain } from 'lucide-react';
import type { MemoryFact } from './types';

export function MemorySidebar({ facts }: { facts: MemoryFact[] }) {
  return (
    <aside className="w-72 border-l border-border bg-surface overflow-y-auto shrink-0 animate-slide-in-right">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary" />
            记忆库
          </h3>
          <Badge size="sm" variant="primary">{facts.length} 条</Badge>
        </div>
        {facts.length === 0 ? (
          <EmptyState
            icon={<Brain className="w-6 h-6" />}
            title="暂无记忆数据"
          />
        ) : (
          <div className="space-y-2">
            {facts.map((fact) => (
              <div key={fact.id} className="p-3 rounded-lg bg-surface-raised border border-border hover:border-border-hover transition-colors">
                <p className="text-xs text-text-secondary leading-relaxed">{fact.content}</p>
                {fact.category && (
                  <Badge size="sm" variant="primary" className="mt-1.5">{fact.category}</Badge>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
