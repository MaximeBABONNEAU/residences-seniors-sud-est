// OBSCURA eval — extract residence cards from a sanitaire-social list page.
// Returns JSON string {count, cards:[{name, addr, link}]}.
// count = total results in the department (parsed from <title>) for pagination.
(() => {
  const clean = s => (s || '').replace(/\s+/g, ' ').trim();
  const cards = Array.from(document.querySelectorAll('.card.block-shadow')).map(c => {
    const nameEl = c.querySelector('.card-title');
    const addrEl = c.querySelector('.card-text.address');
    const a = c.querySelector("a[href*='/fiche/']");
    return {
      name: clean(nameEl ? nameEl.innerText : ''),
      addr: clean(addrEl ? addrEl.innerText : ''),
      link: a ? a.href : ''
    };
  }).filter(r => r.name);
  let count = cards.length;
  const m = (document.title || '').match(/(\d+)\s*[ée]tablissement/i);
  if (m) count = parseInt(m[1], 10);
  return JSON.stringify({ count, cards });
})()
