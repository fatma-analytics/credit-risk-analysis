"""
analysis.py — Analyse du risque de crédit d'un portefeuille de prêts
--------------------------------------------------------------------
Charge le portefeuille, calcule les indicateurs de risque, construit
des buckets de DTI, une lecture par cohorte (millésime), puis entraîne
un modèle de score de défaut (régression logistique) et l'évalue (AUC).

Données 100% fictives. Usage : python analysis.py
"""
import numpy as np
import pandas as pd

LGD = 0.55  # Loss Given Default (perte en cas de défaut) — hypothèse

# ---------------------------------------------------------------- chargement
df = pd.read_csv("loans.csv")
df["defaut"] = (df["status"] == "Défaut").astype(int)
df["non_performant"] = df["status"].isin(["Défaut", "En retard"]).astype(int)

# ---------------------------------------------------------------- indicateurs clés
encours = df["outstanding"].sum()
taux_defaut = df["defaut"].mean()
npl_ratio = df.loc[df["non_performant"] == 1, "outstanding"].sum() / encours
taux_moyen = np.average(df["interest_rate"], weights=df["amount"])
perte_attendue = (df["pd_model"] * LGD * df["outstanding"]).sum()

print("=" * 56)
print("INDICATEURS CLÉS DU PORTEFEUILLE")
print("=" * 56)
print(f"Nombre de prêts            : {len(df):>12,}")
print(f"Montant octroyé            : {df['amount'].sum():>12,.0f} €")
print(f"Encours (EAD)              : {encours:>12,.0f} €")
print(f"Taux de défaut (en nombre) : {taux_defaut:>11.2%}")
print(f"Ratio NPL (en encours)     : {npl_ratio:>11.2%}")
print(f"Taux moyen pondéré         : {taux_moyen:>11.2f} %")
print(f"Perte attendue (PD·LGD·EAD): {perte_attendue:>12,.0f} €")

# ---------------------------------------------------------------- taux de défaut par grade
print("\nTAUX DE DÉFAUT PAR GRADE")
by_grade = (df.groupby("grade")
              .agg(prets=("loan_id", "count"),
                   taux_defaut=("defaut", "mean"),
                   taux_moyen=("interest_rate", "mean"),
                   encours=("outstanding", "sum"))
              .reset_index())
by_grade["taux_defaut"] = (by_grade["taux_defaut"] * 100).round(1)
by_grade["taux_moyen"] = by_grade["taux_moyen"].round(1)
print(by_grade.to_string(index=False))

# ---------------------------------------------------------------- lecture par cohorte (millésime)
print("\nTAUX DE DÉFAUT PAR MILLÉSIME (cohorte)")
by_year = (df.groupby("issue_year")["defaut"].mean() * 100).round(1)
print(by_year.to_string())

# ---------------------------------------------------------------- buckets de DTI
df["dti_bucket"] = pd.cut(df["dti"], bins=[0, 15, 25, 35, 45, 100],
                          labels=["<15%", "15-25%", "25-35%", "35-45%", ">45%"])
print("\nTAUX DE DÉFAUT PAR TRANCHE DE DTI")
print((df.groupby("dti_bucket", observed=True)["defaut"].mean() * 100).round(1).to_string())

# ---------------------------------------------------------------- modèle de score (PD)
print("\n" + "=" * 56)
print("MODÈLE DE SCORE DE DÉFAUT — régression logistique")
print("=" * 56)

features = ["amount", "interest_rate", "annual_income", "dti", "credit_score", "term_months"]
X = df[features].copy()
y = df["defaut"]

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score, classification_report

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.30,
                                          random_state=7, stratify=y)
    scaler = StandardScaler().fit(Xtr)
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(scaler.transform(Xtr), ytr)
    proba = model.predict_proba(scaler.transform(Xte))[:, 1]
    auc = roc_auc_score(yte, proba)

    print(f"AUC (test) : {auc:.3f}")
    print("\nPoids standardisés (impact sur le risque) :")
    coefs = pd.Series(model.coef_[0], index=features).sort_values(key=abs,
                                                                  ascending=False)
    for name, c in coefs.items():
        arrow = "▲ augmente" if c > 0 else "▼ réduit  "
        print(f"  {name:<15} {c:+.3f}   {arrow} le risque")
except ImportError:
    print("scikit-learn non disponible — installez-le avec : pip install scikit-learn")

print("\nAnalyse terminée.")
