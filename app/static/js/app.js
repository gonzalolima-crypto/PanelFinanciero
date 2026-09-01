/* Panel Financiero — frontend
   Habla con el backend Flask por /api/*. La interpretación de voz y de
   comprobantes la hace Gemini del lado del servidor. */

const CATS = {
  gasto_diario: ["Alimentos","Transporte","Salud","Ocio","Servicios","Hogar","Otros"],
  gasto_tarjeta: ["Alimentos","Transporte","Salud","Ocio","Servicios","Hogar","Suscripciones","Otros"],
  impuesto: ["Ganancias","IIBB","Monotributo","ABL/Municipal","Patente","Otros"],
  ingreso_sueldo: [],
  ingreso_extra: ["Freelance","Venta","Bono","Regalo","Otros"]
};
const TYPE_LABEL = {
  gasto_diario:"Gasto diario", gasto_tarjeta:"Gasto tarjeta", impuesto:"Impuesto",
  ingreso_sueldo:"Ingreso sueldo", ingreso_extra:"Ingreso extra"
};
const COLORS = { coral:"#E8654F", amber:"#E8A33D", blue:"#6FA8E8", green:"#6FCF97", ink:"#F2EFE6", dim:"#A9B5AC", grid:"#2A362E" };

let movements = [];
let config = { goalPct: 20 };
let charts = {};

const fmt = n => "$ " + Math.round(n).toLocaleString("es-AR");
const todayISO = () => new Date().toISOString().slice(0,10);
const monthKey = d => d.slice(0,7);
const monthLabel = key => {
  const [y,m] = key.split("-");
  const names = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
  return names[parseInt(m,10)-1] + " " + y;
};

/* ---- API helpers ---- */
async function api(path, opts){
  const res = await fetch(path, opts);
  if(res.status === 401){ window.location.href = '/login'; throw new Error('sesión expirada'); }
  let body = null;
  try{ body = await res.json(); }catch(e){}
  if(!res.ok){ throw new Error((body && body.error) || ('error ' + res.status)); }
  return body;
}

async function loadData(){
  try{ movements = await api('/api/movements'); }
  catch(e){ movements = []; }
  try{ config = await api('/api/config'); }
  catch(e){ config = { goalPct: 20 }; }
}

function setStatus(msg){
  document.getElementById('formStatus').textContent = msg;
  setTimeout(()=>{ document.getElementById('formStatus').textContent=''; }, 2800);
}

function populateCategories(){
  const type = document.getElementById('fType').value;
  const wrap = document.getElementById('fCatWrap');
  const sel = document.getElementById('fCat');
  const opts = CATS[type];
  if(!opts.length){ wrap.style.display='none'; sel.innerHTML=''; return; }
  wrap.style.display='';
  sel.innerHTML = opts.map(c=>`<option value="${c}">${c}</option>`).join('');
}

function populateMonthSelect(){
  const sel = document.getElementById('monthSelect');
  const cur = todayISO().slice(0,7);
  const set = new Set(movements.map(m=>monthKey(m.date)));
  set.add(cur);
  const months = Array.from(set).sort().reverse();
  const prevVal = sel.value || cur;
  sel.innerHTML = months.map(m=>`<option value="${m}">${monthLabel(m)}</option>`).join('');
  sel.value = months.includes(prevVal) ? prevVal : cur;
}

function monthMovements(mk){ return movements.filter(m=>monthKey(m.date)===mk); }
function sumBy(list, type){ return list.filter(m=>m.type===type).reduce((a,m)=>a+m.amount,0); }

