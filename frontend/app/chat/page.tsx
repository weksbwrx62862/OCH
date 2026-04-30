'use client';

import React, { useState, useRef, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import apiClient from '@/lib/api';
import type { StreamEvent } from '@/lib/api';
import { Avatar } from '@/components/ui/Avatar';
import { Spinner } from '@/components/ui/Spinner';
import { MessageSquare } from 'lucide-react';
import type { Message, ToolUse, SessionInfo, MemoryFact } from './types';
import { MessageBubble, ToolCallCard } from './MessageBubble';
import { MemorySidebar } from './MemorySidebar';
import { ChatInput, quickPrompts } from './ChatInput';

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

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-[calc(100vh-var(--topbar-height))]">
        <Spinner size="lg" />
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}

function ChatContent() {
  const searchParams = useSearchParams();
  const sidFromUrl = searchParams.get('sid');
  const [sessionId, setSessionId] = useState<string>(sidFromUrl || '');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [activeToolCalls, setActiveToolCalls] = useState<ToolUse[]>([]);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [maxTurns, setMaxTurns] = useState(8);
  const [usage, setUsage] = useState({ input_tokens: 0, output_tokens: 0 });
  const usageRef = useRef({ input_tokens: 0, output_tokens: 0 });
  const [showMemory, setShowMemory] = useState(false);
  const [memoryFacts, setMemoryFacts] = useState<MemoryFact[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingContentRef = useRef('');
  const activeToolCallsRef = useRef<ToolUse[]>([]);

  useEffect(() => {
    if (sidFromUrl) {
      restoreSession(sidFromUrl);
    } else {
      initSession();
    }
  }, []);

  useEffect(() => {
    if (showMemory) {
      apiClient.get<{ data: MemoryFact[] }>('/memory/facts?per_page=20')
        .then((res) => setMemoryFacts(res.data || []))
        .catch(() => {});
    }
  }, [showMemory]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingContent]);

  const initSession = useCallback(async () => {
    try {
      let agentId = localStorage.getItem('och_default_agent');

      if (!agentId || agentId === 'null' || agentId === 'undefined') {
        const agentRes = await apiClient.post<{ agent: { id: string } }>('/agents/quick-create', {
          name: `ChatBot-${Date.now()}`,
          model: 'claude-sonnet-4-20250514',
        });
        agentId = agentRes.agent.id;
        if (agentId) {
          localStorage.setItem('och_default_agent', agentId);
        }
      }

      if (!agentId) {
        console.error('Failed to get or create agent');
        return;
      }

      const res = await apiClient.post<{ session: SessionInfo }>('/sessions', {
        agent_id: agentId,
        title: 'New Chat',
      });
      setSessionId(res.session.id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  }, []);

  const restoreSession = async (sid: string) => {
    try {
      const sessionRes = await apiClient.get<{ id: string; title: string; status: string }>(`/sessions/${sid}`);
      setSessionId(sessionRes.id);
      const msgsRes = await apiClient.get<{ data: Message[]; total: number }>(`/sessions/${sid}/messages`);
      setMessages(msgsRes.data || []);
    } catch (error) {
      console.error('Failed to restore session, creating new one:', error);
      initSession();
    }
  };

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading || !sessionId) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);
    setStreamingContent('');
    setActiveToolCalls([]);
    streamingContentRef.current = '';
    activeToolCallsRef.current = [];

    setMessages(prev => [...prev, { id: `msg-${Date.now()}`, role: 'user', content: userMessage, created_at: new Date().toISOString() }]);

    try {
      await apiClient.streamChat(
        sessionId,
        userMessage,
        (event: StreamEvent) => {
          switch (event.type) {
            case 'message_saved':
              break;
            case 'thinking':
              setCurrentTurn((event.turn as number) ?? currentTurn + 1);
              setMaxTurns((event.max_turns as number) ?? 8);
              break;
            case 'text_delta':
              setStreamingContent((prev) => {
                const next = prev + (event.content as string);
                streamingContentRef.current = next;
                return next;
              });
              break;
            case 'tool_start':
              setActiveToolCalls((prev) => {
                const toolCall: ToolUse = {
                  name: event.tool_name as string,
                  input: event.input as Record<string, unknown>,
                };
                const next = [...prev, toolCall];
                activeToolCallsRef.current = next;
                return next;
              });
              break;
            case 'tool_end':
              setActiveToolCalls((prev) => {
                const toolName = event.tool_name as string;
                let updated = false;
                const next = prev.map((tc) => {
                  if (!updated && tc.name === toolName && tc.output === undefined) {
                    updated = true;
                    return { ...tc, output: event.output as string, duration_ms: event.duration_ms as number, is_error: event.is_error as boolean, permission_decision: event.permission_decision as string };
                  }
                  return tc;
                });
                activeToolCallsRef.current = next;
                return next;
              });
              break;
            case 'turn_complete':
              setStreamingContent((prev) => prev);
              setUsage(() => {
                const u = (event.usage as typeof usage) || usageRef.current;
                usageRef.current = u;
                return u;
              });
              setIsLoading(false);
              break;
            case 'error':
              setStreamingContent((prev) => {
                const next = prev + `\n\nError: ${event.error}`;
                streamingContentRef.current = next;
                return next;
              });
              setIsLoading(false);
              break;
          }
        },
        { maxTurns: 8 }
      );

      if (streamingContentRef.current) {
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-${Date.now()}-resp`,
            role: 'assistant',
            content: streamingContentRef.current,
            tool_uses: activeToolCallsRef.current.length > 0 ? activeToolCallsRef.current : undefined,
            tokens_input: usageRef.current.input_tokens,
            tokens_output: usageRef.current.output_tokens,
            created_at: new Date().toISOString(),
          },
        ]);
      }

      setStreamingContent('');
      setActiveToolCalls([]);
      streamingContentRef.current = '';
      activeToolCallsRef.current = [];
    } catch (error) {
      console.error('Chat error:', error);
      setIsLoading(false);
    }
  }, [isLoading, sessionId, input, currentTurn]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-var(--topbar-height))] -m-6">
      <div className="flex-1 flex overflow-hidden">
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto py-6 px-4 space-y-6">
            {messages.length === 0 && !streamingContent && (
              <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
                <div className="w-16 h-16 mb-6 rounded-2xl bg-primary-muted flex items-center justify-center border border-border">
                  <MessageSquare className="w-8 h-8 text-primary" />
                </div>
                <h2 className="text-xl font-semibold text-text-primary mb-2">开始新的对话</h2>
                <p className="text-text-tertiary text-sm max-w-md mb-8">
                  与 OpenClaw-Harness Agent 对话。支持工具调用、代码执行、文件操作等 43+ 种能力。
                </p>
                <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
                  {quickPrompts.map((item) => (
                    <button
                      key={item.label}
                      onClick={() => setInput(item.prompt)}
                      className="p-3 rounded-xl border border-border hover:border-border-hover hover:bg-surface-raised transition-all text-left group"
                    >
                      <span className="text-text-tertiary group-hover:text-primary mb-1 block transition-colors">{item.icon}</span>
                      <span className="text-xs text-text-tertiary group-hover:text-text-secondary transition-colors">{item.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <MessageBubble key={msg.id || idx} message={msg} />
            ))}

            {streamingContent && (
              <div className="flex gap-4">
                <Avatar name="AI" size="sm" />
                <div className="flex-1 min-w-0">
                  <div className="prose prose-invert max-w-none">
                    <MarkdownRenderer content={streamingContent} isStreaming />
                  </div>
                  {activeToolCalls.map((tc, idx) => (
                    <ToolCallCard key={idx} toolUse={tc} isActive />
                  ))}
                </div>
              </div>
            )}

            {isLoading && !streamingContent && (
              <div className="flex gap-4 items-start">
                <Avatar name="AI" size="sm" />
                <div className="flex items-center gap-2 pt-1">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:0ms]" />
                    <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:300ms]" />
                  </div>
                  <span className="text-xs text-text-tertiary">思考中...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </main>

        {showMemory && <MemorySidebar facts={memoryFacts} />}
      </div>

      <ChatInput
        input={input}
        setInput={setInput}
        isLoading={isLoading}
        sessionId={sessionId}
        showMemory={showMemory}
        currentTurn={currentTurn}
        maxTurns={maxTurns}
        usage={usage}
        onSend={sendMessage}
        onKeyDown={handleKeyDown}
        onToggleMemory={() => setShowMemory(!showMemory)}
      />
    </div>
  );
}
