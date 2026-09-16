let status = {state: 'waiting', message: 'Ожидание трека', track: '', updated: 0};
console.log('[Velune] Browser Bridge service worker started');
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'velune-status') {
    sendResponse(status);
    return;
  }
  if (message?.type !== 'velune-track') return;
  const track = message.track || {};
  console.log('[Velune] Track from page:', track.source, track.artist, track.title);
  if (!track.title && track.diagnostic) {
    status = {state: 'waiting', message: track.diagnostic,
      track: `Страница: ${track.page || 'VK'}`, updated: Date.now()};
  }
  fetch('http://127.0.0.1:8765/api/browser-track', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(track)
  }).then(response => {
    if (!response.ok) throw new Error(`Velune HTTP ${response.status}`);
    status = {state: track.title ? 'connected' : 'waiting',
      message: track.title ? 'Velune подключена' : (track.diagnostic || 'Трек не найден'),
      track: track.title ? `${track.artist ? track.artist + ' — ' : ''}${track.title}` : 'Трек не найден', updated: Date.now()};
    console.log('[Velune] Sent successfully');
  }).catch(error => {
    status = {state: 'error', message: 'Velune не отвечает на 127.0.0.1:8765',
      track: track.title || '', updated: Date.now()};
    console.error('[Velune] Send failed:', error);
  });
});
