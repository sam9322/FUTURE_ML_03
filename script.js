'use strict';
const DEFAULT_API = 'http://localhost:7860';
let API = DEFAULT_API;
let files = [];
let results = [];
let selIdx = null;
let skills = ['Python', 'Machine Learning', 'SQL'];
let selectedSkills = new Set(skills);

function loadSavedData() {
  const savedApi = localStorage.getItem('resumeIQ_api');
  if (savedApi) API = savedApi;
  const savedResults = localStorage.getItem('resumeIQ_results');
  if (savedResults) { results = JSON.parse(savedResults); renderResults(); updateStats(); }
  const savedSkills = localStorage.getItem('resumeIQ_skills');
  if (savedSkills) { skills = JSON.parse(savedSkills); selectedSkills = new Set(skills); }
  renderSkills(); updateSkillCount(); loadSettings();
}
function saveData() { localStorage.setItem('resumeIQ_results', JSON.stringify(results)); localStorage.setItem('resumeIQ_skills', JSON.stringify(skills)); }
function renderSkills() { const c = document.getElementById('stags'); if(c) c.innerHTML = skills.map(s => `<span class="stag ${selectedSkills.has(s)?'on':''}" onclick="toggleSkill(this,'${s}')">${s}</span>`).join(''); updateSkillCount(); }
function updateSkillCount() { document.getElementById('skillCount').innerText = skills.length; }
function toggleSkill(el,s) { if(selectedSkills.has(s)) selectedSkills.delete(s); else selectedSkills.add(s); el.classList.toggle('on'); saveData(); }
function addSkill() { const inp=document.getElementById('newSkillInput'); const s=inp.value.trim(); if(!s)return; if(!skills.includes(s)){ skills.push(s); selectedSkills.add(s); renderSkills(); inp.value=''; saveData(); toast('s','Skill added',`${s} added`); } }
function getSelectedSkills() { return Array.from(selectedSkills); }

function switchView(v) {
  document.querySelectorAll('.view').forEach(view=>view.classList.remove('active'));
  document.getElementById(`${v}View`).classList.add('active');
  document.querySelectorAll('.ni').forEach(n=>n.classList.remove('active'));
  event.target.closest('.ni').classList.add('active');
  document.getElementById('pageTitle').innerText = v.charAt(0).toUpperCase()+v.slice(1);
  if(v==='analytics') updateAnalytics();
  if(v==='candidates') renderShortlisted();
}
function toggleSidebar(){ document.getElementById('sidebar').classList.toggle('open'); document.getElementById('overlay').classList.toggle('show'); }
function closeSidebar(){ document.getElementById('sidebar').classList.remove('open'); document.getElementById('overlay').classList.remove('show'); }
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeSidebar();});

async function checkAPI(){
  const adot=document.getElementById('adot'),ast=document.getElementById('ast'),sd=document.getElementById('sdot'),sl=document.getElementById('slbl');
  try{ const r=await fetch(`${API}/health`,{signal:AbortSignal.timeout(4000)}); if(r.ok){ adot.className='adot on'; ast.textContent='API online'; sd.style.background='var(--green)'; sl.textContent='Online'; } else throw new Error(); }
  catch{ adot.className='adot off'; ast.textContent='API offline'; sd.style.background='var(--red)'; sl.textContent='Offline'; }
}
checkAPI(); setInterval(checkAPI,30000);

const dz=document.getElementById('dz');
if(dz){
  dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('drag');});
  dz.addEventListener('dragleave',e=>{if(!dz.contains(e.relatedTarget))dz.classList.remove('drag');});
  dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('drag');addFiles(e.dataTransfer.files);});
}
async function addFiles(fl){
  let added=0,dupes=0,invalid=0;
  for(const f of fl){ const ext=f.name.split('.').pop().toLowerCase(); if(!['pdf','docx','txt'].includes(ext)){invalid++;continue;} if(files.find(x=>x.name===f.name&&x.size===f.size)){dupes++;continue;} files.push(f); added++; }
  renderFiles(); updateStats();
  if(added) toast('s',`${added} file${added>1?'s':''} added`,'Ready');
  if(dupes) toast('i','Duplicates skipped',`${dupes} duplicate(s)`);
  if(invalid) toast('e','Unsupported format','Only PDF,DOCX,TXT');
  document.getElementById('finput').value='';
}
function renderFiles(){ const c=document.getElementById('flist'); if(!c)return; c.innerHTML=files.map((f,i)=>{ const ext=f.name.split('.').pop().toLowerCase(); const kb=f.size/1024; const sz=kb>=1024?`${(kb/1024).toFixed(1)} MB`:`${kb.toFixed(0)} KB`; return `<div class="fi"><span class="fe">${ext}</span><span class="fn">${esc(f.name)}</span><span class="fsz">${sz}</span><button class="frm" onclick="rmFile(${i})">×</button></div>`; }).join(''); document.getElementById('nav-count').textContent=files.length; }
function rmFile(i){ files.splice(i,1); renderFiles(); updateStats(); toast('i','File removed',''); }
function clearFiles(){ if(!files.length)return; files=[]; renderFiles(); updateStats(); toast('i','Cleared','All files removed'); }

