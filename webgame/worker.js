/* Runs the real Python engine (unmodified) inside a Web Worker via Pyodide,
   so the UI thread never blocks on AI "thinking" time. Fetches the .py
   sources from this worker's own directory (webgame/) and its siblings
   (repo root), writes them into Pyodide's virtual filesystem at matching
   relative paths, then imports pwa_bridge.py exactly as the local dev
   simulation was verified against.
*/
importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js');

// vfs path -> source URL, relative to this worker script
const SOURCES = {
  '/mahjong/dfncy/block_dfncy.py': '../dfncy/block_dfncy.py',
  '/mahjong/hytreekong.py': '../hytreekong.py',
  '/mahjong/strategy_defense.py': '../strategy_defense.py',
  '/mahjong/strategy_huev.py': '../strategy_huev.py',
  '/mahjong/strategy_initial21_7attr.py': '../strategy_initial21_7attr.py',
  '/mahjong/strategyz0614.py': '../strategyz0614.py',
  '/mahjong/utils/constants.py': '../utils/constants.py',
  '/mahjong/utils/daque.py': '../utils/daque.py',
  '/mahjong/utils/hutype.py': '../utils/hutype.py',
  '/mahjong/utils/hysolx.py': '../utils/hysolx.py',
  '/mahjong/utils/pusolx.py': '../utils/pusolx.py',
  '/mahjong/utils/xzcard.py': '../utils/xzcard.py',
  '/mahjong/utils/xzscore.py': '../utils/xzscore.py',
  '/mahjong/utils/xzutils.py': '../utils/xzutils.py',
  '/mahjong/xzdealer.py': '../xzdealer.py',
  '/mahjong/xzjudger.py': '../xzjudger.py',
  '/mahjong/xzplayer.py': '../xzplayer.py',
  '/mahjong/xzround.py': '../xzround.py',
  '/mahjong/webgame/game_core.py': './game_core.py',
  '/mahjong/webgame/pwa_bridge.py': './pwa_bridge.py',
};

let bridge = null;

async function boot(){
  postMessage({type:'progress', text:'加载 Python 运行时…'});
  const pyodide = await loadPyodide();

  postMessage({type:'progress', text:'下载对局引擎源码…'});
  const files = {};
  await Promise.all(Object.entries(SOURCES).map(async ([vfsPath, url]) => {
    const r = await fetch(url);
    if(!r.ok) throw new Error(`fetch ${url} failed: ${r.status}`);
    files[vfsPath] = await r.text();
  }));

  postMessage({type:'progress', text:'初始化对局引擎…'});
  pyodide.globals.set('_vfs_files', pyodide.toPy(files));
  pyodide.runPython(`
import os
for _path, _content in _vfs_files.items():
    os.makedirs(os.path.dirname(_path), exist_ok=True)
    with open(_path, 'w', encoding='utf-8') as _f:
        _f.write(_content)
import sys
sys.path.insert(0, '/mahjong/webgame')
`);
  bridge = pyodide.pyimport('pwa_bridge');
  postMessage({type:'ready'});
}
const bootPromise = boot().catch(err => {
  postMessage({type:'boot_error', text: String(err)});
  throw err;
});

const DISPATCH = {
  new: (args) => bridge.api_new(args),
  act: (args) => bridge.api_act(args),
  step: () => bridge.api_step(),
  state: () => bridge.api_state(),
  hint: () => bridge.api_hint(),
  daily_par: () => bridge.api_daily_par(),
};

self.onmessage = async (ev) => {
  const {id, fn, args} = ev.data;
  try{
    await bootPromise;
    const jsonStr = DISPATCH[fn](args ? JSON.stringify(args) : undefined);
    const result = jsonStr ? JSON.parse(jsonStr) : null;
    if(result && result._status && result._status >= 400){
      postMessage({id, error: result.error || 'error'});
    } else {
      postMessage({id, result});
    }
  } catch(err){
    postMessage({id, error: String(err && err.message || err)});
  }
};