function renderReceipt(){
  const mk = document.getElementById('monthSelect').value;
  const list = monthMovements(mk);
  const sueldo = sumBy(list,'ingreso_sueldo');
  const extra = sumBy(list,'ingreso_extra');
  const diario = sumBy(list,'gasto_diario');
  const tarjeta = sumBy(list,'gasto_tarjeta');
  const impuestos = sumBy(list,'impuesto');
  const ingresos = sueldo+extra;
  const gastos = diario+tarjeta+impuestos;
  const ahorro = ingresos-gastos;

  document.getElementById('sIngresoSueldo').textContent = fmt(sueldo);
  document.getElementById('sIngresoExtra').textContent = fmt(extra);
  document.getElementById('sGastoDiario').textContent = fmt(diario);
  document.getElementById('sGastoTarjeta').textContent = fmt(tarjeta);
  document.getElementById('sImpuestos').textContent = fmt(impuestos);
  const ahorroEl = document.getElementById('sAhorro');
  ahorroEl.textContent = fmt(ahorro);
  ahorroEl.className = 'val total ' + (ahorro>=0 ? 'pos':'neg');

  const realPct = ingresos>0 ? (ahorro/ingresos*100) : 0;
  const goalPct = config.goalPct;
  document.getElementById('goalPctLabel').textContent = goalPct+'%';
  document.getElementById('goalPctInput').value = goalPct;
  document.getElementById('goalRealPct').textContent = 'real: ' + realPct.toFixed(1) + '%';
  const fillPct = Math.max(0, Math.min(100, (realPct/Math.max(goalPct,1))*100));
  const fillEl = document.getElementById('goalBarFill');
  fillEl.style.width = fillPct+'%';
  fillEl.style.background = realPct>=goalPct ? 'linear-gradient(90deg,#6FCF97,#8fe0b3)' : 'linear-gradient(90deg,#E8A33D,#f0c274)';

  document.getElementById('tableMonthLabel').textContent = monthLabel(mk);
}

