
const API_BASE = '';

let _saved = null;
let _snapshot = null;

const $ = (sel)=>document.querySelector(sel);

function buildKV(containerId, labels, values){
  const wrap = document.getElementById(containerId);
  wrap.innerHTML = '';
  const keys = labels || Object.keys(values||{});
  keys.forEach(k=>{
    const id = `${containerId}__${k.replace(/\s+/g,'_')}`;
    const label = document.createElement('label');
    label.textContent = k;
    label.setAttribute('for', id);
    const input = document.createElement('input');
    input.id = id;
    input.type = 'text';
    let v = (values||{})[k];
    input.value = (v===null || v===undefined) ? '' : String(v);
    wrap.appendChild(label);
    wrap.appendChild(input);
  });
}

function collectKV(containerId){
  const wrap = document.getElementById(containerId);
  const kv = {};
  const inputs = wrap.querySelectorAll('input');
  inputs.forEach(inp=>{
    const label = wrap.querySelector(`label[for="${inp.id}"]`);
    const key = label ? label.textContent : inp.id;
    const val = inp.value;
    if(val !== '') kv[key] = val;
  });
  return kv;
}

function showError(prefix, err){
  try{
    const txt = (typeof err === 'string') ? err : (err?.message || JSON.stringify(err));
    alert(`${prefix}: ${txt}`);
    $('#debug').style.display='block';
    $('#debugText').textContent = `${prefix}\n\n` + txt;
  }catch(e){ alert(prefix); }
}

$('#uploadForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const fd = new FormData();
  const f = document.getElementById('pdf').files[0];
  if(!f) return alert('Válassz PDF-et!');
  fd.append('file', f);
  fd.append('sector', 'default');
  fd.append('lang', $('#lang').value || 'hu');
  try{
    const r = await fetch(`${API_BASE}/preview`, { method:'POST', body: fd });
    const text = await r.text();
    if(!r.ok) throw new Error(text);
    const d = JSON.parse(text);
    _saved = d.saved_pdf;
    _snapshot = d;
    document.getElementById('grid').style.display='grid';
    buildKV('bs_prev', d.bs_labels, d.bs_prev);
    buildKV('bs', d.bs_labels, d.bs);
    buildKV('pl_prev', d.pl_labels, d.pl_prev);
    buildKV('pl', d.pl_labels, d.pl);
    document.getElementById('actions').style.display='flex';
    $('#result').style.display='none';
  }catch(err){ showError('Előnézet hiba', err); }
});

$('#btnRecalc').addEventListener('click', async ()=>{
  if(!_saved){ return alert('Előbb készíts előnézetet.'); }
  $('#spinner').style.display='inline';
  const overrides = {
    bs: collectKV('bs'),
    bs_prev: collectKV('bs_prev'),
    pl: collectKV('pl'),
    pl_prev: collectKV('pl_prev')
  };
  try{
    const fd = new FormData();
    fd.append('saved_pdf', _saved);
    fd.append('sector', 'default');
    fd.append('lang', $('#lang').value || 'hu');
    fd.append('overrides_json', JSON.stringify(overrides));
    const r = await fetch(`${API_BASE}/recalc`, { method:'POST', body: fd });
    const text = await r.text();
    if(!r.ok) throw new Error(text);
    const d = JSON.parse(text);
    $('#result').style.display='block';
    $('#resultJson').textContent = JSON.stringify(d, null, 2);
    $('#decision_code').textContent = d.decision_code || 'UNKNOWN';
    $('#risk_score').textContent = 'Risk: ' + (d.risk_score ?? 'n.a.');
    $('#equity_value').textContent = 'Equity: ' + (d.equity_value ?? 'n.a.');
  }catch(err){ showError('Riport/döntés hiba', err); }
  finally{ $('#spinner').style.display='none'; }
});
