import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(
    page_title="IELTS Student Score Dashboard",
    page_icon="📊",
    layout="wide",
)

# =========================================================
# DATA
# =========================================================
# Current year (from your latest corrected table)
CURRENT_YEAR = 2026
CURRENT_YEAR_DATA = [
    {"Year": CURRENT_YEAR, "Month": "January",  "8.5": 0, "8.0": 12, "7.5": 29, "7.0": 47, "6.5": 31, "6.0": 27, "5.5": 10},
    {"Year": CURRENT_YEAR, "Month": "February", "8.5": 1, "8.0": 8,  "7.5": 41, "7.0": 60, "6.5": 66, "6.0": 38, "5.5": 17},
    {"Year": CURRENT_YEAR, "Month": "March",    "8.5": 0, "8.0": 12, "7.5": 55, "7.0": 91, "6.5": 78, "6.0": 69, "5.5": 26},
    {"Year": CURRENT_YEAR, "Month": "April",    "8.5": 0, "8.0": 5,  "7.5": 24, "7.0": 40, "6.5": 34, "6.0": 34, "5.5": 10},
]

# Previous year (from your new image)
PREVIOUS_YEAR = 2025
PREVIOUS_YEAR_DATA = [
    {"Year": PREVIOUS_YEAR, "Month": "January",  "8.5": 0, "8.0": 0, "7.5": 0,  "7.0": 0,  "6.5": 0,  "6.0": 0,  "5.5": 0},
    {"Year": PREVIOUS_YEAR, "Month": "February", "8.5": 0, "8.0": 3, "7.5": 25, "7.0": 27, "6.5": 30, "6.0": 21, "5.5": 16},
    {"Year": PREVIOUS_YEAR, "Month": "March",    "8.5": 0, "8.0": 6, "7.5": 41, "7.0": 67, "6.5": 58, "6.0": 55, "5.5": 27},
    {"Year": PREVIOUS_YEAR, "Month": "April",    "8.5": 0, "8.0": 2, "7.5": 8,  "7.0": 16, "6.5": 11, "6.0": 13, "5.5": 6},
]

MONTH_ORDER = ["January", "February", "March", "April"]
SCORE_ORDER = [8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5]


# =========================================================
# HELPERS
# =========================================================
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.DataFrame(PREVIOUS_YEAR_DATA + CURRENT_YEAR_DATA)
    return df


def reshape_data(df: pd.DataFrame) -> pd.DataFrame:
    long_df = df.melt(
        id_vars=["Year", "Month"],
        var_name="Score",
        value_name="Students"
    )
    long_df["Score"] = pd.to_numeric(long_df["Score"], errors="coerce")
    long_df["Students"] = pd.to_numeric(long_df["Students"], errors="coerce").fillna(0).astype(int)
    long_df["Month"] = pd.Categorical(long_df["Month"], categories=MONTH_ORDER, ordered=True)
    long_df = long_df.sort_values(["Year", "Month", "Score"], ascending=[True, True, False])
    return long_df


def calculate_kpis(df_long: pd.DataFrame) -> dict:
    total_students = int(df_long["Students"].sum())

    weighted_avg = 0.0
    if total_students > 0:
        weighted_avg = (df_long["Score"] * df_long["Students"]).sum() / total_students

    score_totals = (
        df_long.groupby("Score", as_index=False)["Students"]
        .sum()
        .sort_values("Students", ascending=False)
    )

    month_year_totals = (
        df_long.groupby(["Year", "Month"], as_index=False)["Students"]
        .sum()
        .sort_values("Students", ascending=False)
    )

    top_band = score_totals.iloc[0]["Score"] if not score_totals.empty else "-"
    peak_period = "-"
    if not month_year_totals.empty:
        peak_period = f"{month_year_totals.iloc[0]['Month']} {month_year_totals.iloc[0]['Year']}"

    return {
        "total_students": total_students,
        "weighted_avg": round(weighted_avg, 2),
        "top_band": top_band,
        "peak_period": peak_period,
    }


