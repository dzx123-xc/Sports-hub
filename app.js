/**
 * SportsConnect - Client Application Engine
 * LinkedIn for Sports Platform
 * Handles DataService (REST + Local Fallback), Auth, Modals, Radar & Line Charts,
 * Smart Matching, Player Comparison, Trials, Messaging, Reports, and Role Switching.
 */

// =============================================================================
// 1. Initial State & Demo Fallback Dataset
// =============================================================================
const DEMO_USERS = {
  player1: {
    id: 1, username: 'rahulkumar', email: 'rahul@sportsconnect.com', phone: '+91 98765 43210',
    role: 'Player', full_name: 'Rahul Kumar', avatar: '🏏', location: 'Hyderabad, Telangana',
    bio: 'Passionate top-order batsman with relentless practice ethics. Focus on high conversion rate, explosive gap finding, and disciplined technique.',
    is_verified: 1, rating: 8.4, classification: 'Rising Talent', skill_score: 88.0,
    performance_score: 86.0, progress_pct: 21.0, major_matches: 0, verified_local_matches: 6,
    sport: 'Cricket', position: 'Batsman', experience_years: 2.0, availability: 'Available for Trials',
    age_group: 'Under-23', preferred_role: 'Opening Batsman'
  },
  player2: {
    id: 2, username: 'arjunreddy', email: 'arjun@sportsconnect.com', phone: '+91 98765 43211',
    role: 'Player', full_name: 'Arjun Reddy', avatar: '🏏', location: 'Hyderabad, Telangana',
    bio: 'Dynamic seam-bowling all-rounder with strong middle-order finishing capabilities and athletic boundary fielding.',
    is_verified: 1, rating: 8.1, classification: 'Emerging Player', skill_score: 84.0,
    performance_score: 81.0, progress_pct: 15.0, major_matches: 4, verified_local_matches: 18,
    sport: 'Cricket', position: 'All-rounder', experience_years: 4.5, availability: 'In Club',
    age_group: 'Open Senior', preferred_role: 'Pace Bowling All-rounder'
  },
  player3: {
    id: 3, username: 'kirankumar', email: 'kiran@sportsconnect.com', phone: '+91 98765 43212',
    role: 'Player', full_name: 'Kiran Kumar', avatar: '🏏', location: 'Secunderabad, Telangana',
    bio: 'Right-arm medium fast bowler specializing in late outswing and yorkers at death overs. Rising through district trials.',
    is_verified: 1, rating: 8.3, classification: 'Rising Talent', skill_score: 87.0,
    performance_score: 85.0, progress_pct: 19.0, major_matches: 0, verified_local_matches: 5,
    sport: 'Cricket', position: 'Bowler', experience_years: 1.5, availability: 'Available for Trials',
    age_group: 'Under-21', preferred_role: 'Opening Bowler'
  },
  player4: {
    id: 4, username: 'suniljunior', email: 'sunil@sportsconnect.com', phone: '+91 98765 43213',
    role: 'Player', full_name: 'Sunil Varma', avatar: '⚽', location: 'Hyderabad, Telangana',
    bio: 'Agile center-forward with clinical finishing in tight boxes and sharp link-up play. Top scorer in Regional Youth Cup.',
    is_verified: 1, rating: 8.5, classification: 'Rising Talent', skill_score: 89.0,
    performance_score: 87.0, progress_pct: 23.0, major_matches: 0, verified_local_matches: 8,
    sport: 'Football', position: 'Forward', experience_years: 2.5, availability: 'Available for Trials',
    age_group: 'Under-21', preferred_role: 'Center-Forward / Striker'
  },
  player5: {
    id: 5, username: 'ananyasharma', email: 'ananya@sportsconnect.com', phone: '+91 98765 43214',
    role: 'Player', full_name: 'Ananya Sharma', avatar: '🏸', location: 'Hyderabad, Telangana',
    bio: 'Aggressive singles shuttler with 320 km/h overhead smash and rapid net recovery footwork. National Junior Quarter-Finalist.',
    is_verified: 1, rating: 8.6, classification: 'Rising Talent', skill_score: 91.0,
    performance_score: 88.0, progress_pct: 25.0, major_matches: 1, verified_local_matches: 12,
    sport: 'Badminton', position: 'Singles', experience_years: 3.0, availability: 'Available for Trials',
    age_group: 'Under-19', preferred_role: 'Singles Specialist'
  },
  coach: {
    id: 6, username: 'coachvikram', email: 'coach.vikram@sportsconnect.com', phone: '+91 98765 11111',
    role: 'Coach', full_name: 'Vikram Rathore', avatar: '🧑‍🏫', location: 'Hyderabad, Telangana',
    bio: 'BCCI Level 2 Certified Cricket Coach. Head Scout for Deccan Regional Academy. Scouting future national athletes based on scientific skill data.',
    is_verified: 1, sport: 'Cricket', experience_years: 12.0, specialization: 'Batting Technique & Mental Conditioning',
    certifications: 'BCCI Level 2, ICC Certified Coach', current_org: 'Deccan Regional Academy'
  },
  club: {
    id: 7, username: 'warriorscc', email: 'contact@warriorscc.com', phone: '+91 98765 22222',
    role: 'Club', full_name: 'Hyderabad Warriors CC', avatar: '🛡️', location: 'Hyderabad, Telangana',
    bio: 'Premier Division 1 Club competing across state leagues. Active scouting program for under-23 batting and all-round prospects.',
    is_verified: 1, sport: 'Cricket', established_year: 2012, home_ground: 'Rajiv Gandhi Stadium Annex', division: 'Division 1 State League'
  },
  organizer: {
    id: 9, username: 'tysports', email: 'tournaments@tysports.org', phone: '+91 98765 44444',
    role: 'Organizer', full_name: 'Telangana Youth Sports Council', avatar: '🏆', location: 'Hyderabad, Telangana',
    bio: 'Apex organizing body for verified district tournaments, school championships, and talent evaluation leagues.',
    is_verified: 1, sport: 'Multi-Sport', registration_no: 'TS-SPO-2018-9941'
  },
};

const DEMO_TESTS = {
  1: [
    { name: 'Batting Accuracy', score: 91, max: 100 },
    { name: 'Shot Selection', score: 85, max: 100 },
    { name: 'Reaction Time', score: 94, max: 100 },
    { name: 'Fielding Agility', score: 82, max: 100 },
    { name: 'Running Between Wickets', score: 88, max: 100 },
    { name: 'Fitness & Stamina', score: 86, max: 100 },
    { name: 'Bowling Accuracy', score: 62, max: 100 }
  ],
  2: [
    { name: 'Batting Accuracy', score: 82, max: 100 },
    { name: 'Shot Selection', score: 80, max: 100 },
    { name: 'Reaction Time', score: 86, max: 100 },
    { name: 'Fielding Agility', score: 89, max: 100 },
    { name: 'Running Between Wickets', score: 83, max: 100 },
    { name: 'Fitness & Stamina', score: 91, max: 100 },
    { name: 'Bowling Accuracy', score: 86, max: 100 }
  ],
  3: [
    { name: 'Batting Accuracy', score: 64, max: 100 },
    { name: 'Shot Selection', score: 60, max: 100 },
    { name: 'Reaction Time', score: 89, max: 100 },
    { name: 'Fielding Agility', score: 84, max: 100 },
    { name: 'Running Between Wickets', score: 85, max: 100 },
    { name: 'Fitness & Stamina', score: 92, max: 100 },
    { name: 'Bowling Accuracy', score: 94, max: 100 }
  ],
  4: [
    { name: 'Sprint Speed', score: 92, max: 100 },
    { name: 'Finishing & Shot', score: 88, max: 100 },
    { name: 'Dribbling & Control', score: 90, max: 100 },
    { name: 'Passing & Vision', score: 82, max: 100 },
    { name: 'Stamina & Work Rate', score: 86, max: 100 },
    { name: 'Tactical Awareness', score: 84, max: 100 },
    { name: 'Defending Contribution', score: 58, max: 100 }
  ],
  5: [
    { name: 'Smash Velocity', score: 91, max: 100 },
    { name: 'Footwork Agility', score: 95, max: 100 },
    { name: 'Net Deception', score: 89, max: 100 },
    { name: 'Reaction Speed', score: 94, max: 100 },
    { name: 'Endurance Base', score: 88, max: 100 },
    { name: 'Serve Precision', score: 87, max: 100 },
    { name: 'Backhand Clears', score: 85, max: 100 }
  ]
};

// Sport position mappings
const SPORT_ROLES = {
  Cricket: ['Batsman', 'Bowler', 'All-rounder', 'Wicketkeeper'],
  Football: ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'],
  Basketball: ['Point Guard', 'Shooting Guard', 'Small Forward', 'Power Forward', 'Center'],
  Volleyball: ['Setter', 'Outside Hitter', 'Middle Blocker', 'Opposite Hitter', 'Libero'],
  Badminton: ['Singles', 'Doubles', 'Mixed Doubles'],
  Tennis: ['Baseline Specialist', 'Serve & Volley', 'All-Court'],
  Hockey: ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'],
  Athletics: ['Sprinter (100m/200m)', 'Middle Distance', 'Long Distance', 'Jumps', 'Throws'],
  Wrestling: ['Freestyle', 'Greco-Roman'],
  Swimming: ['Freestyle', 'Backstroke', 'Breaststroke', 'Butterfly', 'Individual Medley'],
  Other: ['Specialist Athlete', 'Team Player']
};

