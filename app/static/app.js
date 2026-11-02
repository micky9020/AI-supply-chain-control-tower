'use strict';
const $ = id => document.getElementById(id);
let orders = [];
const statusLabels = {processing:'En preparación',in_transit:'En tránsito',delayed:'Demorado',delivered:'Entregado'};
const el = (tag, text, cls) => {const x=document.createElement(tag); if(text!==undefined)x.textContent=String(text); if(cls)x.className=cls; return x;};
const money = n => new Intl.NumberFormat('es-PE',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n);
function display(data){
 $('content').hidden=false; $('timestamp').textContent='Datos de demostración';
 const m=$('metrics');m.replaceChildren();
 for(const [label,v] of [['Pedidos totales',data.overview.orders_total],['Activos',data.overview.orders_active],['Demorados',data.overview.orders_delayed],['Riesgo alto',data.overview.high_risk],['Valor de inventario',money(data.overview.inventory_value_usd)],['Puntualidad histórica',data.overview.on_time_rate_pct+'%']]){
   const card=el('div',undefined,'metric');card.append(el('span',label),el('strong',v));m.append(card);
 }
 const chart=$('statusChart');chart.replaceChildren();
 for(const s of data.by_status){const r=el('div',undefined,'chartrow');r.append(el('span',statusLabels[s.name]||s.name));const track=el('div',undefined,'track');const bar=el('div',undefined,'bar');bar.style.width=(s.count/Math.max(1,data.overview.orders_total)*100)+'%';track.append(bar);r.append(track,el('b',s.count));chart.append(r);}
 const alerts=$('alerts'); alerts.replaceChildren();
 if(!data.alerts.length)alerts.append(el('p','Sin alertas para estos datos.'));
 for(const a of data.alerts.slice(0,6)){const card=el('article',undefined,'alert');const title=el('strong',a.order_id+' · '+a.supplier);const pill=el('span',a.risk_level.toUpperCase(),'pill '+a.risk_level);card.append(title,pill,el('p',a.reasons.join(' · ')),el('small',a.suggestion));alerts.append(card);}
 orders=data.orders;renderOrders();$('disclaimer').textContent=data.model.note;
}
function renderOrders(){const q=$('filter').value.trim().toLowerCase();const tbody=$('orders');tbody.replaceChildren();for(const r of orders.filter(x=>(x.order_id+' '+x.supplier+' '+x.sku).toLowerCase().includes(q))){const tr=el('tr');for(const value of [r.order_id,r.supplier,r.origin+' → '+r.destination,r.sku,statusLabels[r.status],r.inventory_coverage_days===null?'Sin demanda':r.inventory_coverage_days,r.risk_level+' ('+r.risk_score+')',r.risk_reasons.join('; ')||'Sin señales'])tr.append(el('td',value));tbody.append(tr);}}
$('filter').addEventListener('input',renderOrders);
$('load').addEventListener('click',async()=>{const key=$('apiKey').value;$('apiKey').value='';if(!key){$('message').textContent='Introduce una clave.';return;}$('message').textContent='Cargando...';try{const response=await fetch('/api/dashboard',{headers:{'X-API-Key':key},cache:'no-store'});if(!response.ok)throw new Error(response.status===401?'Clave incorrecta.':`Error del servidor (${response.status}).`);display(await response.json());$('message').textContent='Datos cargados. La clave no se ha guardado en el navegador.';}catch(e){$('content').hidden=true;$('message').textContent=e.message;}});
