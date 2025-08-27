"""
指数基金投资策略模块

包含以下策略：
1. 定投策略
2. 估值策略
3. 趋势跟踪策略
4. 大小盘轮动策略
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger


class IndexStrategy(Enum):
    """指数投资策略类型"""
    REGULAR_INVEST = "regular_invest"      # 定投策略
    VALUATION = "valuation"                # 估值策略
    TREND_FOLLOWING = "trend_following"    # 趋势跟踪
    ROTATION = "rotation"                  # 大小盘轮动


@dataclass
class IndexMetrics:
    """指数评估指标"""
    code: str                 # 指数代码
    name: str                 # 指数名称
    current_price: float      # 当前点位
    pe_ttm: float            # 滚动市盈率
    pe_percentile: float      # 市盈率分位数
    pb: float                # 市净率
    pb_percentile: float     # 市净率分位数
    dividend_yield: float    # 股息率
    volatility: float        # 波动率


def calculate_metrics(
    index_data: pd.DataFrame,
    lookback_period: int = 252
) -> IndexMetrics:
    """计算指数相关指标
    
    Args:
        index_data: 指数历史数据
        lookback_period: 回看期限（默认一年）
        
    Returns:
        IndexMetrics: 指数评估指标
    """
    try:
        # 基础数据检查
        if len(index_data) < lookback_period:
            raise ValueError(f"数据长度不足{lookback_period}个交易日")
        
        # 获取最新数据
        latest = index_data.iloc[-1]
        
        # 计算波动率
        returns = index_data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        
        # 计算分位数
        pe_percentile = (
            index_data['pe_ttm'].rank(pct=True).iloc[-1]
            if 'pe_ttm' in index_data.columns else None
        )
        pb_percentile = (
            index_data['pb'].rank(pct=True).iloc[-1]
            if 'pb' in index_data.columns else None
        )
        
        return IndexMetrics(
            code=latest['code'],
            name=latest.get('name', ''),
            current_price=latest['close'],
            pe_ttm=latest.get('pe_ttm', 0),
            pe_percentile=pe_percentile,
            pb=latest.get('pb', 0),
            pb_percentile=pb_percentile,
            dividend_yield=latest.get('dividend_yield', 0),
            volatility=volatility
        )
        
    except Exception as e:
        logger.error(f"计算指数指标失败: {str(e)}")
        raise


def analyze_valuation(
    metrics: IndexMetrics,
    pe_threshold: float = 0.3,
    pb_threshold: float = 0.3
) -> Dict:
    """估值分析
    
    Args:
        metrics: 指数评估指标
        pe_threshold: PE分位数阈值
        pb_threshold: PB分位数阈值
        
    Returns:
        Dict: 估值分析结果
    """
    # 估值评分 (0-100)
    pe_score = 100 * (1 - metrics.pe_percentile) if metrics.pe_percentile else 50
    pb_score = 100 * (1 - metrics.pb_percentile) if metrics.pb_percentile else 50
    total_score = (pe_score + pb_score) / 2
    
    # 估值水平判断
    if (metrics.pe_percentile <= pe_threshold and 
        metrics.pb_percentile <= pb_threshold):
        valuation_level = "低估"
    elif (metrics.pe_percentile >= 0.7 and 
          metrics.pb_percentile >= 0.7):
        valuation_level = "高估"
    else:
        valuation_level = "合理"
    
    return {
        'code': metrics.code,
        'name': metrics.name,
        'valuation_level': valuation_level,
        'score': total_score,
        'pe_ttm': metrics.pe_ttm,
        'pe_percentile': metrics.pe_percentile,
        'pb': metrics.pb,
        'pb_percentile': metrics.pb_percentile,
        'suggestion': "建议买入" if valuation_level == "低估" else 
                     "建议减持" if valuation_level == "高估" else 
                     "建议持有"
    }


def analyze_trend(
    index_data: pd.DataFrame,
    ma_short: int = 20,
    ma_long: int = 60
) -> Dict:
    """趋势分析
    
    Args:
        index_data: 指数历史数据
        ma_short: 短期均线周期
        ma_long: 长期均线周期
        
    Returns:
        Dict: 趋势分析结果
    """
    df = index_data.copy()
    
    # 计算均线
    df['ma_short'] = df['close'].rolling(ma_short).mean()
    df['ma_long'] = df['close'].rolling(ma_long).mean()
    
    # 计算趋势强度
    latest = df.iloc[-1]
    strength = (latest['ma_short'] - latest['ma_long']) / latest['ma_long']
    
    # 判断趋势
    if latest['ma_short'] > latest['ma_long']:
        trend = "上升"
        signal = "买入"
    elif latest['ma_short'] < latest['ma_long']:
        trend = "下降"
        signal = "卖出"
    else:
        trend = "盘整"
        signal = "观望"
    
    return {
        'trend': trend,
        'signal': signal,
        'strength': strength,
        'ma_short': latest['ma_short'],
        'ma_long': latest['ma_long']
    }


def calculate_regular_invest_amount(
    base_amount: float,
    metrics: IndexMetrics,
    valuation_factor: float = 0.5,
    trend_factor: float = 0.3,
    volatility_factor: float = 0.2
) -> float:
    """计算定投金额
    
    Args:
        base_amount: 基础定投金额
        metrics: 指数评估指标
        valuation_factor: 估值因子权重
        trend_factor: 趋势因子权重
        volatility_factor: 波动率因子权重
        
    Returns:
        float: 建议定投金额
    """
    # 估值调整系数 (估值越低，投资越多)
    if metrics.pe_percentile and metrics.pb_percentile:
        valuation_adj = 1 + (0.5 - (metrics.pe_percentile + metrics.pb_percentile) / 2)
    else:
        valuation_adj = 1
    
    # 趋势调整系数 (上涨趋势增加投资)
    trend = analyze_trend(pd.DataFrame({'close': [metrics.current_price]}))
    trend_adj = 1.2 if trend['trend'] == "上升" else 0.8 if trend['trend'] == "下降" else 1
    
    # 波动率调整系数 (波动率高时减少投资)
    volatility_adj = 1 / (1 + metrics.volatility)
    
    # 计算最终投资金额
    adjusted_amount = base_amount * (
        valuation_adj * valuation_factor +
        trend_adj * trend_factor +
        volatility_adj * volatility_factor
    )
    
    return round(adjusted_amount, 2)


def get_rotation_signal(
    large_cap_data: pd.DataFrame,
    small_cap_data: pd.DataFrame,
    lookback_period: int = 20
) -> Dict[str, float]:
    """大小盘轮动信号
    
    Args:
        large_cap_data: 大盘指数数据
        small_cap_data: 小盘指数数据
        lookback_period: 回看期限
        
    Returns:
        Dict[str, float]: 配置权重建议
    """
    # 计算动量
    large_momentum = (
        large_cap_data['close'].pct_change(lookback_period).iloc[-1]
    )
    small_momentum = (
        small_cap_data['close'].pct_change(lookback_period).iloc[-1]
    )
    
    # 计算相对强度
    rel_strength = large_momentum - small_momentum
    
    # 分配权重
    if rel_strength > 0.02:  # 大盘明显强势
        weights = {'large_cap': 0.7, 'small_cap': 0.3}
    elif rel_strength < -0.02:  # 小盘明显强势
        weights = {'large_cap': 0.3, 'small_cap': 0.7}
    else:  # 势均力敌
        weights = {'large_cap': 0.5, 'small_cap': 0.5}
    
    return {
        'weights': weights,
        'large_cap_momentum': large_momentum,
        'small_cap_momentum': small_momentum,
        'relative_strength': rel_strength
    }
    
    
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from loguru import logger

class IndexStrategy(Enum):
    """指数投资策略类型"""
    REGULAR_INVEST = "regular_invest"      # 定投策略
    VALUATION = "valuation"                # 估值策略
    TREND_FOLLOWING = "trend_following"    # 趋势跟踪
    ROTATION = "rotation"                  # 大小盘轮动

@dataclass
class IndexFund:
    """指数基金信息"""
    code: str                 # 基金代码
    name: str                 # 基金名称
    index_code: str          # 跟踪指数代码
    pe: float                # 市盈率
    pb: float                # 市净率
    dividend_yield: float    # 股息率
    tracking_error: float    # 跟踪误差
    expense_ratio: float     # 费率
    aum: float              # 规模（亿元）

def analyze_valuation(
    index_data: pd.DataFrame,
    percentile_threshold: float = 0.3
) -> List[Dict]:
    """估值分析
    
    Args:
        index_data: 指数数据
        percentile_threshold: 估值分位数阈值
        
    Returns:
        List[Dict]: 投资建议列表
    """
    recommendations = []
    
    for _, index in index_data.iterrows():
        # 计算估值分位数
        pe_percentile = index['pe_percentile']
        pb_percentile = index['pb_percentile']
        
        # 低估值策略
        if pe_percentile <= percentile_threshold and pb_percentile <= percentile_threshold:
            recommendations.append({
                'code': index['code'],
                'name': index['name'],
                'reason': f"估值处于历史{percentile_threshold*100}%分位数以下",
                'pe': index['pe'],
                'pb': index['pb'],
                'score': 100 - (pe_percentile + pb_percentile) * 50
            })
    
    return sorted(recommendations, key=lambda x: x['score'], reverse=True)

def analyze_trend(
    index_data: pd.DataFrame,
    ma_short: int = 20,
    ma_long: int = 60
) -> Dict[str, str]:
    """趋势分析
    
    Args:
        index_data: 指数数据
        ma_short: 短期均线周期
        ma_long: 长期均线周期
        
    Returns:
        Dict[str, str]: 交易信号
    """
    signals = {}
    
    for code in index_data['code'].unique():
        df = index_data[index_data['code'] == code].copy()
        
        # 计算均线
        df['ma_short'] = df['close'].rolling(ma_short).mean()
        df['ma_long'] = df['close'].rolling(ma_long).mean()
        
        # 判断趋势
        latest = df.iloc[-1]
        if latest['ma_short'] > latest['ma_long']:
            signals[code] = 'buy'
        elif latest['ma_short'] < latest['ma_long']:
            signals[code] = 'sell'
        else:
            signals[code] = 'hold'
            
    return signals

def analyze_rotation(
    index_data: pd.DataFrame,
    lookback_period: int = 20
) -> Dict[str, float]:
    """大小盘轮动分析
    
    Args:
        index_data: 指数数据
        lookback_period: 回看期限(天)
        
    Returns:
        Dict[str, float]: 配置权重建议
    """
    # 计算大小盘相对强度
    large_cap = index_data[index_data['code'] == '000300'].copy()  # 沪深300
    small_cap = index_data[index_data['code'] == '000905'].copy()  # 中证500
    
    large_cap['return'] = large_cap['close'].pct_change(lookback_period)
    small_cap['return'] = small_cap['close'].pct_change(lookback_period)
    
    # 计算相对强度
    latest_large_return = large_cap['return'].iloc[-1]
    latest_small_return = small_cap['return'].iloc[-1]
    
    # 根据相对强度分配权重
    if latest_large_return > latest_small_return:
        return {'000300': 0.7, '000905': 0.3}
    else:
        return {'000300': 0.3, '000905': 0.7}

def get_investment_suggestion(
    index_data: pd.DataFrame,
    strategy: IndexStrategy,
    risk_preference: str = 'moderate'
) -> List[Dict]:
    """获取指数投资建议
    
    Args:
        index_data: 指数数据
        strategy: 投资策略
        risk_preference: 风险偏好
        
    Returns:
        List[Dict]: 投资建议列表
    """
    if strategy == IndexStrategy.VALUATION:
        # 估值策略
        threshold = {
            'conservative': 0.2,
            'moderate': 0.3,
            'aggressive': 0.4
        }.get(risk_preference, 0.3)
        return analyze_valuation(index_data, threshold)
    
    elif strategy == IndexStrategy.TREND_FOLLOWING:
        # 趋势跟踪策略
        signals = analyze_trend(index_data)
        return [{'code': k, 'signal': v} for k, v in signals.items()]
    
    elif strategy == IndexStrategy.ROTATION:
        # 大小盘轮动策略
        weights = analyze_rotation(index_data)
        return [{'code': k, 'weight': v} for k, v in weights.items()]
    
    elif strategy == IndexStrategy.REGULAR_INVEST:
        # 定投策略
        return [{
            'strategy': 'regular_invest',
            'frequency': 'monthly',
            'suggestion': '建议每月定期定额投资核心指数基金'
        }]
        
        
        
        
# # 获取指数数据
# index_data = pd.DataFrame({
#     'code': ['000300', '000905'],
#     'name': ['沪深300', '中证500'],
#     'pe': [12.5, 15.2],
#     'pb': [1.5, 1.8],
#     'pe_percentile': [0.2, 0.3],
#     'pb_percentile': [0.25, 0.35]
# })

# # 1. 估值策略分析
# valuation_suggestions = get_investment_suggestion(
#     index_data,
#     IndexStrategy.VALUATION,
#     'moderate'
# )

# # 2. 趋势跟踪信号
# trend_signals = get_investment_suggestion(
#     index_data,
#     IndexStrategy.TREND_FOLLOWING
# )

# # 3. 大小盘轮动建议
# rotation_weights = get_investment_suggestion(
#     index_data,
#     IndexStrategy.ROTATION
# )