# 📊 Guide Power BI — Student Exam Performance Dashboard

## 1. Import des données

### Fichiers CSV à importer depuis `data/mart/`

| Fichier | Table Power BI |
|---|---|
| `mart_kpis.csv` | KPIs |
| `mart_grade_distribution.csv` | GradeDistribution |
| `mart_gender.csv` | Gender |
| `mart_parental_education.csv` | ParentalEducation |
| `mart_family_income.csv` | FamilyIncome |
| `mart_study_behavior.csv` | StudyBehavior |
| `mart_environment.csv` | Environment |
| `mart_attendance_impact.csv` | AttendanceImpact |
| `mart_subject_by_grade.csv` | SubjectByGrade |
| `mart_risk_profile.csv` | RiskProfile |
| `mart_tutoring_impact.csv` | TutoringImpact |
| `mart_social_media_impact.csv` | SocialMediaImpact |
| `mart_top_students.csv` | TopStudents |
| `mart_correlation_matrix.csv` | CorrelationMatrix |
| `stg_students.csv` | AllStudents |

---

## 2. Mesures DAX essentielles

```dax
// ── KPIs globaux ──────────────────────────────────────────

Total Students =
    COUNTROWS(AllStudents)

Pass Rate % =
    DIVIDE(
        CALCULATE(COUNTROWS(AllStudents), AllStudents[pass_fail] = "Pass"),
        COUNTROWS(AllStudents)
    ) * 100

Fail Rate % =
    100 - [Pass Rate %]

Avg Final Score =
    AVERAGE(AllStudents[final_exam_score])

Avg Study Hours =
    AVERAGE(AllStudents[study_hours_per_day])

Avg Attendance =
    AVERAGE(AllStudents[attendance_rate])

Avg Sleep Hours =
    AVERAGE(AllStudents[sleep_hours])

Avg Social Media =
    AVERAGE(AllStudents[social_media_hours])

// ── Scores par matière ────────────────────────────────────

Avg Math Score =
    AVERAGE(AllStudents[math_score])

Avg Reading Score =
    AVERAGE(AllStudents[reading_score])

Avg Writing Score =
    AVERAGE(AllStudents[writing_score])

Avg Science Score =
    AVERAGE(AllStudents[science_score])

Best Subject =
    VAR m = [Avg Math Score]
    VAR r = [Avg Reading Score]
    VAR w = [Avg Writing Score]
    VAR s = [Avg Science Score]
    VAR best = MAX(MAX(m,r), MAX(w,s))
    RETURN
        SWITCH(
            TRUE(),
            best = m, "Math",
            best = r, "Reading",
            best = w, "Writing",
            "Science"
        )

// ── Risque & alertes ──────────────────────────────────────

At Risk Students =
    CALCULATE(COUNTROWS(AllStudents), AllStudents[is_at_risk] = TRUE())

At Risk % =
    DIVIDE([At Risk Students], [Total Students]) * 100

High Attendance % =
    DIVIDE(
        CALCULATE(COUNTROWS(AllStudents), AllStudents[is_high_attendance] = TRUE()),
        COUNTROWS(AllStudents)
    ) * 100

// ── Comparaisons ──────────────────────────────────────────

Score vs Previous GPA =
    [Avg Final Score] - AVERAGE(AllStudents[gpa_as_score])

Tutoring Uplift =
VAR with_tut = CALCULATE(AVERAGE(AllStudents[final_exam_score]), AllStudents[has_tutoring] = TRUE())
VAR without  = CALCULATE(AVERAGE(AllStudents[final_exam_score]), AllStudents[has_tutoring] = FALSE())
RETURN with_tut - without

// ── Ranking dynamique ─────────────────────────────────────

Grade Rank =
    RANKX(
        ALL(GradeDistribution[grade_category]),
        GradeDistribution[avg_score],
        ,
        DESC,
        DENSE
    )
```

---

## 3. Architecture du Dashboard — 5 pages

