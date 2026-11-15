(() => {
  if (window.__veluneYouTubeBridge) return;
  window.__veluneYouTubeBridge = true;
  console.log('[Velune] YouTube page bridge started');

  let previous = '';
  const text = selectors => {
    for (const selector of selectors) {
      const value = document.querySelector(selector)?.textContent?.trim();
      if (value) return value;
    }
    return '';
  };
  const source = `browser:${location.hostname.replace(/^www\./, '')}`;

  function readYouTube() {
    const video = document.querySelector('video.html5-main-video, video');
    const metadata = navigator.mediaSession?.metadata;
    let title = metadata?.title || text([
      'ytd-watch-metadata h1 yt-formatted-string',
      '#info-contents h1 yt-formatted-string',
      'ytmusic-player-bar .title',
      'ytmusic-player-bar [class*="title"]'
    ]);
    if (!title && video) title = document.title.replace(/\s*-\s*YouTube\s*$/, '').trim();
    if (!video || !title) return null;

    const artist = metadata?.artist || text([
      'ytd-watch-metadata ytd-channel-name a',
      '#owner #channel-name a',
      'ytmusic-player-bar .byline',
      'ytmusic-player-bar [class*="subtitle"]'
    ]);
    const artwork = metadata?.artwork;
    let cover = artwork?.length ? artwork[artwork.length - 1].src : '';
    if (!cover) {
      const videoId = location.href.match(/[?&]v=([^&#]+)/)?.[1];
      if (videoId) cover = `https://i.ytimg.com/vi/${encodeURIComponent(videoId)}/hqdefault.jpg`;
    }
    return {
      source, title, artist, album: metadata?.album || '', cover,
      position: Number(video.currentTime || 0),
      duration: Number.isFinite(video.duration) ? video.duration : 0,
      playing: !video.paused && !video.ended
    };
  }

  function publish() {
    const track = readYouTube();
    const detail = track || {source, title: '', artist: '', playing: false,
      diagnostic: 'Страница подключена, активное видео YouTube не найдено', page: location.hostname};
    const key = JSON.stringify(detail);
    if (key === previous) return;
    previous = key;
    window.dispatchEvent(new CustomEvent('velune-browser-track', {detail}));
  }

  setInterval(publish, 1000);
  document.addEventListener('yt-navigate-finish', publish);
})();
