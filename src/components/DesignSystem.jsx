import React from 'react';
import { 
  Settings, Wind, Anchor, Coffee, MapPin, Compass, Activity, 
  Fingerprint, ChevronRight, Plus, Info, Hexagon, Layers, 
  PenTool, Mountain, Play, Pause, SkipBack, SkipForward,
  Volume2, Download, Share2, Heart, Search, Clock, Tag
} from 'lucide-react';

// -----------------------------------------------------------------------------
// DESIGN TOKENS
// -----------------------------------------------------------------------------

export const ThemeColors = {
  bg: "bg-[#F4F2ED]",
  surface: "bg-[#FFFFFF]",
  surfaceDark: "bg-[#1A1A1A]",
  textMain: "text-[#1A1A1A]",
  textMuted: "text-[#707070]",
  textLight: "text-[#F4F2ED]",
  border: "border-[#D4D4D0]",
  accent: "bg-[#EA580C]",
};

// -----------------------------------------------------------------------------
// ATOMIC COMPONENTS
// -----------------------------------------------------------------------------

// 1. Machined Button
export const MachinedButton = ({ children, variant = 'primary', icon: Icon, onClick, disabled, className = '' }) => {
  const baseStyle = "relative px-6 py-3 font-mono text-xs tracking-widest uppercase transition-all duration-200 active:scale-95 flex items-center justify-center gap-2 border";
  
  const styles = {
    primary: `${baseStyle} bg-[#1A1A1A] text-[#F4F2ED] border-[#1A1A1A] hover:bg-[#333] shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`,
    secondary: `${baseStyle} bg-transparent text-[#1A1A1A] border-[#A0A09C] hover:bg-[#EAE8E4] hover:border-[#1A1A1A] ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`,
    ghost: `${baseStyle} border-transparent text-[#707070] hover:text-[#1A1A1A] hover:bg-[#EAE8E4/50]`,
    accent: `${baseStyle} bg-[#EA580C] text-white border-[#EA580C] hover:bg-[#C2410C]`,
  };

  return (
    <button 
      className={`${styles[variant]} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {Icon && <Icon size={14} strokeWidth={2} />}
      {children}
      {variant === 'primary' && (
        <div className="absolute right-1 top-1 opacity-30">
          <div className="w-[2px] h-[2px] bg-white rounded-full"></div>
        </div>
      )}
    </button>
  );
};

// 2. Dial Slider
export const DialSlider = ({ label, value, onChange, min = 0, max = 100, unit = '' }) => {
  const percentage = ((value - min) / (max - min)) * 100;
  
  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex justify-between text-[10px] font-mono uppercase tracking-wider text-[#707070]">
        <span>{label}</span>
        <span>{value}{unit}</span>
      </div>
      <div 
        className="relative h-8 flex items-center select-none cursor-pointer group"
        onMouseDown={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const handleMove = (moveEvent) => {
            const x = moveEvent.clientX - rect.left;
            const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
            const newValue = min + (percent / 100) * (max - min);
            onChange(Math.round(newValue));
          };
          const handleUp = () => {
            document.removeEventListener('mousemove', handleMove);
            document.removeEventListener('mouseup', handleUp);
          };
          document.addEventListener('mousemove', handleMove);
          document.addEventListener('mouseup', handleUp);
          handleMove(e);
        }}
      >
        <div className="absolute w-full h-[2px] bg-[#D4D4D0] group-hover:bg-[#A0A09C] transition-colors"></div>
        <div className="absolute w-full flex justify-between px-[2px]">
          {[...Array(11)].map((_, i) => (
            <div key={i} className={`w-[1px] ${i % 5 === 0 ? 'h-3 bg-[#707070]' : 'h-1.5 bg-[#D4D4D0]'}`}></div>
          ))}
        </div>
        <div 
          className="absolute w-4 h-6 bg-[#1A1A1A] border border-[#1A1A1A] shadow-sm z-10 transform -translate-x-1/2 transition-all"
          style={{ left: `${percentage}%` }}
        >
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1px] h-full bg-[#F4F2ED] opacity-50"></div>
        </div>
      </div>
    </div>
  );
};

// 3. Mechanical Toggle
export const MechanicalToggle = ({ active, onToggle, label }) => {
  return (
    <div className="flex items-center gap-3">
      {label && <span className="text-xs font-mono text-[#707070] uppercase">{label}</span>}
      <div 
        onClick={onToggle}
        className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors duration-300 ${active ? 'bg-[#1A1A1A]' : 'bg-[#D4D4D0]'}`}
      >
        <div 
          className={`w-4 h-4 bg-[#F4F2ED] rounded-full shadow-md transform transition-transform duration-300 ${active ? 'translate-x-6' : 'translate-x-0'} flex items-center justify-center`}
        >
          <div className="w-2 h-2 border border-[#D4D4D0] rounded-full opacity-50"></div>
        </div>
      </div>
    </div>
  );
};

