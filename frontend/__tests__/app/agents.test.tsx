import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import AgentsPage from '@/app/agents/page';

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    refresh: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/agents',
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

jest.mock('@/lib/hooks/useApi', () => ({
  useApi: jest.fn(),
}));

const mockAgents = {
  data: [
    { id: '1', name: 'Code Assistant', description: '代码助手', model: 'claude-sonnet-4-20250514', is_active: true, created_at: '2025-01-01' },
    { id: '2', name: 'Debug Helper', description: '调试助手', model: 'claude-sonnet-4-20250514', is_active: false, created_at: '2025-01-02' },
  ],
  total: 2,
};

describe('Agents 页面', () => {
  beforeEach(() => {
    const { useApi } = require('@/lib/hooks/useApi');
    useApi.mockReturnValue({
      data: mockAgents,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });
  });

  it('应渲染页面标题', () => {
    render(<AgentsPage />);
    expect(screen.getByText('智能体管理')).toBeInTheDocument();
  });

  it('应显示 Agent 列表', () => {
    render(<AgentsPage />);
    expect(screen.getByText('Code Assistant')).toBeInTheDocument();
    expect(screen.getByText('Debug Helper')).toBeInTheDocument();
  });

  it('应显示创建按钮', () => {
    render(<AgentsPage />);
    expect(screen.getByText(/创建智能体/)).toBeInTheDocument();
  });

  it('应显示 Agent 描述', () => {
    render(<AgentsPage />);
    expect(screen.getByText('代码助手')).toBeInTheDocument();
    expect(screen.getByText('调试助手')).toBeInTheDocument();
  });

  it('应显示活跃状态标签', () => {
    render(<AgentsPage />);
    expect(screen.getByText('活跃')).toBeInTheDocument();
  });

  it('应显示停用状态标签', () => {
    render(<AgentsPage />);
    expect(screen.getByText('停用')).toBeInTheDocument();
  });

  it('应显示加载骨架屏', () => {
    const { useApi } = require('@/lib/hooks/useApi');
    useApi.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
    });

    const { container } = render(<AgentsPage />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });
});
