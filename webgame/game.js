/* XueZhan mahjong UI logic — shared by index.html (desktop, backed by
   server.py over HTTP) and app.html (offline PWA, backed by a Pyodide
   Web Worker). Neither entry duplicates this file; each only supplies
   `window.__transport(path, body) -> Promise<json-or-null>` before this
   script runs, matching the same shape server.py's HTTP API returns. */
const SUITS = ['条','万','筒'];
const NAMES = {0:'你 (南)', 1:'AI·下家 (西)', 2:'AI·对家 (北)', 3:'AI·上家 (东)'};
let S = null;          // last state from the transport
let hintTile = null;

function tileHTML(t, cls='', clickable=false){
  if(!t) return '';
  const c = t[0], n = t[1];
  return `<div class="tile c${c} ${cls}" data-c="${c}" data-n="${n}">
            <span class="num">${n}</span><span class="suit">${SUITS[c]}</span></div>`;
}
function backHTML(cls='small'){ return `<div class="tile back ${cls}"></div>`; }
function sameTile(a,b){ return a && b && a[0]===b[0] && a[1]===b[1]; }

async function api(path, body){
  return window.__transport(path, body);
}

async function newGame(){
  hintTile = null;
  const seedStr = new URLSearchParams(location.search).get('seed');
  const body = {ai: document.getElementById('aiSel').value};
  if(seedStr !== null && seedStr !== '') body.seed = Number(seedStr);
  S = await api('/api/new', body);
  render();
}

async function dailyGame(){
  hintTile = null;
  S = await api('/api/new', {daily: true});
  render();
}

let dailyPar = {};   // daily seed -> AI par score (null while fetching)
function dailyLine(){
  if(!S.daily) return '';
  const seed = S.daily;
  if(dailyPar[seed] === undefined){
    dailyPar[seed] = null;
    api('/api/daily_par', {}).then(r=>{
      if(r && r.par !== undefined){
        dailyPar[seed] = r.par;
        if(S && S.stage === 'over') render();
      }
    });
  }
  const par = dailyPar[seed];
  const my = S.you.score;
  const cmp = (par === null || par === undefined) ? 'AI基准计算中…' :
    (my > par ? `🎉 你比AI多 ${my-par} 分!` :
     my === par ? '与AI打平' : `比AI少 ${par-my} 分`);
  return `<p style="margin-top:10px;font-size:14px"><b>每日挑战 #${seed}</b>
     — 你: ${my>=0?'+':''}${my} · AI替你打这副牌:
     ${par===null||par===undefined?'…':(par>=0?'+':'')+par}<br>${cmp}</p>`;
}

const sleep = ms => new Promise(r=>setTimeout(r,ms));

async function stepLoop(){
  /* replay AI turns one engine action at a time, pausing on visible moves */
  document.body.classList.add('busy');
  try{
    while(S && S.stage === 'play' && !S.pending){
      const before = S.history.length;
      const st = await api('/api/step', {});
      if(!st) break;
      S = st; render();
      if(!st.stepped) break;
      const delay = +document.getElementById('speedSel').value;
      if(delay && S.history.length > before) await sleep(delay);
    }
  } finally {
    document.body.classList.remove('busy');
    render();
  }
}

async function act(body){
  hintTile = null;
  const st = await api('/api/act', body);
  if(st) { S = st; render(); await stepLoop(); }
}

async function hint(){
  if(!S || !S.pending) return;
  const h = await api('/api/hint');
  if(!h || !('action' in h)) return;
  const a = h.action;
  if(Array.isArray(a) && a.length===2 && typeof a[0]==='number'){
    hintTile = a;                       // a tile to discard
    render(true);
    renderHintPanel(h);
  } else {
    const pr = document.getElementById('prompt');
    if(!pr.querySelector('.ai-adv'))
      pr.innerHTML += ` <span class="badge ai-adv" style="background:#6a5416">AI建议: ${actHTML(a)}</span>`;
    if(h.why) document.getElementById('hintDetail').innerHTML = `💡 ${h.why}`;
  }
  renderCoach(h.opps);
}

