/**
 * 前端共享工具函数
 */

/** 状态颜色映射 */
export const STATUS_COLORS: Record<string, string> = {
  active: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  completed: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
  running: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
  pending: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  failed: 'text-red-400 bg-red-400/10 border-red-400/20',
  error: 'text-red-400 bg-red-400/10 border-red-400/20',
  paused: 'text-orange-400 bg-orange-400/10 border-orange-400/20',
  stopped: 'text-gray-400 bg-gray-400/10 border-gray-400/20',
  disabled: 'text-gray-500 bg-gray-500/10 border-gray-500/20',
  configured: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
  success: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  denied: 'text-red-400 bg-red-400/10 border-red-400/20',
  connected: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
};

export const STATUS_LABELS: Record<string, string> = {
  active: '活跃', completed: '已完成', running: '运行中',
  pending: '等待中', failed: '失败', error: '错误',
  paused: '暂停', stopped: '停止', disabled: '禁用',
  configured: '已配置', success: '成功', denied: '拒绝',
  connected: '已连接',
};

/** 格式化日期 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
  return d.toLocaleDateString('zh-CN');
}

/** 截断文本 */
export function truncate(text: string, maxLen: number = 80): string {
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text;
}

/** 获取首字母头像 */
export function getInitials(name: string): string {
  return name.slice(0, 2).toUpperCase();
}
