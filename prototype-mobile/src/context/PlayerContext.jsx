import React, { createContext, useContext, useState, useEffect } from 'react';

const PlayerContext = createContext();

export function PlayerProvider({ children }) {
  const [currentEpisode, setCurrentEpisode] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [progress, setProgress] = useState(0);

  // Mock Playback
  useEffect(() => {
    let interval;
    if (isPlaying && currentEpisode) {
      interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= currentEpisode.duration) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentEpisode]);

  const togglePlay = () => setIsPlaying(!isPlaying);
  const openPlayer = () => setIsExpanded(true);
  const closePlayer = () => setIsExpanded(false);
  const playEpisode = (episode) => {
    if (currentEpisode?.id === episode.id) {
      togglePlay();
    } else {
      setCurrentEpisode(episode);
      setIsPlaying(true);
      setProgress(0);
    }
    setIsExpanded(true);
  };

  return (
    <PlayerContext.Provider value={{
      currentEpisode,
      isPlaying,
      isExpanded,
      progress,
      togglePlay,
      openPlayer,
      closePlayer,
      playEpisode,
      setProgress
    }}>
      {children}
    </PlayerContext.Provider>
  );
}

export const usePlayer = () => useContext(PlayerContext);


