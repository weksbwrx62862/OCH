'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { Wrench, Clock, XCircle, CheckCircle, Shield } from 'lucide-react';
import type { Message, ToolUse } from './types';

const MarkdownRenderer = dynamic(
  () => import('./MarkdownRenderer'),
  {
    loading: () => (
      <div className="animate-pulse space-y-2">
        <div className="h-4 bg-surface-raised rounded w-3/4" />
        <div className="h-4 bg-surface-raised rounded w-full" />
        <div className="h-4 bg-surface-raised rounded w-5/6" />
      </div>
    ),
    ssr: false
  }
);

export const ToolCallCard = React.memo(function ToolCallCard({ toolUse, isActive }: { toolUse: ToolUse; isActive?: boolean }) {
  const isError = toolUse.is_error;
  const isSuccess = !isError && toolUse.output;

  return (
    <div
      className={`my-3 rounded-xl border p-4 ${
        isError
          ? 'border-error/30 bg-error-muted/50'
          : isActive
          ? 'border-primary/30 bg-primary-muted/50'
          : 'border-border bg-surface'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Badge variant={isError ? 'error' : 'primary'} size="sm">
            <Wrench className="w-3 h-3 mr-1" />
            {toolUse.name}
          </Badge>
          {isActive && (
            <span className="text-xs text-primary animate-pulse">执行中...</span>
          )}
        </div>
        {toolUse.duration_ms != null && (
          <span className="text-xs text-text-tertiary flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {toolUse.duration_ms}ms
          </span>
        )}
      </div>

      <div className="mb-2">
        <div className="text-xs text-text-tertiary mb-1">Input:</div>
        <pre className="text-xs bg-background/50 rounded-lg p-2 overflow-x-auto text-text-secondary">
          {JSON.stringify(toolUse.input, null, 2)}
        </pre>
      </div>

      {toolUse.output && (
        <div>
          <div className="text-xs text-text-tertiary mb-1 flex items-center gap-2">
            Output:
            {isError && <span className="text-error flex items-center gap-1"><XCircle className="w-3 h-3" /> Error</span>}
            {isSuccess && <span className="text-success flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Success</span>}
          </div>
          <pre
            className={`text-xs rounded-lg p-2 overflow-x-auto max-h-40 overflow-y-auto whitespace-pre-wrap ${
              isError ? 'bg-error-muted/50 text-error' : 'bg-background/50 text-text-secondary'
            }`}
          >
            {typeof toolUse.output === 'string'
              ? toolUse.output.length > 1000
                ? `${toolUse.output.slice(0, 1000)}\n... (${toolUse.output.length - 1000} more chars)`
                : toolUse.output
              : JSON.stringify(toolUse.output, null, 2)}
          </pre>
        </div>
      )}

      {toolUse.permission_decision && (
        <div className="mt-2 text-xs text-text-tertiary flex items-center gap-1">
          <Shield className="w-3 h-3" />
          Permission:{' '}
          <Badge
            size="sm"
            variant={
              toolUse.permission_decision === 'auto' ? 'success'
              : toolUse.permission_decision === 'allow' ? 'info'
              : 'warning'
            }
          >
            {toolUse.permission_decision}
          </Badge>
        </div>
      )}
    </div>
  );
});

export const MessageBubble = React.memo(function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className="flex gap-4">
      <Avatar
        name={isUser ? 'User' : 'AI'}
        size="sm"
      />
      <div className="flex-1 min-w-0">
        <div className="prose prose-invert max-w-none">
          <MarkdownRenderer content={message.content} />
        </div>

        {message.tool_uses?.map((tool, idx) => (
          <ToolCallCard key={idx} toolUse={tool} />
        ))}

        {(message.tokens_input || message.tokens_output) && (
          <div className="mt-2 flex items-center gap-3 text-xs text-text-tertiary">
            {message.tokens_input && <span>↑ {message.tokens_input.toLocaleString()}</span>}
            {message.tokens_output && <span>↓ {message.tokens_output.toLocaleString()}</span>}
          </div>
        )}
      </div>
    </div>
  );
});
