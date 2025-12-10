import React, { useState, useEffect } from 'react';
import { Settings, Wind, Anchor, Coffee, MapPin, Compass, Activity, Fingerprint, ChevronRight, Plus, Info, Hexagon, Layers, PenTool, Mountain } from 'lucide-react';

// -----------------------------------------------------------------------------
// DESIGN TOKENS & UTILITIES
// -----------------------------------------------------------------------------

// Color Palette (Tailwind config simulation)
// Ivory: #F4F2ED (Snowpeak vibe)
// Matte Black: #1A1A1A (Weber vibe)
// Aluminum: #D1D5DB (Logam/Hardy vibe)
// Accent Orange: #EA580C (Outdoor Gear vibe)

const ThemeColors = {
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
// ATOMS (Basic Components)
// -----------------------------------------------------------------------------

// 1. The "Machined" Button - Inspired by Logam/Weber build quality
const MachinedButton = ({ children, variant = 'primary', icon: Icon }) => {
  const baseStyle = "relative px-6 py-3 font-mono text-xs tracking-widest uppercase transition-all duration-200 active:scale-95 flex items-center justify-center gap-2 border";
  
  const styles = {
    primary: `${baseStyle} bg-[#1A1A1A] text-[#F4F2ED] border-[#1A1A1A] hover:bg-[#333] shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]`,
    secondary: `${baseStyle} bg-transparent text-[#1A1A1A] border-[#A0A09C] hover:bg-[#EAE8E4] hover:border-[#1A1A1A]`,
    ghost: `${baseStyle} border-transparent text-[#707070] hover:text-[#1A1A1A] hover:bg-[#EAE8E4/50]`,
  };

  return (
    <button className={styles[variant]}>
      {Icon && <Icon size={14} strokeWidth={2} />}
      {children}
      {/* Decorative Screw Head simulated */}
      {variant === 'primary' && (
        <div className="absolute right-1 top-1 opacity-30">
          <div className="w-[2px] h-[2px] bg-white rounded-full"></div>
        </div>
      )}
    </button>
  );
};

// 2. The "Dial" Slider - Inspired by Grinder Settings
const DialSlider = ({ label, value, onChange }) => {
  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex justify-between text-[10px] font-mono uppercase tracking-wider text-[#707070]">
        <span>{label}</span>
        <span>{value.toFixed(1)} MM</span>
      </div>
      <div className="relative h-8 flex items-center select-none cursor-pointer group">
        {/* Track */}
        <div className="absolute w-full h-[2px] bg-[#D4D4D0] group-hover:bg-[#A0A09C] transition-colors"></div>
        
        {/* Ticks */}
        <div className="absolute w-full flex justify-between px-[2px]">
          {[...Array(11)].map((_, i) => (
            <div key={i} className={`w-[1px] ${i % 5 === 0 ? 'h-3 bg-[#707070]' : 'h-1.5 bg-[#D4D4D0]'}`}></div>
          ))}
        </div>

        {/* Knob - Weber Style */}
        <div 
          className="absolute w-4 h-6 bg-[#1A1A1A] border border-[#1A1A1A] shadow-sm z-10 transform -translate-x-1/2 transition-all"
          style={{ left: `${value}%` }}
        >
           {/* Indicator Line */}
           <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1px] h-full bg-[#F4F2ED] opacity-50"></div>
        </div>
      </div>
    </div>
  );
};

// 3. The "Toggle" Switch - Mechanical Feel
const MechanicalToggle = ({ active, onToggle }) => {
  return (
    <div 
      onClick={onToggle}
      className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors duration-300 ${active ? 'bg-[#1A1A1A]' : 'bg-[#D4D4D0]'}`}
    >
      <div 
        className={`w-4 h-4 bg-[#F4F2ED] rounded-full shadow-md transform transition-transform duration-300 ${active ? 'translate-x-6' : 'translate-x-0'} flex items-center justify-center`}
      >
        {/* Tiny texture */}
        <div className="w-2 h-2 border border-[#D4D4D0] rounded-full opacity-50"></div>
      </div>
    </div>
  );
};

// 4. The "Spec" Card - Inspired by Andwander tags & Snowpeak layout
const SpecCard = ({ title, subtitle, children }) => {
  return (
    <div className="bg-white border border-[#E5E5E0] p-6 shadow-[0_2px_12px_-4px_rgba(0,0,0,0.05)] hover:shadow-[0_4px_20px_-6px_rgba(0,0,0,0.1)] transition-shadow duration-500">
      <div className="flex justify-between items-start mb-6 border-b border-[#F0F0EB] pb-4 border-dashed">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-[#1A1A1A] flex items-center gap-2">
            <div className="w-2 h-2 bg-[#EA580C] rounded-sm"></div>
            {title}
          </h3>
          <p className="text-[10px] font-mono text-[#90908C] mt-1">{subtitle}</p>
        </div>
        <div className="text-[#D4D4D0]">
          <Activity size={16} />
        </div>
      </div>
      {children}
    </div>
  );
};

// -----------------------------------------------------------------------------
// MANIFESTO SECTION (New: Explains the design philosophy)
// -----------------------------------------------------------------------------
const ManifestoSection = () => {
  const philosophyItems = [
    {
      icon: Hexagon,
      title: "Weber Precision",
      desc: "极简黑与精密加工",
      detail: "借鉴 Logam/Weber 的阳极氧化铝质感与哑光黑，追求极致的公差美学。UI 控件应具有机械操作的确定性。",
      color: "text-[#1A1A1A]"
    },
    {
      icon: Anchor,
      title: "Hardy Heritage",
      desc: "复古机械与结构外露",
      detail: "致敬 Hardy 飞钓轮的棘轮声与金属原色。不隐藏框架，通过线条和分割强调界面的功能结构。",
      color: "text-[#707070]"
    },
    {
      icon: Mountain,
      title: "Snowpeak Canvas",
      desc: "自然色与包容感",
      detail: "基底色摒弃科技冷白，采用象牙白（Ivory）天幕色。营造野奢露营般既自然又精致的舒适氛围。",
      color: "text-[#8B5E3C]"
    },
    {
      icon: Layers,
      title: "Andwander Utility",
      desc: "说明书式排版",
      detail: "数据即装饰。大量使用等宽字体（Monospace）和标签化设计，如同户外机能服饰上的规格说明。",
      color: "text-[#4A5568]"
    }
  ];

  return (
    <div className="border border-[#1A1A1A] bg-[#F4F2ED] relative overflow-hidden">
       {/* Background watermark */}
       <div className="absolute -right-10 -bottom-10 text-[#E5E5E0] opacity-50 pointer-events-none">
          <Fingerprint size={300} strokeWidth={0.5} />
       </div>

       <div className="p-8 relative z-10">
          <div className="flex items-center gap-4 mb-8 border-b border-[#1A1A1A] pb-4">
             <div className="bg-[#1A1A1A] text-[#F4F2ED] px-2 py-1 text-xs font-mono font-bold">DOC_REF: 001</div>
             <h2 className="text-xl font-light tracking-tight uppercase text-[#1A1A1A]">
               Design Manifesto: <span className="font-bold">Tactile Utility</span>
             </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
             {philosophyItems.map((item, idx) => (
                <div key={idx} className="flex gap-4 group">
                   <div className={`mt-1 p-2 border border-[#D4D4D0] bg-white h-fit rounded-sm group-hover:border-[#1A1A1A] transition-colors`}>
                      <item.icon size={18} className={item.color} />
                   </div>
                   <div>
                      <h4 className="text-sm font-bold uppercase tracking-widest text-[#1A1A1A] mb-1">{item.title}</h4>
                      <p className="text-xs font-serif italic text-[#707070] mb-2">{item.desc}</p>
                      <p className="text-[11px] text-[#555] leading-relaxed max-w-xs">{item.detail}</p>
                   </div>
                </div>
             ))}
          </div>

          <div className="mt-8 pt-4 border-t border-dashed border-[#A0A09C] flex justify-between items-center">
             <div className="text-[10px] font-mono text-[#707070] uppercase">
                Est. 2024 / Digital Craftsmanship
             </div>
             <div className="flex gap-2">
                <div className="w-2 h-2 rounded-full bg-[#EA580C]"></div>
                <div className="w-2 h-2 rounded-full bg-[#1A1A1A]"></div>
                <div className="w-2 h-2 rounded-full bg-[#D1D5DB]"></div>
             </div>
          </div>
       </div>
    </div>
  );
};

// -----------------------------------------------------------------------------
// APP MOCKUP
// -----------------------------------------------------------------------------

const App = () => {
  const [grindSize, setGrindSize] = useState(45);
  const [isPowerOn, setIsPowerOn] = useState(true);
  const [activeTab, setActiveTab] = useState('MANIFESTO'); // Default tab changed to show manifesto first

  // Mocking current time for the "Clock" widget
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className={`min-h-screen ${ThemeColors.bg} font-sans selection:bg-[#EA580C] selection:text-white pb-20`}>
      
      {/* HEADER: Minimalist & Functional */}
      <header className="sticky top-0 z-50 bg-[#F4F2ED]/90 backdrop-blur-sm border-b border-[#E5E5E0]">
        <div className="max-w-3xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#1A1A1A] text-white flex items-center justify-center rounded-sm">
              <Fingerprint size={18} strokeWidth={1.5} />
            </div>
            <span className="font-mono text-xs tracking-widest font-bold text-[#1A1A1A]">ANALOG_OS v1.0</span>
          </div>
          <div className="font-mono text-[10px] text-[#707070] hidden sm:block">
             {time.toLocaleTimeString()} / LAT 35.6895° N
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="max-w-3xl mx-auto px-6 py-12 space-y-12">

        {/* HERO SECTION: "Natural Tech" */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl md:text-4xl font-light text-[#1A1A1A] tracking-tight">
              Precision <span className="font-serif italic text-[#707070]">meets</span><br/>
              Wilderness.
            </h1>
            <div className="hidden md:block">
              <MachinedButton variant="secondary" icon={ChevronRight}>Explore</MachinedButton>
            </div>
          </div>
        </section>

        {/* MANIFESTO VISUALIZATION */}
        <section>
          <ManifestoSection />
        </section>

        {/* DASHBOARD TABS: Andwander Label Style */}
        <div className="flex border-b border-[#D4D4D0] gap-8 mt-12">
           {['EQUIPMENT', 'TOPOGRAPHY', 'LOGS'].map((tab) => (
             <button 
               key={tab}
               onClick={() => setActiveTab(tab)}
               className={`pb-3 text-xs font-mono tracking-widest transition-all relative ${activeTab === tab ? 'text-[#1A1A1A] font-bold' : 'text-[#A0A09C]'}`}
             >
               {tab}
               {activeTab === tab && (
                 <div className="absolute bottom-0 left-0 w-full h-[2px] bg-[#EA580C]"></div>
               )}
             </button>
           ))}
        </div>

        {/* WIDGET GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Card 1: Coffee Controller (Weber Style) */}
          <SpecCard title="Grind Control" subtitle="RPM: 1200 / BURR: 83MM">
            <div className="space-y-8 mt-4">
              <div className="flex items-center justify-between">
                 <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${isPowerOn ? 'bg-green-500 animate-pulse' : 'bg-red-400'}`}></div>
                    <span className="text-xs font-bold text-[#1A1A1A]">MOTOR STATUS</span>
                 </div>
                 <MechanicalToggle active={isPowerOn} onToggle={() => setIsPowerOn(!isPowerOn)} />
              </div>
              
              <div className="bg-[#F9F9F7] p-4 border border-[#E5E5E0] rounded-sm">
                <DialSlider label="Coarseness" value={grindSize} onChange={setGrindSize} />
              </div>

              <div className="flex gap-2">
                 <MachinedButton variant="primary" icon={Coffee}>Dose</MachinedButton>
                 <MachinedButton variant="secondary" icon={Settings}>Calibrate</MachinedButton>
              </div>
            </div>
          </SpecCard>

          {/* Card 2: Environment Monitor (Snowpeak/Andwander Style) */}
          <SpecCard title="Field Conditions" subtitle="LOC: ALPS / ELEV: 2400M">
            <div className="space-y-6 mt-2">
              {/* Weather Row */}
              <div className="flex justify-between items-center border-b border-dashed border-[#E5E5E0] pb-4">
                <div className="flex items-center gap-4">
                   <div className="p-3 bg-[#F0F0EB] rounded-sm text-[#4A5568]">
                      <Wind size={20} />
                   </div>
                   <div>
                      <div className="text-2xl font-light text-[#1A1A1A]">12<span className="text-xs text-[#707070] ml-1">km/h</span></div>
                      <div className="text-[10px] font-mono text-[#707070] uppercase">Wind Speed / NW</div>
                   </div>
                </div>
                <div className="text-right">
                   <div className="text-2xl font-light text-[#1A1A1A]">8<span className="text-xs text-[#707070] ml-1">°C</span></div>
                   <div className="text-[10px] font-mono text-[#707070] uppercase">Temp</div>
                </div>
              </div>

              {/* List Items */}
              <div className="space-y-3">
                {[
                  { icon: Anchor, label: "River Level", val: "Normal" },
                  { icon: Compass, label: "Barometer", val: "1013 hPa" },
                  { icon: MapPin, label: "Distance", val: "4.2 km" },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm group cursor-pointer">
                    <div className="flex items-center gap-3 text-[#707070] group-hover:text-[#1A1A1A] transition-colors">
                      <item.icon size={14} />
                      <span>{item.label}</span>
                    </div>
                    <span className="font-mono text-[#1A1A1A] bg-[#F0F0EB] px-2 py-1 text-xs rounded-sm group-hover:bg-[#E5E5E0] transition-colors">{item.val}</span>
                  </div>
                ))}
              </div>

              <button className="w-full py-3 border-t border-[#E5E5E0] text-[10px] font-mono uppercase tracking-widest text-[#707070] hover:text-[#1A1A1A] hover:bg-[#F9F9F7] transition-colors flex items-center justify-center gap-2">
                <Plus size={12} /> View Full Report
              </button>
            </div>
          </SpecCard>

        </div>

        {/* IMAGE / ATMOSPHERE SECTION */}
        <div className="relative w-full aspect-video bg-[#E5E5E0] overflow-hidden group">
           <div className="absolute inset-0 flex items-center justify-center">
              <p className="font-serif text-[#A0A09C] italic">Image Placeholder: River Stream / Coffee Pour</p>
           </div>
           {/* Overlay UI mimicking camera interface or HUD */}
           <div className="absolute inset-0 p-4 flex flex-col justify-between">
              <div className="flex justify-between text-[10px] font-mono text-white/80">
                 <span>ISO 400</span>
                 <span>1/250</span>
                 <span>F2.8</span>
              </div>
              <div className="flex justify-between items-end">
                 <div className="w-8 h-8 border border-white/50 rounded-full flex items-center justify-center backdrop-blur-sm">
                    <div className="w-1 h-1 bg-red-500 rounded-full"></div>
                 </div>
                 <div className="text-[10px] font-mono text-white/80 bg-black/20 backdrop-blur-md px-2 py-1">
                    REC 00:12:45
                 </div>
              </div>
           </div>
        </div>

        {/* FOOTER */}
        <footer className="border-t border-[#D4D4D0] pt-12 pb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
           <div>
              <h4 className="font-bold text-[#1A1A1A] text-sm tracking-widest uppercase mb-2">Studio Analog</h4>
              <p className="text-xs text-[#707070] max-w-xs">Designed for the intersection of mechanical precision and organic living.</p>
           </div>
           <div className="flex gap-6 text-[10px] font-mono text-[#707070] uppercase">
              <a href="#" className="hover:text-[#1A1A1A]">Specs</a>
              <a href="#" className="hover:text-[#1A1A1A]">Manifesto</a>
              <a href="#" className="hover:text-[#1A1A1A]">Contact</a>
           </div>
        </footer>

      </main>
    </div>
  );
};

export default App;