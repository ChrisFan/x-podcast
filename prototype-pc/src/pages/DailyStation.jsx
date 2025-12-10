import React, { useState } from 'react';
import { Clock, Play, Tag, ChevronRight, Calendar, Headphones } from 'lucide-react';
import { SpecCard, TagBadge, MachinedButton } from '../components/DesignSystem';
import { useNavigate } from 'react-router-dom';

// Mock data
const mockEpisodes = [
  {
    id: '1',
    title: '你的今日知识电台 · 2025-01-09',
    date: '2025-01-09',
    duration: 1080, // 18 minutes in seconds
    mode: '通勤模式',
    tags: ['AI', '职场', '管理'],
    description: '今日重点：AI 代理在工作流中的应用、团队管理新思路、消费科技趋势观察',
    topics: [
      { title: 'AI 代理的实践应用', time: '3:20' },
      { title: '管理者的时间分配', time: '6:45' },
      { title: '消费电子新趋势', time: '12:10' },
    ],
    sourceCount: 5,
  },
  {
    id: '2',
    title: '你的今日知识电台 · 2025-01-08',
    date: '2025-01-08',
    duration: 1200,
    mode: '通勤模式',
    tags: ['科技', '商业', '理财'],
    description: '聚焦：大模型成本优化、企业数字化转型、个人投资策略',
    topics: [
      { title: '大模型推理成本分析', time: '2:15' },
      { title: '数字化转型案例', time: '8:30' },
      { title: '资产配置思考', time: '15:00' },
    ],
    sourceCount: 7,
  },
  {
    id: '3',
    title: '睡前电台 · 2025-01-08',
    date: '2025-01-08',
    duration: 1800,
    mode: '睡前模式',
    tags: ['思考', '成长', '哲学'],
    description: '慢节奏的思考时光：关于专注力、长期主义与内心平静',
    topics: [
      { title: '专注力的本质', time: '5:00' },
      { title: '长期主义的实践', time: '12:30' },
      { title: '内心的平静', time: '22:00' },
    ],
    sourceCount: 3,
  },
];

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  return `${mins} 分钟`;
};

export default function DailyStation({ onPlayEpisode, currentEpisode }) {
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState('today');

  const todayEpisodes = mockEpisodes.filter(ep => ep.date === '2025-01-09');
  const historyEpisodes = mockEpisodes.filter(ep => ep.date !== '2025-01-09');

  const handlePlay = (episode) => {
    onPlayEpisode({
      ...episode,
      currentTime: 0,
      duration: episode.duration,
    });
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl md:text-4xl font-light text-[#1A1A1A] tracking-tight mb-2">
              每日个人电台
            </h1>
            <p className="text-sm text-[#707070] max-w-2xl">
              基于你的收藏和阅读，AI 为你生成的专属播客节目
            </p>
          </div>
        </div>
      </section>

      {/* Today's Episodes */}
      {todayEpisodes.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-[#D4D4D0] pb-2">
            <Calendar size={16} className="text-[#EA580C]" />
            <h2 className="text-lg font-bold uppercase tracking-widest text-[#1A1A1A] font-mono">
              今日推荐
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {todayEpisodes.map(episode => (
              <EpisodeCard
                key={episode.id}
                episode={episode}
                onPlay={handlePlay}
                isPlaying={currentEpisode?.id === episode.id}
              />
            ))}
          </div>
        </section>
      )}

      {/* History Episodes */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 border-b border-[#D4D4D0] pb-2">
          <Clock size={16} className="text-[#707070]" />
          <h2 className="text-lg font-bold uppercase tracking-widest text-[#1A1A1A] font-mono">
            历史归档
          </h2>
        </div>
        <div className="space-y-4">
          {historyEpisodes.map(episode => (
            <EpisodeCard
              key={episode.id}
              episode={episode}
              onPlay={handlePlay}
              isPlaying={currentEpisode?.id === episode.id}
              variant="horizontal"
            />
          ))}
        </div>
      </section>

      {/* Empty State */}
      {mockEpisodes.length === 0 && (
        <SpecCard title="暂无节目" subtitle="等待内容生成中...">
          <div className="text-center py-12">
            <Headphones size={48} className="mx-auto text-[#D4D4D0] mb-4" />
            <p className="text-sm text-[#707070] mb-6">
              还没有生成任何节目。添加一些内容到素材箱，系统将自动为你生成播客。
            </p>
            <MachinedButton variant="primary" onClick={() => navigate('/inbox')}>
              前往素材箱
            </MachinedButton>
          </div>
        </SpecCard>
      )}
    </div>
  );
}

function EpisodeCard({ episode, onPlay, isPlaying, variant = 'vertical' }) {
  const navigate = useNavigate();

  if (variant === 'horizontal') {
    return (
      <SpecCard title={episode.title} subtitle={`${episode.mode} · ${formatTime(episode.duration)}`}>
        <div className="space-y-4">
          <p className="text-sm text-[#555] leading-relaxed">{episode.description}</p>
          
          <div className="flex flex-wrap gap-2">
            {episode.tags.map(tag => (
              <TagBadge key={tag}>{tag}</TagBadge>
            ))}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#F0F0EB]">
            <div className="flex items-center gap-4 text-[10px] font-mono text-[#707070]">
              <span className="flex items-center gap-1">
                <Tag size={12} />
                {episode.sourceCount} 个来源
              </span>
              <span className="flex items-center gap-1">
                <Clock size={12} />
                {formatTime(episode.duration)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <MachinedButton
                variant={isPlaying ? 'secondary' : 'primary'}
                icon={isPlaying ? undefined : Play}
                onClick={() => onPlay(episode)}
              >
                {isPlaying ? '播放中' : '播放'}
              </MachinedButton>
              <MachinedButton
                variant="ghost"
                icon={ChevronRight}
                onClick={() => navigate(`/episode/${episode.id}`)}
              >
                详情
              </MachinedButton>
            </div>
          </div>
        </div>
      </SpecCard>
    );
  }

  return (
    <SpecCard title={episode.title} subtitle={`${episode.mode} · ${formatTime(episode.duration)}`}>
      <div className="space-y-4">
        <p className="text-sm text-[#555] leading-relaxed">{episode.description}</p>
        
        <div className="flex flex-wrap gap-2">
          {episode.tags.map(tag => (
            <TagBadge key={tag}>{tag}</TagBadge>
          ))}
        </div>

        {episode.topics && episode.topics.length > 0 && (
          <div className="bg-[#F9F9F7] p-4 border border-[#E5E5E0] rounded-sm">
            <div className="text-[10px] font-mono uppercase tracking-wider text-[#707070] mb-2">
              章节
            </div>
            <div className="space-y-2">
              {episode.topics.map((topic, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-[#1A1A1A]">{topic.title}</span>
                  <span className="font-mono text-[10px] text-[#707070]">{topic.time}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-4 border-t border-[#F0F0EB]">
          <div className="flex items-center gap-4 text-[10px] font-mono text-[#707070]">
            <span className="flex items-center gap-1">
              <Tag size={12} />
              {episode.sourceCount} 个来源
            </span>
          </div>
          <div className="flex items-center gap-2">
            <MachinedButton
              variant={isPlaying ? 'secondary' : 'primary'}
              icon={isPlaying ? undefined : Play}
              onClick={() => onPlay(episode)}
            >
              {isPlaying ? '播放中' : '播放'}
            </MachinedButton>
            <MachinedButton
              variant="ghost"
              icon={ChevronRight}
              onClick={() => navigate(`/episode/${episode.id}`)}
            >
              详情
            </MachinedButton>
          </div>
        </div>
      </div>
    </SpecCard>
  );
}
