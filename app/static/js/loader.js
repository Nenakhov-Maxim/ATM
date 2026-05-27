// ver
(function() {
  if (window.__appLoaderInitialized) {
    return;
  }
  window.__appLoaderInitialized = true;

  let activeRequests = 0;
  let loaderElement = null;
  let styleElement = null;
  let hideTimer = null;
  let visibleAt = null;
  const MIN_VISIBLE_MS = 300;

  function ensureLoader() {
    if (!document.body) {
      return;
    }

    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = 'app-global-loader-style';
      styleElement.textContent = `
        .app-global-loader {
          position: fixed;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.68);
          backdrop-filter: blur(3px);
          opacity: 0;
          visibility: hidden;
          pointer-events: none;
          transition: opacity 0.18s ease, visibility 0.18s ease;
          z-index: 99999;
        }

        .app-global-loader--visible {
          opacity: 1;
          visibility: visible;
          pointer-events: auto;
        }

        .app-global-loader__panel {
          min-width: 180px;
          padding: 18px 22px;
          border-radius: 14px;
          background: rgba(255, 255, 255, 0.96);
          box-shadow: 0 14px 40px rgba(20, 41, 68, 0.18);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          font-family: inherit;
        }

        .app-global-loader__spinner {
          width: 38px;
          height: 38px;
          border: 4px solid rgba(22, 119, 255, 0.18);
          border-top-color: #1677ff;
          border-radius: 50%;
          animation: app-global-loader-spin 0.9s linear infinite;
        }

        .app-global-loader__text {
          color: #23344d;
          font-size: 15px;
          font-weight: 600;
          letter-spacing: 0.02em;
        }

        body.app-global-loader-lock {
          cursor: progress;
        }

        @keyframes app-global-loader-spin {
          from {
            transform: rotate(0deg);
          }

          to {
            transform: rotate(360deg);
          }
        }
      `;
      document.head.appendChild(styleElement);
    }

    if (!loaderElement) {
      loaderElement = document.createElement('div');
      loaderElement.className = 'app-global-loader';
      loaderElement.setAttribute('aria-hidden', 'true');
      loaderElement.innerHTML = `
        <div class="app-global-loader__panel" role="status" aria-live="polite">
          <div class="app-global-loader__spinner"></div>
          <div class="app-global-loader__text">Загрузка...</div>
        </div>
      `;
      document.body.appendChild(loaderElement);
    }
  }

  function syncLoaderState() {
    ensureLoader();
    if (!loaderElement || !document.body) {
      return;
    }

    const shouldShow = activeRequests > 0 || hideTimer !== null;
    loaderElement.classList.toggle('app-global-loader--visible', shouldShow);
    loaderElement.setAttribute('aria-hidden', shouldShow ? 'false' : 'true');
    document.body.classList.toggle('app-global-loader-lock', shouldShow);
  }

  function showLoader() {
    if (hideTimer !== null) {
      window.clearTimeout(hideTimer);
      hideTimer = null;
    }

    if (activeRequests === 0) {
      visibleAt = Date.now();
    }

    activeRequests += 1;
    syncLoaderState();
  }

  function hideLoader() {
    activeRequests = Math.max(0, activeRequests - 1);

    if (activeRequests > 0) {
      syncLoaderState();
      return;
    }

    const elapsed = visibleAt ? Date.now() - visibleAt : MIN_VISIBLE_MS;
    const remaining = Math.max(0, MIN_VISIBLE_MS - elapsed);

    if (remaining === 0) {
      visibleAt = null;
      syncLoaderState();
      return;
    }

    if (hideTimer !== null) {
      window.clearTimeout(hideTimer);
    }

    hideTimer = window.setTimeout(function() {
      hideTimer = null;
      visibleAt = null;
      syncLoaderState();
    }, remaining);

    syncLoaderState();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncLoaderState, { once: true });
  } else {
    ensureLoader();
  }

  window.appLoader = {
    show: showLoader,
    hide: hideLoader,
    reset: function() {
      activeRequests = 0;
      visibleAt = null;
      if (hideTimer !== null) {
        window.clearTimeout(hideTimer);
        hideTimer = null;
      }
      syncLoaderState();
    },
    getActiveRequests: function() {
      return activeRequests;
    }
  };

  if (typeof window.fetch === 'function' && !window.fetch.__appLoaderWrapped) {
    const nativeFetch = window.fetch.bind(window);
    const wrappedFetch = function(resource, init) {
      if (init && init.skipLoader) {
        return nativeFetch(resource, init);
      }

      showLoader();
      return nativeFetch(resource, init).then(
        function(response) {
          hideLoader();
          return response;
        },
        function(error) {
          hideLoader();
          throw error;
        }
      );
    };

    wrappedFetch.__appLoaderWrapped = true;
    window.fetch = wrappedFetch;
  }

  if (window.XMLHttpRequest && !window.XMLHttpRequest.__appLoaderWrapped) {
    const originalSend = window.XMLHttpRequest.prototype.send;

    window.XMLHttpRequest.prototype.send = function() {
      if (this.__skipLoader) {
        return originalSend.apply(this, arguments);
      }

      showLoader();

      this.addEventListener('loadend', hideLoader, { once: true });

      try {
        return originalSend.apply(this, arguments);
      } catch (error) {
        hideLoader();
        throw error;
      }
    };

    window.XMLHttpRequest.__appLoaderWrapped = true;
  }
})();
