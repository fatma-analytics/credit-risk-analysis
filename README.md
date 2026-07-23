# credit-risk-analysis
# Analyse du risque de crédit — portefeuille de prêts

Projet **data analyste** de bout en bout : de l'extraction **SQL** à l'analyse
**Python** (avec un modèle de scoring) jusqu'à un **dashboard interactif**.
Il mesure et visualise le risque de défaut d'un portefeuille de prêts.

> ⚠️ **Données 100 % fictives**, générées pour la démonstration. Aucune donnée réelle.

## En bref

À partir d'un portefeuille de 5 000 prêts, le projet calcule les indicateurs
de risque (taux de défaut, encours / EAD, ratio NPL, perte attendue) et
décompose le risque par grade, millésime, tranche d'endettement (DTI),
région et motif.

**Ce que disent les données :**
- le taux de défaut monte de **1,6 % (grade A)** à **65,4 % (grade G)** ;
- il passe de **2,7 %** (endettement < 15 %) à **44 %** (endettement > 45 %) ;
- un modèle de scoring (régression logistique) atteint un **AUC de 0,78**.

## Fichiers du dépôt

| Fichier                     | Rôle |
|-----------------------------|------|
| `dashboard.html`            | Dashboard interactif (filtres, KPIs, graphiques) — s'ouvre dans un navigateur |
| `credit_risk_analysis.sql`  | Requêtes analytiques (KPIs, défaut par grade, cohortes, DTI, concentration) |
| `analysis.py`               | Analyse pandas + modèle de scoring (régression logistique, AUC) |
| `generate_data.py`          | Génère le portefeuille synthétique (`loans.csv`) |
| `loans.csv`                 | Le portefeuille (une ligne = un prêt) |
| `README.md`                 | Ce fichier |

## Utilisation

```bash
pip install numpy pandas scikit-learn
python generate_data.py     # crée loans.csv
python analysis.py          # indicateurs + modèle de scoring
```




<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/47448825-138a-4a00-9116-92a78ea30b6a" />

## Méthode

1. **SQL** — agrégations sur la table `prets` : indicateurs de portefeuille,
   taux de défaut par grade, lecture par cohorte (millésime), sensibilité au
   DTI, concentration par région / motif, watch list des expositions les plus
   risquées (`PD × encours`).
2. **Python** — nettoyage, feature engineering (buckets DTI, millésimes),
   calcul de la perte attendue, et un modèle de score de défaut
   (régression logistique standardisée, évaluée à l'AUC).
3. **Dashboard** — restitution interactive : les filtres (année, grade,
   région, motif) recalculent tous les indicateurs en direct.

## Compétences illustrées

SQL analytique · pandas · scikit-learn · scoring de risque ·
indicateurs de crédit (PD / LGD / EAD, NPL) · data-visualisation.

---

**Auteur** — [FATMA HAMMAMI]