// 4. Spec Card
export const SpecCard = ({ title, subtitle, children, className = '' }) => {
  return (
    <div className={`bg-white border border-[#E5E5E0] p-6 shadow-[0_2px_12px_-4px_rgba(0,0,0,0.05)] hover:shadow-[0_4px_20px_-6px_rgba(0,0,0,0.1)] transition-shadow duration-500 ${className}`}>
      <div className="flex justify-between items-start mb-6 border-b border-[#F0F0EB] pb-4 border-dashed">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-[#1A1A1A] flex items-center gap-2">
            <div className="w-2 h-2 bg-[#EA580C] rounded-sm"></div>
            {title}
          </h3>
          {subtitle && <p className="text-[10px] font-mono text-[#90908C] mt-1">{subtitle}</p>}
        </div>
        <div className="text-[#D4D4D0]">
          <Activity size={16} />
        </div>
      </div>
      {children}
    </div>
  );
};

// 5. Tag Badge
export const TagBadge = ({ children, variant = 'default', onClick }) => {
  const styles = {
    default: 'bg-[#F0F0EB] text-[#1A1A1A] border-[#E5E5E0]',
    accent: 'bg-[#EA580C] text-white border-[#EA580C]',
    dark: 'bg-[#1A1A1A] text-[#F4F2ED] border-[#1A1A1A]',
  };
  
  return (
    <span 
      className={`inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono uppercase tracking-wider border ${styles[variant]} ${onClick ? 'cursor-pointer hover:opacity-80' : ''}`}
      onClick={onClick}
    >
      {children}
    </span>
  );
};

// 6. Input Field
export const InputField = ({ label, value, onChange, placeholder, type = 'text', icon: Icon, onKeyPress }) => {
  return (
    <div className="flex flex-col gap-2">
      {label && <label className="text-[10px] font-mono uppercase tracking-wider text-[#707070]">{label}</label>}
      <div className="relative">
        {Icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#707070]">
            <Icon size={14} />
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder={placeholder}
          className={`w-full px-4 py-3 border border-[#D4D4D0] bg-white font-mono text-sm text-[#1A1A1A] focus:outline-none focus:border-[#1A1A1A] transition-colors ${Icon ? 'pl-10' : ''}`}
        />
      </div>
    </div>
  );
};

// 7. Textarea
export const TextareaField = ({ label, value, onChange, placeholder, rows = 4 }) => {
  return (
    <div className="flex flex-col gap-2">
      {label && <label className="text-[10px] font-mono uppercase tracking-wider text-[#707070]">{label}</label>}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full px-4 py-3 border border-[#D4D4D0] bg-white font-mono text-sm text-[#1A1A1A] focus:outline-none focus:border-[#1A1A1A] transition-colors resize-none"
      />
    </div>
  );
};

// 8. Select Dropdown
export const SelectField = ({ label, value, onChange, options }) => {
  return (
    <div className="flex flex-col gap-2">
      {label && <label className="text-[10px] font-mono uppercase tracking-wider text-[#707070]">{label}</label>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-3 border border-[#D4D4D0] bg-white font-mono text-sm text-[#1A1A1A] focus:outline-none focus:border-[#1A1A1A] transition-colors cursor-pointer"
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
};

// 9. Progress Bar
export const ProgressBar = ({ value, max = 100, className = '' }) => {
  const percentage = (value / max) * 100;
  return (
    <div className={`w-full h-1 bg-[#E5E5E0] relative ${className}`}>
      <div 
        className="absolute top-0 left-0 h-full bg-[#1A1A1A] transition-all duration-300"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

// 10. Time Display
export const TimeDisplay = ({ seconds, className = '' }) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return (
    <span className={`font-mono text-xs ${className}`}>
      {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
    </span>
  );
};
