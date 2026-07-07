/* Transport for app.html: runs the engine in a Web Worker (worker.js) via
   Pyodide, so AI "thinking" time never blocks the UI thread. Bridges the
   worker's request/response protocol to the same
   window.__transport(path, body) -> Promise<json> shape transport_fetch.js
   provides, so game.js is identical between the two entry points. */
(function(){
  const worker = new Worker('worker.js');
  let nextId = 1;
  const pending = new Map();

  worker.onmessage = (ev) => {
    const msg = ev.data;
    if(msg.type === 'progress'){
      const el = document.getElementById('bootText');
      if(el) el.textContent = msg.text;
      return;
    }
    if(msg.type === 'boot_error'){
      const el = document.getElementById('bootText');
      if(el) el.textContent = '加载失败: ' + msg.text + '（请检查网络后刷新重试）';
      return;
    }
    if(msg.type === 'ready'){
      const splash = document.getElementById('bootSplash');
      if(splash) splash.classList.add('hidden');
      return;
    }
    const p = pending.get(msg.id);
    if(!p) return;
    pending.delete(msg.id);
    if(msg.error){ console.warn(msg.error); p.resolve(null); }
    else p.resolve(msg.result);
  };

  // path -> worker fn name, mirrors server.py's URL routing
  const ROUTES = {
    '/api/new': 'new', '/api/act': 'act', '/api/step': 'step',
    '/api/state': 'state', '/api/hint': 'hint', '/api/daily_par': 'daily_par',
  };

  window.__transport = function(path, body){
    const fn = ROUTES[path];
    if(!fn) return Promise.resolve(null);
    const id = nextId++;
    return new Promise(resolve => {
      pending.set(id, {resolve});
      worker.postMessage({id, fn, args: body});
    });
  };
})();
