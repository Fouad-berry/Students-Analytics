"""
ELT — LOAD (DATA MARTS)
Construction des tables agrégées en 3 couches : Staging → Intermediate → Marts.
13 marts orientés Power BI — analyse de performance académique.
"""

import pandas as pd
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [LOAD] %(message)s")
log = logging.getLogger(__name__)

DB_PATH  = Path("data/student_analytics.db")
MART_DIR = Path("data/mart")


def load_processed() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM processed_students", conn)
    conn.close()
    log.info(f"{len(df):,} lignes chargées depuis processed_students")
    return df


def save(df: pd.DataFrame, name: str, conn: sqlite3.Connection) -> None:
    df.to_sql(name, conn, if_exists="replace", index=False)
    df.to_csv(MART_DIR / f"{name}.csv", index=False)
    log.info(f"  ✓ {name} : {len(df):,} lignes")


# ══════════════════════════════════════════════════════════════
# STAGING
# ══════════════════════════════════════════════════════════════

def build_staging(df: pd.DataFrame, conn: sqlite3.Connection):
    log.info("--- STAGING ---")
    cols = [
        "student_id", "gender", "age", "age_group", "parental_education",
        "parental_edu_rank", "family_income", "internet_access",
        "study_environment", "study_hours_per_day", "attendance_rate",
        "sleep_hours", "social_media_hours", "assignment_completion_rate",
        "participation_score", "online_courses_completed", "tutoring",
        "math_score", "reading_score", "writing_score", "science_score",
        "avg_subject_score", "best_subject", "worst_subject", "score_range",
        "final_exam_score", "previous_gpa", "gpa_as_score", "score_improvement",
        "is_improving", "pass_fail", "grade_category",
        "study_segment", "score_segment", "attendance_segment",
        "risk_score", "is_at_risk", "is_high_attendance",
        "is_heavy_social", "has_tutoring", "has_internet", "is_quiet_env",
    ]
    save(df[cols].copy(), "stg_students", conn)


# ══════════════════════════════════════════════════════════════
# INTERMEDIATE
# ══════════════════════════════════════════════════════════════

def build_intermediate(df: pd.DataFrame, conn: sqlite3.Connection):
    log.info("--- INTERMEDIATE ---")

    # int_subject_scores : stats par matière
    subjects = {
        "Math": "math_score", "Reading": "reading_score",
        "Writing": "writing_score", "Science": "science_score",
    }
    rows = []
    for subject, col in subjects.items():
        rows.append({
            "subject":      subject,
            "avg_score":    round(df[col].mean(), 2),
            "median_score": round(df[col].median(), 2),
            "std_score":    round(df[col].std(), 2),
            "min_score":    round(df[col].min(), 2),
            "max_score":    round(df[col].max(), 2),
            "pct_above_60": round((df[col] >= 60).mean() * 100, 2),
        })
    save(pd.DataFrame(rows), "int_subject_stats", conn)

    # int_pass_by_group : taux de réussite par groupe
    groups = ["gender", "parental_education", "family_income",
              "study_environment", "internet_access", "tutoring"]
    rows = []
    for group in groups:
        for val, grp in df.groupby(group):
            rows.append({
                "group_type":  group,
                "group_value": val,
                "nb_students": len(grp),
                "pct_pass":    round((grp["pass_fail"] == "Pass").mean() * 100, 2),
                "avg_score":   round(grp["final_exam_score"].mean(), 2),
                "avg_study_h": round(grp["study_hours_per_day"].mean(), 2),
            })
    save(pd.DataFrame(rows), "int_pass_by_group", conn)


# ══════════════════════════════════════════════════════════════
# MARTS
# ══════════════════════════════════════════════════════════════

