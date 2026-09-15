const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync('static/overlay.html', 'utf8');
const elements = new Map();
function element(id) {
    if (!elements.has(id)) {
        const classes = new Set();
        elements.set(id, {style: {setProperty() {}}, textContent: '', src: '',
            dataset: {}, lastChild: {textContent: ''}, removeAttribute(name) {delete this[name]},
            classList: {add(x) {classes.add(x)}, remove(x) {classes.delete(x)},
                toggle(x, on) {on ? classes.add(x) : classes.delete(x)}, contains(x) {return classes.has(x)}}});
    }
    return elements.get(id);
}
const intervals = [], images = [], timers = new Map();
let timerId = 0, now = 0, fail = false;
let requestedEndpoint;
let response = {available: true, updated_at: Date.now() / 1000, title: 'Track', artist: 'Artist',
    album: '', source: 'Yandex', cover: '/covers/first', position: 20, duration: 100, playing: true};
const context = vm.createContext({document: {getElementById: element, querySelector: element,
    documentElement: element('root')}, performance: {now: () => now}, Date, Number, Math, String,
    JSON, Error, AbortSignal, URLSearchParams, location: {search: '?theme=neko&source=Yandex&backdrop=1&glow=1'}, encodeURIComponent, Image: class {constructor() {images.push(this)}},
    setTimeout(fn) {const id = ++timerId; timers.set(id, fn); return id},
    clearTimeout(id) {timers.delete(id)}, setInterval(fn) {intervals.push(fn)},
    fetch: async (endpoint) => {requestedEndpoint = endpoint; if (fail) throw new Error('offline'); return {ok: true, json: async () => response}}});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
const flush = async () => {for (let i = 0; i < 8; i++) await Promise.resolve()};
const apply = () => {const id = vm.runInContext('transition', context); if (timers.has(id)) {timers.get(id)(); timers.delete(id)}};
(async () => {
    await flush(); apply();
    assert.equal(requestedEndpoint, '/api/current?source=Yandex');
    assert.equal(element('root').dataset.theme, 'neko');
    assert.equal(element('root').dataset.backdrop, 'on');
    assert.equal(element('root').dataset.glow, 'on');
    assert.equal(images.length, 1);
    images[0].onload();
    intervals[0](); assert.equal(element('progress').style.width, '20%');
    await vm.runInContext('poll()', context);
    assert.equal(images.length, 1, 'unchanged cover must not reload');
    response = {...response, title: 'No cover', cover: '', duration: 0};
    await vm.runInContext('poll()', context); apply(); intervals[0]();
    assert.equal(element('progress').style.width, '0%');
    assert.equal(element('cover').src, undefined);
    images[0].onload(); assert.equal(element('cover').src, undefined, 'old image callback must be ignored');
    fail = true; await vm.runInContext('poll()', context);
    assert.equal(element('card').classList.contains('visible'), false);
    fail = false; await vm.runInContext('poll()', context); apply();
    assert.equal(element('card').classList.contains('visible'), true);
    now = 6000; intervals[0]();
    assert.equal(element('card').classList.contains('visible'), false);
    console.log('Frontend: cover cache, missing cover, unknown duration, offline recovery and stale watchdog OK');
})().catch(error => {console.error(error); process.exitCode = 1});
