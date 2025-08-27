import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# 设置页面配置
st.set_page_config(
    page_title="全球经济指数走势",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 缓存数据加载函数
@st.cache_data
def load_data():
    """加载CSV数据"""
    try:
        df = pd.read_csv("datas/indexes/all_indexes_data_usd2.csv")
        # 确保date列是datetime类型
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        # 如果文件不存在，创建示例数据
        st.error("数据文件未找到，使用示例数据")
        dates = pd.date_range('2020-01-01', '2024-01-01', freq='D')
        import numpy as np
        np.random.seed(42)
        
        data = {
            'date': dates,
            'SP500': 3000 + np.cumsum(np.random.randn(len(dates)) * 10),
            'NASDAQ': 9000 + np.cumsum(np.random.randn(len(dates)) * 30),
            'DJI': 25000 + np.cumsum(np.random.randn(len(dates)) * 50),
            'Gold': 1500 + np.cumsum(np.random.randn(len(dates)) * 5),
        }
        return pd.DataFrame(data)

# 创建图表的函数
@st.cache_data
def create_chart(df, selected_columns, chart_height=800):
    """创建Plotly图表"""
    fig = px.line(
        df,
        x="date",
        y=selected_columns,
        hover_data={"date": "|%B %d, %Y"},
        title='全球经济指数走势图',
        color_discrete_sequence=px.colors.qualitative.Dark24,
    )
    
    fig.update_layout(
        height=chart_height,
        yaxis_title='USD(美元)',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 更新X轴设置
    fig.update_xaxes(
        rangeslider_visible=True,  # 添加滑动块
        minor=dict(ticks="inside", showgrid=True),  # 辅助刻度
        # 范围选择器按钮
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1个月", step="month", stepmode="backward"),
                dict(count=6, label="6个月", step="month", stepmode="backward"),
                dict(count=1, label="1年", step="year", stepmode="backward"),
                dict(count=3, label="3年", step="year", stepmode="backward"),
                dict(count=5, label="5年", step="year", stepmode="backward"),
                dict(count=10, label="10年", step="year", stepmode="backward"),
                dict(count=20, label="20年", step="year", stepmode="backward"),
                dict(step="all", label="全部")
            ])
        )
    )
    
    return fig

def main():
    # 页面标题
    st.title("📈 全球经济指数分析")
    st.markdown("### 关注变化趋势，而不是绝对价格")
    
    # 加载数据
    df = load_data()
    
    # 侧边栏控制
    st.sidebar.header("图表控制")
    
    # 获取数值列（排除date列）
    numeric_columns = [col for col in df.columns if col != 'date']
    
    # 多选框选择要显示的指数
    selected_columns = st.sidebar.multiselect(
        "选择要显示的经济指数:",
        options=numeric_columns,
        default=numeric_columns[:4] if len(numeric_columns) > 4 else numeric_columns,
        help="选择要在图表中显示的经济指数"
    )
    
    if not selected_columns:
        st.warning("请至少选择一个经济指数进行显示")
        return
    
    # 图表高度调节
    chart_height = st.sidebar.slider(
        "图表高度 (像素):",
        min_value=400,
        max_value=1200,
        value=800,
        step=50,
        help="调整图表显示高度"
    )
    
    # 显示范围滑块选项
    show_rangeslider = st.sidebar.checkbox(
        "显示时间范围滑块",
        value=True,
        help="是否显示图表底部的时间范围滑块"
    )
    
    # 数据信息
    with st.sidebar.expander("数据信息"):
        st.write(f"数据记录数: {len(df)}")
        st.write(f"时间范围: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
        st.write(f"可用指数: {len(numeric_columns)} 个")
    
    # 主要内容区域
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # 创建并显示图表
        fig = create_chart(df, selected_columns, chart_height)
        
        # 如果用户取消了范围滑块，更新图表
        if not show_rangeslider:
            fig.update_xaxes(rangeslider_visible=False)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 数据统计")
        
        # 显示最新数据
        if not df.empty:
            latest_data = df.iloc[-1]
            st.write("**最新数据** (", latest_data['date'].strftime('%Y-%m-%d'), ")")
            
            for col in selected_columns:
                if col in latest_data:
                    st.metric(
                        label=col,
                        value=f"${latest_data[col]:,.2f}",
                        delta=f"{((latest_data[col] / df.iloc[-30][col]) - 1) * 100:.2f}%" if len(df) > 30 else None
                    )
    
    # 数据表格展示（可选）
    with st.expander("📋 查看原始数据"):
        # 数据筛选选项
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期:",
                value=df['date'].max() - pd.Timedelta(days=365),
                min_value=df['date'].min().date(),
                max_value=df['date'].max().date()
            )
        with col2:
            end_date = st.date_input(
                "结束日期:",
                value=df['date'].max(),
                min_value=df['date'].min().date(),
                max_value=df['date'].max().date()
            )
        
        # 筛选数据
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        filtered_df = df[mask]
        
        # 显示筛选后的数据
        display_columns = ['date'] + selected_columns
        st.dataframe(
            filtered_df[display_columns].sort_values('date', ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        # 下载按钮
        csv = filtered_df[display_columns].to_csv(index=False)
        st.download_button(
            label="💾 下载筛选数据 (CSV)",
            data=csv,
            file_name=f'economic_indexes_{start_date}_to_{end_date}.csv',
            mime='text/csv'
        )
    
    # 分析洞察（可选功能）
    with st.expander("💡 数据分析洞察"):
        if len(selected_columns) >= 2:
            st.subheader("相关性分析")
            correlation_matrix = df[selected_columns].corr()
            
            # 使用Plotly创建相关性热力图
            fig_corr = px.imshow(
                correlation_matrix,
                text_auto=True,
                aspect="auto",
                title="经济指数相关性热力图",
                color_continuous_scale="RdYlBu"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # 显示最高和最低相关性
            corr_pairs = []
            for i in range(len(selected_columns)):
                for j in range(i+1, len(selected_columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    corr_pairs.append((selected_columns[i], selected_columns[j], corr_value))
            
            corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            
            if corr_pairs:
                st.write("**相关性排名:**")
                for pair in corr_pairs[:3]:  # 显示前3个相关性
                    correlation_strength = "强" if abs(pair[2]) > 0.7 else "中" if abs(pair[2]) > 0.4 else "弱"
                    correlation_direction = "正" if pair[2] > 0 else "负"
                    st.write(f"- {pair[0]} vs {pair[1]}: {pair[2]:.3f} ({correlation_direction}相关, {correlation_strength})")

if __name__ == "__main__":
    main()