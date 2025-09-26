from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash

from loguru import logger


dash.register_page(__name__)


reits_dir = Path('datas/raw/reits')
reits_files = list(reits_dir.glob('reits_realtime_em_*.csv'))


# 获取REITs历史数据文件
def get_reits_hist_files():
    """获取所有REITs历史数据文件"""
    reits_dir = Path('datas/raw/reits')
    hist_files = list(reits_dir.glob('reits_hist_em_*.csv'))
    return hist_files


# 分析REITs数据
def analyze_reits_data(df):
    """分析REITs数据，返回统计信息"""
    if df.empty:
        return {
            'total_reits': 0,
            'rising_reits': 0,
            'falling_reits': 0,
            'flat_reits': 0,
            'avg_change': 0,
            'max_rise': 0,
            'max_fall': 0,
            'total_volume': 0,
            'avg_volume': 0
        }
    
    # 确保数据类型正确
    df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
    df['成交量'] = pd.to_numeric(df['成交量'], errors='coerce')
    
    # 基本统计
    total_reits = len(df)
    rising_reits = len(df[df['涨跌幅'] > 0])
    falling_reits = len(df[df['涨跌幅'] < 0])
    flat_reits = len(df[df['涨跌幅'] == 0])
    
    # 涨跌幅统计
    avg_change = df['涨跌幅'].mean()
    max_rise = df['涨跌幅'].max()
    max_fall = df['涨跌幅'].min()
    
    # 成交量统计
    total_volume = df['成交量'].sum()
    avg_volume = df['成交量'].mean()
    
    analysis = {
        'total_reits': total_reits,
        'rising_reits': rising_reits,
        'falling_reits': falling_reits,
        'flat_reits': flat_reits,
        'avg_change': avg_change,
        'max_rise': max_rise,
        'max_fall': max_fall,
        'total_volume': total_volume,
        'avg_volume': avg_volume
    }
    
    return analysis

# 获取REITs分类
def get_reits_categories(df):
    """根据REITs名称分类"""
    categories = {
        '物流仓储': ['物流', '仓储'],
        '产业园区': ['产业园', '科创', '智造', '产园'],
        '商业地产': ['商业', '奥莱', '消费', '商场'],
        '基础设施': ['高速', '公路', '水利', '能源', '光伏', '清洁能源', '数据中心'],
        '租赁住房': ['租赁', '住房', '安居', '保租房'],
        '其他': []
    }
    
    category_counts = {category: 0 for category in categories.keys()}
    
    for name in df['名称']:
        matched = False
        for category, keywords in categories.items():
            if any(keyword in name for keyword in keywords):
                category_counts[category] += 1
                matched = True
                break
        if not matched:
            category_counts['其他'] += 1
    
    return category_counts


# 处理实时整体数据
df_reits = pd.read_csv('datas/raw/reits/reits_realtime_em.csv')
analysis = analyze_reits_data(df_reits)
category_counts = get_reits_categories(df_reits)

# 获取最新的数据文件用于显示更新时间
latest_file = max(reits_files, key=lambda x: x.stat().st_mtime) if reits_files else None

# 绘制整体的历史数据图
fig = go.Figure()
for hist_file in get_reits_hist_files():
    try:
        df = pd.read_csv(hist_file)
        # 从文件名中提取REITs名称
        reits_name = hist_file.stem.replace('reits_hist_em_', '')
        
        # 确保数据包含必要的列
        if '日期' in df.columns and '今开' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['日期'], 
                y=df['今开'],
                mode='lines',
                name=reits_name,
                hovertemplate=(
                    'REITs: ' + reits_name + 
                    '<br>日期: %{x}<br>开盘价: %{y:.2f}<extra></extra>'
                )
            ))
    except Exception as e:
        logger.warning(f"读取文件 {hist_file} 失败: {e}")

fig.update_layout(
    title='REITs历史价格走势',
    xaxis_title='日期',
    yaxis_title='开盘价',
    legend_title='REITs名称',
    height=1000,
    template='plotly_white'
)
fig.update_xaxes(
    rangeslider_visible=True,  # 添加滑动块
    minor=dict(ticks="inside", showgrid=True),  # 辅助刻度
    # 范围选择器按钮
    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1month", step="month", stepmode="backward"),
            dict(count=6, label="6month", step="month", stepmode="backward"),
            dict(count=1, label="1year", step="year", stepmode="backward"),
            dict(count=3, label="3year", step="year", stepmode="backward"),
            dict(count=5, label="5year", step="year", stepmode="backward"),
            dict(count=10, label="10year", step="year", stepmode="backward"),
            dict(count=20, label="20year", step="year", stepmode="backward"),
            dict(step="all")
        ])
    )
)


# 创建布局
layout = dbc.Container([
    # 页面标题
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1(
                    '🏢 REITs市场分析',
                    className='text-center mb-3',
                    style={'color': '#2E86AB', 'fontWeight': 'bold'}
                ),
                html.P(
                    '房地产投资信托基金(REITs)实时数据与分析',
                    className='text-center text-muted lead mb-4'
                )
            ], className='py-4', style={'backgroundColor': '#f8f9fa'})
        ], width=12)
    ]),
    
    # 数据概览卡片
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader('📊 REITs市场概览'),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H5('市场统计', className='text-primary'),
                                html.Div([
                                    html.Span('总数量: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('total_reits', 0)}", className='text-info')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('上涨: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('rising_reits', 0)}", className='text-success')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('下跌: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('falling_reits', 0)}", className='text-danger')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('平盘: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('flat_reits', 0)}", className='text-warning')
                                ])
                            ])
                        ], md=4),
                        dbc.Col([
                            html.Div([
                                html.H5('涨跌幅统计', className='text-info'),
                                html.Div([
                                    html.Span('平均涨跌: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('avg_change', 0):.2f}%", 
                                             className='text-success' if analysis.get('avg_change', 0) > 0 else 'text-danger')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('最大涨幅: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('max_rise', 0):.2f}%", className='text-success')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('最大跌幅: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('max_fall', 0):.2f}%", className='text-danger')
                                ])
                            ])
                        ], md=4),
                        dbc.Col([
                            html.Div([
                                html.H5('成交量统计', className='text-warning'),
                                html.Div([
                                    html.Span('总成交量: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('total_volume', 0):,.0f}", className='text-info')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('平均成交量: ', className='fw-bold'),
                                    html.Span(f"{analysis.get('avg_volume', 0):,.0f}", className='text-info')
                                ])
                            ])
                        ], md=4)
                    ])
                ])
            ], className='border-0 shadow-sm mb-4')
        ], width=12)
    ]),
    
    # REITs分类统计
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader('📈 REITs分类统计'),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H6(category, className='text-center'),
                                html.H4(count, className='text-center text-primary mb-0'),
                                html.Small(f'{count/analysis.get("total_reits", 1)*100:.1f}%', 
                                         className='text-muted d-block text-center')
                            ])
                        ], md=2) for category, count in category_counts.items()
                    ])
                ])
            ], className='border-0 shadow-sm mb-4')
        ], width=12)
    ]),
    
    # REITs图表
    dcc.Graph(figure=fig,),
    
    # 数据更新时间
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Small(f'数据更新时间: {latest_file.stem.split("_")[-1] if latest_file else "未知"}', 
                         className='text-muted')
            ], className='text-center mt-3')
        ], width=12)
    ])
    
], fluid=True, className='py-4', style={'backgroundColor': '#f8f9fa'})
