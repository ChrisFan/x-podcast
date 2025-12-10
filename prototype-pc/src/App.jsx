import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Fingerprint, Radio, Inbox, Settings, Search, Menu, X } from 'lucide-react';
import { ThemeColors } from './components/DesignSystem';
import DailyStation from './pages/DailyStation';
import InboxPage from './pages/InboxPage';
import SettingsPage from './pages/SettingsPage';
import EpisodeDetail from './pages/EpisodeDetail';
import SearchPage from './pages/SearchPage';
import Player from './components/Player';

function App() {
  const [currentEpisode, setCurrentEpisode] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Update duration when episode changes
  useEffect(() => {
    if (currentEpisode?.duration) {
      setDuration(currentEpisode.duration);
    }
  }, [currentEpisode]);

  return (
    <Router>
      <AppContent 
        currentEpisode={currentEpisode}
        setCurrentEpisode={setCurrentEpisode}
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
        currentTime={currentTime}
        setCurrentTime={setCurrentTime}
        duration={duration}
        setDuration={setDuration}
      />
    </Router>
  );
}

function AppContent({ currentEpisode, setCurrentEpisode, isPlaying, setIsPlaying, currentTime, setCurrentTime, duration, setDuration }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [time, setTime] = useState(new Date());
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const navItems = [
    { path: '/', icon: Radio, label: '每日电台' },
    { path: '/inbox', icon: Inbox, label: '素材箱' },
    { path: '/search', icon: Search, label: '搜索' },
    { path: '/settings', icon: Settings, label: '设置' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className={`min-h-screen ${ThemeColors.bg} font-sans pb-24`}>
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#F4F2ED]/90 backdrop-blur-sm border-b border-[#E5E5E0]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-8 h-8 bg-[#1A1A1A] text-white flex items-center justify-center rounded-sm">
              <Fingerprint size={18} strokeWidth={1.5} />
            </div>
            <span className="font-mono text-xs tracking-widest font-bold text-[#1A1A1A] hidden sm:inline">
              个人知识电台
            </span>
          </div>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map(item => {
              const Icon = item.icon;
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`px-4 py-2 text-xs font-mono uppercase tracking-wider transition-colors flex items-center gap-2 ${
                    isActive(item.path) 
                      ? 'text-[#1A1A1A] font-bold border-b-2 border-[#EA580C]' 
                      : 'text-[#707070] hover:text-[#1A1A1A]'
                  }`}
                >
                  <Icon size={14} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-[#1A1A1A]"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="md:hidden border-t border-[#E5E5E0] bg-white">
            {navItems.map(item => {
              const Icon = item.icon;
              return (
                <button
                  key={item.path}
                  onClick={() => {
                    navigate(item.path);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full px-6 py-4 text-left text-xs font-mono uppercase tracking-wider flex items-center gap-3 border-b border-[#F0F0EB] ${
                    isActive(item.path) 
                      ? 'text-[#1A1A1A] font-bold bg-[#F9F9F7]' 
                      : 'text-[#707070]'
                  }`}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        )}

        {/* Time Display */}
        <div className="hidden md:block absolute right-6 top-1/2 -translate-y-1/2 font-mono text-[10px] text-[#707070]">
          {time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <Routes>
          <Route 
            path="/" 
            element={
              <DailyStation 
                onPlayEpisode={setCurrentEpisode}
                currentEpisode={currentEpisode}
              />
            } 
          />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route 
            path="/episode/:id" 
            element={
              <EpisodeDetail 
                onPlayEpisode={setCurrentEpisode}
                currentEpisode={currentEpisode}
              />
            } 
          />
          <Route path="/search" element={<SearchPage />} />
        </Routes>
      </main>

      {/* Player Bar */}
      {currentEpisode && (
        <Player
          episode={currentEpisode}
          isPlaying={isPlaying}
          setIsPlaying={setIsPlaying}
          currentTime={currentTime}
          setCurrentTime={setCurrentTime}
          duration={currentEpisode.duration || duration}
          setDuration={(val) => {
            setDuration(val);
            if (currentEpisode) {
              setCurrentEpisode({ ...currentEpisode, duration: val });
            }
          }}
        />
      )}
    </div>
  );
}

export default App;