def build_marts(df: pd.DataFrame, conn: sqlite3.Connection):
    log.info("--- MARTS ---")

    # ── mart_kpis ────────────────────────────────────────────────────────
    kpis = pd.DataFrame([{
        "total_students":        len(df),
        "pct_pass":              round((df["pass_fail"] == "Pass").mean() * 100, 2),
        "pct_fail":              round((df["pass_fail"] == "Fail").mean() * 100, 2),
        "avg_final_score":       round(df["final_exam_score"].mean(), 2),
        "median_final_score":    round(df["final_exam_score"].median(), 2),
        "avg_study_hours":       round(df["study_hours_per_day"].mean(), 2),
        "avg_attendance":        round(df["attendance_rate"].mean(), 2),
        "avg_sleep_hours":       round(df["sleep_hours"].mean(), 2),
        "avg_social_media_hours":round(df["social_media_hours"].mean(), 2),
        "avg_previous_gpa":      round(df["previous_gpa"].mean(), 2),
        "pct_with_tutoring":     round(df["has_tutoring"].mean() * 100, 2),
        "pct_with_internet":     round(df["has_internet"].mean() * 100, 2),
        "pct_at_risk":           round(df["is_at_risk"].mean() * 100, 2),
        "pct_improving":         round(df["is_improving"].mean() * 100, 2),
    }])
    save(kpis, "mart_kpis", conn)

    # ── mart_grade_distribution ──────────────────────────────────────────
    grade_order = ["A", "B", "C", "D", "F"]
    grade = (
        df.groupby("grade_category")
        .agg(
            nb_students   =("student_id", "count"),
            avg_score     =("final_exam_score", "mean"),
            avg_study_h   =("study_hours_per_day", "mean"),
            avg_attendance=("attendance_rate", "mean"),
            avg_gpa       =("previous_gpa", "mean"),
            avg_risk      =("risk_score", "mean"),
        )
        .round(2)
        .reset_index()
    )
    grade["grade_category"] = pd.Categorical(grade["grade_category"], categories=grade_order, ordered=True)
    grade = grade.sort_values("grade_category")
    grade["pct_students"] = (grade["nb_students"] / grade["nb_students"].sum() * 100).round(2)
    save(grade, "mart_grade_distribution", conn)

    # ── mart_gender ──────────────────────────────────────────────────────
    gender = (
        df.groupby("gender")
        .agg(
            nb_students    =("student_id", "count"),
            pct_pass       =("pass_fail", lambda x: (x=="Pass").mean() * 100),
            avg_score      =("final_exam_score", "mean"),
            avg_math       =("math_score", "mean"),
            avg_reading    =("reading_score", "mean"),
            avg_writing    =("writing_score", "mean"),
            avg_science    =("science_score", "mean"),
            avg_study_h    =("study_hours_per_day", "mean"),
            avg_social     =("social_media_hours", "mean"),
            avg_attendance =("attendance_rate", "mean"),
        )
        .round(2)
        .reset_index()
    )
    save(gender, "mart_gender", conn)

    # ── mart_parental_education ──────────────────────────────────────────
    edu_order = ["High School", "Bachelor", "Master", "PhD"]
    edu = (
        df.groupby("parental_education")
        .agg(
            nb_students =("student_id", "count"),
            pct_pass    =("pass_fail", lambda x: (x=="Pass").mean() * 100),
            avg_score   =("final_exam_score", "mean"),
            avg_gpa     =("previous_gpa", "mean"),
            avg_study_h =("study_hours_per_day", "mean"),
            avg_risk    =("risk_score", "mean"),
        )
        .round(2)
        .reset_index()
    )
    edu["parental_education"] = pd.Categorical(edu["parental_education"], categories=edu_order, ordered=True)
    edu = edu.sort_values("parental_education")
    save(edu, "mart_parental_education", conn)

    # ── mart_family_income ───────────────────────────────────────────────
    income_order = ["Low", "Medium", "High"]
    income = (
        df.groupby("family_income")
        .agg(
            nb_students    =("student_id", "count"),
            pct_pass       =("pass_fail", lambda x: (x=="Pass").mean() * 100),
            avg_score      =("final_exam_score", "mean"),
            pct_tutoring   =("has_tutoring", "mean"),
            pct_internet   =("has_internet", "mean"),
            avg_study_h    =("study_hours_per_day", "mean"),
        )
        .round(2)
        .reset_index()
    )
    income["family_income"] = pd.Categorical(income["family_income"], categories=income_order, ordered=True)
    income = income.sort_values("family_income")
    income["pct_tutoring"] = (income["pct_tutoring"] * 100).round(2)
    income["pct_internet"] = (income["pct_internet"] * 100).round(2)
    save(income, "mart_family_income", conn)

    # ── mart_study_behavior ──────────────────────────────────────────────
    study_seg_order = ["Très peu (<1h)", "Peu (1-2h)", "Modéré (2-4h)", "Intense (4-6h)", "Très intense (6h+)"]
    behavior = (
        df.groupby("study_segment")
        .agg(
            nb_students =("student_id", "count"),
            pct_pass    =("pass_fail", lambda x: (x=="Pass").mean() * 100),
            avg_score   =("final_exam_score", "mean"),
            avg_attend  =("attendance_rate", "mean"),
            avg_risk    =("risk_score", "mean"),
        )
        .round(2)
        .reset_index()
    )
    behavior["study_segment"] = pd.Categorical(behavior["study_segment"], categories=study_seg_order, ordered=True)
    behavior = behavior.sort_values("study_segment")
    save(behavior, "mart_study_behavior", conn)

    # ── mart_environment ──────────────────────────────────────────────────
    env = (
        df.groupby("study_environment")
        .agg(
            nb_students =("student_id", "count"),
            pct_pass    =("pass_fail", lambda x: (x=="Pass").mean() * 100),
            avg_score   =("final_exam_score", "mean"),
            avg_study_h =("study_hours_per_day", "mean"),
            avg_attend  =("attendance_rate", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("avg_score", ascending=False)
    )
    save(env, "mart_environment", conn)

    # ── mart_attendance_impact ────────────────────────────────────────────
    att = (
        df.groupby("attendance_segment")
        .agg(
            nb_students =("student_id", "count"),
            pct_pass    =("pass_fail", lambda x: (x=="Pass").mean() * 100),
            avg_score   =("final_exam_score", "mean"),
            avg_study_h =("study_hours_per_day", "mean"),
        )
        .round(2)
        .reset_index()
    )
    save(att, "mart_attendance_impact", conn)

    # ── mart_subject_scores ───────────────────────────────────────────────
    subj = df.groupby("grade_category").agg(
        avg_math    =("math_score", "mean"),
        avg_reading =("reading_score", "mean"),
        avg_writing =("writing_score", "mean"),
        avg_science =("science_score", "mean"),
        avg_final   =("final_exam_score", "mean"),
    ).round(2).reset_index()
    subj["grade_category"] = pd.Categorical(subj["grade_category"], categories=["A","B","C","D","F"], ordered=True)
    subj = subj.sort_values("grade_category")
    save(subj, "mart_subject_by_grade", conn)

    # ── mart_risk_profile ─────────────────────────────────────────────────
    at_risk     = df[df["risk_score"] >= 50]
    not_at_risk = df[df["risk_score"] <  50]
    def _risk_row(label, subset):
        return {
            "risk_group": label,
            "nb_students": len(subset),
            "pct_pass":    round((subset["pass_fail"] == "Pass").mean() * 100, 2),
            "avg_score":   round(subset["final_exam_score"].mean(), 2),
            "avg_study":   round(subset["study_hours_per_day"].mean(), 2),
            "avg_social":  round(subset["social_media_hours"].mean(), 2),
            "avg_attend":  round(subset["attendance_rate"].mean(), 2),
        }
    risk = pd.DataFrame([
        _risk_row("À risque (score ≥50)",    at_risk),
        _risk_row("Non à risque (score <50)", not_at_risk),
    ])
    save(risk, "mart_risk_profile", conn)

    # ── mart_tutoring_impact ──────────────────────────────────────────────
    tut = (
        df.groupby(["tutoring", "family_income"])
        .agg(
            nb_students=("student_id", "count"),
            pct_pass   =("pass_fail", lambda x: (x=="Pass").mean() * 100),
            avg_score  =("final_exam_score", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values(["tutoring", "family_income"])
    )
    save(tut, "mart_tutoring_impact", conn)

    # ── mart_social_media_impact ──────────────────────────────────────────
    social_bins = [0, 1, 2, 3, 4, 24]
    social_labels = ["0-1h", "1-2h", "2-3h", "3-4h", "4h+"]
    df["social_segment"] = pd.cut(df["social_media_hours"], bins=social_bins, labels=social_labels, include_lowest=True)
    social = (
        df.groupby("social_segment")
        .agg(
            nb_students=("student_id", "count"),
            pct_pass   =("pass_fail", lambda x: (x=="Pass").mean() * 100),
            avg_score  =("final_exam_score", "mean"),
            avg_study_h=("study_hours_per_day", "mean"),
        )
        .round(2)
        .reset_index()
    )
    save(social, "mart_social_media_impact", conn)

    # ── mart_monthly_best_students (top 100) ──────────────────────────────
    top = (
        df.nlargest(100, "final_exam_score")[[
            "student_id", "gender", "age", "parental_education", "family_income",
            "study_hours_per_day", "attendance_rate", "sleep_hours",
            "math_score", "reading_score", "writing_score", "science_score",
            "final_exam_score", "previous_gpa", "grade_category",
            "risk_score", "avg_subject_score", "best_subject",
        ]]
        .reset_index(drop=True)
    )
    top.insert(0, "rank", range(1, len(top)+1))
    save(top, "mart_top_students", conn)

    # ── mart_correlation_matrix ───────────────────────────────────────────
    corr_cols = [
        "study_hours_per_day", "attendance_rate", "sleep_hours",
        "social_media_hours", "assignment_completion_rate",
        "participation_score", "previous_gpa", "final_exam_score",
    ]
    corr = df[corr_cols].corr().round(3).reset_index()
    corr.rename(columns={"index": "variable"}, inplace=True)
    save(corr, "mart_correlation_matrix", conn)


def run():
    log.info("=== LOAD START ===")
    conn = sqlite3.connect(DB_PATH)
    df = load_processed()
    build_staging(df, conn)
    build_intermediate(df, conn)
    build_marts(df, conn)
    conn.close()
    log.info("=== LOAD DONE ===")


if __name__ == "__main__":
    run()