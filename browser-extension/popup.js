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
  track.textContent = status.track || 'Открой VK, обнови страницу и включи трек';
});
document.getElementById('connect').addEventListener('click', async () => {
  message.textContent = 'Подключение…';
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    if (!tab?.id || !/^https:\/\/([^/]+\.)?vk\.(com|ru)\//.test(tab.url || ''))
      throw new Error('Сначала открой вкладку VK');
    await chrome.scripting.executeScript({target: {tabId: tab.id}, files: ['content.js'], world: 'ISOLATED'});
    await chrome.scripting.executeScript({target: {tabId: tab.id}, files: ['main.js'], world: 'MAIN'});
    message.textContent = 'Подключено — включи трек';
    track.textContent = 'Диагностика обновится через секунду';
  } catch (error) {
    state.className = 'row error';
    message.textContent = error.message;
  }
});