const pids=['p0','p1','p2','p3','p4'];
function resetPipe(){ pids.forEach(id=>document.getElementById(id).className='ps'); }
function setPipe(idx){ for(let i=0;i<idx;i++)document.getElementById(pids[i]).className='ps done'; if(idx<pids.length)document.getElementById(pids[idx]).className='ps active'; }
function donePipe(){ pids.forEach(id=>document.getElementById(id).className='ps done'); }
function setProgress(pct,lbl){ const w=document.getElementById('pw'); if(w)w.classList.add('show'); const pf=document.getElementById('pf'); if(pf)pf.style.width=pct+'%'; const plbl=document.getElementById('plbl'); if(plbl)plbl.textContent=lbl; const ppct=document.getElementById('ppct'); if(ppct)ppct.textContent=Math.round(pct)+'%'; }
function hideProgress(){ const w=document.getElementById('pw'); if(w)w.classList.remove('show'); }

async function runScreening(){
  const jobTitle = document.getElementById('jobTitle').value.trim();
  const jd = document.getElementById('jd').value.trim();
  if(!files.length){ toast('e','No files','Upload resumes'); return; }
  if(!jd){ toast('e','No job description','Paste job description'); return; }
  const wSem=parseInt(document.getElementById('ws').value)||70;
  const wSk=parseInt(document.getElementById('wk').value)||30;
  if(wSem+wSk!==100){ toast('e','Invalid weights','Must add to 100'); return; }
  const btn=document.getElementById('sbtn'); btn.disabled=true; btn.innerHTML='<svg class="spin" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Screening...';
  resetPipe(); setPipe(0); setProgress(5,'Parsing...');
  const out=[]; let failed=0; const selectedSkillsList=getSelectedSkills();
  for(let i=0;i<files.length;i++){
    const f=files[i]; const pct=5+((i/files.length)*75); setProgress(pct,`Processing ${i+1}/${files.length}: ${f.name}`);
    if(i===0)setPipe(1); if(i===Math.floor(files.length/2))setPipe(2);
    const fd=new FormData(); fd.append('file',f); fd.append('job_description',jd); fd.append('semantic_weight',(wSem/100).toString()); fd.append('skill_weight',(wSk/100).toString()); fd.append('required_skills',JSON.stringify(selectedSkillsList));
    if(jobTitle) fd.append('job_title',jobTitle);
    try{
      const resp=await fetch(`${API}/screen-form`,{method:'POST',body:fd,signal:AbortSignal.timeout(30000)});
      if(!resp.ok){ let errMsg=`HTTP ${resp.status}`; try{ const ed=await resp.json(); if(ed&&ed.detail) errMsg=typeof ed.detail==='string'?ed.detail:(ed.detail.message||ed.detail.error||errMsg); }catch(e){} throw new Error(errMsg); }
      const data=await resp.json();
      out.push({...data,_fn:f.name,_fo:f,composite_score:data.composite_score||0,semantic_score:data.semantic_score||0,skill_score:data.skill_score||0,matched_skills:data.matched_skills||[],missing_skills:data.missing_skills||[],recommendation:data.recommendation||'', email:data.email||'N/A', phone:data.phone||'N/A'});
    }catch(err){ failed++; out.push({_fn:f.name,_fo:f,_err:err.message,_fail:true,candidate_name:f.name.replace(/\.[^.]+$/,''),category:'Parse error',semantic_score:0,skill_score:0,composite_score:0,matched_skills:[],missing_skills:selectedSkillsList,recommendation:'Error processing file'}); }
  }
  setPipe(3); setProgress(82,'Computing scores...'); await delay(300);
  setPipe(4); setProgress(94,'Ranking...'); await delay(300);
  out.sort((a,b)=>b.composite_score-a.composite_score);
  results=out; donePipe(); setProgress(100,'Complete'); await delay(500); hideProgress();
  renderResults(); updateStats(); saveData(); saveScreeningToHistory();
  btn.disabled=false; btn.innerHTML='<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2" width="16" height="16"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Re-run Screening';
  if(!failed) toast('s','Screening complete',`${out.length} resume${out.length>1?'s':''} ranked`);
  else toast('e',`${failed} file${failed>1?'s':''} failed`,`${out.length-failed} succeeded`);
}
function delay(ms){return new Promise(r=>setTimeout(r,ms));}

