import React, { useState } from 'react';
import { Search, Filter, Clock, Tag, Play, BookOpen, Calendar } from 'lucide-react';
import { SpecCard, TagBadge, MachinedButton, InputField, SelectField } from '../components/DesignSystem';

// Mock data
const mockResults = {
  episodes: [
    {
      id: '1',
      title: '你的今日知识电台 · 2025-01-09',
      date: '2025-01-09',
      duration: 1080,
      mode: '通勤模式',
      tags: ['AI', '职场'],
      snippet: '...AI 代理在工作流中的应用、团队管理新思路...',
    },
  ],
  items: [
    {
      id: '1',
      title: 'AI 代理在工作流中的应用实践',
      source: 'TechCrunch',
      type: 'browser',
      date: '2025-01-08',
      tags: ['AI', '工作流'],
      snippet: '探讨如何将 AI 代理集成到日常工作流程中...',
    },
  ],
  topics: [
    {
      id: '1',
      name: 'AI 应用',
      count: 12,
      items: ['AI 代理在工作流中的应用实践', '大模型成本优化'],
    },
  ],
};

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [dateRange, setDateRange] = useState('all');
  const [results, setResults] = useState(null);

  const handleSearch = () => {
    if (!query.trim()) return;
    // Simulate search
    setResults(mockResults);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl md:text-4xl font-light text-[#1A1A1A] tracking-tight mb-2">
          搜索
        </h1>
        <p className="text-sm text-[#707070]">
          搜索你的节目和收藏内容
        </p>
      </div>

      {/* Search Bar */}
      <SpecCard title="搜索" subtitle="输入关键词搜索">
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <InputField
                icon={Search}
                placeholder="搜索节目、内容、标签..."
                value={query}
                onChange={setQuery}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <MachinedButton variant="primary" icon={Search} onClick={handleSearch}>
              搜索
            </MachinedButton>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <SelectField
              label="类型"
              value={filter}
              onChange={setFilter}
              options={[
                { value: 'all', label: '全部' },
                { value: 'episodes', label: '节目' },
                { value: 'items', label: '内容' },
                { value: 'topics', label: '主题' },
              ]}
            />
            <SelectField
              label="时间范围"
              value={dateRange}
              onChange={setDateRange}
              options={[
                { value: 'all', label: '全部时间' },
                { value: 'week', label: '最近一周' },
                { value: 'month', label: '最近一月' },
                { value: 'year', label: '最近一年' },
              ]}
            />
          </div>
        </div>
      </SpecCard>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Episodes */}
          {results.episodes.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-widest text-[#1A1A1A] font-mono mb-4">
                节目 ({results.episodes.length})
              </h2>
              <div className="space-y-4">
                {results.episodes.map(episode => (
                  <SpecCard key={episode.id} title={episode.title} subtitle={`${episode.mode} · ${episode.date}`}>
                    <div className="space-y-4">
                      <p className="text-sm text-[#555]">{episode.snippet}</p>
                      <div className="flex flex-wrap gap-2">
                        {episode.tags.map(tag => (
                          <TagBadge key={tag}>{tag}</TagBadge>
                        ))}
                      </div>
                      <div className="flex items-center gap-2 pt-4 border-t border-[#F0F0EB]">
                        <MachinedButton variant="primary" icon={Play}>
                          播放
                        </MachinedButton>
                        <MachinedButton variant="ghost" icon={BookOpen}>
                          查看详情
                        </MachinedButton>
                      </div>
                    </div>
                  </SpecCard>
                ))}
              </div>
            </section>
          )}

          {/* Items */}
          {results.items.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-widest text-[#1A1A1A] font-mono mb-4">
                内容 ({results.items.length})
              </h2>
              <div className="space-y-4">
                {results.items.map(item => (
                  <SpecCard key={item.id} title={item.title} subtitle={`${item.source} · ${item.date}`}>
                    <div className="space-y-4">
                      <p className="text-sm text-[#555]">{item.snippet}</p>
                      <div className="flex flex-wrap gap-2">
                        {item.tags.map(tag => (
                          <TagBadge key={tag}>{tag}</TagBadge>
                        ))}
                      </div>
                      <div className="flex items-center gap-2 pt-4 border-t border-[#F0F0EB]">
                        <MachinedButton variant="ghost" icon={BookOpen}>
                          生成深度研究
                        </MachinedButton>
                      </div>
                    </div>
                  </SpecCard>
                ))}
              </div>
            </section>
          )}

          {/* Topics */}
          {results.topics.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-widest text-[#1A1A1A] font-mono mb-4">
                主题 ({results.topics.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.topics.map(topic => (
                  <SpecCard key={topic.id} title={topic.name} subtitle={`${topic.count} 个相关内容`}>
                    <div className="space-y-3">
                      <div className="text-sm text-[#555]">
                        <div className="text-[10px] font-mono uppercase text-[#707070] mb-2">相关内容</div>
                        <ul className="space-y-1">
                          {topic.items.map((item, idx) => (
                            <li key={idx} className="text-xs">· {item}</li>
                          ))}
                        </ul>
                      </div>
                      <MachinedButton variant="accent" icon={BookOpen}>
                        围绕此主题生成专题
                      </MachinedButton>
                    </div>
                  </SpecCard>
                ))}
              </div>
            </section>
          )}

          {/* No Results */}
          {results.episodes.length === 0 && results.items.length === 0 && results.topics.length === 0 && (
            <SpecCard title="未找到结果">
              <div className="text-center py-12">
                <Search size={48} className="mx-auto text-[#D4D4D0] mb-4" />
                <p className="text-sm text-[#707070]">
                  没有找到匹配的内容，试试其他关键词。
                </p>
              </div>
            </SpecCard>
          )}
        </div>
      )}

      {/* Empty State */}
      {!results && (
        <SpecCard title="开始搜索" subtitle="输入关键词查找你的内容">
          <div className="text-center py-12">
            <Search size={48} className="mx-auto text-[#D4D4D0] mb-4" />
            <p className="text-sm text-[#707070]">
              搜索你听过的节目、收藏的内容，或按主题查找。
            </p>
          </div>
        </SpecCard>
      )}
    </div>
  );
}
