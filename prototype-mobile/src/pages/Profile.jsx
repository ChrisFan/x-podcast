import React from 'react';
import { Settings, Headphones, Heart, Clock, ChevronRight } from 'lucide-react';

export default function Profile() {
  const menuGroups = [
    {
      title: '偏好',
      items: [
        { icon: Headphones, label: '声音与语速' },
        { icon: Clock, label: '生成时间设置' },
      ]
    },
    {
      title: '内容',
      items: [
        { icon: Heart, label: '收藏的节目' },
        { icon: Settings, label: '通用设置' },
      ]
    }
  ];

  return (
    <div className="px-5 pt-12 pb-8">
      <header className="flex items-center gap-4 mb-10">
        <div className="w-16 h-16 rounded-full bg-gray-200 border-2 border-white shadow-md overflow-hidden">
           <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Chris" alt="Avatar" className="w-full h-full" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-primary">Chris</h1>
          <p className="text-sm text-secondary">Pro 会员</p>
        </div>
      </header>

      <div className="space-y-8">
        {menuGroups.map((group, idx) => (
          <div key={idx}>
            <h3 className="text-xs font-bold text-secondary uppercase tracking-widest mb-3 ml-2">
              {group.title}
            </h3>
            <div className="bg-white rounded-xl border border-border overflow-hidden">
              {group.items.map((item, i) => {
                const Icon = item.icon;
                return (
                  <button 
                    key={i}
                    className={`w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors ${
                      i !== group.items.length - 1 ? 'border-b border-border' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center text-primary">
                        <Icon size={16} />
                      </div>
                      <span className="text-sm font-medium text-primary">{item.label}</span>
                    </div>
                    <ChevronRight size={16} className="text-gray-300" />
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-12 text-center">
        <p className="text-[10px] text-gray-300 font-mono">
          Prototype v0.2.0 (Mobile)
        </p>
      </div>
    </div>
  );
}

