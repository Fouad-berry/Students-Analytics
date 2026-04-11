# 🎓 Student Exam Performance Analytics

> Pipeline ELT complet sur un dataset **10 000 profils d'étudiants**.  
> Analyse des facteurs de réussite académique · Dashboard Power BI 5 pages.

---

## 📋 Table des matières

- [Aperçu](#aperçu)
- [Dataset](#dataset)
- [Architecture ELT](#architecture-elt)
- [Structure du projet](#structure-du-projet)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Feature Engineering](#feature-engineering)
- [Data Marts](#data-marts)
- [Dashboard Power BI](#dashboard-power-bi)
- [Tests](#tests)
- [Insights clés](#insights-clés)

---

## Aperçu

Ce projet analyse les **facteurs qui influencent la réussite académique** sur 10 000 étudiants :
heures d'étude, assiduité, sommeil, réseaux sociaux, environnement de travail, contexte familial, etc.

Le pipeline ELT produit un **score de risque** par étudiant, des métriques d'engagement et des données agrégées prêtes pour Power BI.

**Stack :**
```
Python · Pandas · SQLite · Power BI · pytest
```

---

## Dataset

**Fichier :** `data/raw/student_exam_performance.csv` — 10 000 étudiants · 23 colonnes

| Colonne | Type | Description |
|---|---|---|
| `student_id` | str | Identifiant unique |
| `gender` | str | Male / Female |
| `age` | int | 15 à 18 ans |
| `parental_education` | str | High School / Bachelor / Master / PhD |
| `family_income` | str | Low / Medium / High |
| `internet_access` | str | Yes / No |
| `study_environment` | str | Quiet / Moderate / Noisy |
| `study_hours_per_day` | float | Heures d'étude quotidiennes |
| `attendance_rate` | float | % de présence en cours |
| `sleep_hours` | float | Heures de sommeil |
| `social_media_hours` | float | Heures sur réseaux sociaux |
| `assignment_completion_rate` | float | % de devoirs rendus |
| `participation_score` | float | Score de participation (0-100) |
| `online_courses_completed` | int | Nombre de cours en ligne |
| `tutoring` | str | Yes / No |
| `math_score` | float | Score en math (0-100) |
| `reading_score` | float | Score en lecture (0-100) |
| `writing_score` | float | Score en écriture (0-100) |
| `science_score` | float | Score en sciences (0-100) |
| `final_exam_score` | float | Score examen final (0-100) |
| `previous_gpa` | float | GPA précédent (0-4) |
| `pass_fail` | str | Pass / Fail |
| `grade_category` | str | A / B / C / D / F |

---

## Architecture ELT

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            PIPELINE ELT                                  │
│                                                                          │
│  ┌───────────────┐   ┌─────────────────┐   ┌────────────────────────┐  │
│  │   EXTRACT     │──▶│   LOAD (raw)    │──▶│      TRANSFORM         │  │
│  │               │   │                 │   │                        │  │
│  │  CSV → pandas │   │  raw_students   │   │  Nettoyage             │  │
│  │  10 000 lignes│   │  (SQLite)       │   │  Validation des scores │  │
│  └───────────────┘   └─────────────────┘   │  Feature Engineering   │  │
│                                             │  Score de risque       │  │
│                                             │  Segmentations         │  │
│                                             └────────────┬───────────┘  │
│                                                          │              │
│                     ┌────────────────────────────────────┘              │
│                     ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  LOAD — 3 COUCHES                               │    │
│  │                                                                 │    │
│  │  STAGING           INTERMEDIATE          MARTS                  │    │
│  │  ────────          ─────────────         ──────                 │    │
│  │  stg_students ──► int_subject_stats ──► mart_kpis              │    │
│  │               ──► int_pass_by_group ──► mart_grade_distribution │    │
│  │                                     ──► mart_gender             │    │
│  │                                     ──► mart_parental_education │    │
│  │                                     ──► mart_family_income      │    │
│  │                                     ──► mart_study_behavior     │    │
│  │                                     ──► mart_environment        │    │
│  │                                     ──► mart_attendance_impact  │    │
│  │                                     ──► mart_subject_by_grade   │    │
│  │                                     ──► mart_risk_profile       │    │
│  │                                     ──► mart_tutoring_impact    │    │
│  │                                     ──► mart_social_media_impact│    │
│  │                                     ──► mart_top_students       │    │
│  │                                     ──► mart_correlation_matrix │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
               ┌─────────────────────────────────────────┐
               │          POWER BI DASHBOARD             │
               │                                         │
               │  Page 1 : Overview                      │
               │  Page 2 : Facteurs de performance       │
               │  Page 3 : Profils & Démographie         │
               │  Page 4 : Scores par matière            │
               │  Page 5 : Risque & Top étudiants        │
               └─────────────────────────────────────────┘
```

---

## Structure du projet

```
student_analytics/
│
├── data/
│   ├── raw/
│   │   └── student_exam_performance.csv      ← source (10 000 étudiants)
│   ├── processed/
│   │   └── student_exam_processed.csv        ← données enrichies (généré)
│   ├── mart/
│   │   ├── mart_kpis.csv
│   │   ├── mart_grade_distribution.csv
│   │   ├── mart_gender.csv
│   │   ├── mart_parental_education.csv
│   │   ├── mart_family_income.csv
│   │   ├── mart_study_behavior.csv
│   │   ├── mart_environment.csv
│   │   ├── mart_attendance_impact.csv
│   │   ├── mart_subject_by_grade.csv
│   │   ├── mart_risk_profile.csv
│   │   ├── mart_tutoring_impact.csv
│   │   ├── mart_social_media_impact.csv
│   │   ├── mart_top_students.csv
│   │   ├── mart_correlation_matrix.csv
│   │   ├── stg_students.csv
│   │   ├── int_subject_stats.csv
│   │   └── int_pass_by_group.csv
│   └── student_analytics.db                 ← SQLite (généré)
│
├── elt/
│   ├── extract/
│   │   └── extract.py                       ← CSV → raw_students
│   ├── transform/
│   │   └── transform.py                     ← nettoyage + feature engineering
│   └── load/
│       └── load.py                          ← staging + intermediate + marts
│
├── analysis/
│   ├── eda.py                               ← 9 graphiques EDA
│   └── figures/                             ← PNG générés
│
├── powerbi/
│   └── POWERBI_GUIDE.md                     ← guide DAX + 5 pages dashboard
│
├── tests/
│   └── test_pipeline.py                     ← 13 tests pytest
│
├── docs/
├── logs/
├── pipeline.py                              ← orchestrateur ELT
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Installation

```bash
git clone https://github.com/ton-username/student-analytics.git
cd student-analytics

python -m venv venv
source venv/bin/activate       # Mac/Linux
# venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

---

## Utilisation

```bash
# Pipeline ELT complet
python pipeline.py

# Étapes séparées
python elt/extract/extract.py
python elt/transform/transform.py
python elt/load/load.py

# Analyse exploratoire (9 graphiques)
python analysis/eda.py
```

---

## Feature Engineering

| Feature | Calcul | Description |
|---|---|---|
| `avg_subject_score` | Moyenne des 4 matières | Score moyen académique |
| `best_subject` | idxmax des 4 scores | Matière où l'étudiant est le meilleur |
| `worst_subject` | idxmin des 4 scores | Matière la plus faible |
| `score_range` | max - min des 4 scores | Homogénéité académique |
| `gpa_as_score` | previous_gpa / 4 × 100 | GPA converti en score /100 |
| `score_improvement` | final_score - gpa_as_score | Progression vs historique |
| `is_improving` | score_improvement > 0 | Flag amélioration |
| `risk_score` | 40% étude + 40% assiduité + 20% social | Score de risque 0-100 |
| `is_at_risk` | risk_score ≥ 50 | Flag étudiant à risque |
| `study_segment` | 5 tranches d'heures d'étude | Segmentation comportementale |
| `score_segment` | 5 tranches de score final | Segmentation de performance |
| `attendance_segment` | 5 tranches d'assiduité | Segmentation assiduité |

---

## Data Marts

| Mart | Description | Lignes |
|---|---|---|
| `mart_kpis` | 14 KPIs globaux | 1 |
| `mart_grade_distribution` | Stats par grade A→F | 5 |
| `mart_gender` | Comparaison Male vs Female | 2 |
| `mart_parental_education` | Impact éducation parentale | 4 |
| `mart_family_income` | Impact revenu familial | 3 |
| `mart_study_behavior` | Segments heures d'étude | 5 |
| `mart_environment` | Impact environnement | 3 |
| `mart_attendance_impact` | Impact assiduité | 5 |
| `mart_subject_by_grade` | Scores matières par grade | 5 |
| `mart_risk_profile` | À risque vs non à risque | 2 |
| `mart_tutoring_impact` | Soutien scolaire × revenu | 6 |
| `mart_social_media_impact` | Impact réseaux sociaux | 5 |
| `mart_top_students` | Top 100 meilleurs étudiants | 100 |
| `mart_correlation_matrix` | Corrélations entre variables | 8 |

---

## Dashboard Power BI

Voir [`powerbi/POWERBI_GUIDE.md`](powerbi/POWERBI_GUIDE.md) pour :
- Import des données step-by-step
- 20 mesures DAX complètes
- Architecture des 5 pages
- Slicers recommandés

---

## Tests

```bash
pytest tests/ -v
```

13 tests couvrent : doublons, scores hors limites, valeurs manquantes,
best/worst subject, risk_score, segments, GPA, flags.

---

## Insights clés

- **Taux de réussite global : ~48.6%** — presque 1 étudiant sur 2 échoue
- **Corrélation la plus forte** : assiduité → score final
- **Réseaux sociaux > 4h** : taux de réussite chute significativement
- **Environnement Quiet** : meilleur score moyen des 3 environnements
- **Soutien scolaire** : + de points en moyenne pour les étudiants encadrés
- **Éducation parentale PhD** : pas forcément le meilleur prédicteur de réussite

---

## Roadmap

- [ ] Modèle ML de prédiction Pass/Fail (scikit-learn)
- [ ] Dashboard Streamlit public
- [ ] Orchestration Airflow
- [ ] Tests Great Expectations

---

Réalisé par Fouad MOUTAIROU | Data & IA engineer

Mon Portfolio : https://portfolio-fouad.netlify.app

*10 000 étudiants · 23 variables · Score 4.4 → 97.8/100*