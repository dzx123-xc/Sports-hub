/* Normalize server identity for all protected dashboards. */
(async function(){
  const page=location.pathname.split('/').pop();
  const roles={'player-dashboard.html':'Player','coach-dashboard.html':'Coach','club-dashboard.html':'Club','organizer-dashboard.html':'Organizer','referee-dashboard.html':'Referee','admin-portal.html':'Admin'};
  const expected=roles[page];
  if(!expected)return;
  try{
    const res=await fetch('/api/auth/me',{credentials:'same-origin',cache:'no-store'});
    if(!res.ok)throw new Error('unauthorized');
    const {user}=await res.json();
    if(!user||user.role!==expected)throw new Error('forbidden');
    const profile=user[expected.toLowerCase()+'_profile']||{};
    const merged={...user,...profile};
    window.SPORTS_CONNECT_CURRENT_USER=merged;
    localStorage.setItem('scUser',JSON.stringify(merged));
    document.querySelectorAll('[data-current-user-name]').forEach(e=>e.textContent=user.full_name||'');
    document.querySelectorAll('[data-current-user-email]').forEach(e=>e.textContent=user.email||'');
    document.querySelectorAll('[data-current-user-role]').forEach(e=>e.textContent=user.role||'');
    document.querySelectorAll('[data-current-user-location]').forEach(e=>e.textContent=[user.location,user.district,user.state].filter(Boolean).join(', '));
  }catch(e){location.replace('/');}
})();