def calculate_year_summary(df_long: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df_long.groupby("Year")
        .apply(
            lambda x: pd.Series({
                "Total Students": int(x["Students"].sum()),
                "Average IELTS": round((x["Score"] * x["Students"]).sum() / x["Students"].sum(), 2)
                if x["Students"].sum() > 0 else 0
            })
        )
        .reset_index()
    )
    return summary


def build_year_comparison_chart(df_long: pd.DataFrame) -> go.Figure:
    year_month_totals = (
        df_long.groupby(["Year", "Month"], as_index=False)["Students"]
        .sum()
        .sort_values(["Year", "Month"])
    )

    fig = px.bar(
        year_month_totals,
        x="Month",
        y="Students",
        color="Year",
        barmode="group",
        title="Monthly Student Count Comparison by Year"
    )
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def build_average_score_comparison(df_long: pd.DataFrame) -> go.Figure:
    avg_by_year_month = (
        df_long.groupby(["Year", "Month"])
        .apply(
            lambda x: (x["Score"] * x["Students"]).sum() / x["Students"].sum()
            if x["Students"].sum() > 0 else 0
        )
        .reset_index(name="AverageScore")
        .sort_values(["Year", "Month"])
    )

    fig = px.line(
        avg_by_year_month,
        x="Month",
        y="AverageScore",
        color="Year",
        markers=True,
        title="Average IELTS Score by Month and Year"
    )
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def build_distribution_by_year(df_long: pd.DataFrame) -> go.Figure:
    totals = (
        df_long.groupby(["Year", "Score"], as_index=False)["Students"]
        .sum()
        .sort_values(["Year", "Score"], ascending=[True, False])
    )

    fig = px.bar(
        totals,
        x="Score",
        y="Students",
        color="Year",
        barmode="group",
        title="Overall IELTS Band Distribution by Year"
    )
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def build_monthly_band_trend(df_long: pd.DataFrame) -> go.Figure:
    df_long = df_long.copy()
    df_long["Period"] = df_long["Month"].astype(str) + " " + df_long["Year"].astype(str)

    fig = px.line(
        df_long,
        x="Score",
        y="Students",
        color="Period",
        markers=True,
        title="IELTS Band Trend by Month-Year"
    )
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def build_heatmap_for_year(df_long: pd.DataFrame, selected_year: int) -> go.Figure:
    year_df = (
        df_long[df_long["Year"] == selected_year]
        .pivot_table(
            index="Month",
            columns="Score",
            values="Students",
            aggfunc="sum",
            fill_value=0
        )
        .reindex(MONTH_ORDER)
    )

    # ensure score order
    existing_cols = [c for c in SCORE_ORDER if c in year_df.columns.tolist()]
    year_df = year_df[existing_cols]

    fig = px.imshow(
        year_df,
        text_auto=True,
        aspect="auto",
        title=f"Heatmap: Month vs IELTS Band ({selected_year})"
    )
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def build_score_table_by_year(df_long: pd.DataFrame) -> pd.DataFrame:
    table = (
        df_long.groupby(["Year", "Score"], as_index=False)["Students"]
        .sum()
        .pivot(index="Score", columns="Year", values="Students")
        .fillna(0)
        .sort_index(ascending=False)
    )
    return table


