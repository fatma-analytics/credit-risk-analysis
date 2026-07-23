-- =============================================================================
--  ANALYSE DU RISQUE DE CRÉDIT — portefeuille de prêts
--  Requêtes analytiques (SQL ANSI / compatible Snowflake, PostgreSQL)
--  Données 100% fictives.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Schéma de la table source
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prets (
    loan_id        VARCHAR   PRIMARY KEY,
    issue_year     INTEGER,
    grade          CHAR(1),                 -- A (meilleur) .. G (plus risqué)
    amount         NUMERIC,                 -- montant octroyé
    interest_rate  NUMERIC,                 -- taux d'intérêt (%)
    term_months    INTEGER,                 -- durée (36 ou 60)
    purpose        VARCHAR,
    region         VARCHAR,
    annual_income  NUMERIC,
    dti            NUMERIC,                 -- debt-to-income (%)
    credit_score   INTEGER,                 -- score type FICO (300-850)
    pd_model       NUMERIC,                 -- probabilité de défaut estimée
    status         VARCHAR,                 -- En cours / Soldé / En retard / Défaut
    outstanding    NUMERIC                  -- encours restant (EAD)
);

-- Vue de travail : drapeaux de risque réutilisés partout.
CREATE OR REPLACE VIEW v_prets AS
SELECT
    p.*,
    CASE WHEN status = 'Défaut'                        THEN 1 ELSE 0 END AS is_defaut,
    CASE WHEN status IN ('Défaut', 'En retard')        THEN 1 ELSE 0 END AS is_npl,
    CASE
        WHEN dti < 15 THEN '<15%'
        WHEN dti < 25 THEN '15-25%'
        WHEN dti < 35 THEN '25-35%'
        WHEN dti < 45 THEN '35-45%'
        ELSE '>45%'
    END AS dti_bucket
FROM prets p;


-- -----------------------------------------------------------------------------
-- 1. Indicateurs clés du portefeuille (carte de KPIs du dashboard)
--    LGD (Loss Given Default) fixé à 0,55 par hypothèse.
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*)                                                   AS nb_prets,
    SUM(amount)                                                AS montant_octroye,
    SUM(outstanding)                                           AS encours_ead,
    ROUND(AVG(is_defaut) * 100, 2)                             AS taux_defaut_pct,
    ROUND(SUM(outstanding * is_npl) / SUM(outstanding) * 100, 2) AS npl_ratio_pct,
    ROUND(SUM(interest_rate * amount) / SUM(amount), 2)        AS taux_moyen_pondere,
    ROUND(SUM(pd_model * 0.55 * outstanding), 0)               AS perte_attendue
FROM v_prets;


-- -----------------------------------------------------------------------------
-- 2. Taux de défaut et rendement par grade de risque
--    (le graphique central : le risque doit croître de A vers G)
-- -----------------------------------------------------------------------------
SELECT
    grade,
    COUNT(*)                                   AS nb_prets,
    ROUND(AVG(is_defaut) * 100, 1)             AS taux_defaut_pct,
    ROUND(AVG(interest_rate), 1)               AS taux_moyen_pct,
    SUM(outstanding)                           AS encours,
    ROUND(100.0 * SUM(outstanding)
          / SUM(SUM(outstanding)) OVER (), 1)  AS part_encours_pct
FROM v_prets
GROUP BY grade
ORDER BY grade;


-- -----------------------------------------------------------------------------
-- 3. Analyse par cohorte (millésime d'octroi)
--    Suivi du taux de défaut selon l'année de mise en place.
-- -----------------------------------------------------------------------------
SELECT
    issue_year,
    COUNT(*)                        AS nb_prets,
    ROUND(AVG(is_defaut) * 100, 1)  AS taux_defaut_pct,
    SUM(outstanding)                AS encours
FROM v_prets
GROUP BY issue_year
ORDER BY issue_year;


-- -----------------------------------------------------------------------------
-- 4. Sensibilité du risque au taux d'endettement (DTI)
-- -----------------------------------------------------------------------------
SELECT
    dti_bucket,
    COUNT(*)                        AS nb_prets,
    ROUND(AVG(is_defaut) * 100, 1)  AS taux_defaut_pct,
    ROUND(AVG(credit_score), 0)     AS score_moyen
FROM v_prets
GROUP BY dti_bucket
ORDER BY MIN(dti);


-- -----------------------------------------------------------------------------
-- 5. Concentration du risque : encours et pertes par région et par motif
-- -----------------------------------------------------------------------------
SELECT
    region,
    SUM(outstanding)                              AS encours,
    ROUND(AVG(is_defaut) * 100, 1)                AS taux_defaut_pct,
    ROUND(SUM(pd_model * 0.55 * outstanding), 0)  AS perte_attendue
FROM v_prets
GROUP BY region
ORDER BY encours DESC;

SELECT
    purpose,
    COUNT(*)                        AS nb_prets,
    SUM(outstanding)                AS encours,
    ROUND(AVG(is_defaut) * 100, 1)  AS taux_defaut_pct
FROM v_prets
GROUP BY purpose
ORDER BY encours DESC;


-- -----------------------------------------------------------------------------
-- 6. Répartition par statut (santé du portefeuille)
-- -----------------------------------------------------------------------------
SELECT
    status,
    COUNT(*)                                          AS nb_prets,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_pct,
    SUM(outstanding)                                  AS encours
FROM v_prets
GROUP BY status
ORDER BY nb_prets DESC;


-- -----------------------------------------------------------------------------
-- 7. Top 10 des expositions les plus risquées (montant × probabilité de défaut)
--    Utile pour la surveillance rapprochée ("watch list").
-- -----------------------------------------------------------------------------
SELECT
    loan_id, grade, region, purpose,
    outstanding,
    ROUND(pd_model, 3)                         AS pd_estimee,
    ROUND(pd_model * 0.55 * outstanding, 0)    AS perte_attendue
FROM v_prets
WHERE status IN ('En cours', 'En retard')
ORDER BY pd_model * outstanding DESC
LIMIT 10;
