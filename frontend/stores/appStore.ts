import { create } from 'zustand';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

interface AppState {
  user: User | null;
  setUser: (user: User | null) => void;

  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;

  commandPaletteOpen: boolean;
  toggleCommandPalette: () => void;
  setCommandPaletteOpen: (open: boolean) => void;

  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  addToast: (type: Notification['type'], message: string, duration?: number) => void;
}

let notificationId = 0;

export const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),

  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  theme: 'dark',
  setTheme: (theme) => set({ theme }),

  commandPaletteOpen: false,
  toggleCommandPalette: () =>
    set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),

  isLoading: false,
  setIsLoading: (isLoading) => set({ isLoading }),

  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notification, id: `notif-${++notificationId}` },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  addToast: (type, message, duration) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        {
          id: `notif-${++notificationId}`,
          type,
          title: message,
          message,
          duration: duration ?? 4000,
        },
      ],
    })),
}));
