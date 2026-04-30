import '@testing-library/jest-dom';
import apiClient from '@/lib/api';

// Mock fetch 全局
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('API 客户端', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    
    // 清除 localStorage
    localStorage.clear();
  });

  describe('GET 请求', () => {
    it('应正确发送 GET 请求并返回数据', async () => {
      const mockData = { id: '1', name: 'Test Agent' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.get('/agents');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/agents'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('应支持查询参数', async () => {
      const mockData = [{ id: '1' }];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      await apiClient.get('/agents', { page: '1', limit: '10' });

      const calledUrl = mockFetch.mock.calls[0][0];
      expect(calledUrl).toContain('page=1');
      expect(calledUrl).toContain('limit=10');
    });
  });

  describe('POST 请求', () => {
    it('应正确发送 POST 请求并返回数据', async () => {
      const mockData = { id: '2', status: 'created' };
      const postData = { name: 'New Agent', type: 'assistant' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.post('/agents', postData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/agents'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('PUT 请求', () => {
    it('应正确发送 PUT 请求并返回数据', async () => {
      const mockData = { id: '1', name: 'Updated Agent' };
      const updateData = { name: 'Updated Agent' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.put('/agents/1', updateData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/agents/1'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('DELETE 请求', () => {
    it('应正确发送 DELETE 请求并返回数据', async () => {
      const mockData = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.delete('/agents/1');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/agents/1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('错误处理', () => {
    it('应处理 401 未授权错误', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Unauthorized', code: 401 }),
      });

      await expect(apiClient.get('/protected')).rejects.toThrow('Unauthorized');
    });

    it('应处理 500 服务器错误', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal Server Error', code: 500 }),
      });

      await expect(apiClient.get('/error')).rejects.toThrow('Internal Server Error');
    });

    it('应处理网络错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.get('/offline')).rejects.toThrow('Network error');
    });

    it('应处理无法解析的错误响应', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => { throw new Error('Invalid JSON'); },
      });

      await expect(apiClient.get('/bad-response')).rejects.toThrow();
    });
  });

  describe('认证头处理', () => {
    it('应在有 token 时添加 Authorization 头', async () => {
      localStorage.setItem('och_token', 'test-token-123');
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.get('/secure');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token-123',
          }),
        })
      );
    });

    it('应在无 token 时不添加 Authorization 头', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.get('/public');

      const headers = mockFetch.mock.calls[0][1].headers;
      expect(headers.Authorization).toBeUndefined();
    });
  });
});
