# 🏡 Résidences Seniors · Sud-Est de la France

Carte interactive + annuaire des **résidences services seniors** en
**Provence-Alpes-Côte d'Azur** et **Auvergne-Rhône-Alpes** (18 départements).

👉 **Site en ligne : https://merlingame-netizen.github.io/residences-seniors-sud-est/**

## Fonctionnalités

- 🗺️ **Carte interactive** (Leaflet) avec regroupement par clusters et marqueurs colorés par opérateur
- 📋 **Liste filtrable** synchronisée avec la carte (clic fiche ↔ marqueur)
- 🔎 **Filtres** : recherche, région, département, opérateur, fourchette de prix, type de logement (T1/T2/T3)
- 💶 **Prix** « à partir de … €/mois », **surfaces**, **photo** quand disponibles
- ☎️ **Contact** direct : téléphone (`tel:`), site officiel, e-mail, fiche détaillée
- 📱 **Responsive** (bascule carte / liste sur mobile), accessible (contrastes, focus clavier, `prefers-reduced-motion`)

## Données

| Indicateur | Valeur |
|---|---|
| Résidences | **195** |
| Couverture | 18 départements (PACA + Auvergne-Rhône-Alpes) |
| Téléphone | ~100 % |
| Site officiel | ~87 % |
| Géolocalisation | 100 % |

**Méthodologie** *(100 % données publiques)* :

1. **Crawling** via [OBSCURA](https://github.com/h4ckf0r0day/obscura) (navigateur headless) de l'annuaire
   public [sanitaire-social.com](https://www.sanitaire-social.com) → nom, adresse, téléphone, e-mail, site officiel, prix.
2. **Géocodage** des adresses via la [Base Adresse Nationale](https://adresse.data.gouv.fr) (BAN).
3. **Enrichissement** (photo / prix) depuis les sites officiels des opérateurs.

> ⚠️ Les prix sont **indicatifs** et peuvent évoluer — confirmez toujours auprès de la résidence.
> Ce projet est un agrégateur informatif indépendant, sans lien avec les exploitants.

## Lancer en local

```bash
python -m http.server 8100   # puis ouvrir http://localhost:8100
```

## Régénérer les données

```bash
python crawl/crawl.py list      # annuaire -> data/raw/master_list.json
python crawl/crawl.py geocode   # + lat/lng (BAN)
python crawl/crawl.py detail    # fiches -> data/residences.json
python crawl/crawl.py enrich    # sites officiels -> photos/prix
```

## Structure

```
index.html            # application (carte + liste, vanilla JS + Leaflet)
data/residences.json  # jeu de données final (195 résidences)
crawl/                # pipeline OBSCURA (extract_*.js + crawl.py)
.github/workflows/    # déploiement GitHub Pages
```

## Stack

Leaflet · Leaflet.markercluster · CARTO basemaps · OpenStreetMap · Google Fonts (Fraunces + Inter) · vanilla JS (zéro build).

---
*Données agrégées le 2026-06-07. Sources publiques. Usage informatif.*
