import React from 'react';
import { Play, Sparkles, Clock, ChevronRight, Zap } from 'lucide-react';
import { usePlayer } from '../context/PlayerContext';
import { MOCK_EPISODES } from '../lib/utils';

export default function Home() {
  const { playEpisode, currentEpisode, isPlaying } = usePlayer();
  const dailyEpisode = MOCK_EPISODES[0];
  const isDailyPlaying = currentEpisode?.id === dailyEpisode.id && isPlaying;

  return (
    <div className="px-5 pt-12 pb-8">
      {/* Header */}
      <header className="mb-8">
        <p className="text-sm text-secondary font-mono mb-1 uppercase tracking-wider">
          {new Date().toLocaleDateString('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' })}
        </p>
        <h1 className="text-3xl font-light text-primary">
          早安，<span className="font-bold">Chris</span>
        </h1>
      </header>

      {/* Hero Card: Daily Station */}
      <section className="mb-8 relative group">
        <div 
          className="relative w-full aspect-[4/5] rounded-3xl overflow-hidden shadow-2xl cursor-pointer active:scale-[0.98] transition-all duration-300"
          onClick={() => playEpisode(dailyEpisode)}
        >
          {/* Background Gradient */}
          <div className={`absolute inset-0 bg-gradient-to-br ${dailyEpisode.coverGradient} opacity-90`} />
          
          {/* Content Overlay */}
          <div className="absolute inset-0 p-6 flex flex-col justify-between text-white">
            <div className="flex justify-between items-start">
               <div className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 border border-white/10">
                 <Zap size={12} fill="currentColor" />
                 {dailyEpisode.mode === 'commute' ? '通勤模式' : '每日电台'}
               </div>
               <div className="w-8 h-8 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                 <Sparkles size={16} />
               </div>
            </div>

            <div>
              <h2 className="text-3xl font-bold leading-tight mb-2 drop-shadow-md">
                {dailyEpisode.title}
              </h2>
              <p className="text-white/80 text-sm mb-6 font-medium line-clamp-2">
                {dailyEpisode.description}
              </p>
              
              {/* Play Button visual */}
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-white rounded-full flex items-center justify-center text-orange-500 shadow-lg group-hover:scale-110 transition-transform">
                  {isDailyPlaying ? (
                     <div className="flex gap-1 h-4 items-center">
                       <span className="w-1 h-3 bg-current animate-bounce" style={{ animationDelay: '0s' }} />
                       <span className="w-1 h-4 bg-current animate-bounce" style={{ animationDelay: '0.1s' }} />
                       <span className="w-1 h-2 bg-current animate-bounce" style={{ animationDelay: '0.2s' }} />
                     </div>
                  ) : (
                    <Play size={24} fill="currentColor" className="ml-1" />
                  )}
                </div>
                <div className="font-mono text-xs opacity-80">
                  <div className="uppercase tracking-widest mb-0.5">Duration</div>
                  <div>{Math.floor(dailyEpisode.duration / 60)} MINS</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Secondary Section: Quick Actions / History */}
      <section className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-sm font-bold text-primary uppercase tracking-wider">最近更新</h3>
          <span className="text-xs text-secondary">查看全部</span>
        </div>

        <div className="space-y-3">
          {MOCK_EPISODES.slice(1).map(ep => (
            <div 
              key={ep.id} 
              onClick={() => playEpisode(ep)}
              className="bg-white p-4 rounded-xl border border-border flex gap-4 active:bg-gray-50 transition-colors"
            >
              <div className={`w-16 h-16 rounded-lg bg-gradient-to-br ${ep.coverGradient} flex-shrink-0`} />
              <div className="flex-1 min-w-0 flex flex-col justify-center">
                <h4 className="text-base font-bold text-primary truncate mb-1">{ep.title}</h4>
                <div className="flex items-center gap-3 text-xs text-secondary font-mono">
                  <span className="flex items-center gap-1">
                    <Clock size={12} />
                    {Math.floor(ep.duration / 60)} min
                  </span>
                  <span>{ep.date}</span>
                </div>
              </div>
              <button className="w-8 h-8 rounded-full border border-border flex items-center justify-center self-center text-primary">
                <Play size={14} fill="currentColor" />
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