function renderResults() {
  const body = document.getElementById('rbody');
  document.getElementById('rcount').textContent = results.length ? `${results.length} candidate${results.length > 1 ? 's' : ''}` : '';
  if (!results.length) {
    body.innerHTML = '<div class="es"><div class="ei"><svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.4"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0121 9.414V19a2 2 0 01-2 2z"/></svg></div><div class="et2">No results</div><div class="esub">Run screening to see ranked candidates.</div></div>';
    return;
  }
  body.innerHTML = `<div class="rlist">${results.map((r, i) => rcHTML(r, i)).join('')}</div>`;
}

function scClass(s){ const p = Math.round(s * 100); return p >= 65 ? 'rhi' : p >= 45 ? 'rmd' : 'rlo'; }

function rcHTML(r, i) {
  const pS = Math.round((r.semantic_score || 0) * 100);
  const pK = Math.round((r.skill_score || 0) * 100);
  const pC = Math.round((r.composite_score || 0) * 100);
  const chips = [...(r.matched_skills || []).slice(0, 4).map(s => `<span class="chip cmatch">${esc(s)}</span>`), ...(r.missing_skills || []).slice(0, 2).map(s => `<span class="chip cmiss">${esc(s)}</span>`)].join('');
  const errBanner = r._fail ? `<div class="errbanner"><svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Error: ${esc(r._err || 'Unknown')}</div>` : '';
  const recColor = r.composite_score >= 0.7 ? 'var(--green)' : r.composite_score >= 0.5 ? 'var(--amber)' : 'var(--red)';
  const recHtml = r.recommendation ? `<div style="margin-top: 10px; padding: 8px; background: var(--surface-3); border-radius: 6px; font-size: 12px; color: var(--text-2); border-left: 3px solid ${recColor};">📋 ${esc(r.recommendation)}</div>` : '';
  
  const matchedHtml = r.matched_skills && r.matched_skills.length > 0 ? 
    `<div style="margin-top: 8px;"><strong style="color: var(--green);">Matched Skills:</strong> ${r.matched_skills.join(', ')}</div>` : 
    `<div style="margin-top: 8px;"><strong style="color: var(--red);">Matched Skills:</strong> None</div>`;
  
  const missingHtml = r.missing_skills && r.missing_skills.length > 0 ? 
    `<div><strong style="color: var(--red);">Missing Skills:</strong> ${r.missing_skills.join(', ')}</div>` : '';
  
  return `<div class="rc" id="rc${i}" onclick="sel(${i})">
    ${errBanner}
    <div class="rc-top">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:3px">
          <span class="rc-rnk">#${i + 1}</span>
          <span class="rc-name">${esc(r.candidate_name || r._fn)}</span>
        </div>
        <div class="rc-cat">${esc(r.category || r._fn)}</div>
      </div>
      <span class="rsc ${scClass(r.composite_score || 0)}">${pC}%</span>
    </div>
    <div class="bars">
      <div class="br"><span class="bl">Semantic</span><div class="bt"><div class="bf s" style="width:${pS}%"></div></div><span class="bv">${pS}</span></div>
      <div class="br"><span class="bl">Skill</span><div class="bt"><div class="bf sk" style="width:${pK}%"></div></div><span class="bv">${pK}</span></div>
      <div class="br"><span class="bl">Composite</span><div class="bt"><div class="bf c" style="width:${pC}%"></div></div><span class="bv">${pC}</span></div>
    </div>
    ${matchedHtml}
    ${missingHtml}
    ${chips ? `<div class="chips">${chips}</div>` : ''}
    ${recHtml}
  </div>`;
}

function sel(i) {
  if (selIdx !== null) document.getElementById(`rc${selIdx}`)?.classList.remove('sel');
  selIdx = i;
  document.getElementById(`rc${i}`)?.classList.add('sel');
  showDetail(results[i], i + 1);
}

