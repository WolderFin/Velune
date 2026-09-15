const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const elements = new Map(), stored = new Map();
stored.set('music-studio', JSON.stringify({theme:'neko',source:'Browser & Music',backdrop:true,glow:false}));
const element = id => {
    if (!elements.has(id)) elements.set(id, {value:'',src:'',style:{},checked:false,
        handlers:{},addEventListener(name, fn){this.handlers[name]=fn},setAttribute(){},replaceChildren(){},
        classList:{toggle(){},remove(){}}});
    return elements.get(id);
};
const context = vm.createContext({window:{addEventListener(){}}, document:{getElementById:element,querySelectorAll:()=>[],activeElement:null},
    localStorage:{getItem:key=>stored.get(key),setItem:(key,value)=>stored.set(key,value)},
    location:{origin:'http://127.0.0.1:8765'}, URL,JSON,String,Option:class{},AbortSignal,
    fetch:async()=>({ok:true,json:async()=>({sources:[],available:true})}),setInterval(){}});
vm.runInContext(fs.readFileSync('static/index.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1],context);
let url = new URL(element('url').value);
assert.equal(url.searchParams.get('source'),'Browser & Music');
assert.equal(url.searchParams.get('theme'),'neko');
assert.equal(url.searchParams.get('backdrop'),'1');
assert.equal(url.searchParams.has('glow'),false);
element('glow').checked=true; element('glow').handlers.change();
element('backdrop').checked=false; element('backdrop').handlers.change();
element('example').handlers.click();
url = new URL(element('url').value);
assert.equal(url.searchParams.has('backdrop'),false);
assert.equal(url.searchParams.get('glow'),'1');
assert.equal(url.searchParams.has('demo'),false);
assert.equal(new URL(element('preview').src).searchParams.get('demo'),'1');
const saved=JSON.parse(stored.get('music-studio'));
assert.equal(saved.glow,true); assert.equal(saved.backdrop,false);
console.log('Panel: effects are independent, saved, URL-encoded; demo stays out of OBS URL');