// =============================================================================
// 2. DataService (Communicates with REST API, Falls Back to Local Persistence)
// =============================================================================
const DataService = {
  async getMe(userId) {
    try {
      const res = await fetch(`/api/auth/me?user_id=${userId}`);
      if (res.ok) return await res.json();
    } catch (e) {}
    // Fallback
    const u = Object.values(DEMO_USERS).find(x => x.id === parseInt(userId)) || DEMO_USERS.player1;
    return { user: u };
  },

  async getPlayers(params = {}) {
    try {
      const query = new URLSearchParams(params).toString();
      const res = await fetch(`/api/players?${query}`);
      if (res.ok) {
        const data = await res.json();
        if (data.players && data.players.length > 0) return data.players;
      }
    } catch (e) {}
    // Fallback to demo players
    let players = [DEMO_USERS.player1, DEMO_USERS.player2, DEMO_USERS.player3];
    if (params.sport && params.sport !== 'All') players = players.filter(p => p.sport === params.sport);
    if (params.classification && params.classification !== 'All') players = players.filter(p => p.classification === params.classification);
    if (params.min_skill) players = players.filter(p => p.skill_score >= parseFloat(params.min_skill));
    return players;
  },

  async getPlayerDetails(id) {
    try {
      const res = await fetch(`/api/players/${id}`);
      if (res.ok) return (await res.json()).player;
    } catch (e) {}
    // Fallback
    const p = Object.values(DEMO_USERS).find(x => x.id === parseInt(id)) || DEMO_USERS.player1;
    return {
      ...p,
      tests: (DEMO_TESTS[p.id] || DEMO_TESTS[1]).map(t => ({ test_name: t.name, score: t.score, max_score: t.max })),
      certificates: [
        { id: 1, title: 'District Under-19 Championship Trophy - Best Batsman', issuing_org: 'Telangana Cricket Association & TYSC', year: 2025, status: 'verified', verified_by: 'Chief Sports Verifier (Admin)' },
        { id: 2, title: 'State Youth Championship Participation Certificate', issuing_org: 'South Zone Sports Federation', year: 2026, status: 'pending', verified_by: null }
      ],
      matches: [
        {
          match_id: 1, title: 'Hyderabad District T20 - Final', sport: 'Cricket', team_a: 'Warriors XI', team_b: 'Rising Stars XI',
          match_date: '2026-08-28', location: 'Gymkhana Ground, Hyderabad', result_summary: 'Warriors XI won by 18 runs',
          status: 'verified', verified_by: 'Telangana Youth Sports Council (Organizer)',
          team_name: 'Warriors XI', role_played: 'Opening Batsman',
          stats: { runs: 72, balls: 48, fours: 8, sixes: 3, strike_rate: 150.0 },
          performance_rating: 9.2, verified_status: 'verified',
          teammates: [
            { id: 2, full_name: 'Arjun Reddy', avatar: '🏏', role_played: 'All-rounder', stats: { runs: 48, wickets: 2 } }
          ],
          opponents: [
            { id: 3, full_name: 'Kiran Kumar', avatar: '🏏', role_played: 'Bowler', stats: { wickets: 3, runs_conceded: 31 } }
          ]
        }
      ]
    };
  },

  async runSmartMatch(criteria) {
    try {
      const res = await fetch('/api/matching', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(criteria)
      });
      if (res.ok) return await res.json();
    } catch (e) {}
    // Fallback calculation
    return {
      matches: [
        {
          player: DEMO_USERS.player1,
          match_pct: 94,
          reasons: [
            'Same sport: Cricket',
            'Same role: Batsman',
            'Same location: Hyderabad',
            'Skill score meets requirement (88+)',
            'Available for trials / signing',
            'Strong recent performance',
            '🌟 Verified Rising Talent'
          ]
        },
        {
          player: DEMO_USERS.player2,
          match_pct: 91,
          reasons: [
            'Same sport: Cricket',
            'All-rounder capability fits top order',
            'Same location: Hyderabad',
            'Skill score 84/100',
            'Emerging Player with verified match record'
          ]
        },
        {
          player: DEMO_USERS.player3,
          match_pct: 87,
          reasons: [
            'Same sport: Cricket',
            'Bowler pairing for pace trials',
            'Same location: Secunderabad / Hyderabad',
            'High skill test score 87/100',
            '🌟 Verified Rising Talent'
          ]
        }
      ]
    };
  },

  async login(identifier, password) {
    identifier = String(identifier || '').trim();
    password = String(password || '').trim();
    try {
      // Email-first account discovery: an existing system email proceeds to login;
      // an unknown email is directed to account creation.
      if (identifier.includes('@')) {
        const check = await fetch('/api/auth/check-email?email=' + encodeURIComponent(identifier));
        if (check.ok) {
          const status = await check.json();
          if (!status.exists) return { account_exists: false, error: 'No account found for this email. Please create a new account.' };
        }
      }
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password })
      });
      return await res.json();
    } catch (e) {
      return { error: 'Unable to reach the SportsConnect server. Start server.py and try again.' };
    }
  },

  async submitReport(reportData) {
    try {
      const res = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reportData)
      });
      if (res.ok) return await res.json();
    } catch (e) {}
    return { success: true, report_id: 1024, status: 'Under Review' };
  }
};

// =============================================================================
// 3. Canvas Visualizers: Sports Radar Chart & Progress Timeline
// =============================================================================
const ChartRenderer = {
  drawRadar(canvasId, tests = []) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(cx, cy) - 36;

    ctx.clearRect(0, 0, w, h);

    if (!tests || tests.length === 0) {
      tests = [
        { name: 'Accuracy', score: 85 },
        { name: 'Reaction', score: 90 },
        { name: 'Power', score: 80 },
        { name: 'Agility', score: 85 },
        { name: 'Fitness', score: 88 }
      ];
    }

    const total = tests.length;
    const angleStep = (Math.PI * 2) / total;

    // Draw concentric polygon rings (20%, 40%, 60%, 80%, 100%)
    const rings = 5;
    for (let r = 1; r <= rings; r++) {
      const rRadius = (radius / rings) * r;
      ctx.beginPath();
      for (let i = 0; i < total; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const x = cx + rRadius * Math.cos(angle);
        const y = cy + rRadius * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.strokeStyle = r === rings ? 'rgba(0, 230, 118, 0.4)' : 'rgba(255, 255, 255, 0.08)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Draw radial spoke lines & labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10.5px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let i = 0; i < total; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = cx + radius * Math.cos(angle);
      const y = cy + radius * Math.sin(angle);

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.stroke();

      // Label text
      const lx = cx + (radius + 20) * Math.cos(angle);
      const ly = cy + (radius + 20) * Math.sin(angle);
      const name = tests[i].name || tests[i].test_name;
      ctx.fillText(name.split(' ')[0], lx, ly);
    }

    // Draw data polygon
    ctx.beginPath();
    for (let i = 0; i < total; i++) {
      const score = Math.min(100, Math.max(0, tests[i].score || 80));
      const valRadius = (radius * (score / 100));
      const angle = i * angleStep - Math.PI / 2;
      const x = cx + valRadius * Math.cos(angle);
      const y = cy + valRadius * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(0, 230, 118, 0.28)';
    ctx.fill();
    ctx.strokeStyle = '#00e676';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Draw points & score values
    for (let i = 0; i < total; i++) {
      const score = Math.min(100, Math.max(0, tests[i].score || 80));
      const valRadius = (radius * (score / 100));
      const angle = i * angleStep - Math.PI / 2;
      const x = cx + valRadius * Math.cos(angle);
      const y = cy + valRadius * Math.sin(angle);

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = '#00e676';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  },

  drawLineProgress(canvasId, monthlyData = [68, 72, 75, 79, 84, 88]) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const padL = 36, padR = 20, padT = 24, padB = 30;

    ctx.clearRect(0, 0, w, h);

    const months = ['Jan', 'Mar', 'May', 'Jul', 'Aug', 'Sep'];
    const minVal = 50;
    const maxVal = 100;
    const points = [];

    const stepX = (w - padL - padR) / (monthlyData.length - 1);

    // Draw grid horizontal lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';

    [60, 80, 100].forEach(level => {
      const y = padT + (1 - (level - minVal) / (maxVal - minVal)) * (h - padT - padB);
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(w - padR, y);
      ctx.stroke();
      ctx.fillText(level, padL - 6, y + 3);
    });

    // Calculate point coordinates
    monthlyData.forEach((val, i) => {
      const x = padL + i * stepX;
      const y = padT + (1 - (val - minVal) / (maxVal - minVal)) * (h - padT - padB);
      points.push({ x, y, val });
    });

    // Draw area fill
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points[points.length - 1].x, h - padB);
    ctx.lineTo(points[0].x, h - padB);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, padT, 0, h - padB);
    grad.addColorStop(0, 'rgba(0, 210, 255, 0.3)');
    grad.addColorStop(1, 'rgba(0, 210, 255, 0.0)');
    ctx.fillStyle = grad;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = '#00d2ff';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw points & month labels
    ctx.textAlign = 'center';
    points.forEach((p, i) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = '#00d2ff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Month text
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(months[i], p.x, h - 10);
    });
  }
};

