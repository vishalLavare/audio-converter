import axios from 'axios';
import { Capacitor } from '@capacitor/core';

export const DEFAULT_CLOUD_BACKEND = 'https://audio-converter-7v1g.onrender.com';

export const getBaseUrl = () => {
  const customUrl = localStorage.getItem('audio_converter_api_url');
  if (customUrl && customUrl.trim()) {
    const trimmed = customUrl.trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
  }
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.trim()) {
    const trimmed = envUrl.trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
  }
  // Mobile APK (Capacitor) or GitHub Pages live deployment -> use cloud backend
  if (Capacitor.isNativePlatform()) {
    return `${DEFAULT_CLOUD_BACKEND}/api`;
  }
  if (typeof window !== 'undefined' && window.location && (window.location.hostname.includes('github.io') || (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'))) {
    return `${DEFAULT_CLOUD_BACKEND}/api`;
  }
  return '/api';
};

export const setCustomServerUrl = (url) => {
  if (!url || !url.trim()) {
    localStorage.removeItem('audio_converter_api_url');
  } else {
    let clean = url.trim().replace(/\/+$/, '');
    if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
      clean = 'http://' + clean;
    }
    localStorage.setItem('audio_converter_api_url', clean);
  }
};

export const getSavedServerUrl = () => {
  return localStorage.getItem('audio_converter_api_url') || '';
};

export const testServerConnection = async (url) => {
  const raw = (url && url.trim()) ? url.trim().replace(/\/+$/, '') : getBaseUrl().replace(/\/api$/, '');
  const cleanTarget = raw.endsWith('/api') ? raw.replace(/\/api$/, '') : raw;
  
  // Try 1: /api/health
  try {
    const res = await axios.get(`${cleanTarget}/api/health`, { timeout: 8000 });
    return { ok: true, data: res.data };
  } catch (err1) {
    // Try 2: /health
    try {
      const res = await axios.get(`${cleanTarget}/health`, { timeout: 8000 });
      return { ok: true, data: res.data };
    } catch (err2) {
      // Try 3: / or /docs
      try {
        const res = await axios.get(`${cleanTarget}/docs`, { timeout: 8000 });
        return { ok: true, data: 'Connected' };
      } catch {
        throw new Error(err1.response?.data?.detail || err1.message || 'Could not connect to server');
      }
    }
  }
};

const api = axios.create({
  timeout: 45000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to always use current base URL
api.interceptors.request.use((config) => {
  config.baseURL = getBaseUrl();
  return config;
});

export const convertMedia = async (url, bitrate = '192k', platform = 'auto') => {
  try {
    const response = await api.post('/reel/convert', { url, bitrate, platform });
    return response.data;
  } catch (error) {
    if (error.response && error.response.data && error.response.data.error) {
      throw new Error(error.response.data.error);
    }
    throw new Error(error.message || 'Unable to connect to converter service.');
  }
};

export const convertReel = async (url, bitrate = '192k', platform = 'instagram') => {
  return convertMedia(url, bitrate, platform);
};

export const getJobStatus = async (jobId) => {
  try {
    const response = await api.get(`/reel/status/${jobId}`);
    return response.data;
  } catch (error) {
    if (error.response && error.response.data && error.response.data.error) {
      throw new Error(error.response.data.error);
    }
    throw new Error(error.message || 'Error checking conversion status.');
  }
};

export const getDownloadUrl = (jobId) => {
  return `${getBaseUrl()}/reel/download/${jobId}`;
};

export const getVideoDownloadUrl = (jobId) => {
  return `${getBaseUrl()}/reel/download-video/${jobId}`;
};

export const getFullscreenVideoDownloadUrl = (jobId) => {
  return `${getBaseUrl()}/reel/download-video-fullscreen/${jobId}`;
};

export default api;
