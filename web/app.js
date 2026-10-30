(function(){
const D = window.SB, P = window.SB_PRESET || {};
const qs = new URLSearchParams(location.search);
let KID = P.kid || qs.get('kid') || 'all';
const PRINT = !!P.print || qs.get('print') === '1';
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const T = D.teams, KIDS = D.kids;
const kidOf = k => KIDS.find(x => x.key === k);
const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const dparts = iso => { const [y,m,d] = iso.slice(0,10).split('-').map(Number); return {y,m,d,dow:new Date(Date.UTC(y,m-1,d)).getUTCDay()}; };
const fdate = iso => { const p = dparts(iso); return `${DOW[p.dow]} ${MON[p.m-1]} ${p.d}`; };
const ftime = (iso, allDay) => { if (allDay || /T00:00:00/.test(iso)) return 'all day'; const h = +iso.slice(11,13), m = iso.slice(14,16); return `${(h%12)||12}:${m} ${h<12?'AM':'PM'}`; };
const fdays = days => days.length === 1 ? fdate(days[0]) : `${fdate(days[0])} – ${fdate(days[days.length-1]).replace(/^\w+ /,'')}`;
const visible = k => KID === 'all' || KID === k;
const gen = D.generatedAt;

function stat(n, l){ return `<div><b>${n}</b><span>${l}</span></div>`; }

function kidCard(k){
  const s = k.stats, teams = k.teams.map(t => T[t]);
  const totalRes = D.events.filter(e => e.kid === k.key && (e.kind === 'game' || e.kind === 'scrimmage') && e.status === 'played').length;
  return `<div class="kcard" style="--k:${k.color}"><div class="band"></div><div class="in">
   <div class="nm"><div><h3>${esc(k.name)}</h3><div class="full">${esc(k.full)} · born ${fdate(k.born).replace(/^\w+ /,'')}, ${k.born.slice(0,4)}</div></div>
   <div class="age"><b>${k.age}</b>years old</div></div>
   <div class="teamchips">${teams.map(t => `<span class="chip" style="--c:${t.color}">${t.emoji} ${esc(t.name)} · ${t.sport}</span>`).join('')}</div>
   <div class="glance">${stat(s.played,'games played')}${stat(s.upcoming,'upcoming')}${stat(s.travelVenues,'travel venues')}${stat(s.tournaments,'tournaments')}</div>
   <div class="facts">
    <div><span class="k">Results found in team mail:</span> <b>${s.resultsFound}</b> of ${totalRes} played games &amp; scrimmages ${s.resultsFound ? '' : '<span class="nores">· result not found for each one</span>'}</div>
    ${s.farthest ? `<div><span class="k">Farthest trip:</span> ${esc(s.farthest.town)} · ${s.farthest.miles} mi straight-line · ${fdate(s.farthest.date)}${s.farthest.opponent ? ' vs ' + esc(s.farthest.opponent) : ''}</div>` : ''}
    <div><span class="k">States played in:</span> ${s.states.join(' · ')} &nbsp; <span class="k">Venues:</span> ${s.venues} &nbsp; <span class="k">Practices &amp; training:</span> ${s.practices} (${s.practicesPlayed} so far)</div>
    ${s.busiestWeekend ? `<div><span class="k">Busiest weekend:</span> ${fdate(s.busiestWeekend.start)} · ${s.busiestWeekend.games} games</div>` : ''}
    ${s.scrimmages ? `<div><span class="k">Scrimmages:</span> ${s.scrimmages}</div>` : ''}
   </div></div></div>`;
}

function ribbon(){
  const teams = Object.values(T).filter(t => visible(t.kid));
  const x0 = Date.UTC(2026,7,1), x1 = Date.UTC(2026,11,31), W = 1160, L = 190, R = 16, rowH = 34, H = 34 + teams.length*rowH + 8;
  const X = iso => { const p = dparts(iso); return L + (Date.UTC(p.y,p.m-1,p.d) - x0)/(x1-x0)*(W-L-R); };
  let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" font-family="SB Grotesk" font-size="11">`;
  for (let m = 7; m <= 11; m++){ const iso = `2026-${String(m+1).padStart(2,'0')}-01`, x = X(iso);
    s += `<line x1="${x}" x2="${x}" y1="18" y2="${H-4}" stroke="#d6cfc0"/><text x="${x+4}" y="14" fill="#78716c" letter-spacing="2">${MON[m].toUpperCase()}</text>`; }
  const nx = X(gen); s += `<line x1="${nx}" x2="${nx}" y1="16" y2="${H-2}" stroke="#b45309" stroke-width="2" stroke-dasharray="4 3"/><text x="${nx+4}" y="${H-4}" fill="#b45309" font-weight="700">today</text>`;
  teams.forEach((t,i) => {
    const y = 34 + i*rowH + rowH/2;
    s += `<text x="8" y="${y+4}" font-weight="700" fill="${t.color}">${t.emoji} ${esc(t.name.replace(/ \(.*\)/,''))}</text><line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="#ece6d8"/>`;
    D.tournaments.filter(x => x.team === t.key && x.status !== 'canceled').forEach(x => {
      const a = X(x.days[0]) - 5, b = X(x.days[x.days.length-1]) + 5;
      s += `<rect x="${a}" y="${y-12}" width="${b-a}" height="24" rx="5" fill="${t.color}" opacity=".14"><title>${esc(x.name)}</title></rect>`; });
    D.events.filter(e => e.team === t.key && (e.kind === 'game' || e.kind === 'scrimmage')).forEach(e => {
      const x = X(e.start);
      if (e.status === 'canceled') s += `<text x="${x}" y="${y+4}" text-anchor="middle" fill="#a8a29e" font-size="12">×</text>`;
      else if (e.status === 'played') s += `<circle cx="${x}" cy="${y}" r="5.2" fill="${t.color}"><title>${fdate(e.start)} ${esc(e.mark||'')} ${esc(e.opponent||e.core)} · result not found</title></circle>`;
      else s += `<circle cx="${x}" cy="${y}" r="5" fill="#fff" stroke="${t.color}" stroke-width="2"><title>${fdate(e.start)} ${esc(e.mark||'')} ${esc(e.opponent||e.core)}</title></circle>`;
    });
  });
  return s + '</svg>';
}

function teamBook(t){
  const evs = D.events.filter(e => e.team === t.key && ['game','scrimmage','tournament'].includes(e.kind));
  const nextId = (D.events.find(e => e.team === t.key && (e.kind==='game'||e.kind==='scrimmage') && e.status==='upcoming')||{}).id;
  const tours = D.tournaments.filter(x => x.team === t.key);
  const s = t.stats;
  let rows = '', n = 0, shownTour = new Set();
  evs.forEach(e => {
    if (e.kind === 'tournament') {
      const tr = tours.find(x => x.days.includes(e.date) && (x.titles.includes(e.core) || x.days.length === 1 || tours.filter(y => y.days.includes(e.date)).length === 1));
      const key = tr ? tr.name : e.core;
      if (shownTour.has(key)) return; shownTour.add(key);
      const cx = tr && tr.status === 'canceled';
      rows += `<tr class="tour${cx?' cx':''}"><td class="n">🏆</td><td class="d">${tr ? fdays(tr.days) : fdate(e.start)}</td><td colspan="5">${esc(tr ? tr.name : e.core)} ${cx?'<span class="tag cx">canceled</span>':''} <span class="sub2">· ${esc(tr && tr.venues.length ? tr.venues.join(' / ') : (e.location || 'location TBD'))}${tr && tr.miles != null ? ` · ${tr.miles} mi` : ''}</span></td></tr>`;
      return;
    }
    const cx = e.status === 'canceled', up = e.status === 'upcoming';
    if (!cx) n++;
    const notes = [e.notes.kit && ('Kit: ' + e.notes.kit), e.notes.arrival && ('Arrive ' + e.notes.arrival), e.notes.extra].filter(Boolean).join(' · ');
    const fieldLike = sp => /^(Field\b|\d+[AB]\b|Upper Kinder)/i.test(sp || '');
    const spot = e.notes.spot || '';
    const venue = e.venueName || (spot && !fieldLike(spot) ? spot.split(' - ')[0] : '') || (e.address || '');
    const fieldTxt = e.field || (fieldLike(spot) ? spot : (spot.includes(' - ') ? spot.split(' - ').slice(1).join(' - ') : ''));
    const res = e.result && e.result.found ? `<span class="res found">${esc(e.result.score)}</span><div class="sub2">${esc(e.result.source && e.result.source.sender || '')}</div>` : `<span class="res nores">${cx ? '—' : (up ? 'not played yet' : 'result not found')}</span>`;
    rows += `<tr class="${cx?'cx':up?(e.id===nextId?'next':'up'):''}" data-id="${e.id}">
      <td class="n">${cx?'':n}</td><td class="d">${fdate(e.start)}<div class="sub2">${ftime(e.start, e.allDay)}</div></td>
      <td class="opp"><span class="mark">${esc(e.mark || '')}</span><b>${esc(e.opponent || (e.core.match(/championship/i) ? 'Championship game · opponent TBD' : e.core))}</b>
        ${e.kind==='scrimmage'?'<span class="tag scr">scrimmage</span>':''}${cx?'<span class="tag cx">canceled</span>':''}${e.id===nextId?'<span class="tag next">next up</span>':up?'<span class="tag up">upcoming</span>':''}${e.tournament?`<div class="sub2">🏆 ${esc(e.tournament)}</div>`:''}</td>
      <td>${esc(venue || '—')}<div class="sub2">${esc(e.town || 'venue not listed on the calendar')}${fieldTxt?' · '+esc(fieldTxt):''}</div></td>
      <td class="mi">${e.miles != null ? e.miles + ' mi' : '—'}${(e.miles||0) >= D.travelMiles ? '<div><span class="tag trv">travel</span></div>' : ''}</td>
      <td class="sub2">${esc(notes)}</td><td>${res}</td></tr>`;
  });
  const pr = D.events.filter(e => e.team === t.key && (e.kind==='practice'||e.kind==='training') && e.status !== 'canceled');
  const prv = {}; pr.forEach(e => { const v = e.venueName || (e.notes.spot||'').split(' - ')[0] || e.location || 'location not listed'; prv[v] = (prv[v]||0)+1; });
  const kid = kidOf(t.kid);
  return `<div class="team" style="--c:${t.color}" id="team-${t.key}">
   <div class="th"><span class="em">${t.emoji}</span><div><h3>${esc(t.name)}</h3><div class="meta">${t.sport} · ${esc(kid.name)} · source: ${esc(t.calendar)}</div></div>
    <div class="rec">Record<b>${s.resultsFound ? '' : 'not stated'}</b>${s.resultsFound ? '' : 'no scores in team mail yet'}</div></div>
   ${t.bonus ? `<div class="bonus">${esc(t.bonus)}</div>` : ''}
   <div class="tstats"><div><b>${s.games}</b>games</div><div><b>${s.played}</b>played</div><div><b>${s.upcoming}</b>upcoming</div><div><b>${s.tournaments}</b>tournaments</div><div><b>${s.travelVenues}</b>travel venues</div><div><b>${s.resultsFound}/${D.events.filter(e => e.team === t.key && (e.kind==='game'||e.kind==='scrimmage') && e.status==='played').length}</b>played w/ result</div>${s.canceled?`<div><b>${s.canceled}</b>canceled</div>`:''}</div>
   <table class="sb"><thead><tr><th>#</th><th>Date</th><th>Opponent (as listed)</th><th>Venue</th><th style="text-align:right">From home</th><th>Kit · arrival</th><th>Result</th></tr></thead><tbody>${rows}</tbody></table>
   <div class="pracs"><b>${pr.length}</b> practices &amp; training sessions on the calendar (${pr.filter(e=>e.status==='played').length} so far) · ${Object.entries(prv).sort((a,b)=>b[1]-a[1]).map(([v,c])=>`${esc(v)} ×${c}`).join(' · ')}</div>
  </div>`;
}

function tourCards(){
  return `<div class="tgrid">${D.tournaments.filter(x => visible(x.kid)).map(x => { const t = T[x.team];
    const gm = x.games.map(id => D.events.find(e => e.id === id));
    return `<div class="tcard" style="--c:${t.color}"><span class="st tag ${x.status==='canceled'?'cx':x.status==='past'?'':'up'}">${x.status}</span>
     <div class="who">${t.emoji} ${esc(kidOf(x.kid).name)} · ${esc(t.name.replace(/ \(.*\)/,''))}</div><h4>${esc(x.name)}</h4>
     <div class="when">${fdays(x.days)}</div>
     <div class="sub2">${esc(x.venues.join(' / ') || 'location TBD on the calendar')}${x.miles!=null?` · ${x.miles} mi from home`:''}</div>
     ${gm.length ? `<ul>${gm.map(g => `<li>${fdate(g.start)} ${ftime(g.start)} · ${esc(g.mark||'')} ${esc(g.opponent || 'Championship game (TBD)')} — <span class="nores">${g.status==='played' ? (g.result.found ? esc(g.result.score) : 'result not found') : 'not played yet'}</span></li>`).join('')}</ul>` : `<div class="sub2" style="margin-top:8px">No individual games on the calendar for these days yet.</div>`}
    </div>`; }).join('')}</div>`;
}

function venueMap(vs){
  const W = 640, H = 600, lon0 = -78.15, lon1 = -74.55, lat0 = 37.35, lat1 = 40.75;
  const kx = Math.cos(39*Math.PI/180);
  const sx = W/((lon1-lon0)*kx), sy = H/(lat1-lat0), sc = Math.min(sx, sy);
  const X = lon => (lon-lon0)*kx*sc, Y = lat => (lat1-lat)*sc;
  const hx = X(-76.6480219), hy = Y(39.0000000);
  let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" font-family="SB Grotesk">
   <defs><pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="#ece4d0" stroke-width="1"/></pattern></defs>
   <rect width="${W}" height="${H}" fill="url(#g)"/>`;
  [25,50,100].forEach(mi => { const r = mi/69*sc; s += `<circle cx="${hx}" cy="${hy}" r="${r}" fill="none" stroke="#b45309" stroke-opacity=".45" stroke-dasharray="5 5"/><text x="${hx+r*0.71+4}" y="${hy-r*0.71}" font-size="11" fill="#b45309">${mi} mi</text>`; });
  // group by town
  const towns = {}; vs.forEach(v => { if (v.lat == null) return; const k = v.town; (towns[k] = towns[k] || {town:k, lat:v.lat, lon:v.lon, visits:0, kids:new Set(), miles:v.miles}); towns[k].visits += v.visits; v.kids.forEach(x => towns[k].kids.add(x)); });
  const placed = [[hx-60, hy-14, hx+150, hy+24]];
  const hit = b => placed.some(p => !(b[2] < p[0] || b[0] > p[2] || b[3] < p[1] || b[1] > p[3]));
  const dots = Object.values(towns).map(t => ({...t, x: X(t.lon), y: Y(t.lat), r: 4 + Math.sqrt(t.visits)*2.6}));
  dots.forEach(d => placed.push([d.x-d.r, d.y-d.r, d.x+d.r, d.y+d.r]));
  let labels = '';
  dots.sort((a,b)=>b.miles-a.miles).forEach(d => {
    const name = d.town.replace(/, (MD|VA|PA|NJ|DC)$/,''), w = name.length*6.1 + 4;
    const tries = [[d.x+d.r+3, d.y+4, 'start'], [d.x-d.r-3, d.y+4, 'end'], [d.x, d.y-d.r-4, 'middle'], [d.x, d.y+d.r+12, 'middle']];
    for (const [lx, ly, a] of tries) {
      const x0 = a==='start'?lx:a==='end'?lx-w:lx-w/2, b = [x0, ly-10, x0+w, ly+3];
      if (b[0] < 2 || b[2] > W-2 || hit(b)) continue;
      placed.push(b); labels += `<text x="${lx}" y="${ly}" text-anchor="${a}" font-size="11" fill="#292524">${esc(name)}</text>`; break;
    }
  });
  dots.sort((a,b)=>b.visits-a.visits).forEach(d => { const ks = [...d.kids]; const col = ks.length > 1 ? '#57534e' : kidOf(ks[0]).color;
    s += `<circle cx="${d.x}" cy="${d.y}" r="${d.r}" fill="${col}" fill-opacity=".8" stroke="#fff" stroke-width="1.5"><title>${esc(d.town)} · ${d.visits} calendar visits · ${d.miles} mi</title></circle>`; });
  s += labels;
  s += `<path d="M${hx} ${hy-9} l2.6 6 6.4.5-4.9 4.2 1.5 6.3-5.6-3.4-5.6 3.4 1.5-6.3-4.9-4.2 6.4-.5z" fill="#b45309" stroke="#fff"/><text x="${hx+10}" y="${hy+18}" font-size="12" font-weight="700" fill="#b45309">Home · Hometown</text>`;
  s += `<text x="10" y="18" font-size="11" fill="#78716c">Town-level positions (OpenStreetMap geocode). Rings = straight-line miles, not drive time.</text>`;
  s += `<text x="10" y="34" font-size="11" fill="#78716c">● <tspan fill="${kidOf('kida').color}">Kid A</tspan> ● <tspan fill="${kidOf('kidb').color}">Kid B</tspan> ● <tspan fill="#57534e">both</tspan> · dot size = number of calendar visits</text>`;
  return s + '</svg>';
}

function compass(v){
  if (v.lat == null) return '';
  const dy = v.lat - 39.0000000, dx = (v.lon + 76.6480219) * Math.cos(39*Math.PI/180);
  const ang = (Math.atan2(dx, dy) * 180/Math.PI + 360) % 360;
  return ['north','NNE','NE','ENE','east','ESE','SE','SSE','south','SSW','SW','WSW','west','WNW','NW','NNW'][Math.round(ang/22.5) % 16];
}
function venues(){
  const vs = D.venues.filter(v => v.kids.some(visible));
  const list = vs.map(v => {
    const ks = v.kids.filter(visible), col = ks.length > 1 ? '#57534e' : kidOf(ks[0]).color;
    const kinds = Object.entries(v.kinds).map(([k,c]) => `${c} ${k.replace('_',' ')}${c>1&&!k.endsWith('s')?'s':''}`).join(', ');
    const dn = [];
    if (v.directions) dn.push(`<b>On arrival:</b> ${esc(v.directions)}`);
    const spots = v.notes.filter(n => !/^(Field \w+|\w{1,3})$/.test(n) && n !== v.name && n.includes(' - ')).map(n => n.split(' - ').slice(1).join(' - '));
    if (spots.length) dn.push(`<b>Where on site:</b> ${esc([...new Set(spots)].join(' · '))}`);
    if (v.fields.length) dn.push(`<b>Fields used:</b> ${esc(v.fields.join(', '))}`);
    if (v.townNote) dn.push(`<i>${esc(v.townNote)}</i>`);
    const cmp = compass(v);
    if (cmp && v.miles >= 3) dn.unshift(`<b>Heading:</b> ${cmp} of home, ${v.miles} mi straight-line (drive will be longer)`);
    return `<div class="vrow" style="--vc:${col}"><div class="top"><div><b>${esc(v.name)}</b>${v.travel?'<span class="tag trv">travel</span>':''}<div class="sub2">${esc(v.address && v.address !== v.name ? v.address : v.town)}</div></div>
     <div class="mi">${v.miles != null ? v.miles + ' mi' : '—'}</div></div>
     <div class="sub2">${v.teams.map(t => `${T[t].emoji} ${esc(T[t].name.replace(/ \(.*\)/,''))}`).join(' · ')} · ${kinds} · ${fdate(v.first)}${v.first!==v.last?' – '+fdate(v.last).replace(/^\w+ /,''):''}</div>
     ${dn.length ? `<div class="dn">${dn.join('<br>')}</div>` : ''}${v.directions || v.notes.some(n => n.includes(' - ')) ? '' : `<div class="dn"><i>No parking or on-site notes in the calendar for this venue.</i></div>`}</div>`; }).join('');
  return `<div class="vwrap"><div class="map">${venueMap(vs)}</div><div class="vlist">${list}</div></div>`;
}

function sources(){
  const g = D.gmail, cl = g.changeLog.filter(c => visible(T[c.team].kid));
  const cals = {}; D.events.forEach(e => { cals[e.source.calendar] = (cals[e.source.calendar]||0)+1; });
  return `<div class="src"><div class="box"><h3>Where every line came from</h3>
    <table><tr><th>Google Calendar (read-only list_events)</th><th>events Aug 1–Dec 31</th></tr>${Object.entries(cals).map(([c,n])=>`<tr><td>${esc(c)}</td><td class="mono">${n}</td></tr>`).join('')}</table>
    <p class="sub2">Opponents are exactly as the team calendar titles list them. “vs” / “@” is copied from the title; it is not a home/away claim.</p>
    <h3 style="margin-top:14px">Gmail searches (read-only search_threads)</h3>
    <table><tr><th>Search</th><th>threads</th><th>scores</th></tr>${g.searches.map(s=>`<tr><td><span class="mono" style="font-size:10.5px">${esc(s.query.slice(0,120))}${s.query.length>120?'…':''}</span><div class="sub2">${esc(s.what)}</div></td><td class="mono">${s.threads}</td><td class="mono">${s.relevant}</td></tr>`).join('')}</table>
    <p><b>Scores found: ${g.resultsFound}.</b> No team email or app notification in the connected inbox states a score for Kid A's or Kid B's teams, so every played game says <span class="nores">result not found</span>. Drop a stated score into <span class="mono">data/results.json</span> (with its source line) and rebuild to fill it in.</p></div>
   <div class="box"><h3>Schedule changes that arrived by email</h3><p class="sub2">${cl.length} Google Calendar notification emails about these teams (Bravo 11u and Delta send them; Alpha and Charlie are silent imports). Newest first.</p>
    <table><tr><th>Received</th><th>Team</th><th>What</th></tr>${cl.slice(0, PRINT ? 14 : 40).map(c=>`<tr><td class="mono" style="white-space:nowrap">${fdate(c.received)}</td><td>${T[c.team].emoji}</td><td><b>${esc(c.kind)}</b>${c.changed?` (${esc(c.changed)})`:''}: ${esc(c.title.replace(/^(Bravo 11u - Blue|Delta 2031 Green)\s*-?\s*/,''))}<div class="sub2">${esc(c.when)}</div></td></tr>`).join('')}</table></div></div>
   <div class="rules"><b>House rules this book follows.</b> Nothing is invented: no scores, opponents or results that a source didn't state. Ride coverage isn't assigned to anyone here; Parent A and Parent B decide that. Everything was read-only: no calendar edits, no RSVPs, no emails sent. Distances are straight-line from Hometown at town level; real drive times will be longer.</div>`;
}

function render(){
  document.body.classList.toggle('printmode', PRINT);
  const kids = KIDS.filter(k => visible(k.key));
  const ttl = KID === 'all' ? 'The Family' : kidOf(KID).full;
  $('#app').innerHTML = `
  <header class="mast"><div><div class="kick">Fall 2026 · Season Book</div><h1>${KID==='all'?'Season <em>Book</em>':esc(kidOf(KID).name)+'’s <em>Season</em>'}</h1>
   <div class="sub">${esc(ttl)} · Hometown, MD · Aug 1 – Dec 31, 2026 · a yearbook &amp; scorebook from the family calendar and team mail</div></div>
   <div class="stamp"><b>Built ${fdate(gen)}, ${ftime(gen)} ET</b>Read-only snapshot · scores only when a source states them</div></header>
  <nav class="tabs noprint"><a href="#overview">At a glance</a>${kids.map(k=>`<a href="#kid-${k.key}">${esc(k.name)}</a>`).join('')}<a href="#tournaments">Tournaments</a><a href="#venues">Venues</a><a href="#sources">Sources</a><span class="sp"></span>
   <span class="kidf">${['all','kida','kidb'].map(k=>`<button data-k="${k}" class="${KID===k?'on':''}">${k==='all'?'Both kids':esc(kidOf(k).name)}</button>`).join(' ')}</span></nav>
  <section id="overview"><div class="sh"><h2>Season at a glance</h2><span class="note">games played · upcoming · travel venues (≥ ${D.travelMiles} mi straight-line from home)</span></div>
   <div class="kids">${kids.map(kidCard).join('')}</div>
   <div class="ribbonbox"><svg style="display:none"></svg>${ribbon()}<div class="legend"><span>● played</span><span>○ upcoming</span><span>× canceled</span><span>▭ tournament days</span><span style="color:#b45309">┆ today</span></div></div></section>
  ${kids.map((k,i)=>`<section id="kid-${k.key}" class="${PRINT?'pb':''}"><div class="sh"><h2 style="color:${k.color}">${esc(k.name)}’s scorebook</h2><span class="note">${k.teams.map(t=>esc(T[t].name)).join(' · ')}</span></div>${k.teams.map(t=>teamBook(T[t])).join('')}</section>`).join('')}
  <section id="tournaments" class="${PRINT?'pb':''}"><div class="sh"><h2>Tournaments</h2><span class="note">multi-game weekends, grouped from the calendar</span></div>${tourCards()}</section>
  <section id="venues" class="${PRINT?'pb':''}"><div class="sh"><h2>Venues &amp; drive notes</h2><span class="note">nearest first · notes copied from the event descriptions</span></div>${venues()}</section>
  <section id="sources" class="${PRINT?'pb':''}"><div class="sh"><h2>Sources &amp; honesty</h2></div>${sources()}</section>
  <footer>Season Book · TokenMax build night, Oct 7 2026 · ${D.events.length} calendar events · ${D.venues.length} venues · ${D.tournaments.length} tournaments · generated ${esc(gen)}</footer>`;
  document.querySelectorAll('.kidf button').forEach(b => b.onclick = () => { KID = b.dataset.k; const u = new URL(location.href); if (KID==='all') u.searchParams.delete('kid'); else u.searchParams.set('kid', KID); history.replaceState(null,'',u); render(); });
  document.title = (KID==='all' ? 'Season Book' : kidOf(KID).name + "'s Season Book") + ' · Fall 2026';
}
render();
window.__SB_READY = true;
try { const o = {}; ['overview','kid-kida','kid-kidb','tournaments','venues','sources','team-alpha','team-bravo','team-charlie','team-delta'].forEach(id => { const el = document.getElementById(id); if (el) { const r = el.getBoundingClientRect(); o[id] = [Math.round(r.top + scrollY), Math.round(r.height)]; } }); o.total = document.documentElement.scrollHeight; document.documentElement.setAttribute('data-offsets', JSON.stringify(o)); } catch (e) {}
})();
