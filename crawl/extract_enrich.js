// OBSCURA eval — enrich from a residence's official operator website (rendered DOM).
// Best-effort: real og:image photo + "à partir de X €/mois" price + surfaces.
// Returns JSON string: {photo, price, monthly, surface_min, surface_max}
(() => {
  const out = { photo: '', price: null, monthly: false, surface_min: null, surface_max: null };

  // --- real photo: og:image / twitter:image only if it looks like a content photo ---
  let img = (document.querySelector('meta[property="og:image"]') || {}).content
         || (document.querySelector('meta[name="twitter:image"]') || {}).content || '';
  if (img && /\.(jpg|jpeg|webp|png)/i.test(img)
        && !/logo|sprite|favicon|default-|placeholder|share|og-default/i.test(img)) {
    out.photo = img;
  }

  // --- price: "à partir de 1 155 €/mois" ---
  const body = (document.body && document.body.innerText) || '';
  const pm = body.match(/à\s*partir\s*de\s*([0-9  . ]{3,9})\s*€\s*\/?\s*(mois|par\s*mois)?/i);
  if (pm) {
    const v = parseInt(pm[1].replace(/[^0-9]/g, ''), 10);
    if (v >= 400 && v <= 15000) {
      out.price = v;
      out.monthly = /mois/i.test(pm[0]) || /mensuel|\/\s*mois|par mois/i.test(body);
    }
  }

  // --- surfaces: "35 à 85 m²" / "du T1 au T3 de 30 à 70 m²" ---
  const sm = body.match(/(\d{2})\s*(?:à|a|-|au)\s*(\d{2,3})\s*m²/i);
  if (sm) { out.surface_min = parseInt(sm[1], 10); out.surface_max = parseInt(sm[2], 10); }

  return JSON.stringify(out);
})()