function renderTable(){
  const mk = document.getElementById('monthSelect').value;
  const list = monthMovements(mk).slice().sort((a,b)=> b.date.localeCompare(a.date));
  const tbody = document.getElementById('tbody');
  document.getElementById('countLabel').textContent = list.length + ' movimiento(s)';
  document.getElementById('emptyMsg').style.display = list.length? 'none':'block';
  tbody.innerHTML = list.map(m=>{
    const sign = m.type.startsWith('ingreso') ? '+' : '−';
    const color = m.type.startsWith('ingreso') ? 'var(--green)' : (m.type==='impuesto'?'var(--amber)':'var(--coral)');
    return `<tr>
      <td>${m.date}</td>
      <td><span class="tag ${m.type}">${TYPE_LABEL[m.type]}</span></td>
      <td class="cat">${escapeHtml(m.category||'—')}</td>
      <td class="cat" style="color:var(--ink-faint)">${escapeHtml(m.note||'')}</td>
      <td style="text-align:right;color:${color};font-weight:600;">${sign} ${fmt(m.amount)}</td>
      <td><button class="btn secondary" data-id="${m.id}">borrar</button></td>
    </tr>`;
  }).join('');
  tbody.querySelectorAll('button[data-id]').forEach(b=>{
    b.addEventListener('click', ()=> deleteMovement(b.getAttribute('data-id')));
  });
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

function destroyChart(key){ if(charts[key]){ charts[key].destroy(); } }

function baseGridOptions(){
  return {
    scales:{
      x:{ ticks:{ color: COLORS.dim, font:{family:"'JetBrains Mono',monospace", size:10} }, grid:{ color: COLORS.grid } },
      y:{ ticks:{ color: COLORS.dim, font:{family:"'JetBrains Mono',monospace", size:10}, callback:v=>'$'+v.toLocaleString('es-AR') }, grid:{ color: COLORS.grid } }
    },
    plugins:{ legend:{ labels:{ color: COLORS.ink, font:{size:11} } } }
  };
}

function daysInMonth(mk){
  const [y,m] = mk.split('-').map(Number);
  return new Date(y, m, 0).getDate();
}

function renderDailyCharts(){
  const mk = document.getElementById('monthSelect').value;
  const nDays = daysInMonth(mk);
  const labels = Array.from({length:nDays}, (_,i)=> String(i+1).padStart(2,'0'));
  const diarioData = new Array(nDays).fill(0);
  const tarjetaData = new Array(nDays).fill(0);
  monthMovements(mk).forEach(m=>{
    const day = parseInt(m.date.slice(8,10),10)-1;
    if(m.type==='gasto_diario') diarioData[day]+=m.amount;
    if(m.type==='gasto_tarjeta') tarjetaData[day]+=m.amount;
  });

  destroyChart('daily');
  charts.daily = new Chart(document.getElementById('chartDaily'), {
    type:'bar',
    data:{ labels, datasets:[{ label:'Gasto diario', data:diarioData, backgroundColor: COLORS.coral, borderRadius:3 }] },
    options:{ ...baseGridOptions(), responsive:true, maintainAspectRatio:true }
  });

  destroyChart('card');
  charts.card = new Chart(document.getElementById('chartCard'), {
    type:'bar',
    data:{ labels, datasets:[{ label:'Gasto tarjeta', data:tarjetaData, backgroundColor: COLORS.amber, borderRadius:3 }] },
    options:{ ...baseGridOptions(), responsive:true, maintainAspectRatio:true }
  });
}

function lastMonths(n){
  const out=[];
  const d = new Date();
  for(let i=n-1;i>=0;i--){
    const dt = new Date(d.getFullYear(), d.getMonth()-i, 1);
    out.push(dt.toISOString().slice(0,7));
  }
  return out;
}

function renderMonthlyCharts(){
  const months = lastMonths(6);
  const labels = months.map(monthLabel);

  const sueldoArr = months.map(mk=> sumBy(monthMovements(mk),'ingreso_sueldo'));
  const extraArr = months.map(mk=> sumBy(monthMovements(mk),'ingreso_extra'));
  const taxArr = months.map(mk=> sumBy(monthMovements(mk),'impuesto'));
  const ahorroArr = months.map(mk=>{
    const list = monthMovements(mk);
    const ing = sumBy(list,'ingreso_sueldo')+sumBy(list,'ingreso_extra');
    const gas = sumBy(list,'gasto_diario')+sumBy(list,'gasto_tarjeta')+sumBy(list,'impuesto');
    return ing-gas;
  });
  const goalArr = months.map(mk=>{
    const list = monthMovements(mk);
    const ing = sumBy(list,'ingreso_sueldo')+sumBy(list,'ingreso_extra');
    return ing * (config.goalPct/100);
  });

  destroyChart('income');
  charts.income = new Chart(document.getElementById('chartIncome'), {
    type:'bar',
    data:{ labels, datasets:[
      { label:'Sueldo', data:sueldoArr, backgroundColor: COLORS.blue, borderRadius:3, stack:'s' },
      { label:'Extra', data:extraArr, backgroundColor: COLORS.green, borderRadius:3, stack:'s' }
    ]},
    options:{ ...baseGridOptions(), responsive:true, maintainAspectRatio:true, scales:{ ...baseGridOptions().scales, x:{...baseGridOptions().scales.x, stacked:true}, y:{...baseGridOptions().scales.y, stacked:true} } }
  });

  destroyChart('tax');
  charts.tax = new Chart(document.getElementById('chartTax'), {
    type:'line',
    data:{ labels, datasets:[{ label:'Impuestos', data:taxArr, borderColor: COLORS.amber, backgroundColor:'rgba(232,163,61,0.15)', fill:true, tension:0.3, pointBackgroundColor: COLORS.amber }] },
    options:{ ...baseGridOptions(), responsive:true, maintainAspectRatio:true }
  });

  destroyChart('savings');
  charts.savings = new Chart(document.getElementById('chartSavings'), {
    type:'bar',
    data:{ labels, datasets:[
      { type:'bar', label:'Ahorro real', data:ahorroArr, backgroundColor: ahorroArr.map(v=> v>=0? COLORS.green: COLORS.coral), borderRadius:3 },
      { type:'line', label:'Objetivo ('+config.goalPct+'%)', data:goalArr, borderColor: COLORS.dim, borderDash:[5,4], pointRadius:0, tension:0 }
    ]},
    options:{ ...baseGridOptions(), responsive:true, maintainAspectRatio:true }
  });
}

function renderCategoryChart(){
  const mk = document.getElementById('monthSelect').value;
  const list = monthMovements(mk).filter(m=> m.type==='gasto_diario' || m.type==='gasto_tarjeta');
  const byCat = {};
  list.forEach(m=>{ byCat[m.category] = (byCat[m.category]||0) + m.amount; });
  const labels = Object.keys(byCat);
  const data = Object.values(byCat);
  const palette = ["#E8654F","#E8A33D","#6FA8E8","#6FCF97","#B08FE8","#E8D06F","#7EC8C8","#E88FB0"];

  destroyChart('category');
  charts.category = new Chart(document.getElementById('chartCategory'), {
    type:'doughnut',
    data:{ labels, datasets:[{ data, backgroundColor: labels.map((_,i)=>palette[i%palette.length]), borderColor: COLORS.grid, borderWidth:2 }] },
    options:{ responsive:true, maintainAspectRatio:true, plugins:{ legend:{ position:'bottom', labels:{ color: COLORS.ink, font:{size:10.5}, boxWidth:10 } } } }
  });
}

function renderAll(){
  populateMonthSelect();
  renderReceipt();
  renderTable();
  renderDailyCharts();
  renderMonthlyCharts();
  renderCategoryChart();
}

async function deleteMovement(id){
  try{
    await api('/api/movements/'+encodeURIComponent(id), { method:'DELETE' });
    movements = movements.filter(m=>m.id!==id);
    renderAll();
  }catch(e){ setStatus('No se pudo borrar: ' + e.message); }
}

async function addMovement(){
  const type = document.getElementById('fType').value;
  const date = document.getElementById('fDate').value || todayISO();
  const amount = parseFloat(document.getElementById('fAmount').value);
  const category = CATS[type].length ? document.getElementById('fCat').value : '';
  const note = document.getElementById('fNote').value.trim();

  if(!amount || amount<=0){ setStatus('Ingresá un monto válido.'); return; }

  try{
    const mv = await api('/api/movements', {
      method:'POST',
      headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({ type, date, category, amount, note })
    });
    movements.unshift(mv);
    document.getElementById('fAmount').value='';
    document.getElementById('fNote').value='';
    setStatus('Movimiento agregado.');
    renderAll();
  }catch(e){ setStatus('No se pudo guardar: ' + e.message); }
}

/* ---- voz: dictado en vivo (Web Speech API) ---- */
let recognition = null;
let listening = false;
let recognitionSupported = false;

function setVoiceBadge(text, kind){
  const b = document.getElementById('voiceBadge');
  b.textContent = text;
  b.className = 'voice-badge show ' + (kind||'');
}
function clearVoiceBadge(){ document.getElementById('voiceBadge').className = 'voice-badge'; }

function initSpeechRecognition(){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){
    document.getElementById('voiceStatus').textContent =
      'Tu navegador no soporta dictado en vivo. Usá el link "subir un audio grabado" de abajo, o cargá el movimiento a mano.';
    return;
  }
  recognitionSupported = true;
  recognition = new SR();
  recognition.lang = 'es-AR';
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onstart = ()=>{
    listening = true;
    document.getElementById('micBtn').classList.add('listening');
    document.getElementById('voiceStatus').textContent = 'escuchando...';
    clearVoiceBadge();
    const t = document.getElementById('voiceTranscript');
    t.textContent = ''; t.classList.remove('show');
  };
  recognition.onresult = (e)=>{
    let transcript = '';
    for(let i=0;i<e.results.length;i++){ transcript += e.results[i][0].transcript; }
    const t = document.getElementById('voiceTranscript');
    t.textContent = '"' + transcript + '"';
    t.classList.add('show');
    if(e.results[e.results.length-1].isFinal){ parseVoiceText(transcript); }
  };
  recognition.onerror = (e)=>{
    listening = false;
    document.getElementById('micBtn').classList.remove('listening');
    document.getElementById('voiceStatus').textContent = 'No se pudo escuchar (' + e.error + '). Probá de nuevo o subí un audio.';
  };
  recognition.onend = ()=>{
    listening = false;
    document.getElementById('micBtn').classList.remove('listening');
  };
}

