import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="IELTS Student Score Dashboard 2026",
    page_icon="📊",
    layout="wide",
)

# =========================================================
# STATIC DATA FROM IMAGE
# Empty cells were treated as 0
# =========================================================
RAW_DATA = [
    {"Month": "January",  "8.5": 0, "8.0": 12, "7.5": 29, "7.0": 47, "6.5": 31, "6.0": 27, "5.5": 10},
    {"Month": "February", "8.5": 1, "8.0": 8,  "7.5": 41, "7.0": 60, "6.5": 66, "6.0": 38, "5.5": 17},
    {"Month": "March",    "8.5": 0, "8.0": 12, "7.5": 55,  "7.0": 91, "6.5": 78, "6.0": 69, "5.5": 26},
    {"Month": "April",    "8.5": 0, "8.0": 5,  "7.5": 24, "7.0": 40, "6.5": 34, "6.0": 34, "5.5": 10},
]

MONTH_ORDER = ["January", "February", "March", "April"]


# =========================================================
# HELPERS
# =========================================================
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.DataFrame(RAW_DATA)
    return df


def reshape_data(df: pd.DataFrame) -> pd.DataFrame:
    long_df = df.melt(
        id_vars="Month",
        var_name="Score",
        value_name="Students"
    )
    long_df["Score"] = long_df["Score"].astype(float)
    long_df["Students"] = pd.to_numeric(long_df["Students"], errors="coerce").fillna(0).astype(int)
    long_df["Month"] = pd.Categorical(long_df["Month"], categories=MONTH_ORDER, ordered=True)
    long_df = long_df.sort_values(["Month", "Score"], ascending=[True, False])
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

    month_totals = (
        df_long.groupby("Month", as_index=False)["Students"]
        .sum()
        .sort_values("Students", ascending=False)
    )

    top_band = score_totals.iloc[0]["Score"] if not score_totals.empty else "-"
    peak_month = month_totals.iloc[0]["Month"] if not month_totals.empty else "-"

    return {
        "total_students": total_students,
        "weighted_avg": round(weighted_avg, 2),
        "top_band": top_band,
        "peak_month": peak_month,
    }


def build_mixed_chart(df_long: pd.DataFrame) -> go.Figure:
    month_totals = (
        df_long.groupby("Month", as_index=False)["Students"]
        .sum()
        .sort_values("Month")
    )

    avg_by_month = (
        df_long.groupby("Month")
        .apply(
            lambda x: (x["Score"] * x["Students"]).sum() / x["Students"].sum()
            if x["Students"].sum() > 0 else 0
        )
        .reset_index(name="AverageScore")
        .sort_values("Month")
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=month_totals["Month"],
            y=month_totals["Students"],
            name="Total Students",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=avg_by_month["Month"],
            y=avg_by_month["AverageScore"],
            mode="lines+markers",
            name="Average IELTS Score",
            yaxis="y2",
        )
    )

    fig.update_layout(
        title="Monthly Student Count and Average IELTS Score",
        yaxis=dict(title="Students"),
        yaxis2=dict(
            title="Average IELTS",
            overlaying="y",
            side="right",
        ),
        legend=dict(orientation="h", y=1.1, x=0),
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def build_score_distribution(df_long: pd.DataFrame) -> go.Figure:
    totals = (
        df_long.groupby("Score", as_index=False)["Students"]
        .sum()
        .sort_values("Score", ascending=False)
    )

    fig = px.bar(
        totals,
        x="Score",
        y="Students",
        text="Students",
        title="Overall IELTS Score Distribution"
    )
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def build_monthly_trend(df_long: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df_long,
        x="Score",
        y="Students",
        color="Month",
        markers=True,
        title="Monthly Trend by IELTS Band"
    )
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def build_heatmap(df: pd.DataFrame) -> go.Figure:
    score_cols = [c for c in df.columns if c != "Month"]
    heat_df = df.set_index("Month")[score_cols]

    fig = px.imshow(
        heat_df,
        text_auto=True,
        aspect="auto",
        title="Heatmap: Month vs IELTS Band"
    )
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def build_grouped_histogram(df_long: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df_long,
        x="Score",
        y="Students",
        color="Month",
        barmode="group",
        title="Histogram / Grouped Distribution by Month"
    )
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def generate_insights(df_long: pd.DataFrame) -> list[str]:
    insights = []

    score_totals = (
        df_long.groupby("Score", as_index=False)["Students"]
        .sum()
        .sort_values("Students", ascending=False)
    )

    month_totals = (
        df_long.groupby("Month", as_index=False)["Students"]
        .sum()
        .sort_values("Students", ascending=False)
    )

    if not score_totals.empty:
        top = score_totals.iloc[0]
        insights.append(f"The most common IELTS band is {top['Score']} with {int(top['Students'])} students.")

    if not month_totals.empty:
        peak = month_totals.iloc[0]
        insights.append(f"The highest total student volume is in {peak['Month']} with {int(peak['Students'])} students.")

    total_students = df_long["Students"].sum()
    high_band_students = df_long[df_long["Score"] >= 7.0]["Students"].sum()
    if total_students > 0:
        share = round((high_band_students / total_students) * 100, 1)
        insights.append(f"{share}% of students are in IELTS band 7.0 or above.")

    return insights


# =========================================================
# STYLES
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
# LOAD DATA
# =========================================================
df = load_data()
df_long = reshape_data(df)


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("Filters")

selected_months = st.sidebar.multiselect(
    "Select Months",
    options=MONTH_ORDER,
    default=MONTH_ORDER,
)

score_options = sorted(df_long["Score"].unique(), reverse=True)
selected_scores = st.sidebar.multiselect(
    "Select IELTS Bands",
    options=score_options,
    default=score_options,
)

filtered_long = df_long[
    (df_long["Month"].isin(selected_months)) &
    (df_long["Score"].isin(selected_scores))
].copy()

if filtered_long.empty:
    st.warning("No data available for selected filters.")
    st.stop()

filtered_wide = (
    filtered_long.pivot_table(
        index="Month",
        columns="Score",
        values="Students",
        aggfunc="sum",
        fill_value=0
    )
    .reset_index()
)


# =========================================================
# HEADER
# =========================================================
st.title("📊 IELTS Student Score Dashboard")
st.caption("Static dashboard built directly from the table image data")


# =========================================================
# KPIs
# =========================================================
kpis = calculate_kpis(filtered_long)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Students", kpis["total_students"])
c2.metric("Weighted Avg IELTS", kpis["weighted_avg"])
c3.metric("Most Common Band", kpis["top_band"])
c4.metric("Peak Month", kpis["peak_month"])


# =========================================================
# CHARTS
# =========================================================
row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.plotly_chart(build_mixed_chart(filtered_long), use_container_width=True)

with row1_col2:
    st.plotly_chart(build_grouped_histogram(filtered_long), use_container_width=True)

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.plotly_chart(build_monthly_trend(filtered_long), use_container_width=True)

with row2_col2:
    st.plotly_chart(build_score_distribution(filtered_long), use_container_width=True)

st.plotly_chart(build_heatmap(filtered_wide), use_container_width=True)


# =========================================================
# INSIGHTS
# =========================================================
st.subheader("Executive Insights")
for item in generate_insights(filtered_long):
    st.info(item)


# =========================================================
# DATA TABLES
# =========================================================
with st.expander("Show Source Table"):
    st.dataframe(df, use_container_width=True)

with st.expander("Show Long Format Data"):
    st.dataframe(filtered_long, use_container_width=True)
