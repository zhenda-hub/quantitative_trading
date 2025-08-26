import streamlit as st
import pandas as pd
import numpy as np

st.title("📈 折线图 Demo - 10组数据")

# 生成 10 组随机数据
np.random.seed(42)  # 保证可复现
x = np.arange(1, 21)  # 20个点
data = {f"系列{i+1}": np.random.randint(10, 100, size=20) for i in range(10)}

df = pd.DataFrame(data, index=x)

st.subheader("原始数据表")
st.dataframe(df)

st.subheader("折线图展示")
st.line_chart(df, width=2000)   # 一次性展示10条线