/* ---- voz: grabar audio y transcribir en el servidor ---- */
let mediaRecorder = null;
let recordedChunks = [];
let recording = false;

async function startRecording(){
  if(!navigator.mediaDevices || !window.MediaRecorder){
    document.getElementById('voiceStatus').textContent = 'Tu navegador no permite grabar audio. Usá el link para subir un archivo.';
    return;
  }
  try{
    const stream = await navigator.mediaDevices.getUserMedia({ audio:true });
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e=>{ if(e.data.size>0) recordedChunks.push(e.data); };
    mediaRecorder.onstop = async ()=>{
      stream.getTracks().forEach(t=>t.stop());
      const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      await sendAudio(blob, 'grabacion');
    };
    mediaRecorder.start();
    recording = true;
    document.getElementById('micBtn').classList.add('listening');
    document.getElementById('voiceStatus').textContent = 'grabando... tocá el micrófono de nuevo para terminar';
  }catch(e){
    document.getElementById('voiceStatus').textContent = 'No se pudo acceder al micrófono (' + e.message + ').';
  }
}

function stopRecording(){
  if(mediaRecorder && recording){
    recording = false;
    document.getElementById('micBtn').classList.remove('listening');
    document.getElementById('voiceStatus').textContent = 'procesando audio...';
    mediaRecorder.stop();
  }
}

