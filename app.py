import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("ecommerce_campaign_data.csv", parse_dates=["timestamp"])
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.title("Filters")
campaign = st.sidebar.multiselect("Campaign ID", df["campaign_id"].unique(), default=df["campaign_id"].unique())
device = st.sidebar.multiselect("Device Type", df["device_type"].unique(), default=df["device_type"].unique())
location = st.sidebar.multiselect("Location", df["location"].unique(), default=df["location"].unique())

df = df[df["campaign_id"].isin(campaign) & df["device_type"].isin(device) & df["location"].isin(location)]

# --- Title ---
st.markdown(
    "<h1 style='text-align: center;'>📊 Marketing Campaign Performance Dashboard</h1>",
    unsafe_allow_html=True
)

# --- KPIs ---
st.subheader("📌 Key Performance Indicators")

total_users = len(df)
clicked = df["clicked_ad"].sum()
purchased = df["purchased"].sum()
revenue = df["purchase_amount"].sum()

ctr = (clicked / total_users) * 100 if total_users else 0
conversion_rate = (purchased / total_users) * 100 if total_users else 0
aov = revenue / purchased if purchased else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Users", total_users)
col2.metric("CTR (%)", f"{ctr:.2f}")
col3.metric("Conversion Rate (%)", f"{conversion_rate:.2f}")
col4.metric("AOV ($)", f"{aov:.2f}")

with st.expander("ℹ️ KPI Definitions & Formulas"):
    st.markdown("""
    - **CTR (Click-Through Rate)**: `(Total Clicks / Total Users) × 100`
    - **Conversion Rate**: `(Total Purchases / Total Users) × 100`
    - **AOV (Average Order Value)**: `Total Revenue / Total Purchases`
    - **Total Users**: Total number of interactions/rows
    """)

# --- Funnel Analysis ---
st.subheader("🛒 Funnel Analysis")

funnel = {
    "Clicked Ad": df["clicked_ad"].sum(),
    "Viewed Product": (df["products_viewed"] > 0).sum(),
    "Added to Cart": (df["added_to_cart"] > 0).sum(),
    "Purchased": df["purchased"].sum()
}
funnel_df = pd.DataFrame(list(funnel.items()), columns=["Stage", "Users"])
funnel_fig = px.funnel(funnel_df, x="Users", y="Stage", title="User Funnel")
st.plotly_chart(funnel_fig)

with st.expander("ℹ️ Funnel Definitions"):
    st.markdown("""
    This tracks how users move through the buying process:
    - **Clicked Ad** → **Viewed Product** → **Added to Cart** → **Purchased**
    Helps identify where most users drop off.
    """)

# --- Time Series Analysis ---
st.subheader("📆 Time Series: Purchases Over Time")

df["date"] = df["timestamp"].dt.date
daily = df.groupby("date").agg(purchases=("purchased", "sum")).reset_index()
time_fig = px.line(daily, x="date", y="purchases", title="Daily Purchases")
st.plotly_chart(time_fig)

with st.expander("ℹ️ Time Series Insight"):
    st.markdown("""
    Shows **daily purchase behavior**. Useful to:
    - Detect spikes or dips
    - Align campaigns with high-performing days
    """)

# --- Campaign Performance Comparison ---
st.subheader("🎯 Campaign Performance Comparison")

campaign_perf = df.groupby("campaign_id").agg(
    users=("user_id", "count"),
    clicks=("clicked_ad", "sum"),
    purchases=("purchased", "sum"),
    revenue=("purchase_amount", "sum")
).reset_index()
campaign_perf["CTR (%)"] = campaign_perf["clicks"] / campaign_perf["users"] * 100
campaign_perf["Conversion Rate (%)"] = campaign_perf["purchases"] / campaign_perf["users"] * 100
campaign_perf["AOV"] = campaign_perf["revenue"] / campaign_perf["purchases"].replace(0, 1)

st.dataframe(campaign_perf)

with st.expander("ℹ️ Campaign Metric Definitions"):
    st.markdown("""
    - **Users**: Number of visitors targeted in each campaign.
    - **Clicks**: Number of ad clicks.
    - **Purchases**: Number of completed orders.
    - **Revenue**: Total sales amount per campaign.
    - **CTR (%)** = `(Clicks / Users) × 100`
    - **Conversion Rate (%)** = `(Purchases / Users) × 100`
    - **AOV** = `Revenue / Purchases`
    """)

# --- Campaign Highlights (Lollipop Charts) ---
def lollipop_chart(df, metric, title, color="#636EFA"):
    df_sorted = df.sort_values(metric, ascending=True)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_sorted[metric],
        y=df_sorted["campaign_id"],
        mode='markers+text',
        marker=dict(color=color, size=10),
        text=[f"{v:.2f}" for v in df_sorted[metric]],
        textposition="middle right",
        name=metric
    ))

    fig.add_trace(go.Scatter(
        x=df_sorted[metric],
        y=df_sorted["campaign_id"],
        mode='lines',
        line=dict(color=color, width=1),
        showlegend=False
    ))

    fig.update_layout(
        title=title,
        xaxis_title=metric,
        yaxis_title="Campaign ID",
        yaxis=dict(tickmode='linear'),
        height=400
    )
    return fig

st.subheader("🏆 Campaign Metrics Highlights")

st.plotly_chart(lollipop_chart(campaign_perf, "CTR (%)", "Click-Through Rate by Campaign"))
st.plotly_chart(lollipop_chart(campaign_perf, "Conversion Rate (%)", "Conversion Rate by Campaign", color="#00CC96"))
st.plotly_chart(lollipop_chart(campaign_perf, "users", "Number of Users by Campaign", color="#EF553B"))
st.plotly_chart(lollipop_chart(campaign_perf, "clicks", "Number of Clicks by Campaign", color="#AB63FA"))

with st.expander("ℹ️ Highlight Charts Explanation"):
    st.markdown("""
    These lollipop charts display the **top-performing campaigns** in:
    - CTR (%)
    - Conversion Rate (%)
    - Number of Users
    - Number of Clicks
    
    Lollipop charts are used instead of bars for cleaner ranking visuals.
    """)

# --- Location-Based Insights ---
st.subheader("📍 Top Performing Locations")

loc_df = df.groupby("location").agg(
    users=("user_id", "count"),
    purchases=("purchased", "sum")
).reset_index()
loc_df["Conversion Rate (%)"] = loc_df["purchases"] / loc_df["users"] * 100

top_n = 15
loc_df = loc_df.sort_values("Conversion Rate (%)", ascending=False).head(top_n)
loc_fig = px.bar(loc_df, x="location", y="Conversion Rate (%)", title="Top 15 Locations by Conversion Rate")
st.plotly_chart(loc_fig)

with st.expander("ℹ️ Location-Based Analysis"):
    st.markdown("""
    - Measures how different locations perform in terms of **conversion**
    - Formula: `Conversion Rate = (Purchases / Users) × 100`
    - Helps to allocate marketing budget effectively by region
    """)
