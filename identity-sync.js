(async function(){
  const roleByPage={'player-dashboard.html':'Player','coach-dashboard.html':'Coach','club-dashboard.html':'Club','organizer-dashboard.html':'Organizer','referee-dashboard.html':'Referee','admin-portal.html':'Admin'};
  const path=location.pathname.split('/').pop(); const role=roleByPage[path]; if(!role)return;
  try{
    const r=await fetch('/api/auth/me',{credentials:'same-origin'}); if(!r.ok)throw new Error();
    const d=await r.json(); const u=d.user; if(!u||u.role!==role)throw new Error();
    window.SPORTS_CONNECT_CURRENT_USER=u; localStorage.setItem('scUser',JSON.stringify(u));
    const profile=u[role.toLowerCase()+'_profile']||{};
    const sport=profile.sport||u.sport||''; const pos=profile.position||profile.specialization||profile.official_role||''; const loc=[u.location,u.state].filter(Boolean).join(', ');
    const welcome=document.querySelector('.dash-welcome h2');
    if(welcome){const badge=welcome.querySelector('.badge');welcome.textContent='';welcome.append(document.createTextNode((u.avatar||'🏆')+' '+u.full_name+' '));if(badge){badge.textContent=`🟢 ${role}`;welcome.append(badge);}}
    const subtitle=document.querySelector('.dash-welcome p'); if(subtitle) subtitle.textContent=[sport,pos,loc].filter(Boolean).join(' • ');
    const nameIds=['playerNameTitle','coachNameTitle','clubNameTitle','organizerNameTitle','refereeNameTitle']; nameIds.forEach(id=>{const e=document.getElementById(id);if(e)e.textContent=u.full_name;});
    const switcher=document.getElementById('athleteSwitcher'); if(switcher){const wrap=switcher.closest('div'); if(wrap)wrap.style.display='none';}
  }catch(e){location.replace('/');}
})();
