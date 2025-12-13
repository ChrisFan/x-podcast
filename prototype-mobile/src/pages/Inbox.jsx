import React from 'react';
import { Plus, Link, Mail, FileText } from 'lucide-react';

export default function Inbox() {
  const items = [
    { id: 1, title: 'Understanding AI Agents in 2025', source: 'Stratechery', type: 'link', date: '10m ago' },
    { id: 2, title: 'Q1 Product Strategy Draft_v2.pdf', source: 'Email Upload', type: 'file', date: '2h ago' },
    { id: 3, title: 'The Future of Commute Audio', source: 'WeChat', type: 'link', date: '5h ago' },
  ];

  return (
    <div className="px-5 pt-12 pb-8">
      <header className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-light text-primary">素材箱</h1>
        <button className="w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center shadow-lg active:scale-90 transition-transform">
          <Plus size={24} />
        </button>
      </header>

      {/* Filter Tabs */}
      <div className="flex gap-3 mb-6 overflow-x-auto hide-scrollbar pb-2">
        {['全部', '待处理', '已归档', '网页', 'Newsletter'].map((tab, i) => (
          <button 
            key={tab}
            className={`px-4 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-colors ${
              i === 0 ? 'bg-primary text-white' : 'bg-white border border-border text-secondary'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="space-y-3">
        {items.map(item => (
          <div key={item.id} className="bg-white p-4 rounded-xl border border-border shadow-sm">
            <div className="flex items-start gap-3">
              <div className="mt-1 w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center text-secondary flex-shrink-0">
                {item.type === 'link' ? <Link size={16} /> : item.type === 'file' ? <FileText size={16} /> : <Mail size={16} />}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-bold text-primary mb-1 line-clamp-2 leading-snug">
                  {item.title}
                </h4>
                <div className="flex items-center gap-2 text-xs text-secondary">
                  <span className="font-mono text-[10px] uppercase bg-gray-100 px-1.5 py-0.5 rounded text-gray-500">
                    {item.source}
                  </span>
                  <span>·</span>
                  <span>{item.date}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


