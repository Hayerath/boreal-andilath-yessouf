# L5 · Lignage d'un indicateur : le ratio sinistres / primes (S/P)

Ratio S/P annuel par produit = sinistres payés / primes acquises, sinistres rattachés à l'année de survenance.

```mermaid
flowchart LR
  A1[contrats.csv] --> B1[raw.contrats]
  A2[sinistres.jsonl] --> B2[raw.sinistres]
  A3[reglements_*.csv] --> B3[raw.reglements]
  A4[clients.csv] --> B4[raw.clients]
  B1 --> C1[prep.contrats]
  B2 --> C2[prep.sinistres]
  B3 --> C3[prep.reglements]
  B4 --> C4[prep.clients]
  C1 -->|règles bloquantes| Q[(quarantine.rows)]
  C2 -->|règles bloquantes| Q
  C3 -->|règles bloquantes| Q
  C4 -->|doublons| Q
  C1 --> D1[core.dim_contrat]
  C4 --> D4[core.dim_client]
  D1 --> E1[core.fact_exposition<br/>prime_acquise, année-police]
  C3 --> E3[core.fact_reglement]
  C2 --> E2[core.fact_sinistre<br/>montant_regle]
  E3 --> E2
  E1 --> M[marts.portefeuille_annee_produit<br/>ratio_sinistres_primes]
  E2 --> M
  M --> T[Tableau de bord]
  M --> N[Dossier et note]
```

## Lecture
| Étape | Ce qui se passe | Contrôle |
|---|---|---|
| Sources -> raw | copie fidèle, empreinte du fichier | T19 : journal = contenu du brut |
| raw -> prep | typage, dates normalisées, rang des doublons | |
| prep -> quarantaine / core | règles bloquantes : les lignes invalides sont écartées avec un motif | T11 à T15 : brut = cœur + quarantaine |
| core.fact_exposition | prime acquise = prime annuelle x jours couverts / jours de l'année | T10, T20 |
| core.fact_sinistre | montant payé cumulé par sinistre | T08 : tout règlement a un sinistre |
| core -> mart | on somme les sinistres payés et les primes, puis on divise | M01 à M03 : le mart retombe sur le cœur |
| mart -> tableau de bord | lecture seule, aucun recalcul | mêmes chiffres que le dossier |

## Si un chiffre est contesté
Un chiffre du tableau de bord se retrouve dans le mart, puis dans les faits du cœur, puis dans les lignes du
brut, et les lignes écartées se retrouvent dans la quarantaine avec leur motif : on peut vérifier le total de bout en bout.
