import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HomePage from '@/app/page';

// Mock next/link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    const testId = href === '/' ? 'link-home' : `link-${href.replace(/^\//, '')}`;
    return (
      <a href={href} data-testid={testId}>
        {children}
      </a>
    );
  };
});

// Mock next/font/google
jest.mock('next/font/google', () => ({
  Inter: () => ({ variable: '--font-inter' }),
  JetBrains_Mono: () => ({ variable: '--font-mono' }),
}));

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

describe('首页导航组件', () => {
  // 模拟 API 返回数据
  const mockSessionsResponse = {
    data: [
      { id: '1', status: 'active' },
      { id: '2', status: 'inactive' },
    ],
    total: 2,
  };

  const mockAgentsResponse = {
    data: [{ id: '1' }, { id: '2' }, { id: '3' }],
    total: 3,
  };

  const mockAuditResponse = {
    data: [],
    total: 0,
  };

  beforeEach(() => {
    const apiClient = require('@/lib/api').default;
    
    // 设置默认的 mock 返回值
    apiClient.get.mockImplementation((url: string) => {
      if (url.includes('/sessions')) return Promise.resolve(mockSessionsResponse);
      if (url.includes('/agents')) return Promise.resolve(mockAgentsResponse);
      if (url.includes('/audit')) return Promise.resolve(mockAuditResponse);
      return Promise.resolve({ data: [], total: 0 });
    });
  });

  it('应渲染所有导航链接', async () => {
    render(<HomePage />);

    // 等待数据加载完成
    const dashboardLinks = await screen.findAllByTestId('link-home');
    expect(dashboardLinks.length).toBeGreaterThan(0);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();

    // 验证所有主要导航链接存在
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Agents')).toBeInTheDocument();
    expect(screen.getByText('Sessions')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Tools')).toBeInTheDocument();
    expect(screen.getByText('Skills')).toBeInTheDocument();
    expect(screen.getByText('Swarm')).toBeInTheDocument();
    expect(screen.getByText('Audit')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('应高亮当前活动页面（Dashboard）', async () => {
    render(<HomePage />);

    // Dashboard 应该有活跃样式（通过文本内容验证）
    const dashboardLink = await screen.findByText('Dashboard');
    expect(dashboardLink).toBeInTheDocument();
  });

  it('应显示网站标题和 Logo', async () => {
    render(<HomePage />);

    // 验证网站标题
    expect(screen.getByText('OpenClaw-Harness')).toBeInTheDocument();

    // 验证 Logo 文字
    expect(screen.getByText('OCH')).toBeInTheDocument();
  });

  it('应显示统计卡片区域', async () => {
    render(<HomePage />);

    // 等待数据加载完成
    await screen.findByText('活跃会话');
    expect(screen.getByText('智能体总数')).toBeInTheDocument();
    expect(screen.getByText('今日费用')).toBeInTheDocument();
    expect(screen.getByText('Token 用量')).toBeInTheDocument();
  });

  it('应显示快捷操作按钮', async () => {
    render(<HomePage />);

    // 验证快捷操作按钮
    expect(screen.getByText('新建对话')).toBeInTheDocument();
    expect(screen.getByText('管理智能体')).toBeInTheDocument();
    expect(screen.getByText('查看会话')).toBeInTheDocument();
    expect(screen.getByText('任务管理')).toBeInTheDocument();
  });
});
