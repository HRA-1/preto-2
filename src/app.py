import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Preto Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Preto Dashboard")
st.markdown("---")

# Sample data
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total Users", value="1,234", delta="12%")

with col2:
    st.metric(label="Active Sessions", value="567", delta="-3%")

with col3:
    st.metric(label="Revenue", value="$12,345", delta="8%")

st.markdown("---")

# Sample chart
st.subheader("Sample Chart")
df = pd.DataFrame({
    "date": pd.date_range("2024-01-01", periods=30),
    "value": np.random.randn(30).cumsum()
})
fig = px.line(df, x="date", y="value", title="Trend Over Time")
st.plotly_chart(fig, use_container_width=True)
