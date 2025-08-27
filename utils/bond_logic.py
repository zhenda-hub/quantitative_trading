from typing import Dict, List
from enum import Enum
from dataclasses import dataclass
import pandas as pd
from loguru import logger


class Strategy(Enum):
    """可转债策略类型"""
    DOUBLE_LOW = "double_low"      # 双低策略
    PAR_VALUE = "par_value"        # 平价策略
    LOW_PREMIUM = "low_premium"    # 低溢价率策略


@dataclass
class ConvertibleBond:
    """可转债信息"""
    code: str                 # 转债代码
    price: float             # 转债价格
    stock_price: float       # 正股价格
    convert_price: float     # 转股价
    premium_rate: float      # 转股溢价率
    pure_bond_value: float   # 纯债价值
    remain_size: float       # 剩余规模
    stock_pe: float         # 正股市盈率
    credit_rating: str       # 信用评级
    duration: float         # 剩余期限（年）
    industry: str           # 行业
    
    def get_convert_value(self) -> float:
        """计算转股价值"""
        return (self.stock_price * 100) / self.convert_price
    
    def get_double_low_value(self) -> float:
        """计算双低值"""
        return self.premium_rate + self.price

def analyze_bonds(
    bonds_data: pd.DataFrame,
    strategy: Strategy,
    risk_preference: str = 'moderate'
) -> List[Dict]:
    """分析可转债投资策略
    
    Args:
        bonds_data: 可转债数据
        strategy: 策略类型
        risk_preference: 风险偏好 ('conservative'|'moderate'|'aggressive')
    
    Returns:
        List[Dict]: 投资建议列表
    """
    # 风险偏好系数
    risk_factors = {
        'conservative': 0.7,
        'moderate': 1.0,
        'aggressive': 1.3
    }
    risk_factor = risk_factors.get(risk_preference, 1.0)
    
    # 基础筛选条件
    base_conditions = {
        'min_duration': 1.0 * risk_factor,
        'min_size': 1.0,
        'min_price': 90.0,
        'max_premium': 30.0 * risk_factor
    }
    
    # 基础筛选
    filtered = bonds_data[
        (bonds_data['duration'] >= base_conditions['min_duration']) &
        (bonds_data['remain_size'] >= base_conditions['min_size']) &
        (bonds_data['price'] >= base_conditions['min_price']) &
        (bonds_data['premium_rate'] <= base_conditions['max_premium']) &
        (bonds_data['credit_rating'].isin(['AAA', 'AA+', 'AA']))
    ].copy()
    
    if len(filtered) == 0:
        logger.warning("没有符合条件的可转债")
        return []
    
    recommendations = []
    
    if strategy == Strategy.DOUBLE_LOW:
        # 双低策略
        filtered['score'] = 100 - (filtered['premium_rate'] + filtered['price'])
        selected = filtered.nlargest(10, 'score')
        for _, bond in selected.iterrows():
            recommendations.append({
                'code': bond['code'],
                'strategy': strategy.value,
                'score': bond['score'],
                'reason': f"双低值:{bond['premium_rate']+bond['price']:.1f}"
            })
            
    elif strategy == Strategy.LOW_PREMIUM:
        # 低溢价率策略
        filtered['score'] = 100 - filtered['premium_rate']
        selected = filtered.nlargest(10, 'score')
        for _, bond in selected.iterrows():
            recommendations.append({
                'code': bond['code'],
                'strategy': strategy.value,
                'score': bond['score'],
                'reason': f"溢价率:{bond['premium_rate']:.1f}%"
            })
            
    elif strategy == Strategy.PAR_VALUE:
        # 平价策略
        filtered['price_diff'] = abs(
            filtered['price'] - 
            filtered['stock_price'] * 100 / filtered['convert_price']
        )
        filtered['score'] = 100 - filtered['price_diff'] * 10
        selected = filtered[filtered['price_diff'] <= 3].nlargest(10, 'score')
        for _, bond in selected.iterrows():
            recommendations.append({
                'code': bond['code'],
                'strategy': strategy.value,
                'score': bond['score'],
                'reason': f"价差:{bond['price_diff']:.1f}"
            })
            
    return sorted(recommendations, key=lambda x: x['score'], reverse=True)

