import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

window.addEventListener('error', (event) => {
  console.error('Global Error caught:', event.error || event.message);
  const root = document.getElementById('root');
  if (root && (!root.children || root.children.length === 0)) {
    root.innerHTML = `
      <div style="padding: 24px; color: #f87171; font-family: sans-serif; background: #0f172a; min-height: 100vh;">
        <h2 style="font-size: 1.25rem; font-weight: bold; margin-bottom: 8px; color: #fff;">Application Startup Issue</h2>
        <p style="font-size: 0.875rem; margin-bottom: 12px; color: #94a3b8;">An error prevented the app from loading:</p>
        <pre style="background: #1e293b; padding: 12px; border-radius: 8px; font-size: 0.75rem; white-space: pre-wrap; word-break: break-all;">${event.message || event.error}</pre>
        <button onclick="window.location.reload()" style="margin-top: 16px; padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">Reload App</button>
      </div>
    `;
  }
});

try {
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} catch (err) {
  console.error('Root render failed:', err);
  const root = document.getElementById('root');
  if (root) {
    root.innerHTML = `<div style="padding: 24px; color: white; font-family: sans-serif;">Render Error: ${err.message}</div>`;
  }
}
