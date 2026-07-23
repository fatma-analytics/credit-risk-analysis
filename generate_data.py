"""
generate_data.py
Génère un portefeuille de prêts synthétique et réaliste pour l'analyse
du risque de crédit. Données 100% fictives — aucune donnée réelle.

Sortie :
  - loans.csv   : le portefeuille (une ligne = un prêt)
  - loans.json  : version compacte pour le dashboard
"""
import numpy as np
import pandas as pd
import json

rng = np.random.default_rng(42)
N = 5000

GRADES   = list("ABCDEFG")
PURPOSES = ["Trésorerie", "Automobile", "Travaux", "Consolidation de dettes",
            "Immobilier", "Études", "Équipement", "Autre"]
REGIONS  = ["Île-de-France", "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine",
            "Occitanie", "Hauts-de-France", "Provence-Alpes-Côte d'Azur",
            "Grand Est", "Bretagne", "Normandie", "Pays de la Loire"]

# probabilité de défaut de base par grade (sur la durée de vie du prêt)
PD_BASE = {"A": .020, "B": .042, "C": .073, "D": .118, "E": .175, "F": .255, "G": .340}
# taux d'intérêt moyen par grade
RATE_BASE = {"A": 3.2, "B": 4.6, "C": 6.1, "D": 8.0, "E": 10.4, "F": 13.1, "G": 16.2}

# tirage des grades (portefeuille concentré sur B-D)
grade_p = np.array([.14, .22, .24, .18, .12, .07, .03])
grades  = rng.choice(GRADES, size=N, p=grade_p)

issue_year = rng.choice([2019, 2020, 2021, 2022, 2023, 2024],
                        size=N, p=[.10, .13, .17, .20, .22, .18])
term = rng.choice([36, 60], size=N, p=[.62, .38])

# revenu annuel (lognormal), montant du prêt corrélé au revenu
income = np.round(rng.lognormal(mean=10.55, sigma=0.42, size=N)).astype(int)
income = np.clip(income, 14000, 240000)
amount = np.round(income * rng.uniform(0.15, 0.75, N) / 100) * 100
amount = np.clip(amount, 1000, 75000).astype(int)

# DTI (debt-to-income) : plus élevé pour les mauvais grades
grade_idx = np.array([GRADES.index(g) for g in grades])
dti = np.clip(rng.normal(22 + grade_idx * 3.2, 7, N), 3, 55).round(1)

# score de crédit (type FICO 300-850), anti-corrélé au grade et au DTI
score = np.clip(rng.normal(760 - grade_idx * 42 - (dti - 22) * 2.2, 32, N),
                300, 850).astype(int)

rate = np.array([RATE_BASE[g] for g in grades]) + rng.normal(0, 0.6, N)
rate = np.clip(rate, 2.0, 22.0).round(2)

purpose = rng.choice(PURPOSES, size=N,
                     p=[.20, .17, .14, .18, .09, .06, .10, .06])
region  = rng.choice(REGIONS, size=N,
                     p=[.20, .13, .09, .10, .10, .09, .08, .07, .07, .07])

# --- probabilité de défaut individuelle (modèle "vérité terrain") ---
pd_ind = np.array([PD_BASE[g] for g in grades])
pd_ind *= (1 + (dti - 22) / 55)                 # DTI élevé -> risque
pd_ind *= (1 + (700 - score) / 900)             # score faible -> risque
pd_ind *= (1 + (2024 - issue_year) * 0.015)     # millésimes anciens ont vécu +longtemps
pd_ind = np.clip(pd_ind, 0.005, 0.85)

# --- attribution du statut ---
age = (2024 - issue_year)
u = rng.uniform(0, 1, N)
defaulted = u < pd_ind

status = np.empty(N, dtype=object)
frac_paid = np.clip((age * 12) / term, 0, 1)     # part du prêt remboursée
for i in range(N):
    if defaulted[i]:
        status[i] = "Défaut"
    else:
        # anciens prêts largement remboursés -> soldés ; sinon en cours, un peu de retard
        r = rng.uniform(0, 1)
        if frac_paid[i] >= 0.98:
            status[i] = "Soldé"
        elif r < 0.05:
            status[i] = "En retard"
        else:
            status[i] = "En cours"

# encours restant (EAD) : 0 si soldé, sinon principal non amorti
remaining = np.where(status == "Soldé", 0.0,
                     amount * np.clip(1 - frac_paid * rng.uniform(0.7, 1.0, N), 0.05, 1.0))
remaining = np.round(remaining).astype(int)

df = pd.DataFrame({
    "loan_id": [f"L{100000+i}" for i in range(N)],
    "issue_year": issue_year,
    "grade": grades,
    "amount": amount,
    "interest_rate": rate,
    "term_months": term,
    "purpose": purpose,
    "region": region,
    "annual_income": income,
    "dti": dti,
    "credit_score": score,
    "pd_model": pd_ind.round(4),
    "status": status,
    "outstanding": remaining,
})

df.to_csv("loans.csv", index=False)

# version compacte pour le dashboard (array-of-arrays)
schema = ["issue_year", "grade", "amount", "interest_rate", "term_months",
          "purpose", "region", "annual_income", "dti", "credit_score",
          "pd_model", "status", "outstanding"]
rows = df[schema].values.tolist()
with open("loans.json", "w", encoding="utf-8") as f:
    json.dump({"schema": schema,
               "purposes": PURPOSES, "regions": REGIONS, "grades": GRADES,
               "rows": rows}, f, ensure_ascii=False, separators=(",", ":"))

print(f"{N} prêts générés -> loans.csv, loans.json")
print("Répartition des statuts :")
print(df["status"].value_counts())
print(f"\nTaux de défaut global : {(df['status']=='Défaut').mean()*100:.2f}%")
print(f"Encours total : {df['outstanding'].sum():,.0f} €")
