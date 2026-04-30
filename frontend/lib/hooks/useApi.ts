'use client';

import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  refetch: () => Promise<void>;
}

export function useApi<T>(
  url: string | null,
  options?: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: unknown;
    skip?: boolean;
  }
): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const optionsKey = JSON.stringify(options);

  const fetchData = useCallback(async () => {
    if (!url || options?.skip) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const method = options?.method || 'GET';
      let data: T;

      switch (method) {
        case 'POST':
          data = await apiClient.post<T>(url, options?.body);
          break;
        case 'PUT':
          data = await apiClient.put<T>(url, options?.body);
          break;
        case 'DELETE':
          data = await apiClient.delete<T>(url);
          break;
        default:
          data = await apiClient.get<T>(url);
      }

      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error.message : '请求失败',
      });
    }
  }, [url, optionsKey]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}
