import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, X } from 'lucide-react';
import { MachinedButton, ProgressBar, TimeDisplay } from './DesignSystem';

export default function Player({ 
  episode, 
  isPlaying, 
  setIsPlaying, 
  currentTime, 
  setCurrentTime, 
  duration, 
  setDuration 
}) {
  const [volume, setVolume] = useState(100);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const progressRef = useRef(null);

  // Simulate audio playback
  useEffect(() => {
    if (isPlaying && duration > 0) {
      const interval = setInterval(() => {
        setCurrentTime(prev => {
          const next = prev + 0.1;
          if (next >= duration) {
            setIsPlaying(false);
            return duration;
          }
          return next;
        });
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isPlaying, duration, setIsPlaying, setCurrentTime]);

  const handleProgressClick = (e) => {
    if (!progressRef.current) return;
    const rect = progressRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percent = x / rect.width;
    const newTime = percent * duration;
    setCurrentTime(Math.max(0, Math.min(duration, newTime)));
  };

  const skipBackward = () => {
    setCurrentTime(prev => Math.max(0, prev - 15));
  };

  const skipForward = () => {
    setCurrentTime(prev => Math.min(duration, prev + 30));
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#1A1A1A] shadow-[0_-4px_20px_rgba(0,0,0,0.1)] z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4">
        {/* Episode Info */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-bold text-[#1A1A1A] truncate">{episode.title}</h4>
            <p className="text-[10px] font-mono text-[#707070] uppercase">
              {episode.mode} · {formatTime(duration)}
            </p>
          </div>
          <button
            onClick={() => {
              setIsPlaying(false);
              setCurrentTime(0);
            }}
            className="ml-4 p-2 text-[#707070] hover:text-[#1A1A1A] transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Progress Bar */}
        <div 
          ref={progressRef}
          className="relative h-2 bg-[#E5E5E0] cursor-pointer mb-3 group"
          onClick={handleProgressClick}
        >
          <div 
            className="absolute top-0 left-0 h-full bg-[#1A1A1A] transition-all"
            style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
          />
          <div 
            className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-[#1A1A1A] rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ left: `${duration > 0 ? (currentTime / duration) * 100 : 0}%`, marginLeft: '-8px' }}
          />
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={skipBackward}
              className="p-2 text-[#1A1A1A] hover:bg-[#F0F0EB] transition-colors rounded-sm"
              title="后退 15 秒"
            >
              <SkipBack size={18} />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="w-10 h-10 bg-[#1A1A1A] text-white flex items-center justify-center hover:bg-[#333] transition-colors"
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} />}
            </button>
            <button
              onClick={skipForward}
              className="p-2 text-[#1A1A1A] hover:bg-[#F0F0EB] transition-colors rounded-sm"
              title="快进 30 秒"
            >
              <SkipForward size={18} />
            </button>
            <div className="ml-4 flex items-center gap-2">
              <Volume2 size={14} className="text-[#707070]" />
              <input
                type="range"
                min="0"
                max="100"
                value={volume}
                onChange={(e) => setVolume(e.target.value)}
                className="w-20 h-1 bg-[#E5E5E0] appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #1A1A1A 0%, #1A1A1A ${volume}%, #E5E5E0 ${volume}%, #E5E5E0 100%)`
                }}
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-[#707070] uppercase">倍速</span>
              <select
                value={playbackRate}
                onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
                className="px-2 py-1 text-xs font-mono border border-[#D4D4D0] bg-white text-[#1A1A1A] focus:outline-none focus:border-[#1A1A1A]"
              >
                <option value="0.8">0.8x</option>
                <option value="1.0">1.0x</option>
                <option value="1.2">1.2x</option>
                <option value="1.5">1.5x</option>
                <option value="2.0">2.0x</option>
              </select>
            </div>
            <div className="text-[10px] font-mono text-[#707070]">
              <TimeDisplay seconds={currentTime} /> / <TimeDisplay seconds={duration} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
