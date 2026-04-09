"""
tests/test_pipeline.py — Tests unitaires ELT Student Analytics
"""

import pandas as pd
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def raw_df():
    return pd.DataFrame({
        "student_id":               ["S00001","S00002","S00002","S00003","S00004"],
        "gender":                   ["Male","Female","Female","Male","Female"],
        "age":                      [17, 18, 18, 15, 16],
        "parental_education":       ["High School","Bachelor","Bachelor","Master","PhD"],
        "family_income":            ["Medium","Low","Low","High","Medium"],
        "internet_access":          ["Yes","Yes","Yes","No","Yes"],
        "study_environment":        ["Quiet","Moderate","Moderate","Noisy","Quiet"],
        "study_hours_per_day":      [3.0, 5.0, 5.0, 1.0, 2.5],
        "attendance_rate":          [90.0, 85.0, 85.0, 70.0, 95.0],
        "sleep_hours":              [7.0, 8.0, 8.0, 6.5, 7.5],
        "social_media_hours":       [2.0, 1.0, 1.0, 5.0, 3.0],
        "assignment_completion_rate":[80.0,90.0,90.0,60.0,75.0],
        "participation_score":      [70.0,85.0,85.0,50.0,65.0],
        "online_courses_completed": [2, 3, 3, 0, 1],
        "tutoring":                 ["Yes","No","No","Yes","No"],
        "math_score":               [60.0, 75.0, 75.0, 40.0, -5.0],   # -5 invalide
        "reading_score":            [55.0, 80.0, 80.0, 35.0, 65.0],
        "writing_score":            [58.0, 70.0, 70.0, 42.0, 60.0],
        "science_score":            [62.0, 78.0, 78.0, 38.0, 70.0],
        "final_exam_score":         [58.0, 76.0, 76.0, 39.0, 105.0],  # 105 invalide
        "previous_gpa":             [2.5, 3.2, 3.2, 1.8, 2.9],
        "pass_fail":                ["Pass","Pass","Pass","Fail","Pass"],
        "grade_category":           ["D","C","C","F","D"],
    })


class TestClean:
    def test_removes_duplicates(self, raw_df):
        from elt.transform.transform import clean
        df = clean(raw_df)
        assert df["student_id"].duplicated().sum() == 0

    def test_removes_invalid_final_score(self, raw_df):
        from elt.transform.transform import clean
        df = clean(raw_df)
        assert df["final_exam_score"].between(0, 100).all()

    def test_no_null_critical_columns(self, raw_df):
        from elt.transform.transform import clean
        df = clean(raw_df)
        for col in ["student_id","gender","final_exam_score","pass_fail"]:
            assert df[col].isnull().sum() == 0

    def test_strips_strings(self, raw_df):
        raw_df["gender"] = raw_df["gender"].apply(lambda x: f"  {x}  ")
        from elt.transform.transform import clean
        df = clean(raw_df)
        for val in df["gender"]:
            assert val == val.strip()


class TestEnrich:
    def _clean(self, raw_df):
        from elt.transform.transform import clean
        return clean(raw_df)

    def test_avg_subject_score_correct(self, raw_df):
        from elt.transform.transform import enrich
        df = enrich(self._clean(raw_df))
        assert "avg_subject_score" in df.columns
        assert (df["avg_subject_score"] >= 0).all()

    def test_best_subject_valid(self, raw_df):
        from elt.transform.transform import enrich
        df = enrich(self._clean(raw_df))
        valid = {"Math","Reading","Writing","Science"}
        assert set(df["best_subject"].unique()).issubset(valid)

    def test_risk_score_range(self, raw_df):
        from elt.transform.transform import enrich
        df = enrich(self._clean(raw_df))
        assert df["risk_score"].between(0, 100).all()

    def test_study_segment_created(self, raw_df):
        from elt.transform.transform import enrich
        df = enrich(self._clean(raw_df))
        assert "study_segment" in df.columns
        assert df["study_segment"].isnull().sum() == 0

    def test_is_at_risk_boolean(self, raw_df):
        from elt.transform.transform import enrich
        df = enrich(self._clean(raw_df))
        assert df["is_at_risk"].isin([True, False]).all()

    def test_gpa_as_score_range(self, raw_df):
        from elt.transform.transform import enrich
        df = enrich(self._clean(raw_df))
        assert df["gpa_as_score"].between(0, 100).all()

    def test_score_improvement_computed(self, raw_df):
        from elt.transform.transform import enrich
        df = enrich(self._clean(raw_df))
        assert "score_improvement" in df.columns
        assert "is_improving" in df.columns


class TestDataQuality:
    def test_attendance_range(self, raw_df):
        from elt.transform.transform import clean
        df = clean(raw_df)
        assert df["attendance_rate"].between(0, 100).all()

    def test_sleep_hours_range(self, raw_df):
        from elt.transform.transform import clean
        df = clean(raw_df)
        assert df["sleep_hours"].between(0, 24).all()

    def test_gpa_range(self, raw_df):
        from elt.transform.transform import clean
        df = clean(raw_df)
        assert df["previous_gpa"].between(0, 4).all()

    def test_pass_fail_values(self, raw_df):
        from elt.transform.transform import clean
        df = clean(raw_df)
        assert set(df["pass_fail"].unique()).issubset({"Pass","Fail"})