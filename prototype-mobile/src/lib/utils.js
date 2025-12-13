import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Mock Data Shared
export const MOCK_EPISODES = [
  {
    id: '1',
    title: '早安·通勤电台',
    subtitle: 'AI 代理与高效能管理',
    date: '2025-01-09',
    duration: 1080,
    mode: 'commute',
    tags: ['AI', '职场', '管理'],
    description: '今日重点：AI 代理在工作流中的应用、团队管理新思路、消费科技趋势观察',
    coverGradient: 'from-orange-400 to-red-500',
    topics: [
      { title: 'AI 代理的实践应用', time: '03:20' },
      { title: '管理者的时间分配', time: '06:45' },
      { title: '消费电子新趋势', time: '12:10' },
    ],
  },
  {
    id: '2',
    title: '晚间·静心时刻',
    subtitle: '专注力与长期主义',
    date: '2025-01-08',
    duration: 1800,
    mode: 'sleep',
    tags: ['思考', '哲学'],
    description: '慢节奏的思考时光：关于专注力、长期主义与内心平静',
    coverGradient: 'from-indigo-400 to-purple-600',
    topics: [
      { title: '专注力的本质', time: '05:00' },
      { title: '长期主义的实践', time: '12:30' },
    ],
  }
];


