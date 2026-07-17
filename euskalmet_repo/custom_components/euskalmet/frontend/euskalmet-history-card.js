class EuskalmetHistoryCard extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:"open"}); this.date=new Date(); }
  setConfig(config) { this.config={title:"Histórico Euskalmet",measure:"temperature",...config}; }
  set hass(hass) { this._hass=hass; if(!this.loaded) this.load(); }
  getCardSize(){return 6;}
  static getStubConfig(){return {measure:"temperature"};}
  async load(){
    if(!this._hass||this.loading)return; this.loading=true; this.render();
    try { this.data=await this._hass.callWS({type:"euskalmet/history",entry_id:this.config.entry_id,
      year:this.date.getFullYear(),month:this.date.getMonth()+1}); this.error=null; }
    catch(e){this.error=String(e.message||e);} this.loading=false; this.loaded=true; this.render();
  }
  item(){return this.data?.items?.find(i=>i.measureId===this.config.measure);}
  points(field){return (this.item()?.dailySummaries||[]).map((s,i)=>({x:i+1,y:
    typeof s[field]==="object"?s[field]?.value:s[field]})).filter(p=>Number.isFinite(p.y));}
  path(points,w,h,min,max){return points.map((p,i)=>`${i?"L":"M"} ${30+(p.x-1)*(w-45)/30} ${10+(max-p.y)*(h-30)/(max-min||1)}`).join(" ");}
  shift(delta){this.date=new Date(this.date.getFullYear(),this.date.getMonth()+delta,1);this.loaded=false;this.load();}
  render(){
    const labels={temperature:"Temperatura (°C)",precipitation:"Precipitación (mm)",humidity:"Humedad (%)",
      pressure:"Presión (hPa)",irradiance:"Radiación (W/m²)",mean_speed:"Viento medio (m/s)",max_speed:"Racha (m/s)"};
    const fields=this.config.measure==="temperature"?["min","mean","max"]:
      this.config.measure==="precipitation"?["total"]:["mean","max"];
    const series=fields.map(f=>({f,p:this.points(f)})); const values=series.flatMap(s=>s.p.map(p=>p.y));
    const min=Math.min(...values,0),max=Math.max(...values,1),colors=["#42a5f5","#66bb6a","#ef5350"];
    const month=this.date.toLocaleDateString("es-ES",{month:"long",year:"numeric"});
    this.shadowRoot.innerHTML=`<style>:host{display:block}ha-card{padding:16px}header{display:flex;justify-content:space-between;align-items:center}
      h2{font-size:18px;margin:0}button,select{color:var(--primary-text-color);background:transparent;border:1px solid var(--divider-color);border-radius:8px;padding:7px}
      .tools{display:flex;gap:8px;align-items:center}.legend{display:flex;gap:14px;font-size:12px;margin:8px 0}.dot{width:9px;height:9px;border-radius:50%;display:inline-block}
      svg{width:100%;height:260px}.grid{stroke:var(--divider-color);stroke-width:1}.line{fill:none;stroke-width:2}.msg{padding:70px;text-align:center}</style>
      <ha-card><header><div><h2>${this.config.title}</h2><small>${month}</small></div><div class="tools"><button id="prev">‹</button><button id="next">›</button></div></header>
      <select id="measure">${Object.entries(labels).map(([k,v])=>`<option value="${k}" ${k===this.config.measure?"selected":""}>${v}</option>`).join("")}</select>
      ${this.loading?'<div class="msg">Cargando…</div>':this.error?`<div class="msg">${this.error}</div>`:`<div class="legend">${series.map((s,i)=>`<span><i class="dot" style="background:${colors[i]}"></i> ${s.f}</span>`).join("")}</div><svg viewBox="0 0 600 260"><line class="grid" x1="30" y1="230" x2="585" y2="230"/>${series.map((s,i)=>`<path class="line" stroke="${colors[i]}" d="${this.path(s.p,600,260,min,max)}"/>`).join("")}<text x="30" y="250" fill="currentColor">1</text><text x="555" y="250" fill="currentColor">31</text><text x="2" y="18" fill="currentColor">${max.toFixed(1)}</text><text x="2" y="230" fill="currentColor">${min.toFixed(1)}</text></svg>`}</ha-card>`;
    this.shadowRoot.querySelector("#prev")?.addEventListener("click",()=>this.shift(-1));
    this.shadowRoot.querySelector("#next")?.addEventListener("click",()=>this.shift(1));
    this.shadowRoot.querySelector("#measure")?.addEventListener("change",e=>{this.config.measure=e.target.value;this.render();});
  }
}
customElements.define("euskalmet-history-card",EuskalmetHistoryCard);
window.customCards=window.customCards||[];window.customCards.push({type:"euskalmet-history-card",name:"Euskalmet - Histórico",description:"Gráficos diarios históricos de Euskalmet"});
