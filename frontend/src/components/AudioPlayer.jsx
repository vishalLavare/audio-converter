import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, RotateCcw, Music, Video, Maximize, Minimize, Crop, Monitor } from 'lucide-react';

export default function AudioPlayer({ audioUrl, videoUrl, originalVideoUrl, fullscreenVideoUrl, duration }) {
  const audioRef = useRef(null);
  const videoRef = useRef(null);
  const videoContainerRef = useRef(null);

  const initialVideo = fullscreenVideoUrl || videoUrl || originalVideoUrl;
  const [activeVideoSrc, setActiveVideoSrc] = useState(initialVideo);
  const [viewMode, setViewMode] = useState(videoUrl || fullscreenVideoUrl ? 'video' : 'audio'); // 'audio' or 'video'
  const [fitMode, setFitMode] = useState('contain'); // 'contain' (Fit) or 'cover' (Fill/Zoom to crop black bars)
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    setActiveVideoSrc(fullscreenVideoUrl || videoUrl || originalVideoUrl);
  }, [fullscreenVideoUrl, videoUrl, originalVideoUrl]);

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  const toggleFullscreen = () => {
    if (!videoContainerRef.current) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    } else {
      videoContainerRef.current.requestFullscreen().catch(() => {});
    }
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        setTotalDuration(audio.duration);
      }
    };
    const onEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', onEnded);

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', onEnded);
    };
  }, [audioUrl]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch(err => {
        console.error("Playback failed:", err);
      });
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    audioRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleSeek = (e) => {
    const newTime = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds) || seconds < 0) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const handleSwitchTab = (tab) => {
    if (tab === 'video' && audioRef.current && isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else if (tab === 'audio' && videoRef.current && !videoRef.current.paused) {
      videoRef.current.pause();
    }
    setViewMode(tab);
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-lg backdrop-blur-md space-y-3">
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Mode switcher if videoUrl is available */}
      {(videoUrl || fullscreenVideoUrl) && (
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800">
          <div className="flex bg-slate-950/80 p-0.5 rounded-lg border border-slate-800/80 text-xs">
            <button
              type="button"
              onClick={() => handleSwitchTab('video')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                viewMode === 'video'
                  ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Video className="w-3.5 h-3.5" />
              <span>Video Preview</span>
            </button>
            <button
              type="button"
              onClick={() => handleSwitchTab('audio')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                viewMode === 'audio'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Music className="w-3.5 h-3.5" />
              <span>Audio Preview</span>
            </button>
          </div>

          {/* Video Options: Format Switcher & Fit/Fill Toggle */}
          {viewMode === 'video' && (
            <div className="flex items-center gap-2">
              {fullscreenVideoUrl && originalVideoUrl && (
                <div className="flex bg-slate-950/80 p-0.5 rounded-lg border border-slate-800 text-[11px]">
                  <button
                    type="button"
                    onClick={() => setActiveVideoSrc(fullscreenVideoUrl)}
                    className={`px-2 py-1 rounded font-medium transition-all ${
                      activeVideoSrc === fullscreenVideoUrl
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                    title="Play 16:9 widescreen video without black borders"
                  >
                    16:9 Full Screen
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveVideoSrc(originalVideoUrl)}
                    className={`px-2 py-1 rounded font-medium transition-all ${
                      activeVideoSrc === originalVideoUrl
                        ? 'bg-purple-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                    title="Play original 9:16 portrait format"
                  >
                    Original
                  </button>
                </div>
              )}

              {/* Fit / Fill toggle */}
              <button
                type="button"
                onClick={() => setFitMode(fitMode === 'contain' ? 'cover' : 'contain')}
                className={`flex items-center gap-1 px-2 py-1 rounded-lg border text-xs font-medium transition-all ${
                  fitMode === 'cover'
                    ? 'bg-indigo-600/30 border-indigo-500/50 text-indigo-300'
                    : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
                title="Fill screen to zoom past black borders"
              >
                <Crop className="w-3 h-3" />
                <span>{fitMode === 'cover' ? 'Fill (Zoomed)' : 'Fit (Original)'}</span>
              </button>

              {/* Fullscreen toggle button */}
              <button
                type="button"
                onClick={toggleFullscreen}
                className="p-1.5 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                title="Toggle Fullscreen"
              >
                {isFullscreen ? <Minimize className="w-3.5 h-3.5" /> : <Maximize className="w-3.5 h-3.5" />}
              </button>
            </div>
          )}

          <span className="text-xs font-mono text-slate-400">
            {duration || formatTime(totalDuration)}
          </span>
        </div>
      )}

      {/* Video Preview Tab */}
      {viewMode === 'video' && activeVideoSrc ? (
        <div
          ref={videoContainerRef}
          className={`relative rounded-xl overflow-hidden bg-black flex items-center justify-center border border-slate-800/80 transition-all ${
            isFullscreen ? 'w-screen h-screen border-none rounded-none' : 'w-full h-80'
          }`}
        >
          <video
            ref={videoRef}
            src={activeVideoSrc}
            controls
            playsInline
            className={`w-full h-full transition-all ${
              fitMode === 'cover' ? 'object-cover' : 'object-contain'
            }`}
          />
        </div>
      ) : (
        /* Audio Preview Tab */
        <div className="flex flex-col gap-3">
          {/* Top bar with audio visualizer waveform mock & duration */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-pink-400">
                Audio Waveform
              </span>
              {isPlaying && (
                <div className="flex items-center gap-0.5 h-3">
                  <span className="w-1 bg-pink-500 rounded-full animate-pulse h-full" />
                  <span className="w-1 bg-purple-500 rounded-full animate-bounce h-2" />
                  <span className="w-1 bg-amber-500 rounded-full animate-pulse h-3" />
                  <span className="w-1 bg-pink-400 rounded-full animate-bounce h-1.5" />
                </div>
              )}
            </div>
            {!videoUrl && (
              <span className="text-xs font-mono text-slate-400">
                {formatTime(currentTime)} / {duration || formatTime(totalDuration)}
              </span>
            )}
          </div>

        {/* Scrub bar */}
        <div className="relative flex items-center">
          <input
            type="range"
            min="0"
            max={totalDuration || 100}
            step="0.1"
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-pink-500"
          />
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={togglePlay}
              className="p-3 bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white rounded-full shadow-md shadow-pink-500/20 transition-transform active:scale-95 flex items-center justify-center"
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause className="w-4 h-4 fill-white" /> : <Play className="w-4 h-4 fill-white ml-0.5" />}
            </button>

            <button
              type="button"
              onClick={() => {
                if (audioRef.current) {
                  audioRef.current.currentTime = 0;
                  setCurrentTime(0);
                }
              }}
              className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
              title="Restart"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleMute}
              className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? <VolumeX className="w-4 h-4 text-red-400" /> : <Volume2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
      )}
    </div>
  );
}
