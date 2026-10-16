import axios from 'axios';
import { Capacitor } from '@capacitor/core';

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
  if (Capacitor.isNativePlatform()) {
    // Default fallback for Android Emulator / local network dev
    return 'http://10.0.2.2:8000/api';
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
  const target = (url && url.trim()) ? url.trim().replace(/\/+$/, '') : getBaseUrl().replace(/\/api$/, '');
  const testEndpoint = target.endsWith('/api') ? `${target.replace(/\/api$/, '')}/health` : `${target}/health`;
  try {
    const res = await axios.get(testEndpoint, { timeout: 6000 });
    return { ok: true, data: res.data };
  } catch (err) {
    // Also try testing root /docs or /api directly
    try {
      const res = await axios.get(`${target}/docs`, { timeout: 6000 });
      return { ok: true, data: 'Connected' };
    } catch {
      throw new Error(err.response?.data?.detail || err.message || 'Could not connect to server');
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
