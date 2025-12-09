import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Play, Clock, Tag, ExternalLink, Heart, Download, Share2, 
  ChevronLeft, BookOpen, List, X
} from 'lucide-react';
import { SpecCard, TagBadge, MachinedButton, TextareaField } from '../components/DesignSystem';

// Mock data
const mockEpisode = {
  id: '1',
  title: '你的今日知识电台 · 2025-01-09',
  date: '2025-01-09',
  duration: 1080,
  mode: '通勤模式',
  tags: ['AI', '职场', '管理'],
  description: '今日重点：AI 代理在工作流中的应用、团队管理新思路、消费科技趋势观察',
  script: `【开场】

早上好，欢迎收听你的个人知识电台。今天是 2025 年 1 月 9 日，星期四。今天为你准备了 18 分钟的内容，涵盖三个主要话题。

【第一部分：AI 代理的实践应用】

首先，我们来聊聊 AI 代理。最近你收藏了几篇关于 AI 在工作流中应用的文章。简单来说，AI 代理就是能够自主执行任务的 AI 系统，它们可以理解你的意图，然后自动完成一系列操作。

比如，你可以让 AI 代理帮你整理邮件、生成报告，甚至管理你的日程。关键是要设计好工作流，让 AI 知道在什么情况下做什么决策。

根据你收藏的内容，目前比较成熟的场景包括：客户服务自动化、内容生成、数据分析等。但要注意，AI 代理不是万能的，它需要清晰的边界和人工监督。

【第二部分：管理者的时间分配】

接下来，我们看看管理者的时间分配问题。你最近关注了一些关于高效管理的文章。

核心观点是：管理者应该把更多时间花在战略思考和团队培养上，而不是陷入日常事务。一个实用的方法是，把任务分为四类：重要且紧急、重要但不紧急、紧急但不重要、既不重要也不紧急。

对于重要但不紧急的事情，要主动安排时间，而不是等到它变成紧急事项。这需要很强的自律和规划能力。

【第三部分：消费电子新趋势】

最后，我们聊聊消费电子的新趋势。从你收藏的内容来看，今年的重点可能在于：更智能的交互方式、更长的电池续航，以及更个性化的体验。

特别是可穿戴设备，它们正在从简单的健康监测，进化到更全面的生活助手。比如，可以实时监测你的压力水平，并给出建议。

【收尾】

好了，今天的节目就到这里。希望这些内容对你有帮助。明天同一时间，我们继续。

如果你对某个话题特别感兴趣，可以在 App 中点击"生成深度研究"，我会为你准备一个更详细的专题节目。`,
  sources: [
    {
      id: '1',
      title: 'AI 代理在工作流中的应用实践',
      source: 'TechCrunch',
      url: 'https://example.com/1',
      date: '2025-01-08',
    },
    {
      id: '2',
      title: '高效管理者的时间分配法则',
      source: 'Harvard Business Review',
      url: 'https://example.com/2',
      date: '2025-01-07',
    },
    {
      id: '3',
      title: '2025 消费电子趋势报告',
      source: 'The Verge',
      url: 'https://example.com/3',
      date: '2025-01-06',
    },
  ],
  chapters: [
    { title: '开场', time: '0:00' },
    { title: 'AI 代理的实践应用', time: '0:30' },
    { title: '管理者的时间分配', time: '6:45' },
    { title: '消费电子新趋势', time: '12:10' },
    { title: '收尾', time: '17:30' },
  ],
};

