(function(){
  function esc(v){return String(v ?? '').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
  const path = location.pathname.split('/').pop();
  const roleMap={'player-dashboard.html':'Player','coach-dashboard.html':'Coach','club-dashboard.html':'Club','organizer-dashboard.html':'Organizer','referee-dashboard.html':'Referee'};
  const role=roleMap[path];
  if(!role) return;
  let current=null;
  function roleProfile(u){return u?.[role.toLowerCase()+'_profile'] || {};}
  async function load(){ const r=await fetch('/api/auth/me'); if(!r.ok) return null; const d=await r.json(); current=d.user; return current; }
  function value(k){const p=roleProfile(current); return current?.[k] ?? p?.[k] ?? '';}
  function addButton(){
    const top=document.querySelector('.dash-topbar'); if(!top || document.getElementById('profileEditorBtn')) return;
    const b=document.createElement('button'); b.id='profileEditorBtn'; b.className='btn btn-outline btn-sm'; b.textContent='✏️ Edit Profile'; b.onclick=open;
    const actions=top.querySelector(':scope > div:last-child'); (actions||top).prepend(b);
  }
  function open(){
    let modal=document.getElementById('profileEditorModal');
    if(!modal){
      modal=document.createElement('div'); modal.id='profileEditorModal'; modal.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;';
      modal.innerHTML=`<div style="width:min(760px,96vw);max-height:90vh;overflow:auto;background:#10161d;border:1px solid rgba(105,255,131,.35);border-radius:18px;padding:22px;box-shadow:0 24px 80px rgba(0,0,0,.5)"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><div><div style="color:var(--primary);font-size:12px;font-weight:800;letter-spacing:.12em">ACCOUNT PROFILE</div><h2 style="margin:4px 0 0">Edit ${role} Profile</h2></div><button class="btn btn-secondary btn-sm" id="profileEditorClose">✕</button></div><form id="profileEditorForm" style="margin-top:18px;display:grid;grid-template-columns:1fr 1fr;gap:12px"></form><div style="display:flex;justify-content:flex-end;gap:10px;margin-top:16px"><button class="btn btn-secondary" type="button" id="profileEditorCancel">Cancel</button><button class="btn btn-primary" type="submit" form="profileEditorForm">SAVE PROFILE</button></div></div>`;
      document.body.appendChild(modal);
      modal.querySelector('#profileEditorClose').onclick=close; modal.querySelector('#profileEditorCancel').onclick=close;
      modal.addEventListener('click',e=>{if(e.target===modal)close();});
      modal.querySelector('#profileEditorForm').addEventListener('submit',save);
    }
    const form=modal.querySelector('#profileEditorForm');
    const fields=[
      ['full_name','Full Name','text',current?.full_name||''],['phone','Phone Number','text',current?.phone||''],['email','Email Address','email',current?.email||''],
      ['sport','Sport','text',value('sport')],['position','Playing Role / Position','text',value('position')],['availability','Availability','text',value('availability')],
      ['state','State','text',current?.state||''],['district','District','text',current?.district||''],['location','Mandal / City / Town','text',current?.location||''],['village','Village / Local Area','text',value('village')],
      ['bio','Bio','textarea',current?.bio||'']
    ];
    form.innerHTML=fields.map(([n,l,t,v])=>t==='textarea'?`<label style="grid-column:1/-1"><span style="display:block;margin-bottom:5px;color:#cbd5e1;font-size:12px;font-weight:700">${l}</span><textarea name="${n}" rows="4" style="width:100%;background:#0b1016;color:#fff;border:1px solid #263241;border-radius:10px;padding:10px">${esc(v)}</textarea></label>`:`<label><span style="display:block;margin-bottom:5px;color:#cbd5e1;font-size:12px;font-weight:700">${l}</span><input name="${n}" type="${t}" value="${esc(v)}" style="width:100%;background:#0b1016;color:#fff;border:1px solid #263241;border-radius:10px;padding:10px"></label>`).join('');
    modal.style.display='flex';
  }
  function close(){const m=document.getElementById('profileEditorModal'); if(m)m.style.display='none';}
  async function save(e){
    e.preventDefault(); const data=Object.fromEntries(new FormData(e.target).entries());
    try{const r=await fetch('/api/profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const d=await r.json();if(!r.ok)throw new Error(d.error||'Unable to save profile');current=d.user; localStorage.setItem('scUser',JSON.stringify(current)); close(); refreshHeader(); alert('Profile updated successfully.');}
    catch(err){alert(err.message);}
  }
  function refreshHeader(){ if(!current)return; const n=document.getElementById('playerNameTitle'); if(n)n.textContent=current.full_name; const sub=document.getElementById('playerSubtitle'); if(sub)sub.textContent=`${value('sport')||''} | ${value('position')||''} | ${current.location||''}, ${current.state||''}`; const h=document.querySelector('.dash-welcome h2'); if(h && role!=='Player'){ const badge=h.querySelector('.badge'); h.textContent=''; h.append(document.createTextNode(current.full_name+' ')); if(badge)h.append(badge); } }
  window.addEventListener('DOMContentLoaded',async()=>{current=await load();if(current){addButton();refreshHeader();}});
})();
