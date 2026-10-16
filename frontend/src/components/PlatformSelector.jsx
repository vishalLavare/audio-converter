import React from 'react';
import { InstagramIcon, YouTubeIcon, FacebookIcon } from './BrandIcons';
import { Sparkles } from 'lucide-react';

const PLATFORMS = [
  {
    id: 'instagram',
    name: 'Instagram',
    subtitle: 'Reels & Videos',
    badge: 'Popular',
    icon: InstagramIcon,
    activeClasses: 'border-pink-500 bg-gradient-to-br from-purple-950/50 via-pink-950/40 to-slate-900 shadow-lg shadow-pink-500/20 text-white',
    indicatorBg: 'instagram-gradient',
    badgeClasses: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
    iconColor: 'text-pink-400',
  },
  {
    id: 'youtube',
    name: 'YouTube',
    subtitle: 'Videos & Shorts',
    badge: 'HD Audio',
    icon: YouTubeIcon,
    activeClasses: 'border-red-500 bg-gradient-to-br from-red-950/50 via-rose-950/40 to-slate-900 shadow-lg shadow-red-500/20 text-white',
    indicatorBg: 'bg-gradient-to-r from-red-600 via-rose-600 to-red-500',
    badgeClasses: 'bg-red-500/20 text-red-300 border-red-500/30',
    iconColor: 'text-red-500',
  },
  {
    id: 'facebook',
    name: 'Facebook',
    subtitle: 'Reels & Watch',
    badge: 'MP4 / MP3',
    icon: FacebookIcon,
    activeClasses: 'border-blue-500 bg-gradient-to-br from-blue-950/50 via-indigo-950/40 to-slate-900 shadow-lg shadow-blue-500/20 text-white',
    indicatorBg: 'bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500',
    badgeClasses: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    iconColor: 'text-blue-400',
  },
];

export default function PlatformSelector({ selectedPlatform, onSelectPlatform, disabled }) {
  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
          Step 1: Select Platform
        </label>
        <span className="text-[11px] text-slate-400 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-amber-400" />
          Supports Video & MP3
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2.5 sm:gap-3">
        {PLATFORMS.map((platform) => {
          const isSelected = selectedPlatform === platform.id;
          const Icon = platform.icon;

          return (
            <button
              key={platform.id}
              type="button"
              id={`platform-tab-${platform.id}`}
              onClick={() => onSelectPlatform(platform.id)}
              disabled={disabled}
              className={`relative flex flex-col items-center justify-center p-3 sm:p-4 rounded-2xl border transition-all duration-200 cursor-pointer text-center group disabled:opacity-50 disabled:cursor-not-allowed ${
                isSelected
                  ? platform.activeClasses
                  : 'border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 hover:border-slate-700 text-slate-400 hover:text-slate-200'
              }`}
            >
              {/* Active Top Highlight Bar */}
              {isSelected && (
                <div
                  className={`absolute top-0 inset-x-3 h-0.5 rounded-full ${platform.indicatorBg}`}
                />
              )}

              {/* Icon Container */}
              <div
                className={`p-2 sm:p-2.5 rounded-xl mb-2 transition-transform group-hover:scale-110 ${
                  isSelected
                    ? 'bg-white/10 shadow-inner'
                    : 'bg-slate-800/80 text-slate-400'
                }`}
              >
                <Icon className={`w-5 h-5 sm:w-6 sm:h-6 ${isSelected ? platform.iconColor : 'text-slate-400'}`} />
              </div>

              {/* Platform Title */}
              <span className={`text-xs sm:text-sm font-bold tracking-tight block ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                {platform.name}
              </span>

              {/* Subtitle */}
              <span className="text-[10px] sm:text-[11px] text-slate-400 hidden sm:block mt-0.5">
                {platform.subtitle}
              </span>

              {/* Badge */}
              <span
                className={`mt-1.5 px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-semibold border ${
                  isSelected
                    ? platform.badgeClasses
                    : 'bg-slate-800/60 text-slate-500 border-slate-700/60'
                }`}
              >
                {platform.badge}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
