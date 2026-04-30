import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import LoginPage from '@/app/login/page';

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    refresh: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/login',
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

describe('登录页面', () => {
  it('应渲染登录表单', () => {
    render(<LoginPage />);
    expect(screen.getByText('登录')).toBeInTheDocument();
  });

  it('应包含用户名输入框', () => {
    render(<LoginPage />);
    expect(screen.getByPlaceholderText('输入用户名')).toBeInTheDocument();
  });

  it('应包含登录按钮', () => {
    render(<LoginPage />);
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  it('应显示系统标题', () => {
    render(<LoginPage />);
    expect(screen.getByText('OpenClaw-Harness')).toBeInTheDocument();
  });

  it('应显示副标题', () => {
    render(<LoginPage />);
    expect(screen.getByText('多智能体协作平台')).toBeInTheDocument();
  });

  it('应显示开发环境提示', () => {
    render(<LoginPage />);
    expect(screen.getByText(/开发环境/)).toBeInTheDocument();
  });
});
