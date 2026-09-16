(() => {
  if (window.__veluneContentBridge) return;
  window.__veluneContentBridge = true;
  console.log('[Velune] Content bridge started on', location.hostname);
  let previous = '';
  let mainWorldUpdate = 0;
  function send(track) {
    const key = JSON.stringify(track);
    if (key === previous) return;
    previous = key;
    console.log('[Velune] Detected:', track.artist, track.title);
    chrome.runtime.sendMessage({type: 'velune-track', track});
  }
  window.addEventListener('velune-browser-track', event => {
    mainWorldUpdate = Date.now();
    if (event.detail?.source === 'browser:vk.com') send(event.detail);
  });
  setInterval(() => {
    if (Date.now() - mainWorldUpdate < 3000) return;
    const metadata = navigator.mediaSession?.metadata;
    const node = [...document.querySelectorAll('audio,video')].find(item => !item.paused && !item.ended);
    if (!metadata?.title) return;
    const artwork = metadata.artwork;
    send({source: `browser:${location.hostname}`, title: metadata.title || '',
      artist: metadata.artist || '', album: metadata.album || '',
      cover: artwork?.length ? artwork[artwork.length - 1].src : '',
      position: node?.currentTime || 0, duration: Number.isFinite(node?.duration) ? node.duration : 0,
      playing: navigator.mediaSession?.playbackState === 'playing' || Boolean(node)});
  }, 1000);
})();
