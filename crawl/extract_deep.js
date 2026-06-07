// OBSCURA eval (SYNCHRONOUS — OBSCURA does not await Promises) — deep extraction
// from a residence's official operator website (rendered DOM).
// Returns JSON: {gallery:[url], offers:[{type,surface,price}], services:[str], description:str}
(() => {
  const out = { gallery: [], offers: [], services: [], description: '' };
  const seen = new Set();
  const bad = /logo|icone?|sprite|favicon|placeholder|pixel|avatar|drapeau|flag|picto|loader|spinner|blank|share|bouton|button|arrow|fleche|\/map|plan-|qrcode|badge|cookie|partenaire|footer|header-|linge|equipe|\bteam\b|reassurance|step-|etape-|service-icon|\/svg/i;

  const add = (u) => {
    if (!u) return;
    u = u.trim();
    if (u.startsWith('//')) u = 'https:' + u;
    u = u.split('?')[0];
    if (!/^https?:\/\//i.test(u)) return;
    if (!/\.(jpe?g|webp|png)$/i.test(u)) return;
    if (bad.test(u)) return;
    if (seen.has(u)) return;
    seen.add(u); out.gallery.push(u);
  };
  const lastSrcset = (ss) => {
    if (!ss) return null;
    const parts = ss.split(',').map(s => s.trim().split(/\s+/)[0]).filter(Boolean);
    return parts[parts.length - 1];
  };

  document.querySelectorAll('img').forEach(i => {
    add(i.getAttribute('data-src')); add(i.getAttribute('data-lazy-src')); add(i.getAttribute('data-original'));
    add(lastSrcset(i.getAttribute('srcset') || i.getAttribute('data-srcset')));
    const w = parseInt(i.getAttribute('width') || '0', 10) || i.naturalWidth || 0;
    const cls = (i.className || '') + ' ' + (i.id || '') + ' ' + ((i.closest('[class]') || {}).className || '');
    if (w >= 300 || /gallery|galerie|slide|carousel|swiper|hero|cover|photo|visuel|banner|mosa/i.test(cls)) {
      add(i.getAttribute('src') || i.currentSrc);
    }
  });
  document.querySelectorAll('picture source').forEach(s => add(lastSrcset(s.getAttribute('srcset') || s.getAttribute('data-srcset'))));
  document.querySelectorAll('[style*="background-image"],[data-bg],[data-background],[data-bg-src]').forEach(el => {
    add(el.getAttribute('data-bg')); add(el.getAttribute('data-background')); add(el.getAttribute('data-bg-src'));
    const m = (el.getAttribute('style') || '').match(/url\((['"]?)([^'")]+)\1\)/);
    if (m) add(m[2]);
  });

  // prefer real photos (jpg/webp) over png (often icons)
  out.gallery.sort((a, b) => (/\.png$/i.test(a) ? 1 : 0) - (/\.png$/i.test(b) ? 1 : 0));
  const og = (document.querySelector('meta[property="og:image"]') || {}).content;
  if (og && /\.(jpe?g|webp|png)$/i.test(og.split('?')[0]) && !bad.test(og)) {
    const o = og.split('?')[0]; out.gallery = [o, ...out.gallery.filter(u => u !== o)];
  }
  out.gallery = out.gallery.slice(0, 12);

  // description: meta or longest paragraph
  const md = (document.querySelector('meta[name="description"]') || {}).content || '';
  const isLegal = (t) => /rcs|immatricul|siren|siret|capital social|mentions? légales|©|cookie|confidentialité|tous droits réservés|all rights/i.test(t);
  let best = '';
  document.querySelectorAll('p, .description, .presentation, [class*="intro"], [class*="presentation"]').forEach(p => {
    const t = (p.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length > 40 && t.length < 1400 && !isLegal(t) && t.length > best.length) best = t;
  });
  out.description = (best.length > md.length + 20 ? best : md);
  if (isLegal(out.description)) out.description = md;
  out.description = out.description.slice(0, 900);

  // services: vocabulary match on body text
  const body = ' ' + (document.body.innerText || '').toLowerCase() + ' ';
  const SERV = {
    'Restaurant': /restaurant|salle à manger|restauration|table d/, 'Piscine': /piscine|bassin/,
    'Salle de sport': /salle de sport|fitness|gym\b|remise en forme|musculation/, 'Conciergerie': /conciergerie|concierge/,
    'Animations': /animation|activités|atelier/, 'Blanchisserie': /blanchisserie|lingerie|linge/,
    'Salon de coiffure': /coiffure|coiffeur/, 'Bibliothèque': /bibliothèque|médiathèque/,
    'Jardin / Parc': /jardin|parc\b|espaces? verts?/, 'Parking': /parking|stationnement|garage/,
    'Sécurité 24h/24': /24h\/24|24h sur 24|\bh24\b|sécurisé|gardien|veille de nuit|téléassistance|téléalarme/,
    'Espace bien-être': /bien-être|spa\b|balnéo|wellness|détente|jacuzzi/, 'Wifi': /wifi|wi-fi/,
    'Bar / Salon': /\bbar\b|salon de (thé|détente|repos)/, 'Soins / beauté': /esthétique|manucure|pédicure|institut de beauté/,
    'Ménage / entretien': /ménage|aide ménagère|entretien du logement/, 'Terrasse / Balcon': /terrasse|balcon|loggia/,
    'Potager': /potager/, 'Cinéma': /cinéma|salle de projection|home cinéma/, 'Demi-pension': /pension|demi-pension/,
    'Cuisine équipée': /kitchenette|cuisine équipée/, 'Accès PMR': /\bpmr\b|accessibilité|fauteuil roulant/,
    'Navette': /navette/, 'Espace boutique': /boutique|épicerie/
  };
  out.services = Object.keys(SERV).filter(k => SERV[k].test(body));

  // offers: apartment type -> surface / price
  const text = (document.body.innerText || '').replace(/ /g, ' ').replace(/\s+/g, ' ');
  const types = ['Studio', 'T1', 'T2', 'T3', 'T4', 'T5', 'F1', 'F2', 'F3', 'F4'];
  const offers = {};
  types.forEach(t => {
    const reSP = new RegExp(t + '\\b[^.€]{0,80}?(\\d{2,3})\\s*m²[^.€]{0,80}?([0-9 .]{3,8})\\s*€', 'i');
    const reS = new RegExp(t + '\\b[^.]{0,60}?(\\d{2,3})\\s*m²', 'i');
    const reP = new RegExp(t + '\\b[^.]{0,60}?([0-9 .]{3,8})\\s*€', 'i');
    const m = text.match(reSP);
    if (m) { offers[t] = { type: t, surface: parseInt(m[1], 10), price: parseInt(m[2].replace(/[^0-9]/g, ''), 10) }; return; }
    const ms = text.match(reS), mp = text.match(reP);
    const o = { type: t };
    if (ms) o.surface = parseInt(ms[1], 10);
    if (mp) { const p = parseInt(mp[1].replace(/[^0-9]/g, ''), 10); if (p >= 400 && p <= 15000) o.price = p; }
    if (o.surface || o.price) offers[t] = o;
  });
  out.offers = Object.values(offers);
  return JSON.stringify(out);
})()
