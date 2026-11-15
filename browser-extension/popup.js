const state = document.getElementById('state');
const message = document.getElementById('message');
const track = document.getElementById('track');
chrome.runtime.sendMessage({type: 'velune-status'}, status => {
  if (chrome.runtime.lastError || !status) {
    message.textContent = 'Мост ещё не запускался';
    return;
  }
  state.className = `row ${status.state}`;
  message.textContent = status.message;
  track.textContent = status.track || 'Открой медиасервис, обнови страницу и включи трек';
});
document.getElementById('connect').addEventListener('click', async () => {
  message.textContent = 'Подключение…';
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const url = tab?.url || '';
    const isVK = /^https:\/\/([^/]+\.)?vk\.(com|ru)\//.test(url);
    const isYandex = /^https:\/\/music\.yandex\.ru\//.test(url);
    const isYouTube = /^https:\/\/([^/]+\.)?youtube\.com\//.test(url);
    if (!tab?.id || (!isVK && !isYandex && !isYouTube))
      throw new Error('Открой VK, Яндекс Музыку или YouTube');
    await chrome.scripting.executeScript({target: {tabId: tab.id}, files: ['content.js'], world: 'ISOLATED'});
    if (isVK)
      await chrome.scripting.executeScript({target: {tabId: tab.id}, files: ['main.js'], world: 'MAIN'});
    if (isYouTube)
      await chrome.scripting.executeScript({target: {tabId: tab.id}, files: ['youtube.js'], world: 'MAIN'});
    message.textContent = 'Подключено — включи трек';
    track.textContent = 'Диагностика обновится через секунду';
  } catch (error) {
    state.className = 'row error';
    message.textContent = error.message;
  }
});