### Page 1 — Vue d'ensemble (Overview)
```
┌────────────┬────────────┬────────────┬────────────┬────────────┐
│ Total      │ Taux       │ Score      │ Heures     │ % à        │
│ Étudiants  │ Réussite   │ Moyen      │ Étude moy. │ risque     │
│ 10 000     │ XX%        │ XX/100     │ Xh         │ XX%        │
└────────────┴────────────┴────────────┴────────────┴────────────┘
┌──────────────────────────┬──────────────────────────────────────┐
│ Donut : Répartition      │ Bar : Score moyen par grade          │
│ Pass/Fail                │ A → B → C → D → F                   │
│ (KPIs)                   │ (GradeDistribution)                  │
└──────────────────────────┴──────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│ Histogram : Distribution des scores finaux (AllStudents)         │
└──────────────────────────────────────────────────────────────────┘
```

### Page 2 — Facteurs de performance
```
┌──────────────────────────┬──────────────────────────────────────┐
│ Line+Bar : Score vs      │ Bar : Taux réussite par              │
│ heures d'étude           │ segment d'assiduité                  │
│ (StudyBehavior)          │ (AttendanceImpact)                   │
└──────────────────────────┴──────────────────────────────────────┘
┌──────────────────────────┬──────────────────────────────────────┐
│ Bar : Impact réseaux     │ Bar : Environnement de travail       │
│ sociaux (SocialMedia)    │ Quiet vs Moderate vs Noisy           │
└──────────────────────────┴──────────────────────────────────────┘
```

### Page 3 — Profils & Démographie
```
┌──────────────────────────┬──────────────────────────────────────┐
│ Grouped Bar : Scores     │ Bar : Taux réussite par              │
│ par matière/genre        │ éducation parentale                  │
│ (Gender)                 │ (ParentalEducation)                  │
└──────────────────────────┴──────────────────────────────────────┘
┌──────────────────────────┬──────────────────────────────────────┐
│ Bar : Impact revenu      │ Clustered Bar : Impact du            │
│ familial (FamilyIncome)  │ soutien scolaire (TutoringImpact)    │
└──────────────────────────┴──────────────────────────────────────┘
```

### Page 4 — Scores par matière
```
┌──────────────────────────────────────────────────────────────────┐
│ Radar Chart : Profil moyen des 4 matières par grade              │
│ (SubjectByGrade)                                                 │
└──────────────────────────────────────────────────────────────────┘
┌──────────────────────────┬──────────────────────────────────────┐
│ Heatmap (Matrix) :       │ Scatter : Score final vs             │
│ Matrice de corrélation   │ GPA précédent (AllStudents)          │
│ (CorrelationMatrix)      │                                      │
└──────────────────────────┴──────────────────────────────────────┘
```

### Page 5 — Risque & Top étudiants
```
┌──────────────────────────┬──────────────────────────────────────┐
│ Cards : À risque vs      │ Bar : % à risque par                 │
│ Non à risque             │ revenu familial                      │
│ (RiskProfile)            │ (AllStudents)                        │
└──────────────────────────┴──────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│ Table : Top 100 étudiants (TopStudents)                          │
│ Rank | ID | Genre | Score | Grade | Matière forte | Risque      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Slicers recommandés

| Slicer | Source | Type |
|---|---|---|
| Genre | `AllStudents[gender]` | Buttons |
| Âge | `AllStudents[age]` | Between |
| Éducation parentale | `AllStudents[parental_education]` | Dropdown |
| Revenu familial | `AllStudents[family_income]` | Buttons |
| Grade | `AllStudents[grade_category]` | Checklist |
| Pass/Fail | `AllStudents[pass_fail]` | Toggle |
| À risque | `AllStudents[is_at_risk]` | Toggle |

---

## 5. Palette de couleurs recommandée

| Couleur | Hex | Usage |
|---|---|---|
| Indigo | `#4361EE` | Couleur principale |
| Rose | `#F72585` | Alertes, échecs |
| Violet | `#7209B7` | Indicateurs risque |
| Vert | `#2DC653` | Réussite, positif |
| Ambre | `#F4A261` | Intermédiaire |
| Cyan | `#4CC9F0` | Données neutres |