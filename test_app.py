from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

st.set_page_config(page_title="Singapore Job Market Dashboard", layout="wide")
@st.cache_data
def load_data():
    DATA_PATH = Path(__file__).resolve().parent
    df = pd.read_csv(
    DATA_PATH/"cleaned_jobs.csv",
    parse_dates=[
        "metadata_newPostingDate",
        "metadata_originalPostingDate",
        "metadata_expiryDate",
    ],
    )
    # Load category lookup table
    job_categories = pd.read_csv(
        DATA_PATH / "job_categories.csv"
    )
    return df, job_categories

df, job_categories = load_data()

st.title("Singapore Job Market Dashboard")
filtered_df = df.copy()

### Chart Display 

st.header("Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Job Postings", f"{len(filtered_df):,}")

col2.metric("Total Applications", int(df["metadata_totalNumberJobApplication"].sum()))

col3.metric(
    "Average Salary",
    f"${filtered_df['average_salary'].mean():,.0f}" if len(filtered_df) else "N/A",
)

with st.expander("View raw data (1000) rows"):
    st.dataframe(filtered_df.head(1000))

st.header("Trends & Breakdown")

### Function to calculate

tab1, tab2, tab3 = st.tabs(["Experience Requirements", "Salary", "Categories"])

with tab1:
    st.subheader("Experience Requirements")

    # ========================================
    # Prepare Data
    # ========================================

    # Convert experience to numeric
    df["minimumYearsExperience"] = pd.to_numeric(
        df["minimumYearsExperience"],
        errors="coerce"
    )

    # Remove missing values
    df = df.dropna(
        subset=[
            "category_names",
            "positionLevels",
            "minimumYearsExperience"
        ]
    )

    # Remove unrealistic values
    df = df[df["minimumYearsExperience"] <= 20]

    # ========================================
    # Create Experience Groups
    # ========================================

    def experience_group(years):
        if years <= 1:
            return "Entry Level (0–1 yrs)"
        elif years <= 5:
            return "Early Career (2–5 yrs)"
        else:
            return "Experienced (5+ yrs)"

    df["experience_group"] = df["minimumYearsExperience"].apply(experience_group)

    # ========================================
    # Top 5 sectors with the most entry-level jobs
    # ========================================

    entry_df = df[
        df["experience_group"] == "Entry Level (0–1 yrs)"
    ]

    top5_categories = (
        job_categories.groupby("category_name")
        .size()
        .sort_values(ascending=False)
        .head(5)
        .index
        .tolist()
    )

    # ========================================
    # Sidebar filter
    # ========================================

    all_categories = sorted(
        job_categories["category_name"].dropna().unique()
    )

    selected_categories = st.multiselect(
        "Select industries",
        options=all_categories,
        default=top5_categories
    )

    # ========================================
    # Filter the data
    # ========================================
    filtered = df[
        df["category_names"].isin(selected_categories)
    ].copy()

    filtered["job_count"] = 1

    # ========================================
    # Aggregate Data
    # ========================================
    sunburst = (
        filtered.groupby(
            [
                "category_names",
                "experience_group",
                "positionLevels",
            
            ],
            as_index=False
        )
        .agg(
            Job_Postings=("job_count", "sum"),
            Avg_Experience=("minimumYearsExperience", "mean")
        )
    )

    sunburst["Avg_Experience"] = (
        sunburst["Avg_Experience"]
        .round(1)
    )
    # ========================================
    # Create Sunburst
    # ========================================

    fig = px.sunburst(
        sunburst,
        path=[
            "category_names",
            "experience_group",
            "positionLevels"
        ],
        values="Job_Postings",
        color="Avg_Experience",
        color_continuous_scale="RdYlGn_r",
        hover_data={
            "Job_Postings": True,
            "Avg_Experience": ":.1f"
        },
        title="Explore Experience Requirements by Industry"
    )

    fig.update_layout(
        height=800
    )

    st.plotly_chart(
        fig,
        # width='stretch'
        use_container_width=True
    )

    # ========================================
    # Guidance
    # ========================================

    st.markdown("""
    ### How to read this chart

    - *Centre:* Career Sector
    - *Middle Ring:* Position Level
    - *Outer Ring:* Experience Requirement

    💡 Click on any sector or position level to drill down and explore the experience requirements.
    """)

