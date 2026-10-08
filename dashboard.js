const ROLE_CONFIG = {
  Player: {
    icon: '🏃', subtitle: 'PLAYER',
    stats: [['Matches','0','Matches played'],['Wins','0','Wins recorded'],['Teams','0','Teams joined'],['Achievements','0','Achievements']],
    actions: [['⚽','Find Matches','Explore upcoming games and challenges.'],['👥','My Teams','View and manage your teams.'],['📈','Performance','Track your progress and results.']],
    modules: [['MATCHES','Upcoming matches','No matches scheduled yet. Match scheduling will appear here.'],['PERFORMANCE','Performance overview','Your match results, stats and progress will appear here.'],['ACHIEVEMENTS','Achievements','Complete matches and activities to build your sports record.']]
  },
  Coach: {
    icon: '🧑‍🏫', subtitle: 'COACH',
    stats: [['Teams','0','Teams managed'],['Players','0','Players coached'],['Sessions','0','Training sessions'],['Wins','0','Team wins']],
    actions: [['👥','My Teams','Manage your teams and squad members.'],['🏋️','Training','Plan training sessions and drills.'],['📊','Performance','Review team and player performance.']],
    modules: [['TEAM MANAGEMENT','Team overview','Your teams, players and squad management will appear here.'],['TRAINING','Training planner','Create and manage upcoming training sessions.'],['TEAM PERFORMANCE','Performance overview','Track team results and individual player progress.']]
  },
  Organizer: {
    icon: '📅', subtitle: 'ORGANIZER',
    stats: [['Events','0','Events created'],['Participants','0','Registered participants'],['Tournaments','0','Tournaments'],['Matches','0','Matches scheduled']],
    actions: [['📅','Create Event','Plan your next sports event.'],['🏆','Tournaments','Manage tournaments and fixtures.'],['📍','Venues','Manage venues and locations.']],
    modules: [['EVENTS','Events management','Create events, manage registrations and track participation.'],['TOURNAMENTS','Tournament management','Fixtures, teams, rounds and standings will appear here.'],['VENUES','Venue management','Add and manage sports venues for your events.']]
  },
  Referee: {
    icon: '🧑‍⚖️', subtitle: 'REFEREE',
    stats: [['Assigned','0','Assigned matches'],['Completed','0','Completed matches'],['Results','0','Results confirmed'],['Cards','0','Cards recorded']],
    actions: [['📋','Assigned Matches','View matches assigned to you.'],['🕒','Schedule','Check your officiating schedule.'],['📝','Match Management','Enter scores, cards, fouls and match notes.']],
    modules: [['ASSIGNED MATCHES','Next assignments','No matches are assigned yet. Assigned games will appear here.'],['MATCH MANAGEMENT','Manage a match','Record score, cards, fouls, incidents and match statistics.'],['HISTORY','Refereeing history','Completed matches and confirmed results will appear here.']]
  }
};

const $ = id => document.getElementById(id);
const currentRole = document.body.dataset.role;
const config = ROLE_CONFIG[currentRole];