def generate_insights(df_long: pd.DataFrame) -> list[str]:
    insights = []

    year_summary = calculate_year_summary(df_long)
    if len(year_summary) >= 2:
        year_summary = year_summary.sort_values("Year")
        prev_row = year_summary.iloc[0]
        curr_row = year_summary.iloc[-1]

        diff_students = int(curr_row["Total Students"] - prev_row["Total Students"])
        diff_avg = round(curr_row["Average IELTS"] - prev_row["Average IELTS"], 2)

        insights.append(
            f"Total students changed from {int(prev_row['Total Students'])} in {int(prev_row['Year'])} "
            f"to {int(curr_row['Total Students'])} in {int(curr_row['Year'])}, a difference of {diff_students}."
        )
        insights.append(
            f"Average IELTS changed from {prev_row['Average IELTS']} in {int(prev_row['Year'])} "
            f"to {curr_row['Average IELTS']} in {int(curr_row['Year'])}, a difference of {diff_avg}."
        )

    band_totals = (
        df_long.groupby("Score", as_index=False)["Students"]
        .sum()
        .sort_values("Students", ascending=False)
    )
    if not band_totals.empty:
        top = band_totals.iloc[0]
        insights.append(f"The most common IELTS band across selected data is {top['Score']} with {int(top['Students'])} students.")

    period_totals = (
        df_long.groupby(["Year", "Month"], as_index=False)["Students"]
        .sum()
        .sort_values("Students", ascending=False)
    )
    if not period_totals.empty:
        top_period = period_totals.iloc[0]
        insights.append(f"The highest monthly volume is {top_period['Month']} {int(top_period['Year'])} with {int(top_period['Students'])} students.")

    return insights


# =========================================================
# STYLE
# =========================================================
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# LOAD
# =========================================================
df = load_data()
df_long = reshape_data(df)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("Filters")

year_options = sorted(df_long["Year"].unique().tolist())
selected_years = st.sidebar.multiselect(
    "Select Years",
    options=year_options,
    default=year_options
)

selected_months = st.sidebar.multiselect(
    "Select Months",
    options=MONTH_ORDER,
    default=MONTH_ORDER
)

selected_scores = st.sidebar.multiselect(
    "Select IELTS Bands",
    options=SCORE_ORDER,
    default=SCORE_ORDER
)

filtered_long = df_long[
    (df_long["Year"].isin(selected_years)) &
    (df_long["Month"].isin(selected_months)) &
    (df_long["Score"].isin(selected_scores))
].copy()

if filtered_long.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# =========================================================
# HEADER
# =========================================================
st.title("📊 IELTS Student Score Dashboard")
st.caption("Comparison of current year and previous year based on manually entered table data")

# =========================================================
# KPI CARDS
# =========================================================
kpis = calculate_kpis(filtered_long)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Students", kpis["total_students"])
c2.metric("Weighted Avg IELTS", kpis["weighted_avg"])
c3.metric("Most Common Band", kpis["top_band"])
c4.metric("Peak Period", kpis["peak_period"])

# =========================================================
# YEAR SUMMARY
# =========================================================
st.subheader("Year Summary")
summary_df = calculate_year_summary(filtered_long)
st.dataframe(summary_df, use_container_width=True)

# =========================================================
# CHARTS
# =========================================================
row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.plotly_chart(build_year_comparison_chart(filtered_long), use_container_width=True)

with row1_col2:
    st.plotly_chart(build_average_score_comparison(filtered_long), use_container_width=True)

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.plotly_chart(build_distribution_by_year(filtered_long), use_container_width=True)

with row2_col2:
    st.plotly_chart(build_monthly_band_trend(filtered_long), use_container_width=True)

# =========================================================
# HEATMAPS
# =========================================================
st.subheader("Heatmaps by Year")
heatmap_cols = st.columns(max(1, len(selected_years)))
for idx, year in enumerate(selected_years):
    with heatmap_cols[idx]:
        st.plotly_chart(build_heatmap_for_year(filtered_long, year), use_container_width=True)

# =========================================================
# INSIGHTS
# =========================================================
st.subheader("Executive Insights")
for item in generate_insights(filtered_long):
    st.info(item)

# =========================================================
# DETAIL TABLES
# =========================================================
st.subheader("Score Comparison Table")
score_compare_df = build_score_table_by_year(filtered_long)
st.dataframe(score_compare_df, use_container_width=True)

with st.expander("Show source table"):
    st.dataframe(df, use_container_width=True)

with st.expander("Show transformed long-format data"):
    st.dataframe(filtered_long, use_container_width=True)
