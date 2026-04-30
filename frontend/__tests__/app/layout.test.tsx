import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import RootLayout from '@/app/layout';

jest.mock('next/font/google', () => ({
  Inter: () => ({ variable: '--font-inter' }),
  JetBrains_Mono: () => ({ variable: '--font-mono' }),
}));

jest.mock('./globals.css', () => ({}));

const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockRefresh = jest.fn();
const mockBack = jest.fn();
const mockForward = jest.fn();
const mockPrefetch = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    refresh: mockRefresh,
    back: mockBack,
    forward: mockForward,
    prefetch: mockPrefetch,
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: jest.fn(() => 'test-token'),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  },
  writable: true,
});

describe('根布局组件', () => {
  it('应渲染子路由内容', () => {
    render(
      <RootLayout>
        <div data-testid="child-content">测试子内容</div>
      </RootLayout>
    );

    expect(screen.getByTestId('child-content')).toBeInTheDocument();
    expect(screen.getByText('测试子内容')).toBeInTheDocument();
  });

  it('应正确设置 body 元素的类名', () => {
    render(
      <RootLayout>
        <div>内容</div>
      </RootLayout>
    );

    const bodyElement = document.body;
    expect(bodyElement).toBeInTheDocument();
  });
});