// Keep every dashboard bound to the authenticated account, never a demo identity.
function applyAuthenticatedIdentity() {
  const user = SessionManager.getUser ? SessionManager.getUser() : null;
  if (!user) return;
  const name = user.full_name || user.name || user.username || 'SportHub Member';
  const username = user.username ? '@' + user.username : '';
  const ids = {
    player: ['playerNameTitle'],
    coach: ['coachWelcomeName'],
    organizer: ['organizerWelcomeName'],
    club: ['clubWelcomeName']
  };
  const page = location.pathname.toLowerCase();
  const role = String(user.role || '').toLowerCase();
  const targets = role === 'player' ? ids.player : role === 'coach' ? ids.coach : role === 'organizer' ? ids.organizer : role === 'club' ? ids.club : [];
  targets.forEach(id => { const el = document.getElementById(id); if (el) el.textContent = name; });
  const meta = document.getElementById('coachWelcomeMeta');
  if (meta && role === 'coach') meta.textContent = username ? `@${user.username} • ${user.email || 'Registered Coach'}` : 'Your registered Coach profile';
  const userBadges = document.querySelectorAll('[data-auth-username]');
  userBadges.forEach(el => el.textContent = username);
}

// =============================================================================
// 4. Session & Authentication Helper
// =============================================================================
const SessionManager = {
  getUser() {
    try {
      const s = localStorage.getItem('scUser');
      if (s) return JSON.parse(s);
    } catch (e) {}
    return null;
  },

  setUser(user) {
    localStorage.setItem('scUser', JSON.stringify(user));
    localStorage.setItem('sporthubUser', JSON.stringify(user));
    try {
      const users = JSON.parse(localStorage.getItem('sporthubUsers') || '[]');
      const idx = users.findIndex(x => x.username === user.username || x.email === user.email);
      if (idx >= 0) users[idx] = user; else users.push(user);
      localStorage.setItem('sporthubUsers', JSON.stringify(users));
    } catch (e) {}
  },

  async logout() {
    try { await fetch('/api/auth/logout', { method: 'POST' }); } catch (e) {}
    localStorage.removeItem('scUser');
    window.location.href = 'index.html';
  },

  switchDemoUser(roleKey) {
    if (roleKey === 'admin') {
      UIController.showToast('Demo Admin login has been disabled. Use the authorized Admin credentials.', 'info');
      return;
    }
    const u = DEMO_USERS[roleKey];
    if (!u) return;
    this.setUser(u);
    this.redirectForRole(u.role);
  },

  redirectForRole(role) {
    // index.html is now the main authenticated application shell. Keep the
    // individual dashboard pages as legacy/backups, but do not require a
    // page redirect for normal role accounts. Admin still requires the
    // backend-issued protected session before its workspace is displayed.
    const u = this.getUser();
    if (!u) { window.location.href = 'index.html'; return; }
    if (role === 'Admin' && u.username !== 'admin_123') {
      UIController.showToast('Admin access requires the authorized Admin account.', 'info');
      return;
    }
    if (typeof showIndexDashboard === 'function') {
      showIndexDashboard(u);
      return;
    }
    window.location.href = 'index.html';
  }
};

