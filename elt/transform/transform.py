"""
ELT — TRANSFORM
Nettoyage, typage, enrichissement et feature engineering sur raw_students.
Spécificités : scores académiques, comportements, profils socio-éducatifs.
"""

import pandas as pd
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [TRANSFORM] %(message)s")
log = logging.getLogger(__name__)

DB_PATH = Path("data/student_analytics.db")


def load_raw() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM raw_students", conn)
    conn.close()
    log.info(f"{len(df):,} lignes chargées depuis raw_students")
    return df


# ── Nettoyage ──────────────────────────────────────────────────────────────

def clean(df: pd.DataFrame) -> pd.DataFrame:
    log.info("--- Nettoyage ---")
    n0 = len(df)

    df = df.drop_duplicates(subset=["student_id"])
    log.info(f"Doublons supprimés : {n0 - len(df)}")

    critical = ["student_id", "gender", "final_exam_score", "pass_fail", "grade_category"]
    df = df.dropna(subset=critical)

    # Types numériques
    num_cols = [
        "age", "study_hours_per_day", "attendance_rate", "sleep_hours",
        "social_media_hours", "assignment_completion_rate", "participation_score",
        "online_courses_completed", "math_score", "reading_score",
        "writing_score", "science_score", "final_exam_score", "previous_gpa",
    ]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Valeurs aberrantes
    df = df[df["final_exam_score"].between(0, 100)]
    df = df[df["attendance_rate"].between(0, 100)]
    df = df[df["sleep_hours"].between(0, 24)]
    df = df[df["study_hours_per_day"].between(0, 24)]
    df = df[df["previous_gpa"].between(0, 4)]

    # Harmoniser chaînes
    for col in ["gender", "parental_education", "family_income",
                "internet_access", "study_environment", "tutoring", "pass_fail", "grade_category"]:
        df[col] = df[col].str.strip()

    log.info(f"Lignes après nettoyage : {len(df):,} (supprimées : {n0 - len(df)})")
    return df


# ── Enrichissement ─────────────────────────────────────────────────────────

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    log.info("--- Enrichissement ---")

    # ── Score moyen toutes matières ───────────────────────────────────────
    df["avg_subject_score"] = df[
        ["math_score", "reading_score", "writing_score", "science_score"]
    ].mean(axis=1).round(2)

    # ── Sujet fort / faible ───────────────────────────────────────────────
    subjects = {"math_score": "Math", "reading_score": "Reading",
                "writing_score": "Writing", "science_score": "Science"}
    df["best_subject"]  = df[list(subjects.keys())].idxmax(axis=1).map(subjects)
    df["worst_subject"] = df[list(subjects.keys())].idxmin(axis=1).map(subjects)

    # ── Écart entre meilleur et pire score ───────────────────────────────
    df["score_range"] = (
        df[list(subjects.keys())].max(axis=1) -
        df[list(subjects.keys())].min(axis=1)
    ).round(2)

    # ── Amélioration vs GPA précédent ────────────────────────────────────
    # Convertir GPA (0-4) en score 0-100 pour comparaison
    df["gpa_as_score"]      = (df["previous_gpa"] / 4 * 100).round(2)
    df["score_improvement"] = (df["final_exam_score"] - df["gpa_as_score"]).round(2)
    df["is_improving"]      = df["score_improvement"] > 0

    # ── Segmentation heures de travail ────────────────────────────────────
    df["study_segment"] = pd.cut(
        df["study_hours_per_day"],
        bins=[-0.1, 1, 2, 4, 6, 24],
        labels=["Très peu (<1h)", "Peu (1-2h)", "Modéré (2-4h)",
                "Intense (4-6h)", "Très intense (6h+)"],
    )

    # ── Segmentation score final ──────────────────────────────────────────
    df["score_segment"] = pd.cut(
        df["final_exam_score"],
        bins=[-0.1, 40, 50, 60, 70, 100],
        labels=["Critique (<40)", "Faible (40-50)", "Moyen (50-60)",
                "Bon (60-70)", "Excellent (70+)"],
    )

    # ── Segmentation assiduité ────────────────────────────────────────────
    df["attendance_segment"] = pd.cut(
        df["attendance_rate"],
        bins=[-0.1, 60, 75, 85, 95, 100],
        labels=["Très faible (<60%)", "Faible (60-75%)", "Moyen (75-85%)",
                "Bon (85-95%)", "Excellent (95%+)"],
    )

    # ── Score de risque (0-100, élevé = à risque) ────────────────────────
    # Facteurs de risque : peu d'étude, faible assiduité, trop réseaux sociaux
    study_risk   = (1 - df["study_hours_per_day"].clip(0, 8) / 8)
    attend_risk  = (1 - df["attendance_rate"] / 100)
    social_risk  = (df["social_media_hours"].clip(0, 6) / 6)
    df["risk_score"] = ((study_risk * 0.4 + attend_risk * 0.4 + social_risk * 0.2) * 100).round(1)
    df["is_at_risk"] = df["risk_score"] >= 50

    # ── Flags comportementaux ─────────────────────────────────────────────
    df["is_high_attendance"] = df["attendance_rate"] >= 90
    df["is_heavy_social"]    = df["social_media_hours"] >= 4
    df["has_tutoring"]       = df["tutoring"] == "Yes"
    df["has_internet"]       = df["internet_access"] == "Yes"
    df["is_quiet_env"]       = df["study_environment"] == "Quiet"

    # ── Profil parental ordonné ───────────────────────────────────────────
    edu_order = {"High School": 1, "Bachelor": 2, "Master": 3, "PhD": 4}
    df["parental_edu_rank"] = df["parental_education"].map(edu_order)

    # ── Groupe d'âge ─────────────────────────────────────────────────────
    df["age_group"] = df["age"].map({15: "15 ans", 16: "16 ans", 17: "17 ans", 18: "18 ans"})

    log.info("Enrichissement terminé")
    return df


def save_processed(df: pd.DataFrame) -> None:
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("processed_students", conn, if_exists="replace", index=False)
    df.to_csv("data/processed/student_exam_processed.csv", index=False)
    log.info(f"{len(df):,} lignes → processed_students + CSV")
    conn.close()


def run() -> pd.DataFrame:
    log.info("=== TRANSFORM START ===")
    df = load_raw()
    df = clean(df)
    df = enrich(df)
    save_processed(df)
    log.info("=== TRANSFORM DONE ===")
    return df


if __name__ == "__main__":
    run()