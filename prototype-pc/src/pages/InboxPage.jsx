import React, { useState } from 'react';
import { 
  Plus, Link, FileText, Mail, Globe, Filter, Search, 
  Tag, Calendar, Trash2, Play, BookOpen, Clock, X
} from 'lucide-react';
import { SpecCard, TagBadge, MachinedButton, InputField, SelectField } from '../components/DesignSystem';

// Mock data
const mockItems = [
  {
    id: '1',
    title: 'AI 代理在工作流中的应用实践',
    source: 'TechCrunch',
    type: 'browser',
    date: '2025-01-08',
    tags: ['AI', '工作流'],
    summary: '探讨如何将 AI 代理集成到日常工作流程中，提高效率',
    status: 'processed',
    priority: 'normal',
  },
  {
    id: '2',
    title: '高效管理者的时间分配法则',
    source: 'Harvard Business Review',
    type: 'newsletter',
    date: '2025-01-07',
    tags: ['管理', '效率'],
    summary: '分析优秀管理者如何合理分配时间，避免陷入日常事务',
    status: 'processed',
    priority: 'important',
  },
  {
    id: '3',
    title: '2025 消费电子趋势报告',
    source: 'The Verge',
    type: 'browser',
    date: '2025-01-06',
    tags: ['科技', '消费'],
    summary: '全面分析 2025 年消费电子市场的主要趋势和机会',
    status: 'processing',
    priority: 'normal',
  },
  {
    id: '4',
    title: 'Stratechery: The AI Platform Shift',
    source: 'Stratechery',
    type: 'newsletter',
    date: '2025-01-05',
    tags: ['AI', '平台', '战略'],
    summary: 'Ben Thompson 关于 AI 平台转变的深度分析',
    status: 'processed',
    priority: 'normal',
  },
];

const typeLabels = {
  browser: '浏览器',
  newsletter: 'Newsletter',
  manual: '手动添加',
  rss: 'RSS',
  wechat: '微信',
};

