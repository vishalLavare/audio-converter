import React, { useState, useEffect, useRef } from 'react';
import { Music, Sparkles, ShieldCheck, AlertCircle, Video, Layers, Settings } from 'lucide-react';
import PlatformSelector from './components/PlatformSelector';
import UrlInput from './components/UrlInput';
import QualitySelector from './components/QualitySelector';
import Progress from './components/Progress';
import AudioPlayer from './components/AudioPlayer';
import DownloadButton from './components/DownloadButton';
import ServerSettingsModal from './components/ServerSettingsModal';
import { InstagramIcon, YouTubeIcon, FacebookIcon } from './components/BrandIcons';
import { convertMedia, getJobStatus, getDownloadUrl, getVideoDownloadUrl, getFullscreenVideoDownloadUrl } from './api';
import { Capacitor } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { Haptics, ImpactStyle } from '@capacitor/haptics';

const PLATFORM_THEMES = {
  instagram: {
    name: 'Instagram',
    tagline: 'Reel & Video to MP3 / MP4',
    bgMesh: 'bg-mesh-radial-instagram',
    glow1: 'bg-purple-600/15',
    glow2: 'bg-pink-600/15',
    badgeIcon: InstagramIcon,
    badgeColor: 'text-pink-400',
    titleGradient: 'instagram-text-gradient',
    buttonGradient: 'instagram-gradient hover:opacity-95 shadow-pink-500/20',
    buttonLabel: 'Download from Instagram',
  },
  youtube: {
    name: 'YouTube',
    tagline: 'Video & Shorts to MP3 / MP4',
    bgMesh: 'bg-mesh-radial-youtube',
    glow1: 'bg-red-600/15',
    glow2: 'bg-rose-600/15',
    badgeIcon: YouTubeIcon,
    badgeColor: 'text-red-500',
    titleGradient: 'youtube-text-gradient',
    buttonGradient: 'youtube-gradient hover:opacity-95 shadow-red-500/20',
    buttonLabel: 'Download from YouTube',
  },
  facebook: {
    name: 'Facebook',
    tagline: 'Reel & Watch to MP3 / MP4',
    bgMesh: 'bg-mesh-radial-facebook',
    glow1: 'bg-blue-600/15',
    glow2: 'bg-indigo-600/15',
    badgeIcon: FacebookIcon,
    badgeColor: 'text-blue-400',
    titleGradient: 'facebook-text-gradient',
    buttonGradient: 'facebook-gradient hover:opacity-95 shadow-blue-500/20',
    buttonLabel: 'Download from Facebook',
  },
};

