/**
 * OpenClaw-Harness API Client
 *
 * 统一的 API 请求封装，支持 REST 和 SSE 流式请求
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
  timeout?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('och_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  private async request<T>(url: string, options: RequestOptions = {}): Promise<T> {
    const { params, timeout = 30000, ...fetchOptions } = options;

    let fullUrl = `${this.baseUrl}${url}`;
    if (params) {
      const searchParams = new URLSearchParams(params);
      fullUrl += `?${searchParams.toString()}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(fullUrl, {
        ...fetchOptions,
        headers: {
          ...this.getHeaders(),
          ...fetchOptions.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          error: `HTTP Error: ${response.status}`,
          code: response.status,
        }));
        throw new Error(error.error || error.message || 'Request failed');
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  // HTTP Methods
  async get<T>(url: string, params?: Record<string, string>): Promise<T> {
    return this.request<T>(url, { method: 'GET', params });
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>(url, { method: 'DELETE' });
  }

  // SSE Streaming for Chat
  async streamChat(
    sessionId: string,
    message: string,
    onEvent: (event: StreamEvent) => void,
    options?: StreamOptions,
  ): Promise<void> {
    const body = {
      message,
      stream: true,
      maxTurns: options?.maxTurns,
      tools: options?.tools,
    };

    // 使用 Next.js 代理（与 apiClient.post/get 保持一致）
    // 避免直连后端导致的 CORS 和协议混用问题
    const url = `/api/proxy/chat?sessionId=${encodeURIComponent(sessionId)}`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(body),
      });
    } catch (fetchError) {
      console.error('[streamChat] Fetch failed:', fetchError);
      throw new Error(`Network error: ${fetchError instanceof Error ? fetchError.message : 'Unknown error'}`);
    }

    if (!response.ok || !response.body) {
      const errorText = await response.text().catch(() => 'No error body');
      console.error('[streamChat] Stream failed:', response.status, errorText);
      throw new Error(`Stream failed: ${response.status} - ${errorText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') {
              onEvent({ type: 'turn_complete', stop_reason: 'end_turn', usage: { input_tokens: 0, output_tokens: 0, total_tokens: 0 } } as StreamEvent);
              return;
            }

            try {
              const event = JSON.parse(data) as StreamEvent;
              onEvent(event);
            } catch (e) {
              console.warn('[streamChat] SSE parse error:', e, 'data:', data);
            }
          }
        }
      }
    } catch (readError) {
      console.error('[streamChat] Read error:', readError);
      throw readError;
    } finally {
      reader.releaseLock();
    }
  }
}

// 类型定义
export interface StreamEvent {
  type:
    | 'message_saved'
    | 'thinking'
    | 'text_delta'
    | 'tool_start'
    | 'tool_end'
    | 'turn_complete'
    | 'error';
  [key: string]: unknown;
}

export interface StreamOptions {
  maxTurns?: number;
  tools?: string[];
}

// Singleton export
export const apiClient = new ApiClient();

// Convenience exports
export default apiClient;
