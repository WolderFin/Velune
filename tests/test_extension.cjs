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
