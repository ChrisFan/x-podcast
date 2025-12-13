import React, { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Pause, ChevronDown, SkipBack, SkipForward, ListMusic, MoreHorizontal, Share2 } from 'lucide-react';
import { usePlayer } from '../context/PlayerContext';
import { cn } from '../lib/utils';

// Format seconds to MM:SS
const formatTime = (secs) => {
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

export default function Player() {
  const { currentEpisode, isPlaying, isExpanded, progress, togglePlay, openPlayer, closePlayer, setProgress } = usePlayer();

  if (!currentEpisode) return null;

  return (
    <>
      {/* Mini Player */}
      {!isExpanded && (
        <motion.div 
          initial={{ y: 100 }}
          animate={{ y: 0 }}
          className="fixed bottom-[calc(4rem+16px)] left-4 right-4 h-16 bg-[#1A1A1A] rounded-xl shadow-2xl z-40 flex items-center px-4 justify-between"
          onClick={openPlayer}
        >
          <div className="flex items-center gap-3 overflow-hidden">
            {/* Tiny Cover Art */}
            <div className={`w-10 h-10 rounded bg-gradient-to-br ${currentEpisode.coverGradient} flex-shrink-0`} />
            <div className="flex flex-col overflow-hidden">
              <span className="text-white text-sm font-bold truncate">{currentEpisode.title}</span>
              <span className="text-white/60 text-xs truncate">{currentEpisode.subtitle}</span>
            </div>
          </div>
          
          <button 
            onClick={(e) => { e.stopPropagation(); togglePlay(); }}
            className="w-10 h-10 flex items-center justify-center text-white"
          >
            {isPlaying ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" />}
          </button>
          
          {/* Progress Bar Background */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10 overflow-hidden rounded-b-xl">
             <div 
               className="h-full bg-orange-500 transition-all duration-1000 linear"
               style={{ width: `${(progress / currentEpisode.duration) * 100}%` }}
             />
          </div>
        </motion.div>
      )}

      {/* Full Screen Player */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed inset-0 bg-background z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 pt-12 pb-6">
              <button onClick={closePlayer} className="p-2 -ml-2 text-primary">
                <ChevronDown size={28} />
              </button>
              <span className="text-xs font-mono uppercase tracking-widest text-secondary">正在播放</span>
              <button className="p-2 -mr-2 text-primary">
                <MoreHorizontal size={24} />
              </button>
            </div>

            {/* Content Scroll Area */}
            <div className="flex-1 overflow-y-auto px-6 hide-scrollbar pb-8">
              {/* Cover Art */}
              <div className={`w-full aspect-square rounded-2xl bg-gradient-to-br ${currentEpisode.coverGradient} shadow-xl mb-8 flex items-center justify-center`}>
                <span className="text-white/20 font-bold text-6xl">AIRadio</span>
              </div>

              {/* Title Info */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-primary mb-2 leading-tight">{currentEpisode.title}</h2>
                <p className="text-lg text-secondary mb-1">{currentEpisode.subtitle}</p>
                <div className="flex gap-2 mt-3">
                  {currentEpisode.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-black/5 rounded text-xs text-secondary font-medium">
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Script / Chapters Section (The "Breakthrough") */}
              <div className="bg-white rounded-xl p-5 shadow-sm border border-border">
                <h3 className="text-xs font-mono uppercase text-secondary mb-4 tracking-wider">本期摘要 & 脚本</h3>
                <div className="space-y-4">
                  <p className="text-sm leading-relaxed text-primary/80">
                    {currentEpisode.description}
                  </p>
                  <div className="h-px bg-border my-4" />
                  <div className="space-y-3">
                    {currentEpisode.topics.map((topic, idx) => (
                      <div key={idx} className="flex items-center justify-between group cursor-pointer hover:bg-black/5 p-2 rounded -mx-2 transition-colors">
                        <span className="text-sm font-medium text-primary">{topic.title}</span>
                        <span className="text-xs font-mono text-secondary">{topic.time}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Controls Fixed Bottom */}
            <div className="px-6 pb-12 pt-6 bg-background border-t border-border/50">
              {/* Progress */}
              <div className="mb-6">
                <div className="h-1.5 bg-black/10 rounded-full mb-2 overflow-hidden">
                  <div 
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${(progress / currentEpisode.duration) * 100}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs font-mono text-secondary">
                  <span>{formatTime(progress)}</span>
                  <span>{formatTime(currentEpisode.duration)}</span>
                </div>
              </div>

              {/* Buttons */}
              <div className="flex items-center justify-between mb-8">
                 <button className="text-secondary hover:text-primary"><ListMusic size={24} /></button>
                 <div className="flex items-center gap-6">
                   <button 
                     onClick={() => setProgress(p => Math.max(0, p - 15))}
                     className="text-primary hover:text-accent transition-colors"
                   >
                     <SkipBack size={28} />
                   </button>
                   <button 
                    onClick={togglePlay}
                    className="w-16 h-16 bg-primary rounded-full flex items-center justify-center text-white shadow-lg active:scale-95 transition-transform"
                   >
                     {isPlaying ? <Pause size={32} fill="currentColor" /> : <Play size={32} fill="currentColor" className="ml-1" />}
                   </button>
                   <button 
                     onClick={() => setProgress(p => Math.min(currentEpisode.duration, p + 30))}
                     className="text-primary hover:text-accent transition-colors"
                   >
                     <SkipForward size={28} />
                   </button>
                 </div>
                 <button className="text-secondary hover:text-primary"><Share2 size={24} /></button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}


