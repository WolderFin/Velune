const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
let tick, sent;
class CustomEvent { constructor(type, options) { this.type = type; this.detail = options.detail; } }
const context = {
  console, CustomEvent,
  setInterval(callback) { tick = callback; },
  document: {createElement() { return {set innerHTML(value) { this.value = value; }}; }},
  window: {dispatchEvent(event) { sent = event; }},
  getAudioPlayer() { return {_currentAudio: [0,0,0,'Track','Artist',180,0,0,0,0,0,0,0,0,'small,large',{duration:180},''], _isPlaying:true, _listenedTime:42}; }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('browser-extension/main.js', 'utf8'), context);
tick();
assert.equal(sent.type, 'velune-browser-track');
assert.equal(sent.detail.title, 'Track');
assert.equal(sent.detail.artist, 'Artist');
assert.equal(sent.detail.cover, 'large');
assert.equal(sent.detail.position, 42);
assert.equal(sent.detail.playing, true);
console.log('Extension: VK page player metadata bridge OK');

let youtubeTick, youtubeEvent;
const video = {currentTime: 64, duration: 240, paused: false, ended: false};
const youtubeContext = {
  console, CustomEvent,
  setInterval(callback) { youtubeTick = callback; },
  location: {hostname: 'www.youtube.com', href: 'https://www.youtube.com/watch?v=abc123'},
  navigator: {mediaSession: {metadata: {title: 'Video title', artist: 'Channel name',
    album: '', artwork: [{src: 'small.jpg'}, {src: 'large.jpg'}]}}},
  document: {
    title: 'Video title - YouTube',
    querySelector(selector) { return selector.includes('video') ? video : null; },
    addEventListener() {}
  },
  window: {dispatchEvent(event) { youtubeEvent = event; }}
};
vm.createContext(youtubeContext);
vm.runInContext(fs.readFileSync('browser-extension/youtube.js', 'utf8'), youtubeContext);
youtubeTick();
assert.equal(youtubeEvent.type, 'velune-browser-track');
assert.equal(youtubeEvent.detail.source, 'browser:youtube.com');
assert.equal(youtubeEvent.detail.title, 'Video title');
assert.equal(youtubeEvent.detail.artist, 'Channel name');
assert.equal(youtubeEvent.detail.cover, 'large.jpg');
assert.equal(youtubeEvent.detail.position, 64);
assert.equal(youtubeEvent.detail.duration, 240);
assert.equal(youtubeEvent.detail.playing, true);

const manifest = JSON.parse(fs.readFileSync('browser-extension/manifest.json', 'utf8'));
assert.equal(manifest.version, '1.1.0');
assert(manifest.content_scripts.some(entry => entry.js.includes('youtube.js') &&
  entry.matches.some(match => match.includes('youtube.com'))));
assert(manifest.content_scripts.some(entry => entry.js.includes('content.js') &&
  entry.matches.some(match => match.includes('youtube.com'))));

let contentListener, relayedTrack;
const contentContext = {
  console,
  setInterval() {},
  location: {hostname: 'www.youtube.com'},
  navigator: {},
  document: {querySelectorAll() { return []; }},
  window: {addEventListener(type, callback) {
    if (type === 'velune-browser-track') contentListener = callback;
  }},
  chrome: {runtime: {sendMessage(message) { relayedTrack = message.track; }}}
};
vm.createContext(contentContext);
vm.runInContext(fs.readFileSync('browser-extension/content.js', 'utf8'), contentContext);
contentListener({detail: {source: 'browser:youtube.com', title: 'Relayed video', artist: 'Channel'}});
assert.equal(relayedTrack.source, 'browser:youtube.com');
assert.equal(relayedTrack.title, 'Relayed video');
console.log('Extension: YouTube and YouTube Music metadata bridge OK');
