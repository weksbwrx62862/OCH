import '@testing-library/jest-dom';
import { useAppStore } from '@/stores/appStore';

describe('AppStore 状态管理', () => {
  beforeEach(() => {
    useAppStore.setState({
      user: null,
      sidebarOpen: true,
      theme: 'dark',
      commandPaletteOpen: false,
      isLoading: false,
      notifications: [],
    });
  });

  describe('初始状态', () => {
    it('应有正确的初始状态', () => {
      const state = useAppStore.getState();

      expect(state.user).toBeNull();
      expect(state.sidebarOpen).toBe(true);
      expect(state.theme).toBe('dark');
      expect(state.commandPaletteOpen).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.notifications).toEqual([]);
    });
  });

  describe('用户状态管理', () => {
    it('setUser 应更新用户信息', () => {
      const mockUser = { id: '1', email: 'test@example.com', name: 'Test User', role: 'admin' };
      useAppStore.getState().setUser(mockUser);
      expect(useAppStore.getState().user).toEqual(mockUser);
    });

    it('setUser 应支持清除用户信息', () => {
      useAppStore.getState().setUser({ id: '1', email: 'test@example.com', name: 'Test User', role: 'admin' });
      useAppStore.getState().setUser(null);
      expect(useAppStore.getState().user).toBeNull();
    });
  });

  describe('UI 状态管理', () => {
    it('toggleSidebar 应切换侧边栏状态', () => {
      const initialState = useAppStore.getState().sidebarOpen;
      useAppStore.getState().toggleSidebar();
      expect(useAppStore.getState().sidebarOpen).toBe(!initialState);
      useAppStore.getState().toggleSidebar();
      expect(useAppStore.getState().sidebarOpen).toBe(initialState);
    });

    it('setTheme 应更新主题', () => {
      useAppStore.getState().setTheme('light');
      expect(useAppStore.getState().theme).toBe('light');
      useAppStore.getState().setTheme('dark');
      expect(useAppStore.getState().theme).toBe('dark');
    });

    it('toggleCommandPalette 应切换命令面板状态', () => {
      const initial = useAppStore.getState().commandPaletteOpen;
      useAppStore.getState().toggleCommandPalette();
      expect(useAppStore.getState().commandPaletteOpen).toBe(!initial);
    });

    it('setCommandPaletteOpen 应更新命令面板状态', () => {
      useAppStore.getState().setCommandPaletteOpen(true);
      expect(useAppStore.getState().commandPaletteOpen).toBe(true);
      useAppStore.getState().setCommandPaletteOpen(false);
      expect(useAppStore.getState().commandPaletteOpen).toBe(false);
    });
  });

  describe('加载状态管理', () => {
    it('setIsLoading 应更新加载状态', () => {
      useAppStore.getState().setIsLoading(true);
      expect(useAppStore.getState().isLoading).toBe(true);
      useAppStore.getState().setIsLoading(false);
      expect(useAppStore.getState().isLoading).toBe(false);
    });
  });

  describe('通知管理', () => {
    it('addNotification 应添加新通知', () => {
      useAppStore.getState().addNotification({ type: 'success', title: '操作成功', message: '数据已保存' });
      const state = useAppStore.getState();
      expect(state.notifications).toHaveLength(1);
      expect(state.notifications[0]).toMatchObject({ type: 'success', title: '操作成功', message: '数据已保存' });
      expect(state.notifications[0].id).toBeDefined();
    });

    it('addNotification 应为每个通知生成唯一 ID', () => {
      useAppStore.getState().addNotification({ type: 'info', title: '通知 1' });
      useAppStore.getState().addNotification({ type: 'info', title: '通知 2' });
      const state = useAppStore.getState();
      expect(state.notifications).toHaveLength(2);
      expect(state.notifications[0].id).not.toBe(state.notifications[1].id);
    });

    it('removeNotification 应删除指定通知', () => {
      useAppStore.getState().addNotification({ type: 'error', title: '错误' });
      const notificationId = useAppStore.getState().notifications[0].id;
      useAppStore.getState().removeNotification(notificationId);
      expect(useAppStore.getState().notifications).toHaveLength(0);
    });

    it('removeNotification 对不存在的 ID 不应报错', () => {
      useAppStore.getState().addNotification({ type: 'warning', title: '警告' });
      useAppStore.getState().removeNotification('non-existent-id');
      expect(useAppStore.getState().notifications).toHaveLength(1);
    });

    it('addToast 应添加通知', () => {
      useAppStore.getState().addToast('info', '测试消息');
      const state = useAppStore.getState();
      expect(state.notifications).toHaveLength(1);
      expect(state.notifications[0].type).toBe('info');
      expect(state.notifications[0].title).toBe('测试消息');
    });
  });
});