/* ---------------- sound effects (no assets: WebAudio + speech) --------- */
let soundOn = localStorage.getItem('sound') !== '0';
let AC = null;
function ac(){
  if(!AC) AC = new (window.AudioContext || window.webkitAudioContext)();
  if(AC.state === 'suspended') AC.resume();
  return AC;
}
// browsers only allow audio after a user gesture: warm the context up early
document.addEventListener('pointerdown', ()=>{ if(soundOn) try{ac();}catch(e){} });

function tileClick(){          // short "tile hits the table" tick
  if(!soundOn) return;
  try{
    const ctx = ac(), t = ctx.currentTime;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = 'triangle';
    o.frequency.setValueAtTime(1750, t);
    o.frequency.exponentialRampToValueAtTime(650, t + .06);
    g.gain.setValueAtTime(.22, t);
    g.gain.exponentialRampToValueAtTime(.001, t + .09);
    o.connect(g).connect(ctx.destination);
    o.start(t); o.stop(t + .1);
  }catch(e){}
}
function winChime(){           // rising arpeggio for a win
  if(!soundOn) return;
  try{
    const ctx = ac(), t0 = ctx.currentTime;
    [523.25, 659.25, 783.99, 1046.5].forEach((f, i)=>{
      const t = t0 + i * .11;
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = 'sine'; o.frequency.setValueAtTime(f, t);
      g.gain.setValueAtTime(.18, t);
      g.gain.exponentialRampToValueAtTime(.001, t + .3);
      o.connect(g).connect(ctx.destination);
      o.start(t); o.stop(t + .32);
    });
  }catch(e){}
}
function speak(txt){           // voiced call: 碰 / 杠 / 胡 / 自摸
  if(!soundOn || typeof speechSynthesis === 'undefined') return;
  try{
    const u = new SpeechSynthesisUtterance(txt);
    u.lang = 'zh-CN'; u.rate = 1.15; u.pitch = 1.1; u.volume = 1;
    const v = speechSynthesis.getVoices().find(v=>/^zh/i.test(v.lang));
    if(v) u.voice = v;
    speechSynthesis.cancel();  // a fresh call preempts a stale one
    speechSynthesis.speak(u);
  }catch(e){}
}

const VOICE = {pong:'碰', kong:'杠', ankong:'杠', jiakong:'杠',
               hu:'胡', zimo:'自摸', robkong:'抢杠，胡'};
let sndGame = null, sndSeen = 0;
function playNewSounds(){
  /* voice/effects for history entries added since the last render; on a new
     game (or page load) just sync the cursor so nothing replays */
  if(!S || !S.history) return;
  if(S.game_id !== sndGame){ sndGame = S.game_id; sndSeen = S.history.length; return; }
  const fresh = S.history.slice(sndSeen);
  sndSeen = S.history.length;
  if(!fresh.length || !soundOn) return;
  let clicked = false, voice = null, won = false;
  for(const e of fresh){
    const a = e[1];
    if(a === 'discard') clicked = true;
    if(VOICE[a]) voice = VOICE[a];
    if(a === 'hu' || a === 'zimo' || a === 'robkong') won = true;
  }
  if(clicked) tileClick();     // one tick per batch, not a burst
  if(voice) speak(voice);
  if(won) winChime();
}

/* ---------------- coach mode: auto-hint + opponent read ---------------- */
let coachOn = localStorage.getItem('coach') === '1';
let lastCoachKey = null;

function maybeAutoHint(){
  if(!coachOn || !S || S.stage !== 'play' || !S.pending) return;
  const key = `${S.game_id}:${S.history.length}:${S.pending.valid_act}`;
  if(key === lastCoachKey) return;
  lastCoachKey = key;
  hint();
}

function readyLabel(t){
  return t >= 0.75 ? ['高', 'dgr-hi'] : (t >= 0.5 ? ['中', 'dgr-mid'] : ['低', 'dgr-lo']);
}

