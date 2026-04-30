import '@testing-library/jest-dom';
import { renderHook, act } from '@testing-library/react';
import { useApi } from '@/lib/hooks/useApi';

// Mock API client
jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

describe('useApi 自定义 Hook', () => {
  const apiClient = require('@/lib/api').default;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('数据获取逻辑', () => {
    it('应在挂载时自动发起 GET 请求', async () => {
      const mockData = [{ id: '1', name: 'Agent 1' }];
      apiClient.get.mockResolvedValueOnce(mockData);

      const { result } = renderHook(() => useApi('/agents'));

      // 初始状态应该是 loading
      expect(result.current.loading).toBe(true);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeNull();

      // 等待异步操作完成
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      // 验证最终状态
      expect(result.current.data).toEqual(mockData);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(apiClient.get).toHaveBeenCalledWith('/agents');
    });

    it('当 url 为 null 时不应发起请求', () => {
      const { result } = renderHook(() => useApi<string | null>(null));

      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('应支持 POST 方法', async () => {
      const mockData = { id: '2', status: 'created' };
      const postData = { name: 'New Agent' };
      apiClient.post.mockResolvedValueOnce(mockData);

      const { result } = renderHook(() =>
        useApi('/agents', { method: 'POST', body: postData })
      );

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      expect(result.current.data).toEqual(mockData);
      expect(apiClient.post).toHaveBeenCalledWith('/agents', postData);
    });
  });

  describe('错误处理', () => {
    it('应处理 API 错误并设置错误消息', async () => {
      const errorMessage = 'Network Error';
      apiClient.get.mockRejectedValueOnce(new Error(errorMessage));

      const { result } = renderHook(() => useApi('/error-endpoint'));

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  describe('refetch 功能', () => {
    it('refetch 应重新发起请求', async () => {
      const mockData1 = [{ id: '1' }];
      const mockData2 = [{ id: '2' }];
      
      apiClient.get
        .mockResolvedValueOnce(mockData1)
        .mockResolvedValueOnce(mockData2);

      const { result } = renderHook(() => useApi('/agents'));

      // 第一次请求完成
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      expect(result.current.data).toEqual(mockData1);
      expect(apiClient.get).toHaveBeenCalledTimes(1);

      // 手动触发 refetch
      await act(async () => {
        await result.current.refetch();
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      expect(result.current.data).toEqual(mockData2);
      expect(apiClient.get).toHaveBeenCalledTimes(2);
    });
  });

  describe('skip 选项', () => {
    it('skip 为 true 时不应发起请求', () => {
      const { result } = renderHook(() =>
        useApi('/agents', { skip: true })
      );

      expect(result.current.loading).toBe(false);
      expect(apiClient.get).not.toHaveBeenCalled();
    });
  });
});