async function sendAudio(blob, name){
  setVoiceBadge('transcribiendo…','working');
  try{
    const fd = new FormData();
    fd.append('audio', blob, (name||'audio') + '.' + ((blob.type.split('/')[1]||'webm').split(';')[0]));
    const res = await api('/api/voice/transcribe', { method:'POST', body: fd });
    const text = (res && res.text) || '';
    const t = document.getElementById('voiceTranscript');
    t.textContent = '"' + text + '"'; t.classList.add('show');
    await parseVoiceText(text);
  }catch(e){
    setVoiceBadge('no se pudo','err');
    document.getElementById('voiceStatus').textContent = 'No se pudo transcribir el audio: ' + e.message;
  }
}

function micButtonClick(){
  if(recognitionSupported){
    if(!recognition) return;
    if(listening){ recognition.stop(); return; }
    try{ recognition.start(); }
    catch(e){ document.getElementById('voiceStatus').textContent = 'No se pudo iniciar el micrófono.'; }
  }else{
    if(recording) stopRecording(); else startRecording();
  }
}

async function parseVoiceText(transcript){
  transcript = (transcript||'').trim();
  if(!transcript){ setVoiceBadge('no se entendió','err'); return; }
  document.getElementById('voiceStatus').textContent = 'interpretando...';
  setVoiceBadge('procesando…','working');
  try{
    const parsed = await api('/api/voice/parse', {
      method:'POST',
      headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({ text: transcript })
    });

    document.getElementById('fType').value = parsed.type;
    populateCategories();
    document.getElementById('fDate').value = parsed.date || todayISO();
    if(CATS[parsed.type] && CATS[parsed.type].length){
      const catSel = document.getElementById('fCat');
      const match = CATS[parsed.type].find(c=> c.toLowerCase()===String(parsed.category||'').toLowerCase());
      catSel.value = match || CATS[parsed.type][CATS[parsed.type].length-1];
    }
    document.getElementById('fAmount').value = parsed.amount;
    document.getElementById('fNote').value = parsed.note || '';

    setVoiceBadge('listo ✓','ok');
    document.getElementById('voiceStatus').textContent = 'Revisá los datos completados abajo y tocá "Agregar" para guardarlo.';
    document.getElementById('fAmount').scrollIntoView({behavior:'smooth', block:'center'});
  }catch(err){
    setVoiceBadge('no se entendió','err');
    document.getElementById('voiceStatus').textContent = 'No se pudo interpretar: ' + err.message;
  }
}