export default function InboxPage() {
  const [items, setItems] = useState(mockItems);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [addType, setAddType] = useState('link');

  const filteredItems = items.filter(item => {
    if (filter !== 'all' && item.status !== filter) return false;
    if (searchQuery && !item.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl md:text-4xl font-light text-[#1A1A1A] tracking-tight mb-2">
            素材箱
          </h1>
          <p className="text-sm text-[#707070]">
            你的个人信息池，所有收藏和订阅的内容都在这里
          </p>
        </div>
        <MachinedButton variant="primary" icon={Plus} onClick={() => setShowAddModal(true)}>
          添加内容
        </MachinedButton>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SpecCard title="总内容" subtitle="已收集">
          <div className="text-2xl font-light text-[#1A1A1A]">{items.length}</div>
        </SpecCard>
        <SpecCard title="已处理" subtitle="可生成播客">
          <div className="text-2xl font-light text-[#1A1A1A]">
            {items.filter(i => i.status === 'processed').length}
          </div>
        </SpecCard>
        <SpecCard title="处理中" subtitle="正在分析">
          <div className="text-2xl font-light text-[#1A1A1A]">
            {items.filter(i => i.status === 'processing').length}
          </div>
        </SpecCard>
        <SpecCard title="Newsletter" subtitle="专属邮箱">
          <div className="text-2xl font-light text-[#1A1A1A]">
            {items.filter(i => i.type === 'newsletter').length}
          </div>
        </SpecCard>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <InputField
            icon={Search}
            placeholder="搜索内容..."
            value={searchQuery}
            onChange={setSearchQuery}
          />
        </div>
        <SelectField
          value={filter}
          onChange={setFilter}
          options={[
            { value: 'all', label: '全部' },
            { value: 'processed', label: '已处理' },
            { value: 'processing', label: '处理中' },
            { value: 'pending', label: '待处理' },
          ]}
        />
      </div>

      {/* Newsletter Email Card */}
      <SpecCard title="Newsletter 专属邮箱" subtitle="将 Newsletter 转发到此邮箱">
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-[#F9F9F7] border border-[#E5E5E0]">
            <div>
              <div className="text-sm font-mono text-[#1A1A1A] mb-1">
                user_abc123@inbox.podcast.app
              </div>
              <div className="text-[10px] font-mono text-[#707070] uppercase">
                自动接收并处理 Newsletter
              </div>
            </div>
            <button className="px-4 py-2 text-xs font-mono uppercase border border-[#D4D4D0] hover:border-[#1A1A1A] transition-colors">
              复制
            </button>
          </div>
          <p className="text-xs text-[#707070]">
            在订阅 Newsletter 时使用此邮箱，或将自己邮箱收到的 Newsletter 转发到这里。
          </p>
        </div>
      </SpecCard>

      {/* Items List */}
      <div className="space-y-4">
        {filteredItems.length === 0 ? (
          <SpecCard title="暂无内容">
            <div className="text-center py-12">
              <FileText size={48} className="mx-auto text-[#D4D4D0] mb-4" />
              <p className="text-sm text-[#707070] mb-6">
                还没有任何内容。点击上方"添加内容"按钮开始收集。
              </p>
            </div>
          </SpecCard>
        ) : (
          filteredItems.map(item => (
            <InboxItem key={item.id} item={item} onDelete={(id) => {
              setItems(items.filter(i => i.id !== id));
            }} />
          ))
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <AddContentModal
          type={addType}
          onClose={() => setShowAddModal(false)}
          onAdd={(newItem) => {
            setItems([newItem, ...items]);
            setShowAddModal(false);
          }}
        />
      )}
    </div>
  );
}

function InboxItem({ item, onDelete }) {
  const [showDetails, setShowDetails] = useState(false);

  const typeIcon = {
    browser: Globe,
    newsletter: Mail,
    manual: FileText,
    rss: Link,
    wechat: Link,
  };

  const Icon = typeIcon[item.type] || FileText;

  return (
    <SpecCard 
      title={item.title} 
      subtitle={`${typeLabels[item.type]} · ${item.date}`}
    >
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Icon size={14} className="text-[#707070]" />
              <span className="text-[10px] font-mono text-[#707070] uppercase">
                {item.source}
              </span>
              {item.priority === 'important' && (
                <TagBadge variant="accent">重要</TagBadge>
              )}
            </div>
            <p className="text-sm text-[#555] leading-relaxed">{item.summary}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {item.tags.map(tag => (
            <TagBadge key={tag}>{tag}</TagBadge>
          ))}
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-[#F0F0EB]">
          <div className="flex items-center gap-4 text-[10px] font-mono text-[#707070]">
            <span className={`px-2 py-1 border ${
              item.status === 'processed' 
                ? 'bg-green-50 border-green-200 text-green-700'
                : item.status === 'processing'
                ? 'bg-yellow-50 border-yellow-200 text-yellow-700'
                : 'bg-gray-50 border-gray-200 text-gray-700'
            }`}>
              {item.status === 'processed' ? '已处理' : item.status === 'processing' ? '处理中' : '待处理'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {item.status === 'processed' && (
              <MachinedButton variant="ghost" icon={BookOpen} size="sm">
                生成深度研究
              </MachinedButton>
            )}
            <button
              onClick={() => onDelete(item.id)}
              className="p-2 text-[#707070] hover:text-[#EA580C] transition-colors"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      </div>
    </SpecCard>
  );
}

function AddContentModal({ type, onClose, onAdd }) {
  const [link, setLink] = useState('');
  const [text, setText] = useState('');
  const [tags, setTags] = useState('');
  const [priority, setPriority] = useState('normal');

  const handleSubmit = () => {
    const newItem = {
      id: Date.now().toString(),
      title: type === 'link' ? link : text.substring(0, 50) + '...',
      source: type === 'link' ? new URL(link).hostname : '手动添加',
      type: 'manual',
      date: new Date().toISOString().split('T')[0],
      tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      summary: text.substring(0, 100) + '...',
      status: 'processing',
      priority,
    };
    onAdd(newItem);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white border border-[#1A1A1A] max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-[#E5E5E0] flex items-center justify-between">
          <h2 className="text-lg font-bold uppercase tracking-widest text-[#1A1A1A] font-mono">
            添加内容
          </h2>
          <button onClick={onClose} className="text-[#707070] hover:text-[#1A1A1A]">
            <X size={20} />
          </button>
        </div>
        <div className="p-6 space-y-4">
          {type === 'link' ? (
            <InputField
              label="网页链接"
              value={link}
              onChange={setLink}
              placeholder="https://..."
              icon={Link}
            />
          ) : (
            <TextareaField
              label="文本内容"
              value={text}
              onChange={setText}
              placeholder="粘贴或输入文本内容..."
              rows={8}
            />
          )}
          <InputField
            label="标签（逗号分隔）"
            value={tags}
            onChange={setTags}
            placeholder="AI, 管理, 科技"
            icon={Tag}
          />
          <SelectField
            label="优先级"
            value={priority}
            onChange={setPriority}
            options={[
              { value: 'normal', label: '普通' },
              { value: 'important', label: '重要' },
            ]}
          />
          <div className="flex items-center gap-2 pt-4">
            <MachinedButton variant="primary" onClick={handleSubmit}>
              添加
            </MachinedButton>
            <MachinedButton variant="ghost" onClick={onClose}>
              取消
            </MachinedButton>
          </div>
        </div>
      </div>
    </div>
  );
}