def get_trade_signals(
    bonds_data: pd.DataFrame,
    lookback_period: int = 120,
    buy_threshold: float = 0.2,
    sell_threshold: float = 0.8
) -> Dict[str, List[str]]:
    """获取转债交易信号
    
    Args:
        bonds_data: 可转债历史数据
        lookback_period: 回看期限(天)
        buy_threshold: 买入阈值分位数(0-1)
        sell_threshold: 卖出阈值分位数(0-1)
    
    Returns:
        Dict[str, List[str]]: 按信号分类的转债代码列表
    """
    signals = {'buy': [], 'sell': [], 'hold': []}
    
    for code in bonds_data['code'].unique():
        bond_data = bonds_data[bonds_data['code'] == code].copy()
        
        if len(bond_data) < lookback_period:
            continue
        
        # 计算溢价率分位数
        premium_rates = bond_data['premium_rate'].rolling(
            lookback_period
        ).rank(pct=True)
        
        latest_quantile = premium_rates.iloc[-1]
        
        # 生成信号
        if latest_quantile <= buy_threshold:
            signals['buy'].append(code)
        elif latest_quantile >= sell_threshold:
            signals['sell'].append(code)
        else:
            signals['hold'].append(code)
    
    return signals


def build_portfolio(
    bonds_data: pd.DataFrame,
    risk_preference: str = 'moderate',
    max_bonds: int = 10
) -> Dict[str, float]:
    """构建可转债投资组合
    
    Args:
        bonds_data: 可转债数据
        risk_preference: 风险偏好
        max_bonds: 最大持仓数量
    
    Returns:
        Dict[str, float]: 转债代码及权重
    """
    portfolio = {}
    
    # 获取不同策略的推荐列表
    double_low = analyze_bonds(bonds_data, Strategy.DOUBLE_LOW, risk_preference)
    low_premium = analyze_bonds(bonds_data, Strategy.LOW_PREMIUM, risk_preference)
    par_value = analyze_bonds(bonds_data, Strategy.PAR_VALUE, risk_preference)
    
    # 根据风险偏好分配权重
    if risk_preference == 'conservative':
        weights = {'double_low': 0.5, 'low_premium': 0.3, 'par_value': 0.2}
    elif risk_preference == 'moderate':
        weights = {'double_low': 0.4, 'low_premium': 0.3, 'par_value': 0.3}
    else:  # aggressive
        weights = {'double_low': 0.3, 'low_premium': 0.3, 'par_value': 0.4}
    
    # 分配个券权重
    def add_to_portfolio(recommendations: List[Dict], total_weight: float):
        if not recommendations:
            return
        weight_per_bond = total_weight / len(recommendations)
        for rec in recommendations[:max_bonds]:
            portfolio[rec['code']] = weight_per_bond
    
    add_to_portfolio(double_low, weights['double_low'])
    add_to_portfolio(low_premium, weights['low_premium'])
    add_to_portfolio(par_value, weights['par_value'])
    
    return portfolio



class ConvertibleBondStrategy(Enum):
    DOUBLE_LOW = "double_low"  # 双低策略
    PAR_VALUE = "par_value"    # 平价策略
    HIGH_PRICE = "high_price"  # 高价格策略

@dataclass
class BondMetrics:
    code: str                  # 转债代码
    price: float              # 转债价格
    stock_price: float        # 正股价格
    convert_price: float      # 转股价
    premium_rate: float       # 转股溢价率
    pure_bond_value: float    # 纯债价值
    remain_size: float        # 剩余规模
    credit_rating: str        # 信用评级
    duration: float           # 久期

def analyze_convertible_bonds(
    bonds_data: pd.DataFrame,
    strategy: ConvertibleBondStrategy,
    max_premium_rate: float = 30.0,
    min_remain_size: float = 1.0,
) -> List[Dict]:
    """分析可转债并返回投资建议
    
    Args:
        bonds_data: 可转债数据DataFrame
        strategy: 策略类型
        max_premium_rate: 最大转股溢价率
        min_remain_size: 最小剩余规模(亿)
    
    Returns:
        List[Dict]: 投资建议列表
    """
    recommendations = []
    
    # 基础筛选
    bonds_data = bonds_data[
        (bonds_data['remain_size'] >= min_remain_size) &
        (bonds_data['credit_rating'].isin(['AAA', 'AA+', 'AA']))
    ]
    
    if strategy == ConvertibleBondStrategy.DOUBLE_LOW:
        # 双低策略实现
        bonds_data['double_low'] = bonds_data['premium_rate'] + bonds_data['price']
        selected = bonds_data.nsmallest(10, 'double_low')
        
        for _, bond in selected.iterrows():
            recommendations.append({
                'code': bond['code'],
                'reason': f"双低值:{bond['double_low']:.2f}, 溢价率:{bond['premium_rate']:.2f}%",
                'score': 100 - bond['double_low']
            })
            
    elif strategy == ConvertibleBondStrategy.PAR_VALUE:
        # 平价策略实现
        bonds_data['price_diff'] = abs(bonds_data['price'] - bonds_data['convert_value'])
        selected = bonds_data[bonds_data['price_diff'] <= 3].nsmallest(10, 'price_diff')
        
        for _, bond in selected.iterrows():
            recommendations.append({
                'code': bond['code'],
                'reason': f"转股价值差:{bond['price_diff']:.2f}, 价格:{bond['price']:.2f}",
                'score': 100 - bond['price_diff'] * 10
            })
            
    elif strategy == ConvertibleBondStrategy.HIGH_PRICE:
        # 高价格策略实现
        conditions = (
            (bonds_data['price'] >= 110) &
            (bonds_data['premium_rate'] <= max_premium_rate)
        )
        selected = bonds_data[conditions].nlargest(10, 'stock_momentum')
        
        for _, bond in selected.iterrows():
            recommendations.append({
                'code': bond['code'],
                'reason': f"股性强,动量:{bond['stock_momentum']:.2f},价格:{bond['price']:.2f}",
                'score': bond['stock_momentum']
            })
    
    return recommendations