/* ---- adjuntar comprobante ---- */
let pendingAttachment = null;

function setAttachBusy(busy){
  const b = document.getElementById('attachBtn');
  b.classList.toggle('busy', !!busy);
}

async function handleFileSelected(file){
  if(!file) return;
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  const okType = ['application/pdf','image/jpeg','image/png'].includes(file.type);
  const okExt = ['pdf','jpg','jpeg','png'].includes(ext);
  if(!okType && !okExt){
    document.getElementById('attachStatus').textContent = 'Formato no soportado. Usá un PDF (o una foto JPG/PNG).';
    return;
  }
  document.getElementById('attachStatus').textContent = 'analizando comprobante...';
  setAttachBusy(true);
  try{
    const fd = new FormData();
    fd.append('file', file, file.name);
    const parsed = await api('/api/attachment/parse', { method:'POST', body: fd });

    const groups = {};
    (parsed.items||[]).forEach(it=>{
      const cat = it.category && it.category.trim() ? it.category.trim() : 'Otros';
      if(!groups[cat]) groups[cat] = { items:[], included:true };
      groups[cat].items.push({ date: it.date, merchant: it.merchant || '', amount: Number(it.amount)||0 });
    });
    pendingAttachment = {
      fileName: parsed.fileName || file.name,
      cardBrand: parsed.card_brand || '',
      docType: parsed.doc_type || 'ticket',
      groups
    };
    renderAttachmentReview();
    document.getElementById('attachStatus').textContent = 'PDF de resumen de tarjeta (Visa / Mastercard) o de ticket';
  }catch(err){
    document.getElementById('attachStatus').textContent = 'No se pudo interpretar el comprobante: ' + err.message;
  }finally{
    setAttachBusy(false);
  }
}

function renderAttachmentReview(){
  if(!pendingAttachment) return;
  const card = document.getElementById('reviewCard');
  card.style.display = 'block';
  document.getElementById('reviewFile').textContent = 'archivo: ' + pendingAttachment.fileName;
  document.getElementById('reviewBrand').textContent = pendingAttachment.cardBrand
    ? pendingAttachment.cardBrand.toUpperCase() + ' detectada'
    : (pendingAttachment.docType==='ticket' ? 'Ticket' : 'Resumen');
  const totalItems = Object.values(pendingAttachment.groups).reduce((a,g)=>a+g.items.length,0);
  document.getElementById('reviewCount').textContent = totalItems + (totalItems===1 ? ' consumo' : ' consumos');

  const wrap = document.getElementById('reviewGroups');
  wrap.innerHTML = Object.entries(pendingAttachment.groups).map(([cat,g], idx)=>{
    const sum = g.items.reduce((a,i)=>a+i.amount,0);
    const itemsHtml = g.items.map(i=> `<div class="item-row"><span>${i.date} · ${escapeHtml(i.merchant||'—')}</span><span>${fmt(i.amount)}</span></div>`).join('');
    return `<div class="group ${g.included?'':'excluded'}" data-cat="${escapeHtml(cat)}">
      <div class="group-row">
        <div class="group-left">
          <input type="checkbox" ${g.included?'checked':''} data-toggle="${escapeHtml(cat)}">
          <span class="group-name">${escapeHtml(cat)}</span>
          <span class="group-count">${g.items.length} ${g.items.length===1?'consumo':'consumos'}</span>
        </div>
        <span class="group-sum" data-expand="${idx}">${fmt(sum)}</span>
      </div>
      <div class="group-items" id="items-${idx}">${itemsHtml}</div>
    </div>`;
  }).join('');

  Array.from(wrap.querySelectorAll('input[data-toggle]')).forEach(cb=>{
    cb.addEventListener('change', ()=>{
      pendingAttachment.groups[cb.getAttribute('data-toggle')].included = cb.checked;
      renderAttachmentReview();
    });
  });
  Array.from(wrap.querySelectorAll('[data-expand]')).forEach(el=>{
    el.style.cursor = 'pointer';
    el.addEventListener('click', ()=>{
      document.getElementById('items-'+el.getAttribute('data-expand')).classList.toggle('show');
    });
  });

  const total = Object.values(pendingAttachment.groups).filter(g=>g.included)
    .reduce((a,g)=>a+g.items.reduce((x,i)=>x+i.amount,0),0);
  document.getElementById('reviewTotal').textContent = fmt(total);
}

