"""
analysis/eda.py — Analyse Exploratoire Complète
9 graphiques orientés performance académique étudiante
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import sqlite3
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

DB_PATH = Path("data/student_analytics.db")
FIG_DIR = Path("analysis/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = ["#4361EE","#F72585","#3A0CA3","#7209B7","#4CC9F0",
           "#560BAD","#480CA8","#3F37C9","#4895EF","#4CC9F0"]
BLUE, RED, GREEN, PURPLE, AMBER = "#4361EE","#F72585","#2DC653","#7209B7","#F4A261"

sns.set_theme(style="whitegrid", palette=PALETTE)
plt.rcParams.update({"figure.dpi":120,"axes.spines.top":False,"axes.spines.right":False,"font.size":11})


def load() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM processed_students", conn)
    conn.close()
    return df


def sep(t): print(f"\n{'═'*60}\n  {t}\n{'═'*60}")


def overview(df):
    sep("VUE GÉNÉRALE")
    print(f"Étudiants   : {len(df):,}")
    print(f"Taux réussite: {(df['pass_fail']=='Pass').mean()*100:.1f}%")
    print(f"Score moyen  : {df['final_exam_score'].mean():.1f}/100")
    print(f"Notes :")
    for g in ["A","B","C","D","F"]:
        n = (df['grade_category']==g).sum()
        print(f"  {g} : {n:,} ({n/len(df)*100:.1f}%)")


# Fig 1 : Distribution des scores finaux
def plot_score_dist(df):
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    axes[0].hist(df["final_exam_score"],bins=40,color=BLUE,edgecolor="white",alpha=0.85)
    axes[0].axvline(df["final_exam_score"].mean(),color=RED,linestyle="--",linewidth=2,label=f"Moyenne: {df['final_exam_score'].mean():.1f}")
    axes[0].set_title("Distribution des scores finaux",fontweight="bold")
    axes[0].set_xlabel("Score final (/100)")
    axes[0].legend()
    grade_order = ["A","B","C","D","F"]
    counts = df["grade_category"].value_counts().reindex(grade_order)
    colors = [GREEN,BLUE,AMBER,PURPLE,RED]
    bars = axes[1].bar(counts.index,counts.values,color=colors)
    axes[1].bar_label(bars,padding=3,fontsize=10)
    axes[1].set_title("Répartition par grade",fontweight="bold")
    axes[1].set_ylabel("Nombre d'étudiants")
    plt.tight_layout()
    plt.savefig(FIG_DIR/"01_score_distribution.png"); plt.close()
    print("✓ Fig 1 : Distribution scores")


# Fig 2 : Impact heures d'étude sur le score
def plot_study_impact(df):
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    study_bins = ["Très peu (<1h)","Peu (1-2h)","Modéré (2-4h)","Intense (4-6h)","Très intense (6h+)"]
    study_data = df.groupby("study_segment")["final_exam_score"].mean().reindex(study_bins)
    bars = axes[0].bar(study_data.index,study_data.values,color=PALETTE[:5])
    axes[0].bar_label(bars,labels=[f"{v:.1f}" for v in study_data.values],padding=3,fontsize=9)
    axes[0].set_title("Score moyen par heures d'étude",fontweight="bold")
    axes[0].set_ylabel("Score moyen (/100)")
    axes[0].tick_params(axis="x",rotation=20)
    study_pass = df.groupby("study_segment")["pass_fail"].apply(lambda x:(x=="Pass").mean()*100).reindex(study_bins)
    bars2 = axes[1].bar(study_pass.index,study_pass.values,color=GREEN,alpha=0.85)
    axes[1].bar_label(bars2,labels=[f"{v:.1f}%" for v in study_pass.values],padding=3,fontsize=9)
    axes[1].set_title("Taux de réussite par heures d'étude",fontweight="bold")
    axes[1].set_ylabel("% de réussite")
    axes[1].tick_params(axis="x",rotation=20)
    plt.tight_layout()
    plt.savefig(FIG_DIR/"02_study_hours_impact.png"); plt.close()
    print("✓ Fig 2 : Impact heures d'étude")


# Fig 3 : Scores par matière et par genre
def plot_subject_gender(df):
    subjects = ["math_score","reading_score","writing_score","science_score"]
    labels = ["Math","Reading","Writing","Science"]
    male = df[df["gender"]=="Male"][subjects].mean()
    female = df[df["gender"]=="Female"][subjects].mean()
    x = range(len(subjects))
    fig, ax = plt.subplots(figsize=(10,5))
    width = 0.35
    bars1 = ax.bar([i-width/2 for i in x],male.values,width,label="Male",color=BLUE,alpha=0.85,borderRadius=0)
    bars2 = ax.bar([i+width/2 for i in x],female.values,width,label="Female",color=RED,alpha=0.85)
    ax.bar_label(bars1,labels=[f"{v:.1f}" for v in male.values],padding=3,fontsize=9)
    ax.bar_label(bars2,labels=[f"{v:.1f}" for v in female.values],padding=3,fontsize=9)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_title("Scores moyens par matière et par genre",fontsize=14,fontweight="bold")
    ax.set_ylabel("Score moyen")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR/"03_subject_by_gender.png"); plt.close()
    print("✓ Fig 3 : Scores par matière et genre")


# Fig 4 : Heatmap corrélations
def plot_correlation(df):
    corr_cols = ["study_hours_per_day","attendance_rate","sleep_hours",
                 "social_media_hours","assignment_completion_rate",
                 "participation_score","previous_gpa","final_exam_score"]
    labels = ["Heures étude","Assiduité","Sommeil","Réseaux sociaux",
              "Devoirs faits","Participation","GPA précédent","Score final"]
    corr = df[corr_cols].corr()
    corr.index = labels; corr.columns = labels
    fig, ax = plt.subplots(figsize=(10,8))
    sns.heatmap(corr,annot=True,fmt=".2f",cmap="RdBu_r",center=0,ax=ax,
                linewidths=0.5,square=True,cbar_kws={"shrink":0.8})
    ax.set_title("Matrice de corrélation — Facteurs vs Score final",fontsize=13,fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR/"04_correlation_heatmap.png"); plt.close()
    print("✓ Fig 4 : Heatmap corrélations")


# Fig 5 : Éducation parentale et réussite
def plot_parental_edu(df):
    edu_order = ["High School","Bachelor","Master","PhD"]
    edu_pass = df.groupby("parental_education")["pass_fail"].apply(lambda x:(x=="Pass").mean()*100).reindex(edu_order)
    edu_score = df.groupby("parental_education")["final_exam_score"].mean().reindex(edu_order)
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    bars = axes[0].bar(edu_pass.index,edu_pass.values,color=PALETTE[:4])
    axes[0].bar_label(bars,labels=[f"{v:.1f}%" for v in edu_pass.values],padding=3,fontsize=10)
    axes[0].set_title("Taux de réussite par éducation parentale",fontweight="bold")
    axes[0].set_ylabel("% de réussite")
    axes[0].tick_params(axis="x",rotation=15)
    bars2 = axes[1].bar(edu_score.index,edu_score.values,color=PALETTE[4:8])
    axes[1].bar_label(bars2,labels=[f"{v:.1f}" for v in edu_score.values],padding=3,fontsize=10)
    axes[1].set_title("Score moyen par éducation parentale",fontweight="bold")
    axes[1].set_ylabel("Score moyen (/100)")
    axes[1].tick_params(axis="x",rotation=15)
    plt.tight_layout()
    plt.savefig(FIG_DIR/"05_parental_education.png"); plt.close()
    print("✓ Fig 5 : Éducation parentale")


# Fig 6 : Assiduité vs Score (scatter)
def plot_attendance_scatter(df):
    sample = df.sample(min(2000,len(df)),random_state=42)
    fig, ax = plt.subplots(figsize=(10,6))
    colors = sample["pass_fail"].map({"Pass":GREEN,"Fail":RED})
    ax.scatter(sample["attendance_rate"],sample["final_exam_score"],
               c=colors,alpha=0.4,s=15)
    ax.axhline(50,color="gray",linestyle="--",linewidth=1,alpha=0.7,label="Seuil 50pts")
    ax.set_title("Assiduité vs Score final (Pass=vert, Fail=rouge)",fontsize=13,fontweight="bold")
    ax.set_xlabel("Taux d'assiduité (%)")
    ax.set_ylabel("Score final (/100)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR/"06_attendance_vs_score.png"); plt.close()
    print("✓ Fig 6 : Assiduité vs Score")


# Fig 7 : Impact réseaux sociaux
def plot_social_media(df):
    social_bins = [0,1,2,3,4,24]
    social_labels = ["0-1h","1-2h","2-3h","3-4h","4h+"]
    df["_social_seg"] = pd.cut(df["social_media_hours"],bins=social_bins,labels=social_labels,include_lowest=True)
    soc = df.groupby("_social_seg").agg(
        avg_score=("final_exam_score","mean"),
        pct_pass=("pass_fail",lambda x:(x=="Pass").mean()*100)
    ).reset_index()
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    colors = [GREEN,BLUE,AMBER,PURPLE,RED]
    bars = axes[0].bar(soc["_social_seg"].astype(str),soc["avg_score"],color=colors)
    axes[0].bar_label(bars,labels=[f"{v:.1f}" for v in soc["avg_score"]],padding=3,fontsize=10)
    axes[0].set_title("Score moyen vs heures réseaux sociaux",fontweight="bold")
    axes[0].set_ylabel("Score moyen")
    bars2 = axes[1].bar(soc["_social_seg"].astype(str),soc["pct_pass"],color=colors)
    axes[1].bar_label(bars2,labels=[f"{v:.1f}%" for v in soc["pct_pass"]],padding=3,fontsize=10)
    axes[1].set_title("Taux réussite vs heures réseaux sociaux",fontweight="bold")
    axes[1].set_ylabel("% réussite")
    plt.tight_layout()
    plt.savefig(FIG_DIR/"07_social_media_impact.png"); plt.close()
    print("✓ Fig 7 : Impact réseaux sociaux")


# Fig 8 : Environnement de travail
def plot_environment(df):
    env_data = df.groupby("study_environment").agg(
        avg_score=("final_exam_score","mean"),
        pct_pass=("pass_fail",lambda x:(x=="Pass").mean()*100),
        nb_students=("student_id","count")
    ).sort_values("avg_score",ascending=False).reset_index()
    fig, ax = plt.subplots(figsize=(9,5))
    colors = [GREEN,AMBER,RED]
    bars = ax.bar(env_data["study_environment"],env_data["avg_score"],color=colors,width=0.5)
    ax.bar_label(bars,labels=[f"{v:.1f}/100\n({r:.1f}% réussite)"
                               for v,r in zip(env_data["avg_score"],env_data["pct_pass"])],
                 padding=4,fontsize=11)
    ax.set_title("Score moyen par environnement de travail",fontsize=13,fontweight="bold")
    ax.set_ylabel("Score moyen (/100)")
    ax.set_ylim(0,70)
    plt.tight_layout()
    plt.savefig(FIG_DIR/"08_study_environment.png"); plt.close()
    print("✓ Fig 8 : Environnement de travail")


# Fig 9 : Profil de risque
def plot_risk(df):
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    axes[0].hist(df["risk_score"],bins=30,color=PURPLE,edgecolor="white",alpha=0.85)
    axes[0].axvline(50,color=RED,linestyle="--",linewidth=2,label="Seuil risque: 50")
    axes[0].set_title("Distribution du score de risque",fontweight="bold")
    axes[0].set_xlabel("Score de risque (0=sûr, 100=à risque)")
    axes[0].legend()
    risk_income = df.groupby("family_income")["is_at_risk"].mean()*100
    bars = axes[1].bar(["Low","Medium","High"],
                       [risk_income.get("Low",0),risk_income.get("Medium",0),risk_income.get("High",0)],
                       color=[RED,AMBER,GREEN],width=0.5)
    axes[1].bar_label(bars,labels=[f"{v:.1f}%" for v in bars.datavalues],padding=3,fontsize=11)
    axes[1].set_title("% étudiants à risque par revenu familial",fontweight="bold")
    axes[1].set_ylabel("% à risque")
    plt.tight_layout()
    plt.savefig(FIG_DIR/"09_risk_profile.png"); plt.close()
    print("✓ Fig 9 : Profil de risque")


def print_insights(df):
    sep("TOP INSIGHTS")
    print(f"Taux réussite global   : {(df['pass_fail']=='Pass').mean()*100:.1f}%")
    print(f"Score moyen final      : {df['final_exam_score'].mean():.1f}/100")
    print(f"Corr. étude/score      : {df['study_hours_per_day'].corr(df['final_exam_score']):.3f}")
    print(f"Corr. assiduité/score  : {df['attendance_rate'].corr(df['final_exam_score']):.3f}")
    print(f"Corr. social/score     : {df['social_media_hours'].corr(df['final_exam_score']):.3f}")
    print(f"% étudiants à risque   : {df['is_at_risk'].mean()*100:.1f}%")
    print(f"Meilleure matière (moy): Math={df['math_score'].mean():.1f} | Reading={df['reading_score'].mean():.1f}")
    print(f"Env. le + performant   : {df.groupby('study_environment')['final_exam_score'].mean().idxmax()}")


if __name__ == "__main__":
    df = load()
    overview(df)
    sep("GÉNÉRATION FIGURES")
    plot_score_dist(df)
    plot_study_impact(df)
    plot_subject_gender(df)
    plot_correlation(df)
    plot_parental_edu(df)
    plot_attendance_scatter(df)
    plot_social_media(df)
    plot_environment(df)
    plot_risk(df)
    print_insights(df)
    print(f"\n✅ Figures dans : {FIG_DIR}/")