function renderCoach(opps){
  const box = document.getElementById('coachBox');
  if(!box) return;
  if(!opps || !opps.length){ box.innerHTML = ''; return; }
  box.innerHTML =
    `<div class="coach-title">对手估计（只用公开信息推断，不偷看手牌）</div>` +
    opps.map(o=>{
      const who = NAMES[o.id];
      if(o.winning) return `<div class="coach-line">${who}：已胡牌，无威胁</div>`;
      const [lbl, cls] = readyLabel(o.threat);
      const hot = (o.hot && o.hot.length)
        ? '对其危险: ' + o.hot.map(h=>
            `<span class="mini-inline">${tileHTML(h[0],'mini')}</span>`).join('')
        : '你手中暂无明显危险牌';
      const flush = (o.flush !== undefined)
        ? ` · <span class="dgr-hi">⚠️疑似清一色(${SUITS[o.flush]})</span>` : '';
      return `<div class="coach-line">${who}：听牌可能 <b class="${cls}">${lbl}</b>
        (${Math.round(o.threat*100)}%) · 副露${o.n_melds}组${flush}
        · 缺${SUITS[o.daque]}(打${SUITS[o.daque]}对其安全) · ${hot}</div>`;
    }).join('');
}

function dangerCls(d){ return d>=2.5?'dgr-hi':(d>=1.2?'dgr-mid':'dgr-lo'); }

let hintData = null;
function tileCN(t){ return `${t[1]}${SUITS[t[0]]}`; }

function renderHintPanel(h){
  /* ranked discard analysis: effective draws, dfncy effect, deal-in danger */
  hintData = h;
  const box = document.getElementById('hintPanel');
  if(!h.rows){ box.innerHTML=''; return; }
  const head = h.forced_daque
    ? `<div style="width:100%;font-size:12px;opacity:.85">必须先打缺色牌 — 按点炮危险度排序 (点击查看分析):</div>`
    : `<div style="width:100%;font-size:12px;opacity:.85">出牌分析 — 点击任意候选牌查看原因:</div>`;
  const shown = h.rows.slice(0,8);
  let bestIdx = shown.findIndex(r=>sameTile(r.tile, h.action));
  if(bestIdx < 0) bestIdx = 0;
  box.innerHTML = head + shown.map((r,i)=>{
    let cls = sameTile(r.tile, h.action) ? 'hcand best' : 'hcand';
    if(i===bestIdx) cls += ' selected';
    let meta;
    if(h.forced_daque){
      meta = `<span class="${dangerCls(r.danger)}">危险 ${r.danger}</span>`;
    } else {
      meta = (r.keeps ? `进张 <b>${r.eff}</b>`
                      : `<span class="dgr-hi">拆牌→向听${r.after}</span>`) +
             `<br><span class="${dangerCls(r.danger)}">危险 ${r.danger}</span>`;
    }
    return `<div class="${cls}" data-i="${i}">${tileHTML(r.tile,'small')}<div class="meta">${meta}</div></div>`;
  }).join('');
  box.querySelectorAll('.hcand').forEach(el=>{
    el.onclick = ()=>{
      box.querySelectorAll('.hcand').forEach(x=>x.classList.remove('selected'));
      el.classList.add('selected');
      showHintDetail(+el.dataset.i);
    };
  });
  showHintDetail(bestIdx);
}

function showHintDetail(i){
  const el = document.getElementById('hintDetail');
  if(!hintData || !hintData.rows || !hintData.rows[i]){ el.innerHTML=''; return; }
  const r = hintData.rows[i];
  const isAI = sameTile(r.tile, hintData.action);
  let parts = [];
  if(hintData.forced_daque){
    parts.push(`缺色牌必须先打，此牌点炮危险度 ${r.danger}`);
  } else if(!r.keeps){
    parts.push(`拆牌：打出后向听从 ${hintData.cur_dfncy} 退到 ${r.after}，通常不划算`);
  } else {
    parts.push(`打出后保持向听 ${hintData.cur_dfncy}`);
    if(r.detail && r.detail.length){
      const lst = r.detail.map(d=>`${tileCN(d[0])}×${d[1]}`).join('、');
      parts.push(`之后共有 <b>${r.eff}</b> 张有效进张可减少向听：${lst}`);
    } else {
      parts.push('但打出后没有任何有效进张（死型）');
    }
    parts.push(`点炮危险度 <span class="${dangerCls(r.danger)}">${r.danger}</span>`);
  }
  if(r.notes && r.notes.length) parts.push(r.notes.join('；'));
  el.innerHTML = `${isAI?'⭐ AI选择 · ':''}打 <b>${tileCN(r.tile)}</b>：` + parts.join('；');
}