async function confirmAttachment(){
  if(!pendingAttachment) return;
  const type = (pendingAttachment.cardBrand || pendingAttachment.docType==='resumen_tarjeta') ? 'gasto_tarjeta' : 'gasto_diario';
  const payload = [];
  Object.entries(pendingAttachment.groups).forEach(([cat,g])=>{
    if(!g.included) return;
    g.items.forEach(it=>{
      payload.push({
        type,
        date: it.date,
        category: cat,
        amount: it.amount,
        note: (it.merchant ? it.merchant+' — ' : '') + pendingAttachment.fileName
      });
    });
  });
  if(!payload.length){ cancelAttachment(); return; }
  try{
    await api('/api/movements/bulk', {
      method:'POST',
      headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({ movements: payload })
    });
    cancelAttachment();
    await loadData();
    renderAll();
    document.getElementById('attachStatus').textContent = 'Movimientos cargados desde el comprobante.';
  }catch(e){
    document.getElementById('attachStatus').textContent = 'No se pudieron cargar: ' + e.message;
  }
}

function cancelAttachment(){
  pendingAttachment = null;
  document.getElementById('reviewCard').style.display = 'none';
  document.getElementById('fileInput').value = '';
}

async function init(){
  document.getElementById('todayLabel').textContent = new Date().toLocaleDateString('es-AR', { weekday:'long', year:'numeric', month:'long', day:'numeric' });
  document.getElementById('fDate').value = todayISO();
  populateCategories();
  await loadData();
  renderAll();

  document.getElementById('fType').addEventListener('change', populateCategories);
  document.getElementById('fSubmit').addEventListener('click', addMovement);
  document.getElementById('micBtn').addEventListener('click', micButtonClick);
  initSpeechRecognition();

  document.getElementById('audioUploadLink').addEventListener('click', ()=> document.getElementById('audioInput').click());
  document.getElementById('audioInput').addEventListener('change', (e)=>{
    const f = e.target.files[0];
    if(f) sendAudio(f, f.name.replace(/\.[^.]+$/,''));
    e.target.value = '';
  });

  document.getElementById('attachBtn').addEventListener('click', ()=> document.getElementById('fileInput').click());
  document.getElementById('fileInput').addEventListener('change', (e)=> handleFileSelected(e.target.files[0]));
  document.getElementById('reviewConfirm').addEventListener('click', confirmAttachment);
  document.getElementById('reviewCancel').addEventListener('click', cancelAttachment);

  document.getElementById('monthSelect').addEventListener('change', ()=>{
    renderReceipt(); renderTable(); renderDailyCharts(); renderCategoryChart();
  });
  document.getElementById('goalPctInput').addEventListener('change', async (e)=>{
    let v = parseFloat(e.target.value);
    if(isNaN(v)||v<0) v=0; if(v>100) v=100;
    try{
      config = await api('/api/config', {
        method:'PUT',
        headers:{ 'Content-Type':'application/json' },
        body: JSON.stringify({ goalPct: v })
      });
      renderReceipt();
      renderMonthlyCharts();
    }catch(err){ setStatus('No se pudo guardar el objetivo: ' + err.message); }
  });
}
init();
