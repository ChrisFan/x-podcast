import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Radio, Inbox, Compass, User } from 'lucide-react';
import Player from './Player';

export default function MobileLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Radio, label: '电台' },
    { path: '/inbox', icon: Inbox, label: '素材' },
    { path: '/explore', icon: Compass, label: '探索' },
    { path: '/profile', icon: User, label: '我的' },
  ];

  return (
    <div className="min-h-screen bg-background pb-24 relative">
      <div className="max-w-md mx-auto min-h-screen bg-white shadow-2xl overflow-hidden relative">
        {/* Main Content Area */}
        <main className="h-full overflow-y-auto hide-scrollbar">
          <Outlet />
        </main>

        {/* Global Player Overlay */}
        <Player />

        {/* Bottom Navigation */}
        <nav className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-md border-t border-border z-30 pb-safe">
          <div className="flex items-center justify-around h-16 max-w-md mx-auto">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`flex flex-col items-center justify-center w-16 h-full gap-1 transition-colors ${
                    isActive ? 'text-primary' : 'text-gray-400'
                  }`}
                >
                  <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
                  <span className="text-[10px] font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      </div>
    </div>
  );
}