function showDetail(r, rank) {
  document.getElementById('dp').style.display = 'block';
  document.getElementById('dpnm').textContent = r.candidate_name || r._fn;
  document.getElementById('dpct').textContent = r.category || '—';
  document.getElementById('dprk').textContent = `#${rank}`;
  document.getElementById('dpem').textContent = r.email || 'N/A';
  document.getElementById('dpph').textContent = r.phone || 'N/A';
  setGauge(0, r.semantic_score || 0);
  setGauge(1, r.skill_score || 0);
  setGauge(2, r.composite_score || 0);
  const pS = Math.round((r.semantic_score || 0) * 100);
  const pK = Math.round((r.skill_score || 0) * 100);
  const pC = Math.round((r.composite_score || 0) * 100);
  document.getElementById('dsv').textContent = pS + '%';
  document.getElementById('dskv').textContent = pK + '%';
  document.getElementById('dcv').textContent = pC + '%';
  const thresh = document.getElementById('dthv');
  if (pC >= 65) { thresh.textContent = 'Shortlistable'; thresh.style.color = 'var(--green)'; }
  else { thresh.textContent = 'Below threshold'; thresh.style.color = 'var(--red)'; }
  
  const matchedHtml = r.matched_skills && r.matched_skills.length > 0 ? 
    r.matched_skills.map(s => `<span class="dsk m">${esc(s)}</span>`).join('') : 
    '<span style="color: var(--red);">None</span>';
  const missingHtml = r.missing_skills && r.missing_skills.length > 0 ? 
    r.missing_skills.map(s => `<span class="dsk x">${esc(s)}</span>`).join('') : 
    '<span style="color: var(--green);">None</span>';
  
  document.getElementById('dpsk').innerHTML = `<div><strong>Matched:</strong> ${matchedHtml}</div><div style="margin-top: 8px;"><strong>Missing:</strong> ${missingHtml}</div>`;
  
  const recEl = document.getElementById('drec');
  if (recEl) {
    const recColor = r.composite_score >= 0.7 ? 'var(--green)' : r.composite_score >= 0.5 ? 'var(--amber)' : 'var(--red)';
    recEl.innerHTML = r.recommendation ? `<div style="border-left: 3px solid ${recColor}; padding-left: 12px;">${esc(r.recommendation)}</div>` : 'No recommendation available';
  }
}

function setGauge(n, score) { const circ = 2 * Math.PI * 28; const gc = document.getElementById(`gc${n}`); if(gc) gc.style.strokeDashoffset = circ - (circ * score); const gv = document.getElementById(`gv${n}`); if(gv) gv.textContent = Math.round(score * 100) + '%'; }