function seatHTML(p){
  const daque = p.daque===null? '' : `<span class="badge daque">缺${SUITS[p.daque]}</span>`;
  const sc = `<span class="badge ${p.score>=0?'score-pos':'score-neg'}">${p.score>=0?'+':''}${p.score}</span>`;
  const win = p.winning ? `<span class="winner">🏆已胡</span>` : '';
  let html = `<div class="name">${NAMES[p.id]} ${daque} ${sc} ${win}</div>`;
  html += `<div class="tilerow">`;
  for(const meld of p.pile){
    html += `<span class="meld">` + meld.map(t=>tileHTML(t,'mini')).join('') + `</span>`;
  }
  html += `</div>`;
  if('hand' in p){        // revealed at game over
    html += `<div class="tilerow" style="margin-top:5px">` +
            p.hand.map(t=>tileHTML(t,'small')).join('') + `</div>`;
  } else if('n_hand' in p){
    html += `<div class="tilerow" style="margin-top:5px">` +
            backHTML('mini').repeat(p.n_hand) + `</div>`;
  }
  return html;
}

function historyText(e){
  const who = NAMES[e[0]].split(' ')[0];
  const a = e[1];
  const t = e[2];
  const tl = t ? `<span class="mini-inline">${tileHTML(t,'mini')}</span>` : '';
  const map = {draw:'摸牌', discard:'打出', pong:'碰', kong:'明杠', ankong:'暗杠',
               jiakong:'加杠', zimo:'自摸', hu:'胡', robkong:'抢杠胡'};
  let s = `${who} ${map[a]||a} ${a==='draw'?'':tl}`;
  if(a==='hu') s += ` (点炮: ${NAMES[e[3]].split(' ')[0]})`;
  if(a==='robkong') s += ` (被抢: ${NAMES[e[3]].split(' ')[0]})`;
  return s;
}

const VA_LBL = {daque:'定缺', discard:'出牌', pong:'碰', kong:'杠', zikong:'自杠',
                hu:'胡', zimo:'自摸', robkong:'抢杠'};
const HU_CN = {pinghu:'平胡', zimo:'自摸', robkong:'抢杠胡', kongshanghua:'杠上花',
               kongshangpao:'杠上炮', qingyise:'清一色', pengpenghu:'碰碰胡',
               qidui:'七对', jingoudiao:'金钩钓', longqidui:'龙七对',
               shibaluohan:'十八罗汉', tianhu:'天胡', dihu:'地胡'};
const HU_MULT = {zimo:2, robkong:2, kongshanghua:2, kongshangpao:2,
                 pengpenghu:2, qidui:4, jingoudiao:4, qingyise:4};
