import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Gracefully ignore orientation lock errors coming from embedded viewers on devices that don't support it
const shouldIgnoreOrientationError = (reasonOrMessage) => {
  try {
    const text = (() => {
      if (typeof reasonOrMessage === 'string') return reasonOrMessage;
      if (!reasonOrMessage) return '';
      if (reasonOrMessage.message) return String(reasonOrMessage.message);
      return String(reasonOrMessage);
    })().toLowerCase();

    return text.includes('screen.orientation.lock') ||
           text.includes('orientation.lock') ||
           text.includes('is not available on this device');
  } catch (_) {
    return false;
  }
};

// Install capture-phase handlers BEFORE React renders so dev overlay doesn't pick them up
window.addEventListener('error', (event) => {
  if (shouldIgnoreOrientationError(event.error || event.message)) {
    event.preventDefault();
    // do not call console.error to avoid triggering overlay
    return;
  }
}, { capture: true });

window.addEventListener('unhandledrejection', (event) => {
  if (shouldIgnoreOrientationError(event.reason)) {
    event.preventDefault();
    return;
  }
}, { capture: true });

// Filter console.error to prevent overlay from showing for these specific messages in dev
(() => {
  const originalError = console.error;
  console.error = function (...args) {
    if (args.some(arg => shouldIgnoreOrientationError(arg))) {
      // swallow this specific message
      return;
    }
    return originalError.apply(console, args);
  };
})();

// Install a safe shim for screen.orientation.lock so it never rejects
(() => {
  try {
    const scr = window.screen;
    if (!scr) return;
    const ori = scr.orientation;
    const resolved = Promise.resolve();

    const makeSafeLock = (original) => function safeLock(...args) {
      try {
        const res = typeof original === 'function' ? original.apply(this, args) : resolved;
        if (res && typeof res.then === 'function') {
          return res.catch(() => resolved);
        }
        return resolved;
      } catch (_) {
        return resolved;
      }
    };

    if (ori) {
      if (typeof ori.lock === 'function') {
        try { ori.lock = makeSafeLock(ori.lock); } catch (_) { /* non-writable */ }
      } else {
        try { Object.defineProperty(ori, 'lock', { value: makeSafeLock(null), configurable: true }); } catch (_) {}
      }
      if (typeof ori.unlock !== 'function') {
        try { Object.defineProperty(ori, 'unlock', { value: () => {}, configurable: true }); } catch (_) {}
      }
    } else {
      try {
        Object.defineProperty(scr, 'orientation', {
          value: { lock: makeSafeLock(null), unlock: () => {}, type: 'landscape-primary', angle: 0 },
          configurable: true,
        });
      } catch (_) {}
    }
  } catch (_) {
    // ignore
  }
})();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
// Note: we intentionally do not log ignored errors to avoid triggering the dev overlay
// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
