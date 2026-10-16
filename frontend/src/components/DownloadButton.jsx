import React, { useState } from 'react';
import { Download, Music, Video, Clock, HardDrive, CheckCircle2, Share2, Loader2 } from 'lucide-react';
import { InstagramIcon, YouTubeIcon, FacebookIcon } from './BrandIcons';
import { Capacitor } from '@capacitor/core';
import { Share } from '@capacitor/share';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Haptics, ImpactStyle } from '@capacitor/haptics';

const PLATFORM_ICONS = {
  instagram: InstagramIcon,
  youtube: YouTubeIcon,
  facebook: FacebookIcon,
};

const PLATFORM_DOWNLOAD_STYLES = {
  instagram: 'instagram-gradient shadow-pink-500/20',
  youtube: 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-red-500/20',
  facebook: 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-blue-500/20',
};

export default function DownloadButton({
  downloadUrl,
  videoDownloadUrl,
  fullscreenDownloadUrl,
  metadata,
  videoMetadata,
  fullscreenMetadata,
  platform = 'instagram',
  onReset
}) {
  const [downloadingType, setDownloadingType] = useState(null); // 'mp3' | 'video' | 'fullscreen'
  const isNative = Capacitor.isNativePlatform();

  const triggerHaptic = async () => {
    try {
      if (isNative) {
        await Haptics.impact({ style: ImpactStyle.Medium });
      }
    } catch {
      // Haptics optional fallback
    }
  };

  const handleNativeDownloadOrShare = async (url, filename, type) => {
    await triggerHaptic();
    if (!isNative) return; // Fall back to default <a> tag behavior

    setDownloadingType(type);
    try {
      // Fetch the binary data
      const response = await fetch(url);
      const blob = await response.blob();

      // Convert blob to base64
      const reader = new FileReader();
      const base64Data = await new Promise((resolve, reject) => {
        reader.onloadend = () => {
          const res = reader.result;
          const base64 = res.split(',')[1];
          resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });

      // Save to device Cache or Documents
      const savedFile = await Filesystem.writeFile({
        path: filename,
        data: base64Data,
        directory: Directory.Cache,
      });

      // Open native Share Sheet so user can Save to Files, WhatsApp, etc.
      await Share.share({
        title: filename,
        text: `Exported from Audio & Video Converter`,
        url: savedFile.uri,
        dialogTitle: `Save or Share ${filename}`,
      });
    } catch (err) {
      console.warn('Native save/share fallback:', err);
      // Fallback: window.open
      window.open(url, '_blank');
    } finally {
      setDownloadingType(null);
    }
  };

  const currentPlatform = metadata?.platform || videoMetadata?.platform || platform || 'instagram';
  const platformName = currentPlatform.charAt(0).toUpperCase() + currentPlatform.slice(1);
  const PlatformIcon = PLATFORM_ICONS[currentPlatform] || InstagramIcon;

  const title = metadata?.title || videoMetadata?.title;
  const audioFilename = metadata?.filename || `${currentPlatform}_audio.mp3`;
  const videoFilename = videoMetadata?.filename || `${currentPlatform}_video.mp4`;
  const fullscreenFilename = fullscreenMetadata?.filename || `${currentPlatform}_fullscreen.mp4`;
  const duration = metadata?.duration || '00:00';
  const bitrate = metadata?.bitrate || '192 kbps';
  const audioFileSize = metadata?.file_size || 'N/A';
  const videoFileSize = videoMetadata?.file_size || 'N/A';
  const fullscreenFileSize = fullscreenMetadata?.file_size || 'N/A';

  const videoBtnGradient = PLATFORM_DOWNLOAD_STYLES[currentPlatform] || PLATFORM_DOWNLOAD_STYLES.instagram;

  return (
    <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/10 p-5 space-y-4 backdrop-blur-md">
      {/* Success banner */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span className="font-bold text-sm text-emerald-300">
            {platformName} Media Ready
          </span>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/80 text-xs text-slate-300">
          <PlatformIcon className="w-3.5 h-3.5" />
          <span className="capitalize">{currentPlatform}</span>
        </div>
      </div>

      {/* Media Title if available */}
      {title && (
        <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800 text-xs text-slate-200 font-medium truncate">
          <span className="text-slate-500 text-[10px] uppercase tracking-wider block mb-0.5">Title</span>
          <span className="truncate block" title={title}>{title}</span>
        </div>
      )}

      {/* Metadata card */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          <Music className="w-4 h-4 text-emerald-400 shrink-0" />
          <div className="truncate">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Audio</div>
            <div className="font-medium text-slate-200 truncate" title={audioFilename}>
              {bitrate} MP3
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Video className="w-4 h-4 text-purple-400 shrink-0" />
          <div className="truncate">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Video</div>
            <div className="font-medium text-slate-200 truncate" title={videoFilename}>
              MP4 Video
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400 shrink-0" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Duration</div>
            <div className="font-medium text-slate-200">{duration}</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-amber-400 shrink-0" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Sizes</div>
            <div className="font-medium text-slate-200">
              {audioFileSize} <span className="text-slate-500">/</span> {videoFileSize}
            </div>
          </div>
        </div>
      </div>

      {/* Download action buttons */}
      <div className="flex flex-col gap-3 pt-1">
        {/* Full Screen Cropped Video if available */}
        {fullscreenDownloadUrl && (
          <a
            href={fullscreenDownloadUrl}
            download={fullscreenFilename}
            onClick={(e) => {
              if (isNative) {
                e.preventDefault();
                handleNativeDownloadOrShare(fullscreenDownloadUrl, fullscreenFilename, 'fullscreen');
              } else {
                triggerHaptic();
              }
            }}
            id="download-fullscreen-video-button"
            className="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] text-sm text-center cursor-pointer border border-indigo-400/30"
          >
            {downloadingType === 'fullscreen' ? (
              <Loader2 className="w-4 h-4 animate-spin text-cyan-300" />
            ) : (
              <Video className="w-4 h-4 text-cyan-300" />
            )}
            <span>
              {downloadingType === 'fullscreen'
                ? 'Preparing Download...'
                : isNative
                ? 'Save / Share 16:9 Video'
                : 'Download 16:9 Full Screen Video (No Black Bars)'}
            </span>
            <span className="text-[11px] font-normal opacity-90 px-1.5 py-0.5 rounded bg-black/30">
              {fullscreenFileSize}
            </span>
          </a>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          {/* Download MP3 */}
          {downloadUrl && (
            <a
              href={downloadUrl}
              download={audioFilename}
              onClick={(e) => {
                if (isNative) {
                  e.preventDefault();
                  handleNativeDownloadOrShare(downloadUrl, audioFilename, 'mp3');
                } else {
                  triggerHaptic();
                }
              }}
              id="download-mp3-button"
              className="flex-1 py-3 px-4 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] text-sm text-center cursor-pointer"
            >
              {downloadingType === 'mp3' ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : isNative ? (
                <Share2 className="w-4 h-4" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              <span>
                {downloadingType === 'mp3'
                  ? 'Saving...'
                  : isNative
                  ? 'Save / Share MP3'
                  : 'Download MP3'}
              </span>
              <span className="text-[11px] font-normal opacity-85">({audioFileSize})</span>
            </a>
          )}

          {/* Download Original Video */}
          {videoDownloadUrl && (
            <a
              href={videoDownloadUrl}
              download={videoFilename}
              onClick={(e) => {
                if (isNative) {
                  e.preventDefault();
                  handleNativeDownloadOrShare(videoDownloadUrl, videoFilename, 'video');
                } else {
                  triggerHaptic();
                }
              }}
              id="download-video-button"
              className={`flex-1 py-3 px-4 text-white font-bold rounded-xl shadow-lg flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] text-sm text-center cursor-pointer ${videoBtnGradient}`}
            >
              {downloadingType === 'video' ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : isNative ? (
                <Share2 className="w-4 h-4" />
              ) : (
                <Video className="w-4 h-4" />
              )}
              <span>
                {downloadingType === 'video'
                  ? 'Saving...'
                  : isNative
                  ? (fullscreenDownloadUrl ? 'Save Original (9:16)' : 'Save / Share MP4')
                  : (fullscreenDownloadUrl ? 'Original Video (9:16)' : 'Download MP4')}
              </span>
              <span className="text-[11px] font-normal opacity-85">({videoFileSize})</span>
            </a>
          )}
        </div>
      </div>

      {/* Reset button */}
      <div className="pt-1 flex justify-center">
        <button
          type="button"
          onClick={onReset}
          className="w-full py-2.5 px-4 rounded-xl border border-slate-700/80 hover:border-slate-600 bg-slate-900/60 hover:bg-slate-800 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
        >
          Convert Another Link
        </button>
      </div>
    </div>
  );
}
