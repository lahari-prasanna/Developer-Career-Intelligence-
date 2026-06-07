
import streamlit as st
import polars as pl
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Developer Career Intelligence",
    page_icon="💻",
    layout="wide"
)

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    df = pl.read_parquet("master_survey.parquet")
    return df

master_df = load_data()

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("💻 Developer Career Intelligence")
st.sidebar.markdown("Stack Overflow Survey 2020–2025")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Overview", "💰 Salary Analysis", "🔧 Technology Trends", "👥 HR Analytics"]
)

years = sorted(master_df["survey_year"].unique().to_list())
selected_years = st.sidebar.multiselect("Filter by Year", years, default=years)

filtered_df = master_df.filter(pl.col("survey_year").is_in(selected_years))

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Rows loaded:** {filtered_df.shape[0]:,}")
st.sidebar.markdown(f"**Years selected:** {len(selected_years)}")

# ============================================================
# PAGE 1 — OVERVIEW
# ============================================================

if page == "🏠 Overview":

    st.title("🏠 Developer Career Intelligence Warehouse")
    st.markdown("#### Insights from Stack Overflow Developer Survey 2020–2025")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Responses", f"{filtered_df.shape[0]:,}")
    with col2:
        countries = filtered_df.filter(pl.col("country").is_not_null())["country"].n_unique()
        st.metric("Countries", f"{countries}")
    with col3:
        salary_data = filtered_df.with_columns(
            pl.col("salary_usd").cast(pl.Float64, strict=False)
        ).filter(
            pl.col("salary_usd").is_not_null() &
            (pl.col("salary_usd") >= 1000) &
            (pl.col("salary_usd") <= 500000)
        )
        median_sal = salary_data["salary_usd"].median()
        st.metric("Global Median Salary", f"${median_sal:,.0f}")
    with col4:
        st.metric("Years Covered", f"{min(selected_years)}–{max(selected_years)}")

    st.markdown("---")

    st.subheader("📊 Dataset Overview by Year")

    year_summary = (
        filtered_df
        .group_by("survey_year")
        .agg(pl.len().alias("responses"))
        .sort("survey_year")
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(
        year_summary["survey_year"].to_list(),
        year_summary["responses"].to_list(),
        color="steelblue", edgecolor="white", width=0.5
    )
    for x, y in zip(year_summary["survey_year"].to_list(), year_summary["responses"].to_list()):
        ax.text(x, y + 300, f"{y:,}", ha="center", fontsize=9)
    ax.set_xlabel("Survey Year")
    ax.set_ylabel("Number of Responses")
    ax.set_title("Survey Responses Per Year")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")
    st.subheader("🌍 Top 10 Developer Communities")

    country_dist = (
        filtered_df
        .filter(pl.col("country").is_not_null())
        .group_by("country")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(10)
    )

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    countries_list = country_dist["country"].to_list()[::-1]
    counts_list    = country_dist["count"].to_list()[::-1]
    ax2.barh(countries_list, counts_list, color="steelblue", edgecolor="white", height=0.6)
    for i, v in enumerate(counts_list):
        ax2.text(v + 100, i, f"{v:,}", va="center", fontsize=9)
    ax2.set_xlabel("Number of Developers")
    ax2.set_title("Top 10 Countries by Developer Count")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    st.pyplot(fig2)
    plt.close()

# ============================================================
# PAGE 2 — SALARY ANALYSIS
# ============================================================

elif page == "💰 Salary Analysis":

    st.title("💰 Salary Analysis")
    st.markdown("---")

    salary_df = filtered_df.with_columns(
        pl.col("salary_usd").cast(pl.Float64, strict=False)
    ).filter(
        pl.col("salary_usd").is_not_null() &
        (pl.col("salary_usd") >= 1000) &
        (pl.col("salary_usd") <= 500000)
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Median Salary", f"${salary_df['salary_usd'].median():,.0f}")
    with col2:
        st.metric("Mean Salary", f"${salary_df['salary_usd'].mean():,.0f}")
    with col3:
        st.metric("Responses with Salary", f"{salary_df.shape[0]:,}")

    st.markdown("---")

    # Salary by Country
    st.subheader("🌍 Median Salary by Country (Top 20)")

    country_salary = (
        salary_df
        .filter(pl.col("country").is_not_null())
        .group_by("country")
        .agg([
            pl.col("salary_usd").median().alias("median_salary"),
            pl.col("salary_usd").count().alias("count")
        ])
        .filter(pl.col("count") >= 300)
        .sort("median_salary", descending=True)
        .head(20)
    )

    fig, ax = plt.subplots(figsize=(12, 8))
    c_list = country_salary["country"].to_list()[::-1]
    s_list = country_salary["median_salary"].to_list()[::-1]
    colors = ["#e74c3c" if s >= 100000 else "#e67e22" if s >= 70000 else "#3498db" for s in s_list]
    bars = ax.barh(c_list, s_list, color=colors, edgecolor="white", height=0.6)
    for bar, val in zip(bars, s_list):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2, f"${val:,.0f}", va="center", fontsize=9)
    ax.set_xlabel("Median Annual Salary (USD)")
    ax.set_title("Median Developer Salary by Country")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")

    # Salary by Experience
    st.subheader("📈 Salary by Experience Level")

    exp_df = salary_df.with_columns(
        pl.col("years_code_pro")
        .str.replace("More than 50 years", "51")
        .str.replace("Less than 1 year", "0")
        .cast(pl.Float64, strict=False)
        .alias("experience")
    ).filter(
        pl.col("experience").is_not_null() &
        (pl.col("experience") >= 0) &
        (pl.col("experience") <= 50)
    ).with_columns(
        pl.when(pl.col("experience") < 1).then(pl.lit("< 1 year"))
        .when(pl.col("experience") < 3).then(pl.lit("1-2 years"))
        .when(pl.col("experience") < 6).then(pl.lit("3-5 years"))
        .when(pl.col("experience") < 11).then(pl.lit("6-10 years"))
        .when(pl.col("experience") < 21).then(pl.lit("11-20 years"))
        .otherwise(pl.lit("20+ years"))
        .alias("experience_band")
    )

    band_order = ["< 1 year", "1-2 years", "3-5 years", "6-10 years", "11-20 years", "20+ years"]

    exp_salary = (
        exp_df
        .group_by("experience_band")
        .agg(pl.col("salary_usd").median().alias("median_salary"))
        .with_columns(pl.col("experience_band").cast(pl.Enum(band_order)))
        .sort("experience_band")
    )

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.bar(
        exp_salary["experience_band"].to_list(),
        exp_salary["median_salary"].to_list(),
        color="steelblue", edgecolor="white", width=0.5
    )
    for x, y in zip(exp_salary["experience_band"].to_list(), exp_salary["median_salary"].to_list()):
        ax2.text(x, y + 500, f"${y:,.0f}", ha="center", fontsize=9, fontweight="bold")
    ax2.set_xlabel("Experience Level")
    ax2.set_ylabel("Median Salary (USD)")
    ax2.set_title("Salary Progression by Experience")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    plt.xticks(rotation=15)
    st.pyplot(fig2)
    plt.close()

# ============================================================
# PAGE 3 — TECHNOLOGY TRENDS
# ============================================================

elif page == "🔧 Technology Trends":

    st.title("🔧 Technology Trends")
    st.markdown("---")

    tech_type = st.selectbox(
        "Select Technology Category",
        ["Programming Languages", "Databases", "Frameworks", "Cloud Platforms"]
    )

    def get_tech_counts(df, col, skill_col_name):
        total_per_year = (
            df.filter(pl.col(col).is_not_null())
            .group_by("survey_year")
            .agg(pl.len().alias("total"))
        )
        counts = (
            df.filter(pl.col(col).is_not_null())
            .select(["survey_year", col])
            .with_columns(pl.col(col).str.split(";"))
            .explode(col)
            .with_columns(pl.col(col).str.strip_chars().alias(skill_col_name))
            .filter(pl.col(skill_col_name) != "")
            .group_by(["survey_year", skill_col_name])
            .agg(pl.len().alias("count"))
            .join(total_per_year, on="survey_year")
            .with_columns(
                (pl.col("count") / pl.col("total") * 100).round(1).alias("pct")
            )
            .sort(["survey_year", "count"], descending=[False, True])
        )
        return counts

    col_map = {
        "Programming Languages" : ("language_worked_with", "language"),
        "Databases"             : ("database_worked_with", "database"),
        "Frameworks"            : ("webframe_worked_with", "framework"),
        "Cloud Platforms"       : ("platform_worked_with", "platform"),
    }

    col, skill_col = col_map[tech_type]
    counts_df = get_tech_counts(filtered_df, col, skill_col)

    st.subheader(f"Top 10 {tech_type} in {max(selected_years)}")

    top10 = (
        counts_df
        .filter(pl.col("survey_year") == max(selected_years))
        .sort("pct", descending=True)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    skills  = top10[skill_col].to_list()[::-1]
    pcts    = top10["pct"].to_list()[::-1]
    ax.barh(skills, pcts, color="steelblue", edgecolor="white", height=0.6)
    for i, v in enumerate(pcts):
        ax.text(v + 0.3, i, f"{v}%", va="center", fontsize=9)
    ax.set_xlabel("% of Respondents")
    ax.set_title(f"Top 10 {tech_type} ({max(selected_years)})")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")
    st.subheader(f"📈 Trend Over Time — Top 8 {tech_type}")

    top8_skills = (
        counts_df
        .filter(pl.col("survey_year") == max(selected_years))
        .sort("pct", descending=True)
        .head(8)[skill_col]
        .to_list()
    )

    colors = ["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e"]

    fig2, ax2 = plt.subplots(figsize=(12, 6))
    for i, skill in enumerate(top8_skills):
        trend = (
            counts_df
            .filter(pl.col(skill_col) == skill)
            .sort("survey_year")
        )
        if trend.shape[0] > 0:
            ax2.plot(trend["survey_year"].to_list(), trend["pct"].to_list(),
                     marker="o", linewidth=2.5, markersize=6,
                     label=skill, color=colors[i % len(colors)])
    ax2.set_xlabel("Year")
    ax2.set_ylabel("% of Respondents")
    ax2.set_title(f"{tech_type} Trends Over Time")
    ax2.legend(fontsize=8, ncol=2)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(axis="y", alpha=0.3)
    st.pyplot(fig2)
    plt.close()

# ============================================================
# PAGE 4 — HR ANALYTICS
# ============================================================

elif page == "👥 HR Analytics":

    st.title("👥 HR Analytics Platform")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Developer Role Distribution")

        total_devs = filtered_df.filter(pl.col("dev_type").is_not_null()).shape[0]
        role_dist = (
            filtered_df
            .filter(pl.col("dev_type").is_not_null())
            .select("dev_type")
            .with_columns(pl.col("dev_type").str.split(";"))
            .explode("dev_type")
            .with_columns(pl.col("dev_type").str.strip_chars())
            .filter(pl.col("dev_type") != "")
            .group_by("dev_type")
            .agg(pl.len().alias("count"))
            .with_columns((pl.col("count") / total_devs * 100).round(1).alias("pct"))
            .sort("count", descending=True)
            .head(10)
        )

        fig, ax = plt.subplots(figsize=(8, 6))
        roles   = role_dist["dev_type"].to_list()[::-1]
        counts  = role_dist["pct"].to_list()[::-1]
        ax.barh(roles, counts, color="steelblue", edgecolor="white", height=0.6)
        for i, v in enumerate(counts):
            ax.text(v + 0.2, i, f"{v}%", va="center", fontsize=8)
        ax.set_xlabel("% of Developer Pool")
        ax.set_title("Top 10 Developer Roles")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        st.pyplot(fig)
        plt.close()

    with col2:
        st.subheader("Employment Type Distribution")

        employment_fix = {
            "Employed full-time"                                   : "Employed, full-time",
            "Employed part-time"                                   : "Employed, part-time",
            "Employed"                                             : "Employed, full-time",
            "Student"                                              : "Student, full-time",
            "Independent contractor, freelancer, or self-employed" : "Freelancer / Contractor",
            "Independent contractor, freelancer"                   : "Freelancer / Contractor",
            "Not employed, but looking for work"                   : "Not employed, looking",
            "Not employed, and not looking for work"               : "Not employed, not looking",
            "Not employed"                                         : "Not employed, looking",
        }

        total_emp = filtered_df.filter(pl.col("employment").is_not_null()).shape[0]
        emp_dist = (
            filtered_df
            .filter(pl.col("employment").is_not_null())
            .select("employment")
            .with_columns(pl.col("employment").str.split(";"))
            .explode("employment")
            .with_columns(pl.col("employment").str.strip_chars().replace(employment_fix))
            .filter(pl.col("employment") != "")
            .group_by("employment")
            .agg(pl.len().alias("count"))
            .with_columns((pl.col("count") / total_emp * 100).round(1).alias("pct"))
            .sort("count", descending=True)
        )

        fig2, ax2 = plt.subplots(figsize=(8, 6))
        emp_labels = emp_dist["employment"].to_list()
        emp_pcts   = emp_dist["pct"].to_list()
        ax2.pie(emp_pcts, labels=emp_labels, autopct="%1.1f%%",
                startangle=90, textprops={"fontsize": 8})
        ax2.set_title("Employment Type Breakdown")
        st.pyplot(fig2)
        plt.close()

    st.markdown("---")
    st.subheader("📈 Skill Growth vs Decline (2020 → 2025)")

    all_years = master_df["survey_year"].unique().to_list()
    if 2020 in all_years and 2025 in all_years:

        def get_growth(df, col, skill_col):
            total = df.filter(pl.col(col).is_not_null()).group_by("survey_year").agg(pl.len().alias("total"))
            counts = (
                df.filter(pl.col(col).is_not_null())
                .select(["survey_year", col])
                .with_columns(pl.col(col).str.split(";"))
                .explode(col)
                .with_columns(pl.col(col).str.strip_chars().alias(skill_col))
                .filter(pl.col(skill_col) != "")
                .group_by(["survey_year", skill_col])
                .agg(pl.len().alias("count"))
                .join(total, on="survey_year")
                .with_columns((pl.col("count") / pl.col("total") * 100).round(1).alias("pct"))
            )
            result = []
            for skill in counts[skill_col].unique().to_list():
                yearly = counts.filter(
                    (pl.col(skill_col) == skill) &
                    (pl.col("survey_year").is_in([2020, 2025]))
                ).sort("survey_year")
                if yearly.shape[0] == 2:
                    result.append({
                        "skill"  : skill,
                        "growth" : round(yearly["pct"][1] - yearly["pct"][0], 1)
                    })
            return pl.DataFrame(result)

        lang_g  = get_growth(master_df, "language_worked_with", "skill").with_columns(pl.lit("Language").alias("category"))
        db_g    = get_growth(master_df, "database_worked_with",  "skill").with_columns(pl.lit("Database").alias("category"))
        fw_g    = get_growth(master_df, "webframe_worked_with",  "skill").with_columns(pl.lit("Framework").alias("category"))

        all_g = pl.concat([lang_g, db_g, fw_g])

        top_grow = all_g.sort("growth", descending=True).head(8)
        top_decl = all_g.sort("growth", descending=False).head(8)

        cat_colors = {"Language": "#3498db", "Database": "#2ecc71", "Framework": "#e67e22"}

        col3, col4 = st.columns(2)

        with col3:
            st.markdown("**🚀 Fastest Growing**")
            fig3, ax3 = plt.subplots(figsize=(8, 5))
            s = top_grow["skill"].to_list()[::-1]
            g = top_grow["growth"].to_list()[::-1]
            c = [cat_colors.get(r, "#95a5a6") for r in top_grow["category"].to_list()[::-1]]
            ax3.barh(s, g, color=c, edgecolor="white", height=0.6)
            for i, v in enumerate(g):
                ax3.text(v + 0.1, i, f"+{v}%", va="center", fontsize=8, color="#27ae60")
            ax3.set_title("Top Growing Skills")
            ax3.spines["top"].set_visible(False)
            ax3.spines["right"].set_visible(False)
            st.pyplot(fig3)
            plt.close()

        with col4:
            st.markdown("**📉 Declining Skills**")
            fig4, ax4 = plt.subplots(figsize=(8, 5))
            s2 = top_decl["skill"].to_list()[::-1]
            g2 = [abs(v) for v in top_decl["growth"].to_list()[::-1]]
            c2 = [cat_colors.get(r, "#95a5a6") for r in top_decl["category"].to_list()[::-1]]
            ax4.barh(s2, g2, color=c2, edgecolor="white", height=0.6)
            for i, v in enumerate(top_decl["growth"].to_list()[::-1]):
                ax4.text(abs(v) + 0.1, i, f"{v}%", va="center", fontsize=8, color="#e74c3c")
            ax4.set_title("Top Declining Skills")
            ax4.spines["top"].set_visible(False)
            ax4.spines["right"].set_visible(False)
            st.pyplot(fig4)
            plt.close()

    else:
        st.info("Select years including both 2020 and 2025 to see growth analysis.")
