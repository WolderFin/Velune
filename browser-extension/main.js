(() => {
  if (window.__veluneMainBridge) return;
  window.__veluneMainBridge = true;
  console.log('[Velune] VK page bridge started');
  const decode = value => {
    const node = document.createElement('textarea');
    node.innerHTML = String(value || '');
    return node.value;
  };
  let previous = '';
  let warned = false;
  const visibleText = selectors => {
    for (const selector of selectors) {
      const nodes = [...document.querySelectorAll(selector)];
      const node = nodes.find(item => item.getClientRects().length && item.textContent?.trim());
      if (node) return node.textContent.trim();
    }
    return '';
  };
  function readVK() {
    try {
      const player = typeof getAudioPlayer === 'function' ? getAudioPlayer() : null;
      const audio = player?._currentAudio;
      if (!audio || !audio[3]) {
        const title = visibleText(['.audio_page_player_title_song', '.AudioPlayerBlock__title',
          '[data-testid="audio-player-title"]', '[class*="AudioPlayer"] [class*="title"]']);
        const artist = visibleText(['.audio_page_player_title_performer', '.AudioPlayerBlock__author',
          '[data-testid="audio-player-artist"]', '[class*="AudioPlayer"] [class*="artist"]']);
        if (!title) return null;
        return {source: 'browser:vk.com', title, artist, album: '', cover: '',
          position: 0, duration: 0, playing: true};
      }
      const times = audio[15] || {};
      const artwork = String(audio[14] || '').split(',').filter(Boolean);
      return {
        source: 'browser:vk.com', title: decode(audio[3]) + (audio[16] ? ` (${decode(audio[16])})` : ''),
        artist: decode(audio[4]), album: '', cover: artwork.at(-1) || '',
        position: Number(player._listenedTime ?? player.stats?.currentPosition ?? 0),
        duration: Number(times.duration ?? audio[5] ?? 0), playing: Boolean(player._isPlaying)
      };
    } catch (error) {
      if (!warned) console.error('[Velune] VK player read failed:', error);
      warned = true;
      return null;
    }
  }
  setInterval(() => {
    const track = readVK();
    if (!track) {
      const diagnostic = {source: 'browser:vk.com', title: '', artist: '', playing: false,
        diagnostic: 'Страница подключена, плеер VK не найден', page: location.hostname};
      const diagnosticKey = JSON.stringify(diagnostic);
      if (diagnosticKey !== previous) {
        previous = diagnosticKey;
        window.dispatchEvent(new CustomEvent('velune-browser-track', {detail: diagnostic}));
      }
      return;
    }
    const key = JSON.stringify(track);
    if (key === previous) return;
    previous = key;
    window.dispatchEvent(new CustomEvent('velune-browser-track', {detail: track}));
  }, 1000);
})();
