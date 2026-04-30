'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Wrench, BookOpen, Settings, Brain, ArrowUp, FolderSearch, Search, Bug, Code } from 'lucide-react';

const quickPrompts = [
  { icon: <FolderSearch className="w-5 h-5" />, label: '分析项目结构', prompt: '请帮我分析当前项目的目录结构和主要模块' },
  { icon: <Search className="w-5 h-5" />, label: '搜索代码', prompt: '搜索所有包含 TODO 或 FIXME 的文件' },
  { icon: <Bug className="w-5 h-5" />, label: '调试问题', prompt: '我遇到了一个 bug，请帮我定位和修复' },
  { icon: <Code className="w-5 h-5" />, label: '编写代码', prompt: '帮我写一个 RESTful API 的基础框架' },
];

interface ChatInputProps {
  input: string;
  setInput: (v: string) => void;
  isLoading: boolean;
  sessionId: string;
  showMemory: boolean;
  currentTurn: number;
  maxTurns: number;
  usage: { input_tokens: number; output_tokens: number };
  onSend: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onToggleMemory: () => void;
}

export function ChatInput({
  input, setInput, isLoading, sessionId, showMemory,
  currentTurn, maxTurns, usage,
  onSend, onKeyDown, onToggleMemory,
}: ChatInputProps) {
  return (
    <footer className="border-t border-border bg-surface/90 backdrop-blur-sm p-4">
      <div className="max-w-4xl mx-auto">
        <div className="relative flex items-end gap-2 rounded-2xl border border-border bg-surface-raised p-2 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="输入消息... (Shift+Enter 换行)"
            rows={1}
            disabled={isLoading}
            className="flex-1 bg-transparent resize-none outline-none px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary max-h-32 disabled:opacity-50"
            style={{ minHeight: '40px' }}
          />
          <Button
            onClick={onSend}
            disabled={!input.trim() || isLoading}
            size="sm"
            icon={<ArrowUp className="w-4 h-4" />}
          >
            发送
          </Button>
        </div>

        <div className="flex items-center gap-2 mt-2 px-1">
          <Link href="/tools" className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-text-tertiary hover:text-text-secondary hover:bg-surface-raised transition-colors">
            <Wrench className="w-3.5 h-3.5" />
            <span>Tools</span>
          </Link>
          <Link href="/skills" className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-text-tertiary hover:text-text-secondary hover:bg-surface-raised transition-colors">
            <BookOpen className="w-3.5 h-3.5" />
            <span>Skills</span>
          </Link>
          <Link href="/settings" className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-text-tertiary hover:text-text-secondary hover:bg-surface-raised transition-colors">
            <Settings className="w-3.5 h-3.5" />
            <span>Settings</span>
          </Link>
          <button
            onClick={onToggleMemory}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
              showMemory
                ? 'text-primary bg-primary-muted'
                : 'text-text-tertiary hover:text-text-secondary hover:bg-surface-raised'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>Memory</span>
          </button>
          <div className="ml-auto flex items-center gap-3 text-xs text-text-tertiary">
            {isLoading && (
              <>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-success rounded-full animate-pulse" />
                  Turn {currentTurn}/{maxTurns}
                </span>
                <span>Tokens: {(usage.input_tokens + usage.output_tokens).toLocaleString()}</span>
              </>
            )}
            {!isLoading && sessionId && (
              <span>Session: {sessionId.slice(0, 8)}...</span>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
}

export { quickPrompts };