export default function App() {
  const [platform, setPlatform] = useState('instagram');
  const [url, setUrl] = useState('');
  const [bitrate, setBitrate] = useState('192k');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [videoMetadata, setVideoMetadata] = useState(null);
  const [videoDownloadUrl, setVideoDownloadUrl] = useState(null);
  const [fullscreenMetadata, setFullscreenMetadata] = useState(null);
  const [fullscreenDownloadUrl, setFullscreenDownloadUrl] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  const pollIntervalRef = useRef(null);

  const theme = PLATFORM_THEMES[platform] || PLATFORM_THEMES.instagram;
  const ActivePlatformIcon = theme.badgeIcon;

  // Initialize mobile status bar
  useEffect(() => {
    if (Capacitor.isNativePlatform()) {
      try {
        StatusBar.setStyle({ style: Style.Dark });
        StatusBar.setBackgroundColor({ color: '#020617' });
      } catch (err) {
        console.warn('StatusBar config error:', err);
      }
    }
  }, []);

  // Poll job status
  useEffect(() => {
    if (!jobId || status === 'completed' || status === 'failed') {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      return;
    }

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId);
        setStatus(data.status);
        setProgress(data.progress || 0);
        setCurrentStep(data.current_step || '');

        if (data.status === 'completed') {
          setMetadata(data.metadata);
          setVideoMetadata(data.video_metadata);
          setFullscreenMetadata(data.fullscreen_metadata);
          setDownloadUrl(data.download_url ? getDownloadUrl(jobId) : null);
          setVideoDownloadUrl(data.video_download_url ? getVideoDownloadUrl(jobId) : null);
          setFullscreenDownloadUrl(data.fullscreen_download_url ? getFullscreenVideoDownloadUrl(jobId) : null);
          setIsProcessing(false);
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        } else if (data.status === 'failed') {
          setError(data.error || 'Conversion failed. Please try again.');
          setIsProcessing(false);
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    pollIntervalRef.current = setInterval(poll, 1200);
    poll();

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [jobId, status]);

  const handlePlatformChange = (newPlatform) => {
    if (isProcessing) return;
    setPlatform(newPlatform);
    setError(null);
  };

  const handleStartConversion = async (e) => {
    e.preventDefault();
    if (!url.trim()) {
      setError(`Please enter a valid public ${theme.name} URL.`);
      return;
    }

    // Reset state
    setError(null);
    setMetadata(null);
    setDownloadUrl(null);
    setVideoMetadata(null);
    setVideoDownloadUrl(null);
    setIsProcessing(true);
    setStatus('validating');
    setProgress(10);
    setCurrentStep(`Submitting ${theme.name} request...`);

    try {
      const response = await convertMedia(url.trim(), bitrate, platform);
      setJobId(response.job_id);
    } catch (err) {
      setIsProcessing(false);
      setStatus('failed');
      setError(err.message || `Unable to start ${theme.name} conversion.`);
    }
  };

  const handleReset = () => {
    setUrl('');
    setJobId(null);
    setStatus(null);
    setProgress(0);
    setCurrentStep('');
    setError(null);
    setMetadata(null);
    setDownloadUrl(null);
    setVideoMetadata(null);
    setVideoDownloadUrl(null);
    setFullscreenMetadata(null);
    setFullscreenDownloadUrl(null);
    setIsProcessing(false);
  };

  return (
    <div className="relative min-h-screen bg-slate-950 flex flex-col justify-between overflow-x-hidden">
      {/* Dynamic Background Gradients */}
      <div className={`fixed inset-0 pointer-events-none transition-all duration-700 ${theme.bgMesh}`} />
      <div className={`fixed -top-40 -right-40 w-96 h-96 rounded-full blur-3xl pointer-events-none transition-colors duration-700 ${theme.glow1}`} />
      <div className={`fixed -bottom-40 -left-40 w-96 h-96 rounded-full blur-3xl pointer-events-none transition-colors duration-700 ${theme.glow2}`} />

      {/* Main Container */}
      <main className="relative z-10 container mx-auto px-4 py-6 sm:py-12 max-w-2xl mobile-safe-top mobile-safe-bottom">
        {/* Top Control Bar with Status & Server Config */}
        <div className="flex items-center justify-between mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs font-semibold text-slate-300 shadow-sm backdrop-blur-md">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden sm:inline">Universal Media Downloader</span>
            <span className="sm:hidden">Downloader</span>
          </div>

          <button
            type="button"
            onClick={async () => {
              if (Capacitor.isNativePlatform()) {
                try { await Haptics.impact({ style: ImpactStyle.Light }); } catch {}
              }
              setShowSettings(true);
            }}
            title="Backend Server Settings"
            className="p-2 px-3 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-all shadow-sm backdrop-blur-md cursor-pointer flex items-center gap-1.5 text-xs"
          >
            <Settings className="w-3.5 h-3.5" />
            <span className="text-[11px] font-medium">Server</span>
          </button>
        </div>

        {/* Header */}
        <header className="text-center mb-8 sm:mb-10">
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-3">
            {theme.name} <span className="text-slate-400 font-light">→</span>{' '}
            <span className={theme.titleGradient}>MP3 & Video</span>
          </h1>
          <p className="text-sm sm:text-base text-slate-400 max-w-md mx-auto">
            Extract high quality MP3 audio and download original MP4 video from public {theme.name} content.
          </p>
        </header>

        {/* Main Glass Card */}
        <div className="glass-panel rounded-3xl p-6 sm:p-8 space-y-6">
          <form onSubmit={handleStartConversion} className="space-y-6">
            {/* Step 1: Select Platform */}
            <PlatformSelector
              selectedPlatform={platform}
              onSelectPlatform={handlePlatformChange}
              disabled={isProcessing}
            />

            {/* Step 2: Media URL Input */}
            <UrlInput
              url={url}
              setUrl={setUrl}
              platform={platform}
              onPlatformChange={handlePlatformChange}
              disabled={isProcessing}
            />

            {/* Step 3: Quality Selector */}
            <QualitySelector
              bitrate={bitrate}
              setBitrate={setBitrate}
              platform={platform}
              disabled={isProcessing}
            />

            {/* Step 4: Submit Button */}
            {!isProcessing && status !== 'completed' && (
              <button
                type="submit"
                id="convert-submit-button"
                className={`w-full py-3.5 px-6 rounded-xl font-bold text-white text-base shadow-xl transition-all transform active:scale-[0.99] flex items-center justify-center gap-2 group cursor-pointer ${theme.buttonGradient}`}
              >
                <ActivePlatformIcon className="w-5 h-5 group-hover:scale-110 transition-transform" />
                <span>{theme.buttonLabel}</span>
              </button>
            )}
          </form>

          {/* Processing and Progress Section */}
          {status && status !== 'completed' && (
            <Progress
              status={status}
              progress={progress}
              currentStep={currentStep}
              error={error}
              platform={platform}
            />
          )}

          {/* Completed Section: Audio / Video Player & Download */}
          {status === 'completed' && (downloadUrl || videoDownloadUrl) && (
            <div className="space-y-6 pt-2 animate-in fade-in duration-300">
              {/* Audio / Video Preview Player */}
              <AudioPlayer
                audioUrl={downloadUrl}
                videoUrl={fullscreenDownloadUrl || videoDownloadUrl}
                originalVideoUrl={videoDownloadUrl}
                fullscreenVideoUrl={fullscreenDownloadUrl}
                duration={metadata?.duration}
              />

              {/* Download & File Details */}
              <DownloadButton
                downloadUrl={downloadUrl}
                videoDownloadUrl={videoDownloadUrl}
                fullscreenDownloadUrl={fullscreenDownloadUrl}
                metadata={metadata}
                videoMetadata={videoMetadata}
                fullscreenMetadata={fullscreenMetadata}
                platform={platform}
                onReset={handleReset}
              />
            </div>
          )}

          {/* Error Alert if failed before/outside progress card */}
          {error && status !== 'failed' && (
            <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-sm text-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}
        </div>

        {/* Legal & Compliance Notice */}
        <aside className="mt-8 p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80 text-xs text-slate-400 space-y-1.5 backdrop-blur-sm">
          <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Authorized Public Media Processing</span>
          </div>
          <p className="leading-relaxed">
            This utility processes publicly available Instagram Reels, YouTube videos/Shorts, and Facebook Reels that you are authorized to download and convert.
            Private accounts, copyright protections, paywalls, and authentication bypasses are strictly not supported.
          </p>
        </aside>

        {/* Mobile / Web Server Configuration Modal */}
        <ServerSettingsModal
          isOpen={showSettings}
          onClose={() => setShowSettings(false)}
        />
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-800/60 py-6 text-center text-xs text-slate-500">
        <p>Instagram &bull; YouTube &bull; Facebook Media Downloader &bull; Built with FastAPI, FFmpeg & React</p>
      </footer>
    </div>
  );
}