// =============================================================================
// 5. Global Modals & Toast Controller
// =============================================================================
const UIController = {
  showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✓' : 'ℹ'}</span> <div>${message}</div>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  },

  openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add('open');
  },

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('open');
  },

  openReportModal(targetUserName, targetUserId, itemType = 'profile') {
    let modal = document.getElementById('reportModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'reportModal';
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-window">
          <div class="modal-header">
            <h3>🚨 Report Suspicious Item or Profile</h3>
            <button class="modal-close" onclick="UIController.closeModal('reportModal')">✕</button>
          </div>
          <div class="modal-body">
            <p style="font-size:13px; color:var(--text-secondary); margin-bottom:14px;">
              SportsConnect protects sports data integrity. Reports enter the Admin Investigation Queue and are verified against official records before action is taken.
            </p>
            <div class="form-group">
              <label class="form-label">Reported Entity</label>
              <input id="reportTargetName" class="form-input" readonly value="">
              <input id="reportTargetId" type="hidden" value="">
            </div>
            <div class="form-group">
              <label class="form-label">Report Category</label>
              <select id="reportCategory" class="form-select">
                <option value="fake_certificate">Fake or Forged Certificate</option>
                <option value="incorrect_stats">Incorrect / Unverified Match Stats</option>
                <option value="fake_profile">Fake Profile or Impersonation</option>
                <option value="spam">Spam or Inappropriate Behavior</option>
                <option value="other">Other Sports Ethics Violation</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Detailed Description</label>
              <textarea id="reportDescription" class="form-textarea" rows="3" placeholder="Provide details of the discrepancy..."></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Evidence Link or Reference</label>
              <input id="reportEvidence" class="form-input" placeholder="Official tournament URL, certificate serial number, etc.">
            </div>
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:16px;">
              <button class="btn btn-outline" onclick="UIController.closeModal('reportModal')">Cancel</button>
              <button class="btn btn-danger" onclick="UIController.submitReportForm()">Submit Report</button>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }
    document.getElementById('reportTargetName').value = targetUserName;
    document.getElementById('reportTargetId').value = targetUserId;
    this.openModal('reportModal');
  },

  async submitReportForm() {
    const targetId = document.getElementById('reportTargetId').value;
    const cat = document.getElementById('reportCategory').value;
    const desc = document.getElementById('reportDescription').value;
    const ev = document.getElementById('reportEvidence').value;
    const user = SessionManager.getUser();

    if (!desc.trim()) {
      alert('Please provide a short description.');
      return;
    }

    const res = await DataService.submitReport({
      reporter_id: user ? user.id : 6,
      reported_user_id: parseInt(targetId) || 2,
      reported_item_type: 'profile',
      report_type: cat,
      description: desc,
      evidence_text: ev
    });

    this.closeModal('reportModal');
    this.showToast(`Report #${res.report_id || '1024'} submitted. Status: 🟡 Under Review.`, 'success');
  },

  openComparisonModal(p1 = DEMO_USERS.player1, p2 = DEMO_USERS.player2) {
    let modal = document.getElementById('compareModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'compareModal';
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-window" style="max-width: 820px;">
          <div class="modal-header">
            <h3>⚖️ Player Comparison: ${p1.full_name} vs ${p2.full_name}</h3>
            <button class="modal-close" onclick="UIController.closeModal('compareModal')">✕</button>
          </div>
          <div class="modal-body">
            <p style="font-size:12px; color:var(--text-muted); margin-bottom:16px;">
              ⚠️ <em>Platform note: Do not automatically declare a player "better" based solely on metrics. Classification is balanced across skill testing, verified performance, and improvement rate.</em>
            </p>
            <div class="comparison-grid">
              <div class="comparison-column ${p1.classification === 'Rising Talent' ? 'winner' : ''}">
                <div style="font-size:32px; margin-bottom:4px;">${p1.avatar || '🏏'}</div>
                <h4>${p1.full_name}</h4>
                <div class="badge ${p1.classification === 'Rising Talent' ? 'badge-rising' : 'badge-emerging'}" style="margin: 6px auto;">
                  ${p1.classification}
                </div>
                <div style="margin-top:14px; display:flex; flex-direction:column; gap:8px; text-align:left; font-size:13px;">
                  <div><b>Sport / Role:</b> ${p1.sport} (${p1.position})</div>
                  <div><b>Overall Skill Score:</b> <span style="color:var(--primary); font-weight:700;">${p1.skill_score}/100</span></div>
                  <div><b>Verified Match Perf:</b> ${p1.performance_score}/100</div>
                  <div><b>Progress / Improvement:</b> <span class="progress-up">+${p1.progress_pct}%</span></div>
                  <div><b>Major Matches:</b> ${p1.major_matches}</div>
                  <div><b>Verified Local Matches:</b> ${p1.verified_local_matches}</div>
                  <div><b>Availability:</b> <span style="color:var(--primary);">${p1.availability}</span></div>
                </div>
              </div>
              <div class="comparison-column">
                <div style="font-size:32px; margin-bottom:4px;">${p2.avatar || '🏏'}</div>
                <h4>${p2.full_name}</h4>
                <div class="badge ${p2.classification === 'Rising Talent' ? 'badge-rising' : 'badge-emerging'}" style="margin: 6px auto;">
                  ${p2.classification}
                </div>
                <div style="margin-top:14px; display:flex; flex-direction:column; gap:8px; text-align:left; font-size:13px;">
                  <div><b>Sport / Role:</b> ${p2.sport} (${p2.position})</div>
                  <div><b>Overall Skill Score:</b> <span style="color:var(--cyan); font-weight:700;">${p2.skill_score}/100</span></div>
                  <div><b>Verified Match Perf:</b> ${p2.performance_score}/100</div>
                  <div><b>Progress / Improvement:</b> <span class="progress-up">+${p2.progress_pct}%</span></div>
                  <div><b>Major Matches:</b> ${p2.major_matches}</div>
                  <div><b>Verified Local Matches:</b> ${p2.verified_local_matches}</div>
                  <div><b>Availability:</b> ${p2.availability}</div>
                </div>
              </div>
            </div>
            <div style="margin-top:20px; text-align:center;">
              <button class="btn btn-primary" onclick="UIController.closeModal('compareModal')">Done</button>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }
    this.openModal('compareModal');
  },

  openSmartMatchModal(matchItem) {
    let modal = document.getElementById('smartMatchModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'smartMatchModal';
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-window">
          <div class="modal-header">
            <h3>🎯 Smart Talent Match Breakdown</h3>
            <button class="modal-close" onclick="UIController.closeModal('smartMatchModal')">✕</button>
          </div>
          <div class="modal-body" id="smartMatchModalBody"></div>
        </div>
      `;
      document.body.appendChild(modal);
    }

    const p = matchItem.player;
    const body = document.getElementById('smartMatchModalBody');
    body.innerHTML = `
      <div class="match-explanation-box">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h4 style="font-size:18px;">${p.full_name}</h4>
            <div style="font-size:12px; color:var(--text-secondary);">${p.sport} • ${p.position} • ${p.location}</div>
          </div>
          <div class="match-score-pill">${matchItem.match_pct}% Match</div>
        </div>
        <p style="font-size:11px; color:var(--text-muted); margin-top:8px;">
          <em>The match percentage is an algorithmic recommendation based on verified metrics, not a guarantee of future game outcomes.</em>
        </p>
      </div>

      <h4 style="font-size:14px; margin-bottom:8px;">Why ${matchItem.match_pct}% Match?</h4>
      <ul class="match-checklist">
        ${(matchItem.reasons || []).map(r => `<li><span class="check">✓</span> ${r}</li>`).join('')}
      </ul>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:24px;">
        <button class="btn btn-outline" onclick="UIController.closeModal('smartMatchModal')">Close</button>
        <button class="btn btn-primary" onclick="UIController.showToast('Trial invitation dispatched to ${p.full_name}!'); UIController.closeModal('smartMatchModal');">Invite for Trial</button>
      </div>
    `;
    this.openModal('smartMatchModal');
  },

  openMessagesModal(partnerName = 'Coach Vikram Rathore', partnerRole = 'BCCI Level 2 Scout') {
    let modal = document.getElementById('chatModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'chatModal';
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-window" style="max-width: 620px;">
          <div class="modal-header">
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="font-size:24px;" id="chatPartnerAvatar">🧑‍🏫</span>
              <div>
                <h3 id="chatPartnerName" style="font-size:16px;">Coach Vikram Rathore</h3>
                <small id="chatPartnerMeta" style="color:var(--cyan); font-size:11.5px;">BCCI Level 2 Coach & Scout &bull; Online</small>
              </div>
            </div>
            <button class="modal-close" onclick="UIController.closeModal('chatModal')">✕</button>
          </div>
          <div class="modal-body" style="padding: 16px;">
            <div class="chat-window" style="height: 380px;">
              <div class="chat-messages" id="chatMessageStream">
                <div class="chat-bubble received">
                  <b>Coach Vikram</b><br>
                  Hello Rahul! I reviewed your verified 72 runs in the District T20 Final. Exceptional conversion and back-foot technique against pace.
                </div>
                <div class="chat-bubble sent">
                  <b>You</b><br>
                  Thank you Coach! Really appreciate your feedback. I have been focusing on quick singles and reaction timing in powerplays.
                </div>
                <div class="chat-bubble received" style="border: 1px solid rgba(255,184,0,0.4); background: rgba(255,184,0,0.08);">
                  <div class="badge badge-verified" style="margin-bottom:4px;">🏏 Selection Trial Invitation</div>
                  <b>Under-23 State Super League Combine</b><br>
                  Date: 20 September 2026, 09:00 AM<br>
                  Venue: Rajiv Gandhi Stadium Annex Ground, Hyderabad<br>
                  <div style="margin-top:8px; display:flex; gap:8px;">
                    <button class="btn btn-primary btn-sm" onclick="UIController.showToast('Trial invitation confirmed! Added to schedule.');">Accept Invitation</button>
                    <button class="btn btn-outline btn-sm" onclick="UIController.showToast('Declined trial invitation.');">Decline</button>
                  </div>
                </div>
              </div>
              <div class="chat-input-row">
                <input id="chatInputText" class="form-input" placeholder="Type message or reply..." onkeydown="if(event.key==='Enter') UIController.sendChatMessage()">
                <button class="btn btn-primary btn-sm" onclick="UIController.sendChatMessage()">Send ➔</button>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }
    this.openModal('chatModal');
  },

  sendChatMessage() {
    const input = document.getElementById('chatInputText');
    const txt = input.value.trim();
    if (!txt) return;

    const stream = document.getElementById('chatMessageStream');
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble sent';
    bubble.innerHTML = `<b>You</b><br>${txt}`;
    stream.appendChild(bubble);
    input.value = '';
    stream.scrollTop = stream.scrollHeight;

    // Typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'chat-bubble received';
    typingIndicator.id = 'chatTypingIndicator';
    typingIndicator.style.fontStyle = 'italic';
    typingIndicator.style.opacity = '0.7';
    typingIndicator.innerHTML = `<i>Coach Vikram is typing... ✍️</i>`;
    stream.appendChild(typingIndicator);
    stream.scrollTop = stream.scrollHeight;

    // Contextual intelligent responses
    setTimeout(() => {
      const el = document.getElementById('chatTypingIndicator');
      if (el) el.remove();
      const lower = txt.toLowerCase();
      let replyText = 'Noted! Looking forward to seeing your execution in the nets this Friday.';
      if (lower.includes('trial') || lower.includes('time') || lower.includes('when') || lower.includes('date')) {
        replyText = 'The Under-23 Combine starts at 09:00 AM sharp at Rajiv Gandhi Stadium Annex Ground. Bring your spike shoes, whites, and bat. Evaluators will assess reaction time and conversion rate under match-simulated pressure!';
      } else if (lower.includes('bat') || lower.includes('shot') || lower.includes('technique') || lower.includes('score')) {
        replyText = 'Your 72 runs in the Final showed outstanding shot selection against 135+ km/h pace. Maintain that high elbow in defense and keep punishing loose deliveries through extra cover.';
      } else if (lower.includes('thank') || lower.includes('coach') || lower.includes('hello') || lower.includes('hi') || lower.includes('hey')) {
        replyText = 'Keep that dedication burning! You have top-tier reaction timing (94/100) and your +21% improvement curve puts you right at the top of our scout priority list.';
      } else if (lower.includes('contract') || lower.includes('club') || lower.includes('selection')) {
        replyText = 'Hyderabad Warriors CC management is already reviewing your verified profile. If your trials go as well as your district matches, a formal squad placement offer will follow.';
      }

      const reply = document.createElement('div');
      reply.className = 'chat-bubble received';
      reply.innerHTML = `<b>Coach Vikram</b><br>${replyText}`;
      stream.appendChild(reply);
      stream.scrollTop = stream.scrollHeight;
    }, 850);
  },

  openApplyTrialModal(trialTitle = 'Under-23 District Selection Trials', clubName = 'Hyderabad Warriors CC') {
    let modal = document.getElementById('applyTrialModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'applyTrialModal';
      modal.className = 'modal-overlay';
      document.body.appendChild(modal);
    }
    modal.innerHTML = `
      <div class="modal-window" style="max-width: 540px;">
        <div class="modal-header">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:22px;">📋</span>
            <h3 style="font-size:17px;">Apply for Selection Trial</h3>
          </div>
          <button class="modal-close" onclick="UIController.closeModal('applyTrialModal')">✕</button>
        </div>
        <div class="modal-body">
          <div style="background:rgba(0, 230, 153, 0.07); border:1px solid rgba(0, 230, 153, 0.25); border-radius:var(--radius-md); padding:14px; margin-bottom:16px;">
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;">Target Combine</div>
            <div style="font-size:15px; font-weight:700; color:var(--primary); margin-top:2px;">${trialTitle}</div>
            <div style="font-size:12.5px; color:var(--text-secondary); margin-top:2px;">Hosted by: <b>${clubName}</b> &bull; Venue: Rajiv Gandhi Stadium Annex</div>
          </div>

          <div style="margin-bottom:14px; font-size:13px; color:var(--text-secondary);">
            Your verified credentials will be automatically attached to this scout application:
          </div>

          <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin-bottom:16px;">
            <div style="background:var(--bg-surface-elevated); padding:10px; border-radius:var(--radius-md); border:1px solid var(--border-subtle); text-align:center;">
              <small style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Skill Rating</small>
              <strong style="display:block; font-size:16px; color:var(--primary); margin-top:2px;">88 / 100</strong>
            </div>
            <div style="background:var(--bg-surface-elevated); padding:10px; border-radius:var(--radius-md); border:1px solid var(--border-subtle); text-align:center;">
              <small style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Classification</small>
              <strong style="display:block; font-size:13px; color:var(--gold); margin-top:3px;">🌟 Rising Talent</strong>
            </div>
            <div style="background:var(--bg-surface-elevated); padding:10px; border-radius:var(--radius-md); border:1px solid var(--border-subtle); text-align:center;">
              <small style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Progress Rate</small>
              <strong style="display:block; font-size:16px; color:var(--cyan); margin-top:2px;">+21%</strong>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Preferred Session Slot</label>
            <select class="form-select" id="trialSlotSelect">
              <option>Saturday Morning (09:00 AM - 12:00 PM) - Top Order Batting & Pace Nets</option>
              <option>Saturday Afternoon (02:00 PM - 05:00 PM) - Match Simulation & Fielding</option>
              <option>Sunday Morning (08:30 AM - 11:30 AM) - Final Selection Combine</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">Candidate Statement / Scout Note</label>
            <textarea class="form-input" id="trialNote" rows="3" placeholder="Highlight your current form, recent match highlights, or readiness...">Ready for high-intensity trials. Focused on opening powerplay execution and running conversion. Verified match score: 72 runs in District T20 Final.</textarea>
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:16px;">
            <button class="btn btn-outline btn-sm" onclick="UIController.closeModal('applyTrialModal')">Cancel</button>
            <button class="btn btn-primary btn-sm" onclick="UIController.submitTrialApplication('${trialTitle}', '${clubName}')">
              Submit Verified Application ➔
            </button>
          </div>
        </div>
      </div>
    `;
    this.openModal('applyTrialModal');
  },

  submitTrialApplication(title, club) {
    this.closeModal('applyTrialModal');
    this.showToast(`Application successfully submitted for "${title}"! Scout team has been notified.`, 'success');
  },

  openNotificationsModal() {
    let modal = document.getElementById('notifModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'notifModal';
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-window">
          <div class="modal-header">
            <h3>🔔 Notifications & Updates</h3>
            <button class="modal-close" onclick="UIController.closeModal('notifModal')">✕</button>
          </div>
          <div class="modal-body">
            <div style="display:flex; flex-direction:column; gap:12px;">
              <div style="background:var(--bg-surface-elevated); padding:12px 16px; border-radius:var(--radius-md); border-left:4px solid var(--primary);">
                <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted);">
                  <span>Opportunities &bull; Trials</span>
                  <span>14m ago</span>
                </div>
                <div style="font-size:14px; font-weight:700; margin:2px 0;">🏏 Trial Invitation Received</div>
                <p style="font-size:12.5px; color:var(--text-secondary);">Hyderabad Warriors CC invited you to the Under-23 State League Selection Trials.</p>
              </div>

              <div style="background:var(--bg-surface-elevated); padding:12px 16px; border-radius:var(--radius-md); border-left:4px solid var(--gold);">
                <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted);">
                  <span>Performance &bull; Classification</span>
                  <span>2h ago</span>
                </div>
                <div style="font-size:14px; font-weight:700; margin:2px 0;">🌟 Classified as Rising Talent</div>
                <p style="font-size:12.5px; color:var(--text-secondary);">Composite score updated to 88.0 and featured in regional talent spotlight.</p>
              </div>

              <div style="background:var(--bg-surface-elevated); padding:12px 16px; border-radius:var(--radius-md); border-left:4px solid var(--cyan);">
                <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted);">
                  <span>Verification &bull; Certificates</span>
                  <span>Yesterday</span>
                </div>
                <div style="font-size:14px; font-weight:700; margin:2px 0;">🟢 Certificate Verified</div>
                <p style="font-size:12.5px; color:var(--text-secondary);">Your District Under-19 Championship Trophy certificate was approved by Admin.</p>
              </div>
            </div>

            <div style="margin-top:20px; text-align:right;">
              <button class="btn btn-outline btn-sm" onclick="UIController.closeModal('notifModal'); UIController.showToast('All notifications marked as read.');">
                Mark All Read ✓
              </button>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }
    this.openModal('notifModal');
  },

  toggleTheme() {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const newTheme = isLight ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('scTheme', newTheme);
  },

  initTheme() {
    const saved = localStorage.getItem('scTheme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
  }
};

// =============================================================================
// 6. Dynamic Sport Selector Helper for Registration
// =============================================================================
function handleSportChange(sportSelectId, roleSelectId) {
  const sportSel = document.getElementById(sportSelectId);
  const roleSel = document.getElementById(roleSelectId);
  if (!sportSel || !roleSel) return;

  const roles = SPORT_ROLES[sportSel.value] || SPORT_ROLES.Other;
  roleSel.innerHTML = roles.map(r => `<option value="${r}">${r}</option>`).join('');
}

// Ensure theme is set on load
window.addEventListener('DOMContentLoaded', () => {
  UIController.initTheme();
});

// =============================================================================
// 7. Tournament Knockout Bracket & Match Inspector System
// =============================================================================
const TOURNAMENT_DATA = {
  'hyd-t20': {
    id: 'hyd-t20',
    title: 'Hyderabad District T20 Championship',
    subtitle: 'Under-23 & Open District League',
    organizer: 'Telangana Youth Sports Council',
    verifierCert: 'TS-SPO-2018-9941',
    venue: 'Gymkhana Grounds, Secunderabad',
    status: 'Completed',
    champion: 'Warriors XI',
    rounds: [
      {
        title: 'Quarter-Finals',
        matches: [
          {
            id: 'qf1',
            name: 'Quarter-Final 1',
            date: '24 Aug 2026',
            venue: 'Gymkhana Grounds',
            teamA: { name: 'Warriors XI', score: '184/5 (20.0)', winner: true, seed: 'Seed 1' },
            teamB: { name: 'Deccan Strikers', score: '152/9 (20.0)', winner: false, seed: 'Seed 8' },
            mvp: 'Arjun Reddy (54 runs, 2 wkts)',
            auditCode: 'TS-QF1-0081'
          },
          {
            id: 'qf2',
            name: 'Quarter-Final 2',
            date: '24 Aug 2026',
            venue: 'Gymkhana Grounds',
            teamA: { name: 'Charminar CC', score: '168/7 (20.0)', winner: true, seed: 'Seed 4' },
            teamB: { name: 'Secunderabad Royals', score: '164/8 (20.0)', winner: false, seed: 'Seed 5' },
            mvp: 'Sunil Varma (61 runs off 44 balls)',
            auditCode: 'TS-QF2-0082'
          },
          {
            id: 'qf3',
            name: 'Quarter-Final 3',
            date: '25 Aug 2026',
            venue: 'Rajiv Gandhi Stadium Annex',
            teamA: { name: 'Rising Stars XI', score: '190/4 (20.0)', winner: true, seed: 'Seed 2' },
            teamB: { name: 'Golconda Titans', score: '186/6 (20.0)', winner: false, seed: 'Seed 7' },
            mvp: 'Kiran Kumar (4 wkts for 18 runs)',
            auditCode: 'TS-QF3-0083'
          },
          {
            id: 'qf4',
            name: 'Quarter-Final 4',
            date: '25 Aug 2026',
            venue: 'Rajiv Gandhi Stadium Annex',
            teamA: { name: 'Cyberabad Kings', score: '175/6 (20.0)', winner: true, seed: 'Seed 3' },
            teamB: { name: 'Nizamabad Colts', score: '142/10 (17.4)', winner: false, seed: 'Seed 6' },
            mvp: 'Fahad Khan (3 wkts, 32 runs)',
            auditCode: 'TS-QF4-0084'
          }
        ]
      },
      {
        title: 'Semi-Finals',
        matches: [
          {
            id: 'sf1',
            name: 'Semi-Final 1',
            date: '26 Aug 2026',
            venue: 'Gymkhana Grounds',
            teamA: { name: 'Warriors XI', score: '176/6 (20.0)', winner: true },
            teamB: { name: 'Charminar CC', score: '172/8 (20.0)', winner: false },
            mvp: 'Rahul Kumar (58 runs, 4x4, 2x6)',
            auditCode: 'TS-SF1-0091'
          },
          {
            id: 'sf2',
            name: 'Semi-Final 2',
            date: '26 Aug 2026',
            venue: 'Rajiv Gandhi Stadium Annex',
            teamA: { name: 'Rising Stars XI', score: '182/5 (20.0)', winner: true },
            teamB: { name: 'Cyberabad Kings', score: '178/9 (20.0)', winner: false },
            mvp: 'Ravi Teja (64 runs off 39 balls)',
            auditCode: 'TS-SF2-0092'
          }
        ]
      },
      {
        title: 'Championship Final',
        matches: [
          {
            id: 'final',
            name: 'Grand Championship Final',
            date: '28 Aug 2026',
            venue: 'Gymkhana Grounds, Secunderabad',
            teamA: { name: 'Warriors XI', score: '188/4 (20.0)', winner: true, isChampion: true },
            teamB: { name: 'Rising Stars XI', score: '185/8 (20.0)', winner: false },
            mvp: 'Rahul Kumar (72 runs, 48 balls - 🌟 Player of the Final)',
            mvpPlayerId: 1,
            auditCode: 'TS-FNL-0100',
            highlight: 'Warriors XI won by 3 runs. Verified by TYSC Chief Match Referee.'
          }
        ]
      }
    ]
  }
};

const TournamentController = {
  getBracketHTML(tournId = 'hyd-t20') {
    const t = TOURNAMENT_DATA[tournId] || TOURNAMENT_DATA['hyd-t20'];
    let html = `
      <div class="bracket-wrapper">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; flex-wrap:wrap; gap:10px;">
          <div>
            <h4 style="font-size:16px; font-weight:800; color:var(--text-primary); display:flex; align-items:center; gap:8px;">
              <span>🏆</span> ${t.title}
              <span class="badge badge-verified">🟢 Official Bracket</span>
            </h4>
            <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
              Sanctioned by ${t.organizer} &bull; Reg: ${t.verifierCert} &bull; ${t.venue}
            </div>
          </div>
          <div style="display:flex; gap:8px;">
            <span class="badge badge-gold" style="font-size:11.5px;">👑 Champion: ${t.champion}</span>
          </div>
        </div>

        <div class="bracket-tree">
    `;

    t.rounds.forEach((round, rIdx) => {
      html += `
        <div class="bracket-column">
          <div class="bracket-round-title">
            <span>${rIdx === 0 ? '⚡' : (rIdx === 1 ? '🔥' : '👑')}</span> ${round.title}
          </div>
          <div class="bracket-matches">
      `;

      round.matches.forEach(m => {
        html += `
          <div class="bracket-match-node" onclick="TournamentController.openMatchModal('${m.id}', '${tournId}')" title="Click to view verified scorecard">
            <div class="bracket-match-header">
              <span>${m.name}</span>
              <span>${m.date}</span>
            </div>
            <div class="bracket-team ${m.teamA.winner ? 'winner' : ''}">
              <span>${m.teamA.winner ? '✓ ' : ''}${m.teamA.name} ${m.teamA.seed ? `<small style="color:var(--text-muted);">(${m.teamA.seed})</small>` : ''}</span>
              <span class="team-score">${m.teamA.score}</span>
            </div>
            <div class="bracket-team ${m.teamB.winner ? 'winner' : ''}">
              <span>${m.teamB.winner ? '✓ ' : ''}${m.teamB.name} ${m.teamB.seed ? `<small style="color:var(--text-muted);">(${m.teamB.seed})</small>` : ''}</span>
              <span class="team-score">${m.teamB.score}</span>
            </div>
            <div style="padding:4px 10px; font-size:10.5px; background:rgba(0,0,0,0.2); color:var(--cyan); border-top:1px solid rgba(255,255,255,0.04); display:flex; justify-content:space-between;">
              <span>⭐ ${m.mvp.split('(')[0]}</span>
              <span style="color:var(--primary);">Details ➔</span>
            </div>
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;
    });

    html += `
        </div>

        <div class="bracket-trophy-card">
          <div style="font-size:24px; margin-bottom:4px;">🏆</div>
          <h4 style="font-size:16px; font-weight:800; color:var(--gold);">CHAMPIONS: ${t.champion}</h4>
          <p style="font-size:12.5px; color:var(--text-secondary); max-width:600px; margin:4px auto 10px;">
            Hyderabad District T20 Championship trophy awarded to Hyderabad Warriors CC.
            Rahul Kumar named Player of the Tournament (202 runs, strike rate 146.4, 🌟 Rising Talent).
          </p>
          <div style="display:flex; justify-content:center; gap:10px;">
            <a href="player-dashboard.html" class="btn btn-primary btn-sm">Inspect Rahul's Resume ➔</a>
            <button class="btn btn-outline btn-sm" onclick="UIController.showToast('Verification record #TS-VFY-2026-88219 confirmed on SQLite ledger.', 'success')">Verify On-Chain Audit</button>
          </div>
        </div>
      </div>
    `;

    return html;
  },

  renderBracket(containerId, tournId = 'hyd-t20') {
    const el = document.getElementById(containerId);
    if (el) {
      el.innerHTML = this.getBracketHTML(tournId);
    }
  },

  openBracketModal(tournId = 'hyd-t20') {
    let modal = document.getElementById('tournamentBracketModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'tournamentBracketModal';
      modal.className = 'modal-overlay';
      document.body.appendChild(modal);
    }
    modal.innerHTML = `
      <div class="modal-window" style="max-width: 960px; width: 95%;">
        <div class="modal-header">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:22px;">🏆</span>
            <h3 style="font-size:17px;">Tournament Knockout Bracket</h3>
          </div>
          <button class="modal-close" onclick="UIController.closeModal('tournamentBracketModal')">✕</button>
        </div>
        <div class="modal-body" style="padding: 16px 20px;">
          ${this.getBracketHTML(tournId)}
        </div>
      </div>
    `;
    UIController.openModal('tournamentBracketModal');
  },

  openMatchModal(matchId, tournId = 'hyd-t20') {
    const t = TOURNAMENT_DATA[tournId] || TOURNAMENT_DATA['hyd-t20'];
    let matchObj = null;
    let roundTitle = '';
    for (const r of t.rounds) {
      const found = r.matches.find(m => m.id === matchId);
      if (found) {
        matchObj = found;
        roundTitle = r.title;
        break;
      }
    }
    if (!matchObj) return;

    let modal = document.getElementById('bracketMatchModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'bracketMatchModal';
      modal.className = 'modal-overlay';
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="modal-window" style="max-width: 580px;">
        <div class="modal-header">
          <div>
            <div class="badge badge-verified" style="margin-bottom:4px;">🟢 Verified Match Record</div>
            <h3 style="font-size:16px;">${matchObj.name} - ${roundTitle}</h3>
          </div>
          <button class="modal-close" onclick="UIController.closeModal('bracketMatchModal')">✕</button>
        </div>
        <div class="modal-body">
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">
            <div style="background:${matchObj.teamA.winner ? 'rgba(0, 230, 153, 0.09)' : 'var(--bg-surface-elevated)'}; border:1px solid ${matchObj.teamA.winner ? 'var(--primary)' : 'var(--border-subtle)'}; border-radius:var(--radius-md); padding:12px; text-align:center;">
              <div style="font-size:11px; color:var(--text-muted); text-transform:uppercase;">${matchObj.teamA.winner ? 'Winner 👑' : 'Runner'}</div>
              <div style="font-size:16px; font-weight:800; color:var(--text-primary); margin-top:2px;">${matchObj.teamA.name}</div>
              <div style="font-size:18px; font-weight:900; color:var(--primary); font-family:monospace; margin-top:4px;">${matchObj.teamA.score}</div>
            </div>
            <div style="background:${matchObj.teamB.winner ? 'rgba(0, 230, 153, 0.09)' : 'var(--bg-surface-elevated)'}; border:1px solid ${matchObj.teamB.winner ? 'var(--primary)' : 'var(--border-subtle)'}; border-radius:var(--radius-md); padding:12px; text-align:center;">
              <div style="font-size:11px; color:var(--text-muted); text-transform:uppercase;">${matchObj.teamB.winner ? 'Runner' : 'Winner 👑'}</div>
              <div style="font-size:16px; font-weight:800; color:var(--text-primary); margin-top:2px;">${matchObj.teamB.name}</div>
              <div style="font-size:18px; font-weight:900; color:var(--text-primary); font-family:monospace; margin-top:4px;">${matchObj.teamB.score}</div>
            </div>
          </div>

          <div style="background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:14px; margin-bottom:16px;">
            <div style="font-size:11.5px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;">⭐ Player of the Match</div>
            <div style="font-size:15px; font-weight:700; color:var(--gold); margin-top:2px;">${matchObj.mvp}</div>
            <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">Official match award verified by Telangana Youth Sports Council.</div>
            ${matchObj.mvpPlayerId === 1 ? `
              <div style="margin-top:10px;">
                <a href="player-dashboard.html" class="btn btn-primary btn-sm" style="font-size:12px; padding:4px 12px; text-decoration:none;">
                  View Rahul Kumar's Verified Resume ➔
                </a>
              </div>
            ` : ''}
          </div>

          <div style="display:flex; flex-direction:column; gap:6px; font-size:12px; color:var(--text-secondary); border-top:1px solid var(--border-subtle); padding-top:12px;">
            <div>📍 <b>Venue:</b> ${matchObj.venue} &bull; <b>Date:</b> ${matchObj.date}</div>
            <div>🛡️ <b>Sanctioning Verifier:</b> ${t.organizer} (Reg: ${t.verifierCert})</div>
            <div>🔐 <b>Audit Ledger Hash:</b> <code>${matchObj.auditCode}</code></div>
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:16px;">
            <button class="btn btn-outline btn-sm" onclick="UIController.closeModal('bracketMatchModal')">Close</button>
            <button class="btn btn-primary btn-sm" onclick="UIController.showToast('Official Scorecard PDF exported for ${matchObj.name}!', 'success'); UIController.closeModal('bracketMatchModal');">
              📥 Export Official Scorecard
            </button>
          </div>
        </div>
      </div>
    `;
    UIController.openModal('bracketMatchModal');
  }
};
window.TournamentController = TournamentController;

// =============================================================================
// Registration: role-specific fields, availability and cascading locations
// =============================================================================
const REG_SPORTS = ['Football','Cricket','Basketball','Tennis','Badminton','Volleyball','Athletics','Hockey','Kabaddi','Swimming','Wrestling','Table Tennis','Boxing','Archery'];
const REG_POSITIONS = {
  Football:['Goalkeeper','Centre Back','Left Back','Right Back','Defensive Midfielder','Central Midfielder','Attacking Midfielder','Left Winger','Right Winger','Striker / Centre Forward'],
  Cricket:['Opening Batter','Top-order Batter','Middle-order Batter','Wicketkeeper-Batter','All-rounder','Fast Bowler','Medium Pace Bowler','Off-spin Bowler','Leg-spin Bowler','Left-arm Spinner','Captain'],
  Basketball:['Point Guard','Shooting Guard','Small Forward','Power Forward','Center'],
  Tennis:['Singles Player','Doubles Player','All-court Player','Baseline Player','Serve-and-volley Player'],
  Badminton:['Singles Player','Doubles - Front Court','Doubles - Rear Court','Mixed Doubles Player'],
  Volleyball:['Setter','Outside Hitter','Opposite Hitter','Middle Blocker','Libero','Defensive Specialist','Serving Specialist'],
  Athletics:['Sprinter','Middle-distance Runner','Long-distance Runner','Hurdler','Relay Runner','Long Jumper','High Jumper','Triple Jumper','Pole Vaulter','Shot Putter','Discus Thrower','Javelin Thrower'],
  Hockey:['Goalkeeper','Defender','Midfielder','Forward'], Kabaddi:['Raider','Defender - Corner','Defender - Cover','All-rounder'],
  Swimming:['Freestyle','Backstroke','Breaststroke','Butterfly','Individual Medley','Distance Swimmer'],
  Wrestling:['Freestyle Wrestler','Greco-Roman Wrestler'], 'Table Tennis':['Singles Player','Doubles Player','Mixed Doubles Player'],
  Boxing:['Flyweight','Bantamweight','Featherweight','Lightweight','Welterweight','Middleweight','Light Heavyweight','Heavyweight'],
  Archery:['Recurve Archer','Compound Archer','Barebow Archer']
};
const REG_AVAILABILITY=['Morning (6:00 AM – 11:00 AM)','Afternoon (12:00 PM – 5:00 PM)','Evening (5:00 PM – 10:00 PM)'];
const REG_KERALA = {
Thiruvananthapuram:['Thiruvananthapuram City','Kazhakkoottam','Kovalam','Neyyattinkara','Nedumangad','Attingal','Varkala','Kattakada'], Kollam:['Kollam City','Chinnakada','Kavanad','Kundara','Kottarakkara','Punalur','Karunagappally','Paravur'], Pathanamthitta:['Pathanamthitta','Adoor','Thiruvalla','Pandalam','Konni','Ranni'], Alappuzha:['Alappuzha','Cherthala','Aroor','Ambalappuzha','Haripad','Kayamkulam','Mavelikkara','Chengannur'], Kottayam:['Kottayam','Changanassery','Pala','Vaikom','Ettumanoor','Erattupetta'], Idukki:['Thodupuzha','Kattappana','Munnar','Kumily','Adimali','Nedumkandam'], Ernakulam:['Kochi','Ernakulam','Kakkanad','Edappally','Kaloor','Vyttila','Fort Kochi','Tripunithura','Aluva','Angamaly','Perumbavoor','Muvattupuzha'], Thrissur:['Thrissur City','Punkunnam','Ollur','Mannuthy','Guruvayur','Chavakkad','Kunnamkulam','Irinjalakuda','Chalakudy'], Palakkad:['Palakkad','Ottapalam','Shoranur','Pattambi','Chittur','Mannarkkad','Alathur','Kanjikode'], Malappuram:['Malappuram','Manjeri','Perinthalmanna','Tirur','Ponnani','Kottakkal','Nilambur','Kondotty'], Kozhikode:['Kozhikode City','Nadakkavu','Mavoor Road','Palayam','Kallai','Feroke','Beypore','Kunnamangalam','Mukkam','Koduvally','Vatakara','Koyilandy'], Wayanad:['Kalpetta','Mananthavady','Sulthan Bathery','Vythiri','Meppadi','Panamaram'], Kannur:['Kannur City','Thalassery','Payyanur','Taliparamba','Iritty','Mattannur','Koothuparamba','Panoor'], Kasaragod:['Kasaragod','Kanhangad','Nileshwaram','Uppala','Manjeshwar','Bekal','Cheruvathur']};
const REG_AP_FALLBACK = ['Ananthapuramu','Annamayya','Alluri Sitharama Raju','Anakapalli','Bapatla','Chittoor','Dr. B.R. Ambedkar Konaseema','East Godavari','Eluru','Guntur','Kakinada','Krishna','Kurnool','Markapuram','Nandyal','Ntr','Palnadu','Parvathipuram Manyam','Prakasam','Srikakulam','Sri Potti Sriramulu Nellore','Sri Sathya Sai','Tirupati','Visakhapatnam','Vizianagaram','West Godavari','Y.S.R. Kadapa','Polavaram'];
let REG_AP_ROWS=[];
const REG_AP_CSV='https://raw.githubusercontent.com/mchittineni/india-village-finder/refs/heads/main/andhra_pradesh/data/andhra_pradesh_villages.csv';
const regOptions=(arr,ph)=>`<option value="">${ph}</option>`+arr.map(x=>`<option value="${String(x).replace(/"/g,'&quot;')}">${x}</option>`).join('');
function regSportSelect(id,label,change=''){return `<select id="${id}" class="form-select" ${change} required>${regOptions(REG_SPORTS,label)}</select>`;}
function regAvailability(id){return `<select id="${id}" class="form-select" required>${regOptions(REG_AVAILABILITY,'Choose availability')}</select>`;}
function registrationDetails(role){
 const loc=`<div class="form-group"><label class="form-label">Location</label><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"><select id="regState" class="form-select" onchange="regStateChanged()" required>${regOptions(['Andhra Pradesh','Kerala'],'Choose state')}</select><select id="regDistrict" class="form-select" onchange="regDistrictChanged()" required><option value="">Choose district</option></select><select id="regArea" class="form-select" onchange="regAreaChanged()" required><option value="">Choose city / town / mandal</option></select><select id="regVillage" class="form-select" required><option value="">Choose village / local area</option></select></div></div>`;
 if(role==='Player') return `<div class="form-group"><label class="form-label">Sport</label>${regSportSelect('regSport','Choose sport','onchange="regSportChanged()"')}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"><div class="form-group"><label class="form-label">Skill Level</label><select id="regSkill" class="form-select" required>${regOptions(['Beginner','Intermediate','Advanced','Professional'],'Choose skill level')}</select></div><div class="form-group"><label class="form-label">Position / Playing Role</label><select id="regPosition" class="form-select" required><option value="">Choose position</option></select></div></div><div class="form-group"><label class="form-label">Availability</label>${regAvailability('regAvailability')}</div>${loc}`;
 if(role==='Coach') return `<div class="form-group"><label class="form-label">Main Sport</label>${regSportSelect('regSport','Choose sport','onchange="regSportChanged()"')}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"><div class="form-group"><label class="form-label">Coaching Experience (years)</label><input id="regExperience" type="number" min="0" class="form-input" required></div><div class="form-group"><label class="form-label">Coaching Role / Specialization</label><select id="regPosition" class="form-select" required><option value="">Choose coaching role</option></select></div></div><div class="form-group"><label class="form-label">Current Team (optional)</label><input id="regTeam" class="form-input"></div><div class="form-group"><label class="form-label">Availability</label>${regAvailability('regAvailability')}</div>${loc}`;
 if(role==='Organizer') return `<div class="form-group"><label class="form-label">Primary Sport</label>${regSportSelect('regSport','Choose sport')}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"><div class="form-group"><label class="form-label">Organizer Type</label><select id="regOrganizerType" class="form-select" required>${regOptions(['Individual','Club','School / College','Academy','Sports Organization'],'Choose organizer type')}</select></div><div class="form-group"><label class="form-label">Organizer Role</label><select id="regPosition" class="form-select" required>${regOptions(['Tournament Director','Event Coordinator','Fixture Manager','Venue Coordinator','Team Coordinator','Operations Manager'],'Choose organizer role')}</select></div></div><div class="form-group"><label class="form-label">Organization / Club Name</label><input id="regOrganization" class="form-input" required></div><div class="form-group"><label class="form-label">Availability</label>${regAvailability('regAvailability')}</div>${loc}`;
 return `<div class="form-group"><label class="form-label">Main Sport</label>${regSportSelect('regSport','Choose sport','onchange="regSportChanged()"')}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"><div class="form-group"><label class="form-label">Refereeing Level</label><select id="regLevel" class="form-select" required>${regOptions(['Local','District','State','National','International'],'Choose level')}</select></div><div class="form-group"><label class="form-label">Official Role</label><select id="regPosition" class="form-select" required><option value="">Choose official role</option></select></div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"><input id="regExperience" type="number" min="0" class="form-input" placeholder="Experience (years)" required><input id="regCertification" class="form-input" placeholder="Certification / license" required></div><div class="form-group"><label class="form-label">Availability</label>${regAvailability('regAvailability')}</div>${loc}`;
}
function selectRole(role){selectedRegRole=role; ['Player','Coach','Organizer','Referee'].forEach(r=>{const b=document.getElementById('roleBtn'+r);if(b)b.classList.toggle('selected',r===role);});const c=document.getElementById('registrationRoleDetails');if(c){c.innerHTML=registrationDetails(role); if(document.getElementById('regSport')) regSportChanged(); regStateChanged();}}
function regStateChanged(){const d=document.getElementById('regDistrict'),a=document.getElementById('regArea'),v=document.getElementById('regVillage'),state=document.getElementById('regState')?.value;if(!d)return; a.innerHTML='<option value="">Choose city / town / mandal</option>';v.innerHTML='<option value="">Choose village / local area</option>'; if(state==='Kerala'){d.innerHTML=regOptions(Object.keys(REG_KERALA),'Choose district');} else if(state==='Andhra Pradesh'){const ds=[...new Set((REG_AP_ROWS.length?REG_AP_ROWS.map(r=>r.District):REG_AP_FALLBACK))].sort();d.innerHTML=regOptions(ds,'Choose district'); if(!REG_AP_ROWS.length) loadAPData();} else d.innerHTML='<option value="">Choose district</option>';}
async function loadAPData(){try{const txt=await (await fetch(REG_AP_CSV)).text(); const lines=txt.split(/\r?\n/).slice(1); REG_AP_ROWS=lines.map(l=>{const p=l.split(',');return p.length>=7?{District:p[1],Mandal:p[3],Village:p[5]}:null}).filter(Boolean); const st=document.getElementById('regState');if(st?.value==='Andhra Pradesh')regStateChanged();}catch(e){console.warn('AP location dataset unavailable; fallback districts used.',e);}}
function regDistrictChanged(){const state=document.getElementById('regState')?.value,d=document.getElementById('regDistrict')?.value,a=document.getElementById('regArea'),v=document.getElementById('regVillage');if(!a)return;v.innerHTML='<option value="">Choose village / local area</option>';let vals=[];if(state==='Kerala')vals=REG_KERALA[d]||[];else if(state==='Andhra Pradesh')vals=[...new Set(REG_AP_ROWS.filter(r=>r.District===d).map(r=>r.Mandal))].sort();a.innerHTML=regOptions(vals,'Choose city / town / mandal');}
function regAreaChanged(){const state=document.getElementById('regState')?.value,d=document.getElementById('regDistrict')?.value,a=document.getElementById('regArea')?.value,v=document.getElementById('regVillage');if(!v)return;let vals=[];if(state==='Andhra Pradesh')vals=[...new Set(REG_AP_ROWS.filter(r=>r.District===d&&r.Mandal===a).map(r=>r.Village))].sort();else if(state==='Kerala')vals=[a];v.innerHTML=regOptions(vals,'Choose village / local area');}
function regSportChanged(){const sport=document.getElementById('regSport')?.value,el=document.getElementById('regPosition');if(!el)return;let vals=REG_POSITIONS[sport]||[];if(selectedRegRole==='Coach')vals=vals.map(x=>x+' Coach').concat(['Head Coach','Assistant Coach','Fitness / Conditioning Coach','Skills Coach']);if(selectedRegRole==='Referee')vals=sport==='Football'?['Referee','Assistant Referee','Fourth Official']:sport==='Cricket'?['On-field Umpire','Third Umpire','Match Referee','Reserve Umpire']:['Main Referee / Umpire','Assistant Official','Line Judge','Score Official'];el.innerHTML=regOptions(vals,selectedRegRole==='Coach'?'Choose coaching role':selectedRegRole==='Referee'?'Choose official role':'Choose position');}
async function handleLandingRegister(){
 const role=selectedRegRole,name=document.getElementById('regName')?.value.trim(),username=document.getElementById('regUsername')?.value.trim(),email=document.getElementById('regEmail')?.value.trim().toLowerCase(),phone=document.getElementById('regPhone')?.value.trim(),password=document.getElementById('regPassword')?.value;
 if(!name||!username||!email||!phone||!password){UIController.showToast('Please complete the basic account fields.','info');return;}
 const state=document.getElementById('regState')?.value,district=document.getElementById('regDistrict')?.value,area=document.getElementById('regArea')?.value,village=document.getElementById('regVillage')?.value;
 const sport=document.getElementById('regSport')?.value||'Multi-Sport',position=document.getElementById('regPosition')?.value||'';
 if(!state||!district||!area||!village||!document.getElementById('regAvailability')?.value){UIController.showToast('Please select state, district, city/town/mandal, local area and availability.','info');return;}
 const payload={role,full_name:name,username,email,phone,password,sport,position,availability:document.getElementById('regAvailability').value,state,district,city:area,village,location:`${village}, ${area}, ${district}, ${state}`,skill_level:document.getElementById('regSkill')?.value||'',experience_years:document.getElementById('regExperience')?.value||0,current_team:document.getElementById('regTeam')?.value||'',organizer_type:document.getElementById('regOrganizerType')?.value||'',organization_name:document.getElementById('regOrganization')?.value||'',refereeing_level:document.getElementById('regLevel')?.value||'',certification:document.getElementById('regCertification')?.value||''};
 try{const r=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok){UIController.showToast(data.error||'Registration failed.','info');return;}SessionManager.setUser(data.user||payload);UIController.showToast('Account created successfully.');setTimeout(()=>SessionManager.redirectForRole((data.user||payload).role),700);}catch(e){UIController.showToast('Start server.py first, then create your account.','info');}
}
window.addEventListener('DOMContentLoaded',()=>{if(document.getElementById('registrationRoleDetails'))selectRole('Player');});