function huWayCN(w){
  const m = /^(\d+) gen$/.exec(w);
  return m ? `${m[1]}根` : (HU_CN[w] || w);
}
function fanText(hu_way){
  /* mirrors utils/xzscore.py compute_hu_score */
  if(!hu_way || !hu_way.length) return '';
  if(hu_way.includes('tianhu')) return '天胡 = 32番';
  if(hu_way.includes('dihu')) return '地胡 = 32番';
  let fan = 1; const parts = ['1番'];
  for(const w of hu_way){
    const m = /^(\d+) gen$/.exec(w);
    if(m){ const k = Math.pow(2, +m[1]); fan *= k; parts.push(`×${k}(${m[1]}根)`); }
    else if(HU_MULT[w]){ fan *= HU_MULT[w]; parts.push(`×${HU_MULT[w]}(${HU_CN[w]})`); }
  }
  return parts.length > 1 ? `${parts.join('')} = ${fan}番` : '1番';
}
const KINDMAP = {
  hu:e=>`胡牌 ${e.fan}番 (${NAMES[e.others[0]].split(' ')[0]}点炮)`,
  zimo:e=>`自摸 ${e.fan}番 ×${e.others.length}家`,
  dianpao:e=>`点炮给${NAMES[e.others[0]].split(' ')[0]}`,
  beizimo:e=>`被${NAMES[e.others[0]].split(' ')[0]}自摸 ${e.fan}番`,
  tianhu:e=>`天胡 ${e.fan}番`, dihu:e=>`地胡 ${e.fan}番`,
  beitiandihu:e=>`被天胡/地胡`,
  chadajiao:e=>`查大叫 (${e.others.length}家未听牌赔付)`,
  beichadajiao:e=>`被查大叫 (流局时未听牌)`,
  chahuazhu:e=>`查花猪`,
  beichahuazhu:e=>`被查花猪 (手中仍有缺色牌)`,
  kong:e=>(e.amount>=0?'杠牌收入':'杠牌支出') +
          (e.tile?` (${e.tile[1]}${SUITS[e.tile[0]]})`:''),
  zhuanyi_in:e=>'呼叫转移收入 (杠上炮)',
  zhuanyi_out:e=>'呼叫转移 — 杠钱转给胡家',
  tuishui_out:e=>'退税 — 流局未听牌退还杠钱',
  tuishui_back:e=>'退税收回',
};
function settleHTML(p){
  if(!p.settle || !p.settle.length) return '';
  const lines = p.settle.map(e=>{
    const f = KINDMAP[e.kind];
    return `<div class="line"><span>${f?f(e):e.kind}</span>
            <b>${e.amount>=0?'+':''}${e.amount}</b></div>`;
  }).join('');
  return `<details class="settle"><summary>${NAMES[p.id]} 结算明细
          (${p.score>=0?'+':''}${p.score})</summary>${lines}</details>`;
}
function actHTML(a){
  if(Array.isArray(a) && a.length===2 && typeof a[0]==='number')
    return `<span class="mini-inline">${tileHTML(a,'mini')}</span>`;
  if(Array.isArray(a))
    return `${VA_LBL[a[0]]||a[0]} <span class="mini-inline">${tileHTML(a[1],'mini')}</span>`;
  if(typeof a==='number') return `缺${SUITS[a]}`;
  return VA_LBL[a] || ({stand:'过', pong:'碰', kong:'杠', ankong:'暗杠',
                        jiakong:'加杠'})[a] || a;
}
function reviewHTML(decs){
  if(!decs || !decs.length) return '';
  const dis = decs.filter(d=>!d.agree);
  if(!dis.length) return `<p style="margin-top:10px">👏 本局你的所有决策都与AI策略一致</p>`;
  const lines = dis.slice(0,15).map(d=>
    `<div class="line"><span class="badge">第${d.n_history}手</span>
     <span>${VA_LBL[d.valid_act]||d.valid_act}:</span>
     <span>你 ${actHTML(d.human)}</span> <span>· AI ${actHTML(d.strategy)}</span>
     ${(d.deficiency!==null && d.deficiency!==undefined)
        ? `<span class="badge">向听${d.deficiency}</span>` : ''}</div>`).join('');
  return `<p style="margin-top:10px;font-weight:600;color:#ffd964">决策回顾 —
          与AI不同的 ${dis.length} 手</p><div id="reviewList">${lines}</div>`;
}