export default function EpisodeDetail({ onPlayEpisode, currentEpisode }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [showFullScript, setShowFullScript] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);
  const [feedback, setFeedback] = useState('');

  const episode = mockEpisode; // In real app, fetch by id

  const handlePlay = () => {
    onPlayEpisode({
      ...episode,
      currentTime: 0,
      duration: episode.duration,
    });
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm font-mono text-[#707070] hover:text-[#1A1A1A] transition-colors"
      >
        <ChevronLeft size={16} />
        返回
      </button>

      {/* Episode Header */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-light text-[#1A1A1A] mb-2">
            {episode.title}
          </h1>
          <div className="flex items-center gap-4 text-sm text-[#707070]">
            <span className="flex items-center gap-1">
              <Clock size={14} />
              {formatTime(episode.duration)}
            </span>
            <span className="font-mono uppercase">{episode.mode}</span>
            <span>{episode.date}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {episode.tags.map(tag => (
            <TagBadge key={tag}>{tag}</TagBadge>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <MachinedButton
            variant={currentEpisode?.id === episode.id ? 'secondary' : 'primary'}
            icon={Play}
            onClick={handlePlay}
          >
            {currentEpisode?.id === episode.id ? '继续播放' : '播放'}
          </MachinedButton>
          <MachinedButton
            variant="ghost"
            icon={isFavorited ? Heart : Heart}
            onClick={() => setIsFavorited(!isFavorited)}
            className={isFavorited ? 'text-[#EA580C]' : ''}
          >
            收藏
          </MachinedButton>
          <MachinedButton variant="ghost" icon={Download}>
            下载
          </MachinedButton>
          <MachinedButton variant="ghost" icon={Share2}>
            分享
          </MachinedButton>
        </div>
      </div>

      {/* Chapters */}
      <SpecCard title="章节" subtitle={`共 ${episode.chapters.length} 个章节`}>
        <div className="space-y-2">
          {episode.chapters.map((chapter, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-[#F9F9F7] border border-[#E5E5E0] hover:border-[#1A1A1A] transition-colors cursor-pointer"
              onClick={() => {
                // Navigate to chapter time
                onPlayEpisode({
                  ...episode,
                  currentTime: parseTime(chapter.time),
                  duration: episode.duration,
                });
              }}
            >
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 bg-[#1A1A1A] text-white flex items-center justify-center text-[10px] font-mono">
                  {idx + 1}
                </div>
                <span className="text-sm text-[#1A1A1A]">{chapter.title}</span>
              </div>
              <span className="text-[10px] font-mono text-[#707070]">{chapter.time}</span>
            </div>
          ))}
        </div>
      </SpecCard>

      {/* Script */}
      <SpecCard title="完整脚本" subtitle="点击展开查看文字版">
        <div className="space-y-4">
          <div className={`text-sm text-[#555] leading-relaxed whitespace-pre-line ${!showFullScript ? 'line-clamp-6' : ''}`}>
            {episode.script}
          </div>
          <button
            onClick={() => setShowFullScript(!showFullScript)}
            className="text-xs font-mono uppercase tracking-wider text-[#707070] hover:text-[#1A1A1A] transition-colors"
          >
            {showFullScript ? '收起' : '展开全文'}
          </button>
        </div>
      </SpecCard>

      {/* Sources */}
      <SpecCard title="内容来源" subtitle={`基于 ${episode.sources.length} 个来源生成`}>
        <div className="space-y-3">
          {episode.sources.map(source => (
            <div
              key={source.id}
              className="flex items-start justify-between p-4 bg-[#F9F9F7] border border-[#E5E5E0] hover:border-[#1A1A1A] transition-colors"
            >
              <div className="flex-1">
                <h4 className="text-sm font-bold text-[#1A1A1A] mb-1">{source.title}</h4>
                <div className="flex items-center gap-3 text-[10px] font-mono text-[#707070]">
                  <span>{source.source}</span>
                  <span>·</span>
                  <span>{source.date}</span>
                </div>
              </div>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-4 p-2 text-[#707070] hover:text-[#1A1A1A] transition-colors"
              >
                <ExternalLink size={16} />
              </a>
            </div>
          ))}
        </div>
      </SpecCard>

      {/* Feedback */}
      <SpecCard title="反馈" subtitle="帮助我们改进内容质量">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono uppercase text-[#707070]">难度评价</span>
            <div className="flex items-center gap-2">
              {['太浅', '刚好', '太深'].map((label, idx) => (
                <button
                  key={idx}
                  onClick={() => setFeedback(label)}
                  className={`px-4 py-2 text-xs font-mono uppercase border transition-colors ${
                    feedback === label
                      ? 'bg-[#1A1A1A] text-white border-[#1A1A1A]'
                      : 'bg-white text-[#707070] border-[#D4D4D0] hover:border-[#1A1A1A]'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </SpecCard>

      {/* Generate Deep Research */}
      <SpecCard title="深度研究" subtitle="围绕本主题生成专题播客">
        <div className="space-y-4">
          <p className="text-sm text-[#555]">
            想要更深入地了解这个话题？点击下方按钮，我们将为你生成一个 15-30 分钟的深度研究播客。
          </p>
          <MachinedButton variant="accent" icon={BookOpen}>
            生成深度研究播客
          </MachinedButton>
        </div>
      </SpecCard>
    </div>
  );
}

function parseTime(timeStr) {
  const [mins, secs] = timeStr.split(':').map(Number);
  return mins * 60 + secs;
}
