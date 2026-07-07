/* Transport for index.html: talks to server.py's HTTP API. Unchanged
   behavior from the original inline implementation. */
window.__transport = async function(path, body){
  const opts = body ? {method:'POST', headers:{'Content-Type':'application/json'},
                       body:JSON.stringify(body)} : {};
  const r = await fetch(path, opts);
  const j = await r.json();
  if(!r.ok){ console.warn(j); return null; }
  return j;
};
