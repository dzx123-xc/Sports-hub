(async function(){
  const path = location.pathname.split('/').pop() || 'index.html';
  const roles = {
    'player-dashboard.html':'Player',
    'coach-dashboard.html':'Coach',
    'club-dashboard.html':'Club',
    'organizer-dashboard.html':'Organizer',
    'referee-dashboard.html':'Referee',
    'admin-portal.html':'Admin'
  };
  if (!roles[path]) return;
  try {
    const r = await fetch('/api/auth/me', {credentials:'same-origin'});
    if (!r.ok) throw new Error('unauthorized');
    const d = await r.json();
    if (!d.user || d.user.role !== roles[path]) throw new Error('forbidden');
    window.SPORTS_CONNECT_CURRENT_USER = d.user;
    localStorage.setItem('scUser', JSON.stringify(d.user));
  } catch (e) {
    location.replace('/');
  }
})();