window.addEventListener('DOMContentLoaded', () => setTimeout(applyAuthenticatedIdentity, 0));


// Universal authenticated identity sync for all dashboard types.
// Any real logged-in account is displayed using its registered name/username;
// demo names remain only inside demo/scouting content cards.
(function(){
  function syncAuthenticatedIdentity(){
    let user=null;
    try{ user=JSON.parse(localStorage.getItem('scUser') || localStorage.getItem('sporthubUser') || 'null'); }catch(e){}
    if(!user || !user.role) return;
    const name=user.full_name || user.name || user.username || 'SportHub Member';
    const username=user.username ? '@'+user.username : '';
    const role=user.role;
    const byId=(id)=>document.getElementById(id);
    const set=(id,text)=>{const el=byId(id);if(el && text) el.textContent=text;};

    if(role==='Player'){
      set('playerNameTitle',name);
      set('resFullName',name);
      set('dashboardName',name);
      set('headerName',name);
      const sub=byId('playerSubtitle');
      if(sub) sub.textContent=[user.sport,user.position,user.location || [user.city,user.district,user.state].filter(Boolean).join(', ')].filter(Boolean).join(' | ');
    }else if(role==='Coach'){
      set('coachWelcomeName','Coach '+name);
      set('coachWelcomeMeta',[username,user.sport,user.city || user.location,user.district,user.state].filter(Boolean).join(' • ') || 'Your registered Coach profile');
      set('dashboardName',name); set('headerName',name); set('sideName',name);
    }else if(role==='Organizer'){
      set('organizerWelcomeName',name);
      set('dashboardName',name); set('headerName',name); set('sideName',name);
      const welcomeMeta=byId('organizerWelcomeMeta');
      if(welcomeMeta) welcomeMeta.textContent=[username,user.sport,user.city || user.location,user.district,user.state].filter(Boolean).join(' • ') || 'Your registered Organizer profile';
    }else if(role==='Referee'){
      set('dashboardName',name); set('headerName',name); set('sideName',name);
    }else if(role==='Club'){
      set('clubWelcomeName',name);
      set('dashboardName',name); set('headerName',name); set('sideName',name);
      const brandName=byId('clubBrandUserName');
      if(brandName) brandName.textContent=username || name;
    }
    document.querySelectorAll('[data-auth-name]').forEach(el=>el.textContent=name);
    document.querySelectorAll('[data-auth-username]').forEach(el=>el.textContent=username);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',syncAuthenticatedIdentity);
  else syncAuthenticatedIdentity();
  window.syncAuthenticatedIdentity=syncAuthenticatedIdentity;
})();
