from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


st.set_page_config(page_title="Singapore Job Market Dashboard123", layout="wide")
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
with st.sidebar:
    st.header("Filters")
    category_options = sorted(job_categories["category_name"].dropna().unique())
    selected_categories = st.multiselect(
        "Category", category_options, default=category_options
    )

    employment_options = sorted(filtered_df["employmentTypes"].dropna().unique())
    selected_employment = st.selectbox("Employment Type", ["All"] + employment_options)

    open_only = st.checkbox("Show only open postings")

    min_exp = int(filtered_df["minimumYearsExperience"].min())
    max_exp = int(filtered_df["minimumYearsExperience"].max())
    experience_range = st.slider(
        "Minimum Years Experience", min_exp, max_exp, (min_exp, max_exp)
    )

    salary_range = st.sidebar.slider(
    "Salary Range",
    int(filtered_df["salary_minimum"].min()),
    int(filtered_df["salary_maximum"].max()),
    (
        int(filtered_df["salary_minimum"].min()),
        int(filtered_df["salary_maximum"].max())
    )
    )

    filtered_df = filtered_df[
    (filtered_df["salary_maximum"] >= salary_range[0]) &
    (filtered_df["salary_minimum"] <= salary_range[1])
    ]

st.metric(
    "Job Postings",
    f"{filtered_df['metadata_jobPostId'].nunique():,}"
)

filtered_df = filtered_df[filtered_df["category_names"].isin(selected_categories)]
if selected_employment != "All":
    filtered_df = filtered_df[filtered_df["employmentTypes"] == selected_employment]
if open_only:
    filtered_df = filtered_df[filtered_df["status_jobStatus"] == "Open"]
filtered_df = filtered_df[filtered_df["minimumYearsExperience"].between(*experience_range)]

st.header("Overview")

col1, col2, col3 = st.columns(3)
total_jobs = filtered_df['metadata_jobPostId'].nunique()
col1.metric("Total Job Postings", f"{total_jobs:,}")
print(filtered_df.info())
print(filtered_df.metadata_jobPostId.value_counts())

col2.metric(
    "Average Salary",
    f"${filtered_df['average_salary'].mean():,.0f}" if len(df) else "N/A",
)
col3.metric("Total Applications", int(df["metadata_totalNumberJobApplication"].sum()))

with st.expander("View raw data"):
    st.dataframe(filtered_df)

st.header("Trends & Breakdown")

postings_by_month = (
    filtered_df.groupby(df["metadata_newPostingDate"].dt.to_period("M")).size().rename("postings")
)
postings_by_month.index = postings_by_month.index.to_timestamp()

avg_salary_by_category = (
    filtered_df.groupby("category_names")["average_salary"].mean().sort_values(ascending=False)
)

#tab1, tab2, tab3 = st.tabs(["Trends", "Categories", "Salary"])
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Trends", "Salary", "Categories", "Categories wise Postings", "position Levels"])


with tab1:
    st.subheader("Postings Over Time")
    st.line_chart(postings_by_month)
    st.subheader("Cumulative Postings")
    st.area_chart(postings_by_month.cumsum())

with tab2:
    st.subheader("Experience vs Salary")
    st.scatter_chart(filtered_df, x="minimumYearsExperience", y="average_salary")

with tab3:
    st.subheader("Average Salary by Category")
    st.bar_chart(avg_salary_by_category)

#Create a horizontal bar chart of categories and count of  job postings
with tab4:
    st.subheader("Categories by Job Postings")
    category_counts = filtered_df.groupby("category_names").size()
    st.bar_chart(category_counts.sort_values(ascending=True), use_container_width=True)

with tab5:
    top_companies = filtered_df['positionLevels'].value_counts().head(5)
    # Extract the sizes (the counts) and labels (the company names) dynamically
    sizes = top_companies.values
    labels = top_companies.index

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    #st.subheader("Job Type Distribution")
    # 3. Display the chart in Streamlit
    st.pyplot(fig) 
