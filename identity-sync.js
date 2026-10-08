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
    window.dispatchEvent(new CustomEvent('sportsconnect:authenticated',{detail:merged}));

    localStorage.setItem('scUser',JSON.stringify(merged));

    const setText=(ids,value)=>{
      ids.forEach(id=>{const el=document.getElementById(id);if(el&&value!==undefined&&value!==null)el.textContent=value;});
    };
    const userLocation=[user.location,user.district,user.state].filter(Boolean).join(', ');
    const sport=merged.sport||user.sport||'';
    const position=merged.position||merged.specialization||merged.official_role||'';

    if(expected==='Player'){
      setText(['playerNameTitle','resFullName'],user.full_name||user.username);
      setText(['playerSubtitle'],[sport,position,userLocation].filter(Boolean).join(' | '));
    }
    if(expected==='Coach'){
      setText(['coachWelcomeName','headerName','sideName'],user.full_name||user.username);
      setText(['scoutLocation'],location);
    }
    if(expected==='Club'){
      setText(['clubWelcomeName','headerName','sideName'],user.full_name||user.username);
    }
    if(expected==='Organizer'){
      setText(['organizerWelcomeName','headerName','sideName'],user.full_name||user.username);
    }
    if(expected==='Referee'){
      setText(['sideName','dashboardName','headerName','profileName'],user.full_name||user.username);
      setText(['sideLocation','profileLocation'],userLocation||'Complete profile');
    }

    document.querySelectorAll('[data-current-user-name]').forEach(e=>e.textContent=user.full_name||'');
    document.querySelectorAll('[data-current-user-email]').forEach(e=>e.textContent=user.email||'');
    document.querySelectorAll('[data-current-user-role]').forEach(e=>e.textContent=user.role||'');
    document.querySelectorAll('[data-current-user-location]').forEach(e=>e.textContent=userLocation);
  }catch(e){
    location.replace('/');
  }
})();