with tab2:

    # 1. Subheader
    st.subheader("Experience vs Salary")

    # 2. Extract min & max bounds from the base DataFrame `df`
    min_exp = int(df["minimumYearsExperience"].min())
    max_exp = int(df["minimumYearsExperience"].max())

    min_sal = float(df["average_salary"].min())
    max_sal = float(df["average_salary"].max())

    # 3. Create side-by-side sliders on top of the chart
    col1, col2 = st.columns(2)

    with col1:
        exp_range = st.slider(
            "Filter Experience (Years)",
            min_value=min_exp,
            max_value=max_exp,
            value=(min_exp, max_exp),  # Defaults to full range
        )

    with col2:
        sal_range = st.slider(
            "Filter Salary ($)",
            min_value=min_sal,
            max_value=max_sal,
            value=(min_sal, max_sal),  # Defaults to full range
            step=1000.0,
        )

    # 4. Filter the dataframe based on slider selections
    filtered_df = df[
        (df["minimumYearsExperience"] >= exp_range[0])
        & (df["minimumYearsExperience"] <= exp_range[1])
        & (df["average_salary"] >= sal_range[0])
        & (df["average_salary"] <= sal_range[1])
    ]

    # Set data to filtered_df as required
    data = filtered_df

    # 5. Create explicit figure and axis objects
    fig, ax = plt.subplots(figsize=(12, 6))

    # Render Seaborn boxplot directly onto 'ax'
    sns.boxplot(
        data=data,
        x="minimumYearsExperience",
        y="average_salary",
        color="#6baed6",
        showfliers=False,  # Hide extreme outliers for a cleaner look
        ax=ax,  # Pass the Streamlit-compatible axis here
    )

    # Apply titles and labels to 'ax'
    ax.set_title(
        "Salary Distribution Across Experience Levels",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Minimum Years of Experience", fontsize=12)
    ax.set_ylabel("Average Salary ($)", fontsize=12)
    ax.yaxis.set_major_formatter("${x:,.0f}")
    ax.tick_params(axis="x", rotation=0)

    # Render in Streamlit
    st.pyplot(fig)

    # Free up memory after rendering (important for 1M rows)
    plt.close(fig)

#Create a horizontal bar chart of categories and count of  job postings
with tab3:
   
    st.subheader("📊 Job Postings by Category")

    # --- 1. Efficient Aggregation with Caching ---
    # Caching prevents re-running the 2M row groupby on every user interaction
    @st.cache_data
    def get_category_counts(job_categories):
        return (
            job_categories.groupby("category_name")["metadata_jobPostId"]
            .nunique()
            .reset_index(name="distinct_postings")
            .sort_values(by="distinct_postings", ascending=True)  # Ascending for horizontal bottom-to-top layout
        )

    # Run aggregation
    category_counts = get_category_counts(job_categories)

    # --- 2. Create Plotly Horizontal Bar Chart ---
    fig = px.bar(
        category_counts,
        x="distinct_postings",
        y="category_name",
        orientation="h",
        title="Distinct Job Postings by Category",
        labels={
            "distinct_postings": "Number of Distinct Job Postings",
            "category_name": "Category Name",
        },
        text_auto=",.0f",  # Displays formatted numbers on each bar
        color="distinct_postings",
        color_continuous_scale="Viridis",
    )

    # Adjust layout height so all 43 categories have room to breathe
    fig.update_layout(
        height=1100,  # Gives roughly ~25px per category
        coloraxis_showscale=False,  # Hide color bar legend
        margin=dict(l=20, r=20, t=50, b=50),
    )

    # --- 3. Render in Streamlit ---
    st.plotly_chart(fig, use_container_width=True)
