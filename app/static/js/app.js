/* Panel Financiero — frontend
   Habla con el backend Flask por /api/*. La interpretación de voz y de
   comprobantes la hace Groq del lado del servidor. */

// Categorías de gasto (mismas para "gasto diario" y "gasto con tarjeta").
// Primero las categorías propias del usuario, después las genéricas, "Otros" al final.
const CATS_GASTO = [
  "Compra de Super","Colegio","Gastos Delfi","Gastos Lu","Delivery","Gastos Autos",
  "Gastos Viajes","Regalos","Ropa","Gastos Padres",
  "Alimentos","Transporte","Salud","Ocio","Servicios","Hogar","Suscripciones","Otros"
];
const CATS = {
  gasto_diario: CATS_GASTO,
  gasto_tarjeta: CATS_GASTO,
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
const fmtUsd = n => "US$ " + Number(n||0).toLocaleString("es-AR", {minimumFractionDigits:2, maximumFractionDigits:2});
const fmtCur = (n, cur) => cur === 'USD' ? fmtUsd(n) : fmt(n);
const curOf = m => (m.currency || 'ARS');
const todayISO = () => new Date().toISOString().slice(0,10);
const monthKey = d => d.slice(0,7);
const monthLabel = key => {
  const [y,m] = key.split("-");
  const names = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
  return names[parseInt(m,10)-1] + " " + y;
};
// Fecha con la que un movimiento se imputa a un mes. Para casi todo es la
// fecha real; para los consumos de un resumen de tarjeta es la fecha de
// vencimiento (el mes en que se paga).
const effDate = m => m.effective_date || m.date;
const effMonth = m => monthKey(effDate(m));

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
  const set = new Set(movements.map(effMonth));
  set.add(cur);
  const months = Array.from(set).sort().reverse();
  const prevVal = sel.value || cur;
  sel.innerHTML = months.map(m=>`<option value="${m}">${monthLabel(m)}</option>`).join('');
  sel.value = months.includes(prevVal) ? prevVal : cur;
}

