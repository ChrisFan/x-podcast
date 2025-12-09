import React, { useState } from 'react';
import { 
  User, Radio, Volume2, Clock, Bell, Mail, 
  Moon, Sun, Activity, Zap, Coffee
} from 'lucide-react';
import { SpecCard, MachinedButton, DialSlider, MechanicalToggle, SelectField } from '../components/DesignSystem';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    // User preferences
    topics: ['科技', '商业', '职场', '理财'],
    scenes: ['通勤', '睡前'],
    duration: 20,
    
    // Voice settings
    voice: 'formal-male',
    speed: 1.0,
    bgm: false,
    
    // Generation settings
    generateTime: '07:30',
    generateCount: 1,
    notifications: true,
    
    // Theme
    theme: 'light',
  });

  const voiceOptions = [
    { value: 'formal-male', label: '正式新闻主播风（男声）' },
    { value: 'casual-female', label: '轻松聊天风（女声）' },
    { value: 'tech-male', label: '理工风格（男声）' },
    { value: 'calm-female', label: '沉稳女声（适合睡前）' },
  ];

  const topicOptions = ['科技', '商业', '职场', '理财', '健康', '兴趣', '设计', '哲学'];
  const sceneOptions = ['通勤', '睡前', '运动', '深度'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl md:text-4xl font-light text-[#1A1A1A] tracking-tight mb-2">
          设置
        </h1>
        <p className="text-sm text-[#707070]">
          个性化你的播客体验
        </p>
      </div>

      {/* User Preferences */}
      <SpecCard title="内容偏好" subtitle="告诉我们你的兴趣">
        <div className="space-y-6">
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider text-[#707070] mb-3 block">
              感兴趣的话题
            </label>
            <div className="flex flex-wrap gap-2">
              {topicOptions.map(topic => {
                const isSelected = settings.topics.includes(topic);
                return (
                  <button
                    key={topic}
                    onClick={() => {
                      if (isSelected) {
                        setSettings({
                          ...settings,
                          topics: settings.topics.filter(t => t !== topic),
                        });
                      } else {
                        setSettings({
                          ...settings,
                          topics: [...settings.topics, topic],
                        });
                      }
                    }}
                    className={`px-4 py-2 text-xs font-mono uppercase border transition-colors ${
                      isSelected
                        ? 'bg-[#1A1A1A] text-white border-[#1A1A1A]'
                        : 'bg-white text-[#707070] border-[#D4D4D0] hover:border-[#1A1A1A]'
                    }`}
                  >
                    {topic}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider text-[#707070] mb-3 block">
              主要收听场景
            </label>
            <div className="flex flex-wrap gap-2">
              {sceneOptions.map(scene => {
                const isSelected = settings.scenes.includes(scene);
                return (
                  <button
                    key={scene}
                    onClick={() => {
                      if (isSelected) {
                        setSettings({
                          ...settings,
                          scenes: settings.scenes.filter(s => s !== scene),
                        });
                      } else {
                        setSettings({
                          ...settings,
                          scenes: [...settings.scenes, scene],
                        });
                      }
                    }}
                    className={`px-4 py-2 text-xs font-mono uppercase border transition-colors ${
                      isSelected
                        ? 'bg-[#EA580C] text-white border-[#EA580C]'
                        : 'bg-white text-[#707070] border-[#D4D4D0] hover:border-[#1A1A1A]'
                    }`}
                  >
                    {scene}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <DialSlider
              label="期望单期时长"
              value={settings.duration}
              onChange={(val) => setSettings({ ...settings, duration: val })}
              min={10}
              max={30}
              unit=" 分钟"
            />
          </div>
        </div>
      </SpecCard>

      {/* Voice Settings */}
      <SpecCard title="声音设置" subtitle="选择你喜欢的主播和语速">
        <div className="space-y-6">
          <SelectField
            label="声线偏好"
            value={settings.voice}
            onChange={(val) => setSettings({ ...settings, voice: val })}
            options={voiceOptions}
          />

          <div>
            <DialSlider
              label="语速"
              value={settings.speed * 10}
              onChange={(val) => setSettings({ ...settings, speed: val / 10 })}
              min={8}
              max={15}
              unit="x"
            />
            <div className="flex items-center justify-between mt-2 text-[10px] font-mono text-[#707070]">
              <span>慢</span>
              <span>正常</span>
              <span>略快</span>
            </div>
          </div>

          <MechanicalToggle
            label="背景音乐"
            active={settings.bgm}
            onToggle={() => setSettings({ ...settings, bgm: !settings.bgm })}
          />
        </div>
      </SpecCard>

      {/* Generation Settings */}
      <SpecCard title="生成设置" subtitle="配置每日播客的生成时间">
        <div className="space-y-6">
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider text-[#707070] mb-2 block">
              每日生成时间
            </label>
            <input
              type="time"
              value={settings.generateTime}
              onChange={(e) => setSettings({ ...settings, generateTime: e.target.value })}
              className="w-full px-4 py-3 border border-[#D4D4D0] bg-white font-mono text-sm text-[#1A1A1A] focus:outline-none focus:border-[#1A1A1A]"
            />
          </div>

          <div>
            <DialSlider
              label="每日生成节目数"
              value={settings.generateCount}
              onChange={(val) => setSettings({ ...settings, generateCount: val })}
              min={1}
              max={2}
              unit=" 期"
            />
          </div>

          <MechanicalToggle
            label="推送提醒"
            active={settings.notifications}
            onToggle={() => setSettings({ ...settings, notifications: !settings.notifications })}
          />
        </div>
      </SpecCard>

      {/* Newsletter Email */}
      <SpecCard title="Newsletter 邮箱" subtitle="你的专属收件地址">
        <div className="space-y-4">
          <div className="p-4 bg-[#F9F9F7] border border-[#E5E5E0]">
            <div className="text-sm font-mono text-[#1A1A1A] mb-1">
              user_abc123@inbox.podcast.app
            </div>
            <div className="text-[10px] font-mono text-[#707070] uppercase">
              自动接收并处理 Newsletter
            </div>
          </div>
          <MachinedButton variant="secondary" icon={Mail}>
            复制邮箱地址
          </MachinedButton>
        </div>
      </SpecCard>

      {/* Account Info */}
      <SpecCard title="账户信息" subtitle="登录方式与基础信息">
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-[#F9F9F7] border border-[#E5E5E0]">
            <div>
              <div className="text-sm font-bold text-[#1A1A1A] mb-1">手机号登录</div>
              <div className="text-[10px] font-mono text-[#707070]">138****8888</div>
            </div>
            <button className="text-xs font-mono uppercase text-[#707070] hover:text-[#1A1A1A] transition-colors">
              修改
            </button>
          </div>
          <div className="flex items-center justify-between p-4 bg-[#F9F9F7] border border-[#E5E5E0]">
            <div>
              <div className="text-sm font-bold text-[#1A1A1A] mb-1">用户 ID</div>
              <div className="text-[10px] font-mono text-[#707070]">user_abc123</div>
            </div>
          </div>
        </div>
      </SpecCard>

      {/* Stats */}
      <SpecCard title="使用统计" subtitle="你的收听数据">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-light text-[#1A1A1A] mb-1">127</div>
            <div className="text-[10px] font-mono text-[#707070] uppercase">总收听时长（小时）</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-light text-[#1A1A1A] mb-1">89</div>
            <div className="text-[10px] font-mono text-[#707070] uppercase">已听节目数</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-light text-[#1A1A1A] mb-1">156</div>
            <div className="text-[10px] font-mono text-[#707070] uppercase">素材收集数</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-light text-[#1A1A1A] mb-1">12</div>
            <div className="text-[10px] font-mono text-[#707070] uppercase">深度研究数</div>
          </div>
        </div>
      </SpecCard>

      {/* Save Button */}
      <div className="flex justify-end">
        <MachinedButton variant="primary">
          保存设置
        </MachinedButton>
      </div>
    </div>
  );
}