function updateStats(){ const n=files.length; document.getElementById('ss').textContent=results.length; document.getElementById('sf').textContent=n?`${n} file${n>1?'s':''} ready`:'No files'; if(!results.length){ document.getElementById('sh').textContent='0'; document.getElementById('shp').textContent='Threshold: ≥ 65%'; document.getElementById('sa').textContent='—'; return; } const good=results.filter(r=>!r._fail&&(r.composite_score||0)>=0.65); document.getElementById('sh').textContent=good.length; document.getElementById('shp').textContent=`${Math.round(good.length/results.length*100)}% match rate`; const valids=results.filter(r=>!r._fail); const avg=valids.reduce((s,r)=>s+(r.composite_score||0),0)/Math.max(1,valids.length); document.getElementById('sa').textContent=Math.round(avg*100)+'%'; }
function actShortlist(){ if(selIdx!==null){ toast('s','Shortlisted',`${results[selIdx].candidate_name||results[selIdx]._fn} shortlisted`); let shortlisted=JSON.parse(localStorage.getItem('resumeIQ_shortlisted')||'[]'); if(!shortlisted.find(s=>s.name===results[selIdx]._fn)){ shortlisted.push(results[selIdx]); localStorage.setItem('resumeIQ_shortlisted',JSON.stringify(shortlisted)); updateStats(); renderShortlisted(); } } }
function actDownload(){ if(selIdx===null)return; const r=results[selIdx]; if(r._fo){ const a=document.createElement('a'); a.href=URL.createObjectURL(r._fo); a.download=r._fn; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),10000); }else{ toast('i','Download unavailable',''); } }
function actReject(){ if(selIdx!==null) toast('i','Rejected',`${results[selIdx].candidate_name||results[selIdx]._fn} rejected`); }
function exportCSV(){ if(!results.length){ toast('e','Nothing to export','Run screening first.'); return; } const rows=[['Rank','Candidate Name','Category','Semantic %','Skill %','Composite %','Matched Skills','Missing Skills','Recommendation','Status']]; results.forEach((r,i)=>rows.push([i+1,r.candidate_name||r._fn,r.category||'',Math.round((r.semantic_score||0)*100),Math.round((r.skill_score||0)*100),Math.round((r.composite_score||0)*100),(r.matched_skills||[]).join('; '),(r.missing_skills||[]).join('; '),r.recommendation||'',r._fail?'Error':'OK'])); const csv=rows.map(r=>r.map(v=>`"${String(v).replace(/"/g,'""')}"`).join(',')).join('\r\n'); const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'})); const a=document.createElement('a'); a.href=url; a.download=`screening_${new Date().toISOString().slice(0,10)}.csv`; a.click(); setTimeout(()=>URL.revokeObjectURL(url),10000); toast('s','CSV exported',`${results.length} records`); }
function updateAnalytics(){ document.getElementById('analyticsTotal').innerText=results.length; const shortlisted=JSON.parse(localStorage.getItem('resumeIQ_shortlisted')||'[]'); document.getElementById('analyticsRate').innerText=results.length?Math.round(shortlisted.length/results.length*100)+'%':'0%'; const avg=results.length?Math.round(results.reduce((s,r)=>s+(r.composite_score||0),0)/results.length*100):0; document.getElementById('analyticsAvg').innerText=avg?`${avg}%`:'—'; const allSkills=new Set(); results.forEach(r=>{(r.matched_skills||[]).forEach(s=>allSkills.add(s));(r.missing_skills||[]).forEach(s=>allSkills.add(s));}); document.getElementById('analyticsSkills').innerText=allSkills.size; const skillCount=new Map(); results.forEach(r=>{(r.matched_skills||[]).forEach(s=>skillCount.set(s,(skillCount.get(s)||0)+1));}); const topSkills=Array.from(skillCount.entries()).sort((a,b)=>b[1]-a[1]).slice(0,10); document.getElementById('topSkillsList').innerHTML=topSkills.map(([s,c])=>`<span class="stag on">${s} (${c})</span>`).join('')||'<span>No skills data yet</span>'; const history=JSON.parse(localStorage.getItem('resumeIQ_history')||'[]'); document.getElementById('historyList').innerHTML=history.slice().reverse().slice(0,20).map(h=>`<div style="padding:10px;border-bottom:1px solid var(--border);"><strong>${h.date}</strong><br>${h.total} resumes, ${h.shortlisted} shortlisted, avg ${h.avgMatch}%</div>`).join('')||'<span>No history yet</span>'; }
function saveScreeningToHistory(){ const history=JSON.parse(localStorage.getItem('resumeIQ_history')||'[]'); const total=results.length; const shortlisted=JSON.parse(localStorage.getItem('resumeIQ_shortlisted')||'[]').length; const avgMatch=results.length?Math.round(results.reduce((s,r)=>s+(r.composite_score||0),0)/results.length*100):0; history.push({date:new Date().toLocaleString(),total,shortlisted,avgMatch}); if(history.length>50)history.shift(); localStorage.setItem('resumeIQ_history',JSON.stringify(history)); }
function renderShortlisted(){ const shortlisted=JSON.parse(localStorage.getItem('resumeIQ_shortlisted')||'[]'); const container=document.getElementById('shortlistContainer'); if(!shortlisted.length){ container.innerHTML='<div class="es"><div class="et2">No shortlisted candidates</div><div class="esub">Shortlist candidates from Screening tab.</div></div>'; return; } container.innerHTML=shortlisted.map((c,i)=>`<div class="rc" style="margin-bottom:10px;"><div class="rc-top"><span class="rc-rnk">#${i+1}</span><span class="rc-name">${esc(c.candidate_name||c.name||c._fn)}</span><span class="rsc ${c.composite_score>=0.65?'rhi':c.composite_score>=0.45?'rmd':'rlo'}">${Math.round((c.composite_score||0)*100)}%</span></div><div class="bars"><div class="br"><span class="bl">Composite</span><div class="bt"><div class="bf c" style="width:${Math.round((c.composite_score||0)*100)}%"></div></div><span class="bv">${Math.round((c.composite_score||0)*100)}%</span></div></div><div class="chips">${(c.matched_skills||[]).slice(0,5).map(s=>`<span class="chip cmatch">${esc(s)}</span>`).join('')}</div></div>`).join(''); }
function updateAPI(){ const newApi=document.getElementById('apiEndpoint').value; localStorage.setItem('resumeIQ_api',newApi); API=newApi; document.getElementById('apiTestResult').innerHTML='<span style="color:var(--green);">API endpoint updated. Reload page to apply fully.</span>'; checkAPI(); }
function saveDefaultWeights(){ const sem=document.getElementById('defaultSemWeight').value; const skill=document.getElementById('defaultSkillWeight').value; localStorage.setItem('resumeIQ_semWeight',sem); localStorage.setItem('resumeIQ_skillWeight',skill); document.getElementById('apiTestResult').innerHTML='<span style="color:var(--green);">Default weights saved.</span>'; }
function saveThreshold(){ const threshold=document.getElementById('thresholdValue').value; localStorage.setItem('resumeIQ_threshold',threshold); document.getElementById('apiTestResult').innerHTML='<span style="color:var(--green);">Threshold saved.</span>'; }
function exportAllData(){ const data={results:results,shortlisted:JSON.parse(localStorage.getItem('resumeIQ_shortlisted')||'[]'),skills:skills,settings:{api:localStorage.getItem('resumeIQ_api'),semWeight:localStorage.getItem('resumeIQ_semWeight'),skillWeight:localStorage.getItem('resumeIQ_skillWeight'),threshold:localStorage.getItem('resumeIQ_threshold')}}; const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=`resumeiq_export_${new Date().toISOString().slice(0,19)}.json`; a.click(); URL.revokeObjectURL(url); toast('s','Export complete','All data exported as JSON'); }
function clearAllData(){ if(confirm('Delete all screening results, shortlisted candidates, and settings?')){ localStorage.clear(); location.reload(); } }
function loadSettings(){ const savedApi=localStorage.getItem('resumeIQ_api'); if(savedApi) document.getElementById('apiEndpoint').value=savedApi; const savedSem=localStorage.getItem('resumeIQ_semWeight'); if(savedSem) document.getElementById('defaultSemWeight').value=savedSem; const savedSkill=localStorage.getItem('resumeIQ_skillWeight'); if(savedSkill) document.getElementById('defaultSkillWeight').value=savedSkill; const savedThreshold=localStorage.getItem('resumeIQ_threshold'); if(savedThreshold) document.getElementById('thresholdValue').value=savedThreshold; }
const ICONS={s:'<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',e:'<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2"><path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',i:'<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'};
function toast(type,title,msg){ const el=document.createElement('div'); el.className=`toast ts`; if(type==='e')el.className='toast te'; else if(type==='i')el.className='toast ti'; else el.className='toast ts'; el.innerHTML=`<div class="tic">${ICONS[type]||ICONS.i}</div><div class="tt"><div class="ttl">${esc(title)}</div><div class="tmg">${esc(msg||'')}</div></div>`; document.getElementById('toasts').appendChild(el); setTimeout(()=>{el.style.animation='tOut .25s ease forwards';setTimeout(()=>el.remove(),260);},4500); }
function esc(s){if(typeof s!=='string')return String(s||'');return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
loadSavedData();

async function analyzeForJD() {
  if (!files.length) {
    toast('e', 'No files uploaded', 'Please upload a resume first.');
    return;
  }
  const f = files[0];
  const btn = document.getElementById('analyzeBtn');
  const oldHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<svg class="spin" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Analyzing...';
  
  const fd = new FormData();
  fd.append('file', f);
  
  try {
    const resp = await fetch(`${API}/extract-text`, {method: 'POST', body: fd, signal: AbortSignal.timeout(30000)});
    if (!resp.ok) { let errMsg=`HTTP ${resp.status}`; try{ const ed=await resp.json(); if(ed&&ed.detail) errMsg=typeof ed.detail==='string'?ed.detail:(ed.detail.message||ed.detail.error||errMsg); }catch(e){} throw new Error(errMsg); }
    const data = await resp.json();
    
    // Auto-fill inputs
    document.getElementById('jobTitle').value = data.guessed_title || f.name.split('.')[0];
    const jdEl = document.getElementById('jd');
    jdEl.value = data.text;
    document.getElementById('cc').textContent = data.text.length;
    
    // Auto-fill skills
    if (data.skills && data.skills.length > 0) {
      data.skills.forEach(s => {
        if (!skills.includes(s)) skills.push(s);
        selectedSkills.add(s);
      });
      renderSkills();
      saveData();
    }
    
    toast('s', 'Auto-filled', 'Job Title, Description, and Skills updated');
  } catch (err) {
    toast('e', 'Analysis failed', err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = oldHtml;
  }
}