function monthMovements(mk){ return movements.filter(m=>effMonth(m)===mk); }
function sumBy(list, type, cur){
  cur = cur || 'ARS';
  return list.filter(m=>m.type===type && curOf(m)===cur).reduce((a,m)=>a+m.amount,0);
}
function monthHasUsd(list){ return list.some(m=>curOf(m)==='USD'); }

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

  // --- bloque en dólares ---
  const uIngresos = sumBy(list,'ingreso_sueldo','USD') + sumBy(list,'ingreso_extra','USD');
  const uDiario = sumBy(list,'gasto_diario','USD');
  const uTarjeta = sumBy(list,'gasto_tarjeta','USD');
  const uImpuestos = sumBy(list,'impuesto','USD');
  const uAhorro = uIngresos - (uDiario+uTarjeta+uImpuestos);
  document.getElementById('uIngresos').textContent = fmtUsd(uIngresos);
  document.getElementById('uGastoDiario').textContent = fmtUsd(uDiario);
  document.getElementById('uGastoTarjeta').textContent = fmtUsd(uTarjeta);
  document.getElementById('uImpuestos').textContent = fmtUsd(uImpuestos);
  const uAhorroEl = document.getElementById('uAhorro');
  uAhorroEl.textContent = fmtUsd(uAhorro);
  uAhorroEl.className = 'val total ' + (uAhorro>=0 ? 'pos':'neg');
  document.getElementById('usdBlock').classList.toggle('empty', !monthHasUsd(list));

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
    const isIngreso = m.type.startsWith('ingreso');
    const isReintegro = !isIngreso && m.amount < 0;   // devolución en un gasto
    const sign = (isIngreso || isReintegro) ? '+' : '−';
    const color = (isIngreso || isReintegro) ? 'var(--green)'
      : (m.type==='impuesto' ? 'var(--amber)' : 'var(--coral)');
    const imputado = monthKey(m.date) !== effMonth(m)
      ? `<div style="color:var(--ink-faint);font-size:10px;">se paga ${monthLabel(effMonth(m))}</div>` : '';
    const cur = curOf(m);
    const nota = (m.note||'') + (isReintegro ? ' · reintegro' : '');
    return `<tr>
      <td>${m.date}${imputado}</td>
      <td><span class="tag ${m.type}">${TYPE_LABEL[m.type]}${cur==='USD' ? ' · US$' : ''}</span></td>
      <td class="cat">${escapeHtml(m.category||'—')}</td>
      <td class="cat" style="color:var(--ink-faint)">${escapeHtml(nota)}</td>
      <td style="text-align:right;color:${color};font-weight:600;">${sign} ${fmtCur(Math.abs(m.amount), cur)}</td>
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
  // Se ubica cada gasto en el DÍA REAL de la compra (m.date), aunque el mes
  // mostrado sea el de imputación (vencimiento). Si el día no existe en ese
  // mes, se acota al último día. Los gráficos van en pesos (los consumos en
  // dólares se ven en el bloque US$ del resumen).
  monthMovements(mk).forEach(m=>{
    if(curOf(m)!=='ARS') return;
    let day = parseInt(m.date.slice(8,10),10) - 1;
    if(isNaN(day)) return;
    day = Math.max(0, Math.min(day, nDays-1));
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
  const list = monthMovements(mk).filter(m=> (m.type==='gasto_diario' || m.type==='gasto_tarjeta') && curOf(m)==='ARS' && m.amount>0);
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
  const currency = document.getElementById('fCurrency').value;
  const note = document.getElementById('fNote').value.trim();

  if(!amount || amount<=0){ setStatus('Ingresá un monto válido.'); return; }

  try{
    const mv = await api('/api/movements', {
      method:'POST',
      headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({ type, date, category, amount, note, currency })
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

    const items = (parsed.items||[]).map(it=>({
      date: it.date,
      merchant: it.merchant || '',
      amount: Number(it.amount)||0,
      currency: (it.currency === 'USD') ? 'USD' : 'ARS',
      category: (it.category && it.category.trim()) ? it.category.trim() : 'Otros',
      included: true
    }));
    pendingAttachment = {
      fileName: parsed.fileName || file.name,
      cardBrand: parsed.card_brand || '',
      docType: parsed.doc_type || 'ticket',
      dueDate: parsed.due_date || '',          // fecha de vencimiento detectada (o '')
      recon: parsed.reconciliation || null,
      items
    };
    renderAttachmentReview();
    document.getElementById('attachStatus').textContent = 'PDF de resumen de tarjeta (Visa / Mastercard) o de ticket';
  }catch(err){
    document.getElementById('attachStatus').textContent = 'No se pudo interpretar el comprobante: ' + err.message;
  }finally{
    setAttachBusy(false);
  }
}

function updateImpMonth(){
  const v = (document.getElementById('reviewDueDate')||{}).value || '';
  document.getElementById('reviewImpMonth').textContent =
    v ? '→ se carga en ' + monthLabel(monthKey(v)) : '';
}

function renderImputacion(){
  const box = document.getElementById('reviewImputacion');
  const input = document.getElementById('reviewDueDate');
  if(!pendingAttachment || pendingAttachment.docType !== 'resumen_tarjeta'){
    box.style.display = 'none';
    return;
  }
  box.style.display = 'block';
  if(!input.value) input.value = pendingAttachment.dueDate || '';
  box.classList.toggle('warn', !input.value);
  document.getElementById('reviewImpLabel').textContent = pendingAttachment.dueDate
    ? 'Los consumos de este resumen se imputan al mes en que lo pagás (vencimiento). En el detalle vas a ver la fecha real de cada compra.'
    : 'No se detectó la fecha de vencimiento. Indicá cuándo pagás este resumen: los consumos se cargan en ese mes.';
  updateImpMonth();
  input.onchange = ()=>{
    box.classList.toggle('warn', !input.value);
    updateImpMonth();
  };
}

const money = (ars, usd) => {
  const parts = [];
  if(ars || !usd) parts.push(fmt(ars));
  if(usd) parts.push(fmtUsd(usd));
  return parts.join('  +  ');
};

function groupedAttachmentItems(){
  // agrupa los ítems por categoría, respetando el orden de CATS_GASTO
  const byCat = {};
  pendingAttachment.items.forEach((it, idx)=>{ (byCat[it.category] = byCat[it.category] || []).push(idx); });
  const order = CATS_GASTO.filter(c => byCat[c]).concat(Object.keys(byCat).filter(c => !CATS_GASTO.includes(c)));
  return order.map(cat => ({ cat, idxs: byCat[cat] }));
}

function renderAttachmentReview(){
  if(!pendingAttachment) return;
  const card = document.getElementById('reviewCard');
  card.style.display = 'block';
  document.getElementById('reviewFile').textContent = 'archivo: ' + pendingAttachment.fileName;
  document.getElementById('reviewBrand').textContent = pendingAttachment.cardBrand
    ? pendingAttachment.cardBrand.toUpperCase() + ' detectada'
    : (pendingAttachment.docType==='ticket' ? 'Ticket' : 'Resumen');
  const items = pendingAttachment.items;
  document.getElementById('reviewCount').textContent = items.length + (items.length===1 ? ' consumo' : ' consumos');

  renderImputacion();

  const catOptions = c => CATS_GASTO.map(o=>`<option${o===c?' selected':''}>${o}</option>`).join('');
  const sumIdxs = (idxs, cur) => idxs.filter(i=>items[i].currency===cur).reduce((a,i)=>a+items[i].amount,0);

  const wrap = document.getElementById('reviewGroups');
  wrap.innerHTML = groupedAttachmentItems().map(({cat, idxs}, gi)=>{
    const allInc = idxs.every(i=>items[i].included);
    const someInc = idxs.some(i=>items[i].included);
    const ars = sumIdxs(idxs,'ARS'), usd = sumIdxs(idxs,'USD');
    const rows = idxs.map(i=>{
      const it = items[i], neg = it.amount < 0;
      return `<div class="item-row" data-i="${i}">
        <label class="ir-left"><input type="checkbox" data-inc="${i}" ${it.included?'checked':''}>
          <span>${it.date} · ${escapeHtml(it.merchant||'—')}${neg?' · reintegro':''}</span></label>
        <span class="ir-right">
          <select data-cat="${i}">${catOptions(it.category)}</select>
          <span${neg?' style="color:var(--green)"':''}>${(neg?'+ ':'')}${fmtCur(Math.abs(it.amount), it.currency)}</span>
        </span>
      </div>`;
    }).join('');
    return `<div class="group ${allInc?'':(someInc?'partial':'excluded')}">
      <div class="group-row">
        <div class="group-left">
          <input type="checkbox" data-gtoggle="${gi}" ${allInc?'checked':''}>
          <span class="group-name">${escapeHtml(cat)}</span>
          <span class="group-count">${idxs.length} ${idxs.length===1?'consumo':'consumos'}</span>
        </div>
        <span class="group-sum" data-expand="${gi}">${money(ars, usd)}</span>
      </div>
      <div class="group-items" id="items-${gi}">${rows}</div>
    </div>`;
  }).join('');

  const groups = groupedAttachmentItems();
  wrap.querySelectorAll('input[data-gtoggle]').forEach(cb=>{
    cb.addEventListener('change', ()=>{
      groups[+cb.getAttribute('data-gtoggle')].idxs.forEach(i=> items[i].included = cb.checked);
      renderAttachmentReview();
    });
  });
  wrap.querySelectorAll('input[data-inc]').forEach(cb=>{
    cb.addEventListener('change', ()=>{ items[+cb.getAttribute('data-inc')].included = cb.checked; renderAttachmentReview(); });
  });
  wrap.querySelectorAll('select[data-cat]').forEach(sel=>{
    sel.addEventListener('change', ()=>{ items[+sel.getAttribute('data-cat')].category = sel.value; renderAttachmentReview(); });
  });
  wrap.querySelectorAll('[data-expand]').forEach(el=>{
    el.style.cursor = 'pointer';
    el.addEventListener('click', ()=> document.getElementById('items-'+el.getAttribute('data-expand')).classList.toggle('show'));
  });

  const inc = items.filter(i=>i.included);
  const totArs = inc.filter(i=>i.currency==='ARS').reduce((a,i)=>a+i.amount,0);
  const totUsd = inc.filter(i=>i.currency==='USD').reduce((a,i)=>a+i.amount,0);
  document.getElementById('reviewTotal').textContent = money(totArs, totUsd);

  renderRecon();
}

function renderRecon(){
  const el = document.getElementById('reviewRecon');
  const r = pendingAttachment && pendingAttachment.recon;
  if(!r || !r.statement){ el.style.display = 'none'; return; }
  el.style.display = 'block';
  const st = r.statement, c = r.check || {};
  const inc = pendingAttachment.items.filter(i=>i.included);
  const pos = (arr, cur) => arr.filter(i=>i.currency===cur && i.amount>0).reduce((a,i)=>a+i.amount,0);
  const negs = (arr, cur) => arr.filter(i=>i.currency===cur && i.amount<0).reduce((a,i)=>a+i.amount,0);
  const consArs = pos(inc,'ARS'), consUsd = pos(inc,'USD');
  const devArs = negs(inc,'ARS'), devUsd = negs(inc,'USD');
  const netoArs = consArs + devArs, netoUsd = consUsd + devUsd;
  const expArs = c.expected_ars || 0, expUsd = c.expected_usd || 0;
  const okArs = Math.abs(netoArs - expArs) <= 1.0, okUsd = Math.abs(netoUsd - expUsd) <= 0.5;

  const rr = (label, val, cls='') => `<div class="rr ${cls}"><span>${label}</span><span class="v">${val}</span></div>`;
  let html = '<h4>Reconciliación con tu resumen</h4>';
  html += rr('Consumos en pesos', fmt(consArs));
  if(consUsd) html += rr('Consumos en dólares', fmtUsd(consUsd));
  if(devArs) html += rr('Devoluciones / reintegros', '<span class="neg">'+fmt(devArs)+'</span>');
  if(devUsd) html += rr('Devoluciones en dólares', '<span class="neg">'+fmtUsd(devUsd)+'</span>');
  html += rr('Se carga al panel', money(netoArs, netoUsd), 'tot');

  if(st.cargos && st.cargos.length){
    html += '<div class="note">Cargos del resumen (NO se cargan al panel — solo para que cuadres):</div>';
    st.cargos.forEach(row=>{
      html += rr(escapeHtml(row.label), row.usd ? (fmt(row.ars)+'  '+fmtUsd(row.usd)) : fmt(row.ars), 'sub');
    });
    html += rr('Subtotal cargos', money(c.cargos_total_ars||0, c.cargos_total_usd||0), 'sub');
  }
  html += rr('SALDO ACTUAL del resumen', money(c.saldo_actual_ars||0, c.saldo_actual_usd||0), 'saldo');
  const ok = okArs && okUsd;
  html += `<div class="chk ${ok?'ok':'bad'}">`
    + (ok
       ? '✓ Los consumos cargados coinciden con el total de consumos del resumen.'
       : 'Los consumos cargados no coinciden con el total del resumen (esperado: '
         + money(expArs, expUsd) + '). Puede ser que hayas destildado algún ítem.')
    + '</div>';
  el.innerHTML = html;
}
async function confirmAttachment(){
  if(!pendingAttachment) return;
  const isResumen = pendingAttachment.docType === 'resumen_tarjeta';
  const type = (pendingAttachment.cardBrand || isResumen) ? 'gasto_tarjeta' : 'gasto_diario';

  let eff = '';
  if(isResumen){
    eff = (document.getElementById('reviewDueDate').value || '').trim();
    if(!eff){
      document.getElementById('reviewImputacion').classList.add('warn');
      document.getElementById('reviewDueDate').focus();
      document.getElementById('attachStatus').textContent = 'Indicá la fecha de vencimiento antes de cargar.';
      return;
    }
  }

  const payload = pendingAttachment.items.filter(it=>it.included).map(it=>{
    const mv = {
      type,
      date: it.date,
      category: it.category,
      amount: it.amount,
      currency: it.currency || 'ARS',
      note: (it.merchant ? it.merchant+' — ' : '') + pendingAttachment.fileName
    };
    if(eff) mv.effective_date = eff;
    return mv;
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
  document.getElementById('reviewImputacion').style.display = 'none';
  document.getElementById('reviewRecon').style.display = 'none';
  document.getElementById('reviewDueDate').value = '';
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
