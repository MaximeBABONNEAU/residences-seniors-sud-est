// OBSCURA eval — extract contact/price/photo from a sanitaire-social /fiche/ page.
// Returns JSON string: {phone,email,website,photo,desc,prices{T1,T2,T3},surface_min,surface_max,monthly}
(() => {
  const out = { phone: '', email: '', website: '', photo: '', desc: '',
                prices: {}, surface_min: null, surface_max: null, monthly: false };

  // --- JSON-LD Organization: phone / email / official website / address ---
  document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
    try {
      const j = JSON.parse(s.textContent);
      const arr = Array.isArray(j) ? j : [j];
      arr.forEach(o => {
        if (o && o['@type'] === 'Organization') {
          if (o.telephone) out.phone = String(o.telephone).replace(/[^0-9+]/g, '');
          if (o.email) out.email = String(o.email).trim();
          if (o.url && !/sanitaire-social/i.test(o.url)) out.website = o.url;
        }
      });
    } catch (e) {}
  });

  // --- photo (og:image) + description (meta) ---
  const og = document.querySelector('meta[property="og:image"]');
  if (og && og.content) out.photo = og.content;
  const md = document.querySelector('meta[name="description"]');
  if (md && md.content) out.desc = md.content.trim();

  // --- prices: "Prix F1 ou T1 (mensuel) :1149,00€" ---
  const body = (document.body && document.body.innerText) || '';
  if (/mensuel/i.test(body)) out.monthly = true;
  const re = /Prix[^:T]*T(\d)[^:]*:\s*([0-9  .]+)(?:,\d{2})?\s*€/gi;
  let m;
  while ((m = re.exec(body))) {
    const t = 'T' + m[1];
    const val = parseInt(m[2].replace(/[^0-9]/g, ''), 10);
    if (val && val > 100) out.prices[t] = val;
  }
  // --- surfaces: "du T1 au T3 de 35 à 85 m²" or "30 m²" ---
  const sm = body.match(/de\s*(\d{2})\s*[àa]\s*(\d{2,3})\s*m²/i);
  if (sm) { out.surface_min = parseInt(sm[1], 10); out.surface_max = parseInt(sm[2], 10); }

  return JSON.stringify(out);
})()