function render(keepHint=false){
  if(!keepHint){
    hintTile = null;
    hintData = null;
    const hp = document.getElementById('hintPanel');
    if(hp) hp.innerHTML = '';
    const hd = document.getElementById('hintDetail');
    if(hd) hd.innerHTML = '';
    const cb = document.getElementById('coachBox');
    if(cb) cb.innerHTML = '';
  }
  if(!S || S.stage==='none'){ return; }

  playNewSounds();

  // daque overlay
  const dq = document.getElementById('daqueOverlay');
  if(S.stage==='choose_daque'){
    dq.classList.remove('hidden');
    document.getElementById('daqueButtons').innerHTML =
      [0,1,2].map(c=>`<button onclick="act({type:'daque',color:${c}})">打缺 ${SUITS[c]}</button>`).join('');
    document.getElementById('daqueHint').textContent =
      `AI 策略建议：缺${SUITS[S.daque_suggestion]}`;
    // show hand in background too
  } else {
    dq.classList.add('hidden');
  }

  // seats 1..3 (highlight whoever acted last while AI turns replay)
  const lastActor = S.history.length ? S.history[S.history.length-1][0] : null;
  for(const p of S.opponents){
    const el = document.getElementById('seat'+p.id);
    el.innerHTML = seatHTML(p);
    el.classList.toggle('active', S.stage==='play' && !S.pending && p.id===lastActor);
  }
  // my seat header
  const me = S.you;
  document.getElementById('myName').innerHTML =
    `${NAMES[0]} ${me.daque!==null?`<span class="badge daque">缺${SUITS[me.daque]}</span>`:''}
     <span class="badge ${me.score>=0?'score-pos':'score-neg'}">${me.score>=0?'+':''}${me.score}</span>
     ${me.winning?'<span class="winner">🏆已胡</span>':''}`;
  document.getElementById('myPile').innerHTML =
    me.pile.map(meld=>`<span class="meld">`+meld.map(t=>tileHTML(t,'mini')).join('')+`</span>`).join('');

  // deficiency badge
  const dfb = document.getElementById('dfncyBox');
  dfb.textContent = (me.deficiency===null || me.deficiency===undefined) ? '' :
      (me.deficiency===0 ? '听牌!' : `向听数 (dfncy): ${me.deficiency}`);

  // current-move banner: the latest action + whose turn, always visible
  const nb = document.getElementById('nowBar');
  const lastE = S.history.length ? S.history[S.history.length-1] : null;
  let turn = '';
  if(S.stage === 'over') turn = `<span class="turn">本局结束</span>`;
  else if(S.pending) turn = `<span class="turn">→ ${S.pending.prompt}</span>`;
  else if(S.stage === 'play') turn = `<span class="turn">AI 行动中…</span>`;
  nb.innerHTML = (lastE ? `<span>${historyText(lastE)}</span>` :
                  `<span>对局开始</span>`) + turn;

  // wall + discards
  document.getElementById('wall').textContent =
    `牌墙剩余 ${S.wall} 张 · 弃牌 ${S.table.length} 张`;
  const disc = document.getElementById('discards');
  disc.innerHTML = S.table.map((t,i)=>
      tileHTML(t, 'small'+(i===S.table.length-1?' last':''))).join('');
  disc.scrollTop = disc.scrollHeight;

  // my hand
  const pend = S.pending;
  const discarding = pend && pend.type==='discard';
  const allowed = discarding ? pend.allowed : [];
  document.getElementById('myhand').innerHTML = me.hand.map(t=>{
    let cls = '';
    if(me.daque!==null && t[0]===me.daque) cls += ' daqued';
    if(discarding){
      cls += allowed.some(a=>sameTile(a,t)) ? ' clickable' : ' disabled';
    }
    if(hintTile && sameTile(hintTile,t)) cls += ' hint';
    return tileHTML(t, cls, true);
  }).join('');
  if(discarding){
    document.querySelectorAll('#myhand .tile.clickable').forEach(el=>{
      el.onclick = ()=>act({type:'discard', tile:[+el.dataset.c, +el.dataset.n]});
    });
  }

  // action buttons
  const LBL = {pong:'碰', kong:'杠', hu:'胡', zimo:'自摸', robkong:'抢杠胡',
               pass:'过', ankong:'暗杠', jiakong:'加杠'};
  const btns = document.getElementById('buttons');
  const promptEl = document.getElementById('prompt');
  if(pend && pend.type==='choice'){
    promptEl.innerHTML = pend.prompt +
      (pend.tile?` <span class="mini-inline">${tileHTML(pend.tile,'mini')}</span>`:'');
    btns.innerHTML = pend.options.map((o,i)=>{
      const label = (LBL[o.label]||o.label) +
        (o.tile?` ${o.tile[1]}${SUITS[o.tile[0]]}`:'');
      return `<button data-i="${i}">${label}</button>`;
    }).join(' ');
    btns.querySelectorAll('button').forEach(b=>{
      b.onclick = ()=>act({type:'action', action:pend.options[+b.dataset.i].action});
    });
  } else if(discarding){
    promptEl.textContent = pend.prompt;
    btns.innerHTML = '';
  } else {
    promptEl.textContent = S.stage==='over' ? '本局结束' : '';
    btns.innerHTML = '';
  }
  document.getElementById('seat0').classList.toggle('active', !!pend);
  document.getElementById('hintBtn').disabled = !pend;

  // history log, newest entry on top — no scrolling needed
  document.getElementById('log').innerHTML =
    S.history.slice().reverse().map(e=>`<div>${historyText(e)}</div>`).join('');

  // game over overlay
  if(S.stage==='over'){
    const rows = [S.you, ...S.opponents].map(p=>
      `<tr><td>${NAMES[p.id]}</td><td>${p.score>=0?'+':''}${p.score}</td>
       <td>${p.winning
          ? '🏆 '+(p.hu_way||[]).map(huWayCN).join('·') +
            `<br><span style="opacity:.75;font-size:12px">${fanText(p.hu_way)}</span>`
          : '未胡'}</td></tr>`).join('');
    const dv = S.divergence || {n:0, agree:0};
    const dvLine = dv.n ? `<p style="margin-top:10px; font-size:13.5px">你的决策与AI策略一致:
        <b>${dv.agree}/${dv.n}</b> (${Math.round(100*dv.agree/dv.n)}%)</p>` : '';
    document.getElementById('finalScores').innerHTML =
      `<table class="scores"><tr><th>玩家</th><th>得分</th><th>结果</th></tr>${rows}</table>
       ${dailyLine()}
       ${dvLine}
       ${S.error?`<p style="color:#f88">engine error — see server log</p>`:''}`;
    const everyone = [S.you, ...S.opponents];
    const kinds = [].concat(...everyone.map(p=>(p.settle||[]).map(e=>e.kind)));
    let expl = '';
    if(kinds.includes('chadajiao')||kinds.includes('beichadajiao'))
      expl += '<div>· 查大叫：流局时未听牌者按听牌者可胡的最大番数赔付。</div>';
    if(kinds.includes('chahuazhu')||kinds.includes('beichahuazhu'))
      expl += '<div>· 查花猪：流局时手中仍有缺色牌者赔付16番。</div>';
    if(kinds.includes('tuishui_out'))
      expl += '<div>· 退税：流局时未听牌者退还杠牌所得。</div>';
    if(kinds.includes('zhuanyi_in')||kinds.includes('zhuanyi_out'))
      expl += '<div>· 呼叫转移：杠后打出的牌被胡（杠上炮），该杠的收入转给胡家。</div>';
    document.getElementById('settleBox').innerHTML =
      everyone.map(settleHTML).join('') +
      (expl?`<div style="margin-top:8px;font-size:12.5px;opacity:.85">${expl}</div>`:'');
    document.getElementById('reviewBox').innerHTML = reviewHTML(S.decisions);
    document.getElementById('overOverlay').classList.remove('hidden');
  } else {
    document.getElementById('overOverlay').classList.add('hidden');
  }

  maybeAutoHint();
}

