import React from 'react';
import { Sliders } from 'lucide-react';

const BITRATES = [
  { value: '128k', label: '128 kbps', badge: 'Standard' },
  { value: '192k', label: '192 kbps', badge: 'High Quality', recommended: true },
  { value: '256k', label: '256 kbps', badge: 'Very High' },
  { value: '320k', label: '320 kbps', badge: 'Ultra HD' },
];

const ACCENT_STYLES = {
  instagram: {
    selected: 'border-pink-500 bg-gradient-to-br from-pink-500/20 to-purple-600/20 text-white shadow-md shadow-pink-500/10 ring-1 ring-pink-500/50',
    badge: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
    activeText: 'text-pink-300',
    icon: 'text-pink-400',
  },
  youtube: {
    selected: 'border-red-500 bg-gradient-to-br from-red-500/20 to-rose-600/20 text-white shadow-md shadow-red-500/10 ring-1 ring-red-500/50',
    badge: 'bg-red-500/20 text-red-300 border-red-500/30',
    activeText: 'text-red-300',
    icon: 'text-red-400',
  },
  facebook: {
    selected: 'border-blue-500 bg-gradient-to-br from-blue-500/20 to-indigo-600/20 text-white shadow-md shadow-blue-500/10 ring-1 ring-blue-500/50',
    badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    activeText: 'text-blue-300',
    icon: 'text-blue-400',
  },
};

export default function QualitySelector({ bitrate, setBitrate, platform = 'instagram', disabled }) {
  const accent = ACCENT_STYLES[platform] || ACCENT_STYLES.instagram;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <Sliders className={`w-3.5 h-3.5 ${accent.icon}`} />
          Step 3: Select Audio Quality
        </label>
        <span className="text-xs text-slate-400">MP3 (LAME CBR)</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {BITRATES.map((item) => {
          const isSelected = bitrate === item.value;
          return (
            <button
              key={item.value}
              type="button"
              disabled={disabled}
              onClick={() => setBitrate(item.value)}
              className={`relative px-3 py-2.5 rounded-xl border text-left transition-all duration-200 flex flex-col justify-between cursor-pointer ${
                isSelected
                  ? accent.selected
                  : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700 hover:bg-slate-800/40'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-sm font-bold">{item.label}</span>
                {item.recommended && (
                  <span className={`text-[9px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded-full border ${accent.badge}`}>
                    Default
                  </span>
                )}
              </div>
              <span className={`text-[11px] mt-1 ${isSelected ? accent.activeText : 'text-slate-400'}`}>
                {item.badge}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
