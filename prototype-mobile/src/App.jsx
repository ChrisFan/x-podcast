import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { PlayerProvider } from './context/PlayerContext';
import MobileLayout from './components/MobileLayout';
import Home from './pages/Home';
import Inbox from './pages/Inbox';
import Profile from './pages/Profile';

function App() {
  return (
    <PlayerProvider>
      <Router>
        <Routes>
          <Route element={<MobileLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/inbox" element={<Inbox />} />
            <Route path="/explore" element={<div className="pt-20 text-center text-gray-400">探索页面开发中...</div>} />
            <Route path="/profile" element={<Profile />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Router>
    </PlayerProvider>
  );
}

export default App;


