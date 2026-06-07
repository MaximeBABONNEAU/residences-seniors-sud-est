# Task Plan — Carte Résidences Seniors Sud-Est

**Objectif** : Site HTML (GitHub Pages) avec carte interactive + liste filtrable des
résidences services seniors en **PACA + Auvergne-Rhône-Alpes**. Données crawlées via
**OBSCURA** : nom, opérateur, adresse, prix « à partir de », surfaces (T1/T2/T3), photo, contact.

**Zone (18 départements)**
- PACA : 04, 05, 06, 13, 83, 84
- Auvergne-Rhône-Alpes : 01, 03, 07, 15, 26, 38, 42, 43, 63, 69, 73, 74

**Stack** : OBSCURA (crawl) → residences.json → Leaflet + MarkerCluster + vanilla JS → GitHub Pages.
**Repo cible** : nouveau dépôt public `merlingame-netizen/residences-seniors-sud-est`.

## Phases
- [x] P0. Install OBSCURA (h4ckf0r0day/obscura v0.1.7, binaire Windows) — OK
- [x] P0. frontend-design skill (direction UI : light, warm, Fraunces+Inter)
- [ ] P1. Crawl opérateurs → liste résidences (URLs détail) filtrées zone
- [ ] P2. Crawl fiches détail → nom/adresse/prix/surface/photo/contact/site
- [ ] P3. Géocodage (api-adresse.data.gouv.fr) → lat/lng + dept
- [ ] P4. Normalisation → data/residences.json (dédup)
- [ ] P5. Build index.html (carte + liste + filtres, responsive)
- [ ] P6. Vérif locale (preview, console, responsive)
- [ ] P7. Deploy GitHub repo + Pages

## Opérateurs cibles (RSS)
Domitys, Les Senioriales, Ovelia, Cogedim Club, Les Jardins d'Arcadie, Villavie,
Heurus, Nohée, Happy Senior, Steva, Les Girandières, Espace & Vie.

## Notes data
- Prix/surfaces souvent « sur devis » → champs optionnels, badge « sur devis » si absent.
- Photo : og:image ou 1ère image résidence.
- Contact : tel: + lien site officiel résidence.
- Schéma residences.json : voir gate facts (id, name, operator, address, postal_code, city,
  dept, lat, lng, price_from_eur, surfaces{T1,T2,T3}, photo_url, phone, website, source_url, crawl_date).
