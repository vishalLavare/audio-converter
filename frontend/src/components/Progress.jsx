import React from 'react';
import { CheckCircle2, Loader2, AlertCircle, Radio } from 'lucide-react';

const STEPS = [
  { key: 'validating', label: 'Validating URL' },
  { key: 'getting_media', label: 'Connecting to source' },
  { key: 'downloading', label: 'Downloading video' },
  { key: 'extracting', label: 'Extracting audio' },
  { key: 'converting', label: 'Converting to MP3' },
  { key: 'completed', label: 'Completed' },
];

const PLATFORM_PROGRESS_GRADIENTS = {
  instagram: 'instagram-gradient',
  youtube: 'bg-gradient-to-r from-red-600 via-rose-500 to-amber-500',
  facebook: 'bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400',
};

const PLATFORM_SPINNER_COLORS = {
  instagram: 'text-pink-500',
  youtube: 'text-red-500',
  facebook: 'text-blue-500',
};

export default function Progress({ status, progress, currentStep, error, platform = 'instagram' }) {
  const getStepIndex = () => {
    if (status === 'completed') return 5;
    if (status === 'failed') return -1;
    if (progress < 25) return 0; // Validating
    if (progress < 40) return 1; // Connecting
    if (progress < 60) return 2; // Downloading video
    if (progress < 80) return 3; // Extracting audio
    if (progress < 100) return 4; // Converting to MP3
    return 5;
  };

  const currentStepIdx = getStepIndex();
  const platformName = platform.charAt(0).toUpperCase() + platform.slice(1);
  const progressBarGradient = PLATFORM_PROGRESS_GRADIENTS[platform] || PLATFORM_PROGRESS_GRADIENTS.instagram;
  const spinnerColor = PLATFORM_SPINNER_COLORS[platform] || PLATFORM_SPINNER_COLORS.instagram;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {status === 'failed' ? (
            <AlertCircle className="w-5 h-5 text-red-400" />
          ) : status === 'completed' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <Loader2 className={`w-5 h-5 ${spinnerColor} animate-spin`} />
          )}
          <span className="font-semibold text-sm text-slate-100">
            {status === 'failed'
              ? 'Conversion Failed'
              : status === 'completed'
              ? 'Conversion Complete'
              : `Processing ${platformName} Media...`}
          </span>
        </div>
        <span className="text-sm font-mono font-bold text-slate-200">
          {status === 'failed' ? 'Error' : `${progress}%`}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ease-out rounded-full ${
            status === 'failed'
              ? 'bg-red-500'
              : status === 'completed'
              ? 'bg-emerald-500'
              : progressBarGradient
          }`}
          style={{ width: `${status === 'failed' ? 100 : progress}%` }}
        />
      </div>

      {/* Active step description */}
      <div className="text-xs text-slate-400 font-mono flex items-center justify-between">
        <span className="truncate pr-2">{currentStep || 'Initializing...'}</span>
        {status !== 'completed' && status !== 'failed' && (
          <span className="flex items-center gap-1 text-[11px] text-amber-400 shrink-0">
            <Radio className="w-3 h-3 animate-pulse text-emerald-400" /> Live
          </span>
        )}
      </div>

      {/* Step Indicators Checklist */}
      <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-3 gap-2">
        {STEPS.map((step, idx) => {
          const isDone = status === 'completed' || currentStepIdx > idx;
          const isCurrent = status !== 'completed' && status !== 'failed' && currentStepIdx === idx;

          return (
            <div
              key={step.key}
              className={`flex items-center gap-2 p-2 rounded-lg text-xs transition-colors ${
                isDone
                  ? 'bg-emerald-950/20 text-emerald-300 border border-emerald-900/30'
                  : isCurrent
                  ? 'bg-slate-800/80 text-slate-200 border border-slate-700 ring-1 ring-slate-500/30'
                  : 'bg-slate-900/40 text-slate-500 border border-slate-800/40'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className={`w-3.5 h-3.5 ${spinnerColor} animate-spin shrink-0`} />
              ) : (
                <div className="w-3.5 h-3.5 rounded-full border border-slate-700 shrink-0" />
              )}
              <span className="truncate">{step.label}</span>
            </div>
          );
        })}
      </div>

      {/* Error alert if failed */}
      {status === 'failed' && error && (
        <div className="p-3 bg-red-950/50 border border-red-800/60 rounded-xl text-xs text-red-200 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}
    </div>
  );
}