function getUser(){
  try{return JSON.parse(localStorage.getItem('scUser') || localStorage.getItem('sporthubUser') || 'null');}catch(e){return null;}
}
function getUsers(){
  try{return JSON.parse(localStorage.getItem('sporthubUsers') || '[]');}catch(e){return [];}
}
function saveUser(user){
  localStorage.setItem('sporthubUser', JSON.stringify(user));
  const users=getUsers();
  const idx=users.findIndex(u=>u.email===user.email);
  if(idx>=0) users[idx]=user; else users.push(user);
  localStorage.setItem('sporthubUsers',JSON.stringify(users));
}
function esc(v){return String(v ?? '').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function value(...keys){const u=getUser()||{};for(const k of keys)if(u[k])return u[k];return '';}

function render(){
  if(!config){$('dashboardRoot').innerHTML='<div class="dashboard-error"><h2>Invalid dashboard</h2><p>Please return to SportHub and log in again.</p><a class="green-btn compact" href="index.html">Back to SportHub</a></div>';return;}
  const user=getUser();
  if(!user || user.role!==currentRole){
    $('dashboardRoot').innerHTML=`<div class="dashboard-error"><div class="dashboard-error-icon">🔐</div><h2>${config.subtitle} Dashboard</h2><p>No active ${currentRole} session was found.</p><a class="green-btn compact" href="index.html">Login as ${currentRole}</a></div>`;
    return;
  }
  $('sideRole').textContent=config.subtitle;
  $('sideName').textContent=user.name || user.full_name || user.username || 'Member';
  $('sideAvatar').textContent=config.icon;
  $('dashboardIcon').textContent=config.icon;
  $('dashboardName').textContent=user.name || user.full_name || user.username || 'SportHub Member';
  $('headerAvatar').textContent=config.icon;
  $('headerName').textContent=user.name || user.full_name || user.username || 'Member';
  $('dashboardRole').textContent=currentRole;
  $('roleDescription').textContent=roleDescription(currentRole);
  $('roleStats').innerHTML=config.stats.map(s=>`<div class="stat-card"><div class="stat-icon">${config.icon}</div><strong>${s[1]}</strong><span>${s[0]}</span><small>${s[2]}</small></div>`).join('');
  $('quickActions').innerHTML=config.actions.map((a,i)=>`<button class="role-hero-card action-card" onclick="openModule(${i})"><span class="hero-icon">${a[0]}</span><b>${a[1]}</b><p>${a[2]}</p><span class="hero-action">Open →</span></button>`).join('');
  $('roleModules').innerHTML=config.modules.map((m,i)=>`<article class="dashboard-panel role-module" id="module-${i}"><div class="panel-heading"><div><div class="panel-title">${m[0]}</div><h3>${m[1]}</h3></div><span class="status-chip">READY</span></div><div class="module-empty"><span>${config.icon}</span><div><b>${m[2]}</b><small>This area is prepared for the next SportHub feature phase.</small></div></div></article>`).join('');
  $('profileName').value=user.name||'';$('profilePhone').value=user.phone||'';$('profileEmail').value=user.email||'';
  $('profileSport').value=value(currentRole.toLowerCase()+'Sport','sport');
  $('profileState').value=user.state||'';$('profileDistrict').value=value(currentRole.toLowerCase()+'District','district');$('profileLocation').value=value(currentRole.toLowerCase()+'Location','location');$('profileVillage').value=user.village||'';
  $('profileAvailability').value=value(currentRole.toLowerCase()+'Availability','availability');
  $('profileRole').value=roleValue(user);
  $('profileBio').value=user.bio||'';
  $('sideLocation').textContent=locationText(user);
  $('profileSummary').textContent=locationText(user);
  $('notificationsList').innerHTML=notifications(user).map(n=>`<div class="notification"><span>${n[0]}</span><div><b>${n[1]}</b><small>${n[2]}</small></div></div>`).join('');
}
function roleDescription(role){return {Player:'Manage matches, teams, performance and your sports profile from one place.',Coach:'Manage teams, players, training plans and team performance from one place.',Organizer:'Create events and tournaments, manage participants, venues and fixtures.',Referee:'Manage assigned matches, officiating schedules, scores, incidents and results.'}[role];}
function roleValue(u){const p=currentRole.toLowerCase();return u[p+'Position']||u[p+'Specialization']||u.rolePosition||u.position||u.role||'';}
function locationText(u){const parts=[u.village,u[prefixKey('Location')],u[prefixKey('District')],u.state].filter(Boolean);return parts.length?parts.join(' • '):'Complete profile';}
function prefixKey(kind){return currentRole.toLowerCase()+kind;}
function notifications(u){return [["🔔","Welcome to SportHub",`Your ${currentRole.toLowerCase()} dashboard is ready.`],["🏆","Role dashboard active",`You are signed in as ${currentRole}.`],["📍","Local discovery",u.state?`Your location is set to ${u.state}.`:'Complete your location to improve local discovery.']];}
function openModule(i){document.getElementById('module-'+i)?.scrollIntoView({behavior:'smooth',block:'center'});}
function saveProfile(event){
  event.preventDefault();const user=getUser();if(!user)return;
  user.name=$('profileName').value.trim();user.phone=$('profilePhone').value.trim();user.email=$('profileEmail').value.trim().toLowerCase();
  user.sport=$('profileSport').value;user.state=$('profileState').value;user.district=$('profileDistrict').value;user.location=$('profileLocation').value;user.village=$('profileVillage').value;user.availability=$('profileAvailability').value;user.position=$('profileRole').value;user.bio=$('profileBio').value.trim();
  saveUser(user);render();toast('Profile updated successfully.');
}
function logout(){localStorage.removeItem('sporthubSession');localStorage.removeItem('sporthubUser');window.location.href='index.html';}
function toast(message){const t=$('toast');t.textContent=message;t.classList.add('show');clearTimeout(window._toast);window._toast=setTimeout(()=>t.classList.remove('show'),2800);}
function toggleSidebar(){$('sidebar')?.classList.toggle('open');}
function scrollToId(id){document.getElementById(id)?.scrollIntoView({behavior:'smooth',block:'center'});$('sidebar')?.classList.remove('open');}

window.addEventListener('DOMContentLoaded',render);
