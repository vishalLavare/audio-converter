import React from 'react';
import { Link2, ClipboardPaste, X, Sparkles, ArrowRightLeft } from 'lucide-react';
import { InstagramIcon, YouTubeIcon, FacebookIcon } from './BrandIcons';

const PLATFORM_CONFIG = {
  instagram: {
    name: 'Instagram',
    label: 'Instagram Reel or Video URL',
    placeholder: 'https://www.instagram.com/reel/Daf2gF3vCzS/',
    exampleUrl: 'https://www.instagram.com/reel/Daf2gF3vCzS/',
    exampleLabel: 'Use Example Reel',
    icon: InstagramIcon,
    accentBorder: 'focus-within:border-pink-500/80 focus-within:ring-pink-500/20',
    hint: 'Instagram Reels, Video posts, or IGTV links are supported.',
  },
  youtube: {
    name: 'YouTube',
    label: 'YouTube Video or Shorts URL',
    placeholder: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    exampleUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    exampleLabel: 'Use Example Video',
    icon: YouTubeIcon,
    accentBorder: 'focus-within:border-red-500/80 focus-within:ring-red-500/20',
    hint: 'YouTube standard videos, Shorts, and youtu.be links are supported.',
  },
  facebook: {
    name: 'Facebook',
    label: 'Facebook Reel or Video URL',
    placeholder: 'https://www.facebook.com/reel/123456789/',
    exampleUrl: 'https://www.facebook.com/reel/123456789/',
    exampleLabel: 'Use Example Reel',
    icon: FacebookIcon,
    accentBorder: 'focus-within:border-blue-500/80 focus-within:ring-blue-500/20',
    hint: 'Public Facebook Reels, Watch videos, and fb.watch links are supported.',
  },
};

export default function UrlInput({
  url,
  setUrl,
  platform = 'instagram',
  onPlatformChange,
  disabled
}) {
  const config = PLATFORM_CONFIG[platform] || PLATFORM_CONFIG.instagram;
  const PlatformIcon = config.icon;

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        const cleaned = text.trim();
        setUrl(cleaned);
        autoDetectAndPrompt(cleaned);
      }
    } catch (err) {
      console.warn('Clipboard access denied or unsupported', err);
    }
  };

  const handleClear = () => {
    setUrl('');
  };

  // Detect if url matches another platform
  const detectPlatformFromUrl = (val) => {
    if (!val) return null;
    const lower = val.toLowerCase();
    if (lower.includes('youtube.com') || lower.includes('youtu.be')) return 'youtube';
    if (lower.includes('facebook.com') || lower.includes('fb.watch')) return 'facebook';
    if (lower.includes('instagram.com')) return 'instagram';
    return null;
  };

  const detected = detectPlatformFromUrl(url);
  const isMismatch = detected && detected !== platform;

  const autoDetectAndPrompt = (newVal) => {
    const det = detectPlatformFromUrl(newVal);
    if (det && det !== platform && onPlatformChange) {
      // Prompt user or switch
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label htmlFor="media-url-input" className="block text-xs font-bold uppercase tracking-wider text-slate-300">
          Step 2: Enter {config.name} URL
        </label>
        <button
          type="button"
          onClick={() => setUrl(config.exampleUrl)}
          disabled={disabled}
          className="text-xs text-slate-300 hover:text-white transition-colors flex items-center gap-1 font-medium disabled:opacity-50 cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          {config.exampleLabel}
        </button>
      </div>

      <div
        className={`relative rounded-xl border border-slate-700/80 bg-slate-900/90 shadow-inner focus-within:ring-2 transition-all duration-200 ${config.accentBorder}`}
      >
        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
          <PlatformIcon className="w-4 h-4 opacity-75" />
        </div>

        <input
          id="media-url-input"
          type="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
          }}
          disabled={disabled}
          placeholder={config.placeholder}
          className="w-full pl-11 pr-24 py-3.5 bg-transparent text-sm sm:text-base text-slate-100 placeholder-slate-500 focus:outline-none disabled:opacity-50 rounded-xl"
        />

        <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center gap-1">
          {url ? (
            <button
              type="button"
              onClick={handleClear}
              disabled={disabled}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              title="Clear input"
            >
              <X className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handlePaste}
              disabled={disabled}
              className="px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700 rounded-md transition-colors flex items-center gap-1 cursor-pointer"
              title="Paste from clipboard"
            >
              <ClipboardPaste className="w-3.5 h-3.5" />
              Paste
            </button>
          )}
        </div>
      </div>

      {/* Platform Mismatch Assistant Banner */}
      {isMismatch && onPlatformChange && (
        <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between text-xs text-amber-200 animate-in fade-in">
          <div className="flex items-center gap-2">
            <span className="text-base">💡</span>
            <span>
              This link is from <strong className="capitalize text-white">{detected}</strong>.
            </span>
          </div>
          <button
            type="button"
            onClick={() => onPlatformChange(detected)}
            className="px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-100 font-semibold text-[11px] flex items-center gap-1 transition-colors cursor-pointer"
          >
            <ArrowRightLeft className="w-3 h-3" />
            Switch to {detected.charAt(0).toUpperCase() + detected.slice(1)}
          </button>
        </div>
      )}

      {/* Helper text */}
      <p className="text-[11px] text-slate-500 pl-1">
        {config.hint}
      </p>
    </div>
  );
}