document.getElementById('newBtn').onclick = newGame;
document.getElementById('dailyBtn').onclick = dailyGame;
document.getElementById('hintBtn').onclick = hint;
const sndBtn = document.getElementById('sndBtn');
if(sndBtn){
  const paint = ()=>{ sndBtn.textContent = soundOn ? '🔊' : '🔇';
                      sndBtn.title = soundOn ? '关闭音效' : '打开音效'; };
  paint();
  sndBtn.onclick = ()=>{
    soundOn = !soundOn;
    localStorage.setItem('sound', soundOn ? '1' : '0');
    if(soundOn){ try{ac();}catch(e){} tileClick(); }
    else if(typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
    paint();
  };
}
const coachChk = document.getElementById('coachChk');
if(coachChk){
  coachChk.checked = coachOn;
  coachChk.onchange = ()=>{
    coachOn = coachChk.checked;
    localStorage.setItem('coach', coachOn ? '1' : '0');
    lastCoachKey = null;
    if(S) render();          // on: auto-hint fires; off: panels clear
  };
}

// phones are landscape-only: mark touch devices so the portrait rotate
// prompt (style.css #rotateOverlay) also works where pointer:coarse lies
if('ontouchstart' in window || navigator.maxTouchPoints > 0)
  document.body.classList.add('touch');

(async function init(){
  S = await api('/api/state');
  if(!S || S.stage==='none') await newGame(); else render();
})();
