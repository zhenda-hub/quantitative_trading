import streamlit as st
import plotly.express as px

# 准备数据和图表
df = px.data.iris()
fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")

# 显示
st.title("Iris Dataset Visualization")
st.plotly_chart(fig, use_container_width=True)