def get_convertible_bond_portfolio(
    bonds_data: pd.DataFrame,
    risk_preference: str = 'moderate',
    portfolio_size: int = 10
) -> Dict[str, float]:
    """构建可转债投资组合
    
    Args:
        bonds_data: 可转债数据
        risk_preference: 风险偏好 ('conservative'|'moderate'|'aggressive')
        portfolio_size: 组合大小
        
    Returns:
        Dict[str, float]: 转债代码及配置权重
    """
    portfolio = {}
    
    # 根据风险偏好选择策略组合
    if risk_preference == 'conservative':
        # 保守型: 80%双低 + 20%平价
        double_low = analyze_convertible_bonds(
            bonds_data, 
            ConvertibleBondStrategy.DOUBLE_LOW,
            max_premium_rate=20
        )
        par_value = analyze_convertible_bonds(
            bonds_data,
            ConvertibleBondStrategy.PAR_VALUE
        )
        
        # 分配权重
        for bond in double_low[:8]:
            portfolio[bond['code']] = 0.1  # 每个转债10%权重
        for bond in par_value[:2]:
            portfolio[bond['code']] = 0.1
            
    elif risk_preference == 'moderate':
        # 均衡型: 40%双低 + 40%平价 + 20%高价格
        strategies = [
            (ConvertibleBondStrategy.DOUBLE_LOW, 4, 0.1),
            (ConvertibleBondStrategy.PAR_VALUE, 4, 0.1),
            (ConvertibleBondStrategy.HIGH_PRICE, 2, 0.1)
        ]
        
        for strategy, count, weight in strategies:
            bonds = analyze_convertible_bonds(bonds_data, strategy)
            for bond in bonds[:count]:
                portfolio[bond['code']] = weight
                
    else:  # aggressive
        # 激进型: 30%平价 + 70%高价格
        par_value = analyze_convertible_bonds(
            bonds_data,
            ConvertibleBondStrategy.PAR_VALUE
        )
        high_price = analyze_convertible_bonds(
            bonds_data,
            ConvertibleBondStrategy.HIGH_PRICE,
            max_premium_rate=50
        )
        
        for bond in par_value[:3]:
            portfolio[bond['code']] = 0.1
        for bond in high_price[:7]:
            portfolio[bond['code']] = 0.1
            
    return portfolio

def get_rebalance_suggestions(
    current_portfolio: Dict[str, float],
    target_portfolio: Dict[str, float],
    threshold: float = 0.05
) -> Dict[str, float]:
    """生成调仓建议
    
    Args:
        current_portfolio: 当前持仓
        target_portfolio: 目标配置
        threshold: 调仓阈值
        
    Returns:
        Dict[str, float]: 调仓建议(正数表示买入,负数表示卖出)
    """
    suggestions = {}
    
    # 计算需要调整的仓位
    for code in set(current_portfolio) | set(target_portfolio):
        current_weight = current_portfolio.get(code, 0)
        target_weight = target_portfolio.get(code, 0)
        diff = target_weight - current_weight
        
        if abs(diff) >= threshold:
            suggestions[code] = diff
            
    return suggestions



# # 1. 基本分析
# recommendations = analyze_bonds(
#     bonds_data,
#     strategy=Strategy.DOUBLE_LOW,
#     risk_preference='moderate'
# )

# # 2. 获取交易信号
# signals = get_trade_signals(
#     bonds_data,
#     lookback_period=120,
#     buy_threshold=0.2,
#     sell_threshold=0.8
# )

# # 3. 构建组合
# portfolio = build_portfolio(
#     bonds_data,
#     risk_preference='moderate',
#     max_bonds=10
# )