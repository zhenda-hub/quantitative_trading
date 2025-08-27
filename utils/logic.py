from typing import Dict, List, Tuple, Optional
from loguru import logger


def get_period(
    unemp_month_on_month: float,
    cpi_month_on_month: float,
    threshold: float = 0.05
) -> str:
    """根据失业率和CPI的环比变化判断经济周期阶段"""
    logger.info(f'unemp: {unemp_month_on_month}， cpi： {cpi_month_on_month}')

    if unemp_month_on_month > 0 and cpi_month_on_month > 0:
        if unemp_month_on_month > threshold and cpi_month_on_month > threshold:
            return '上升'
        else:
            return '高点'
    if unemp_month_on_month < 0 and cpi_month_on_month < 0:
        if abs(unemp_month_on_month) > threshold and abs(cpi_month_on_month) > threshold:
            return '下降'
        else:
            return '低点'

    return '未知'


def calculate_index_weights(
    period: str,
    risk_preference: str = 'moderate'
) -> Dict[str, float]:
    """
    根据经济周期和风险偏好计算指数配置权重
    
    Args:
        period: 经济周期阶段 ('上升', '高点', '下降', '低点', '未知')
        risk_preference: 风险偏好 ('conservative', 'moderate', 'aggressive')
    
    Returns:
        Dict[str, float]: 各指数的配置权重
    """
    # 基础配置
    weights = {
        '000300': 0.0,  # 沪深300
        '000905': 0.0,  # 中证500
        '399006': 0.0,  # 创业板
        'HSI': 0.0,     # 恒生指数
        'SPX': 0.0      # 标普500
    }
    
    # 风险系数
    risk_factors = {
        'conservative': 0.7,
        'moderate': 1.0,
        'aggressive': 1.3
    }
    
    risk_factor = risk_factors.get(risk_preference, 1.0)
    
    if period == '上升':
        # 经济上升期：增加小盘股和成长股配置
        weights.update({
            '000300': 0.3 * risk_factor,
            '000905': 0.25 * risk_factor,
            '399006': 0.25 * risk_factor,
            'HSI': 0.1 * risk_factor,
            'SPX': 0.1 * risk_factor
        })
    elif period == '高点':
        # 经济高点：降低权益资产配置，增加防御性板块
        weights.update({
            '000300': 0.4 * risk_factor,
            '000905': 0.15 * risk_factor,
            '399006': 0.15 * risk_factor,
            'HSI': 0.15 * risk_factor,
            'SPX': 0.15 * risk_factor
        })
    elif period == '下降':
        # 经济下降期：增加大盘蓝筹配置，降低小盘股配置
        weights.update({
            '000300': 0.5 * risk_factor,
            '000905': 0.1 * risk_factor,
            '399006': 0.1 * risk_factor,
            'HSI': 0.15 * risk_factor,
            'SPX': 0.15 * risk_factor
        })
    elif period == '低点':
        # 经济低点：逐步增加权益配置，关注成长股机会
        weights.update({
            '000300': 0.35 * risk_factor,
            '000905': 0.2 * risk_factor,
            '399006': 0.2 * risk_factor,
            'HSI': 0.125 * risk_factor,
            'SPX': 0.125 * risk_factor
        })
    else:
        # 未知阶段：采用相对均衡的配置
        weights.update({
            '000300': 0.4 * risk_factor,
            '000905': 0.15 * risk_factor,
            '399006': 0.15 * risk_factor,
            'HSI': 0.15 * risk_factor,
            'SPX': 0.15 * risk_factor
        })
    
    return weights


def analyze_bond_metrics(
    ytm: float,           # 到期收益率
    duration: float,      # 久期
    convexity: float,    # 凸性
    credit_rating: str,   # 信用评级
    liquidity: float      # 流动性指标（成交量/存量）
) -> Tuple[float, str]:
    """
    分析债券指标，返回投资评分和建议
    
    Args:
        ytm: 到期收益率（%）
        duration: 久期（年）
        convexity: 凹性
        credit_rating: 信用评级
        liquidity: 流动性指标
    
    Returns:
        Tuple[float, str]: (评分, 建议)
    """
    # 评分权重
    weights = {
        'ytm': 0.3,
        'duration': 0.2,
        'convexity': 0.1,
        'credit': 0.25,
        'liquidity': 0.15
    }
    
    # 信用评级得分映射
    credit_scores = {
        'AAA': 1.0, 'AA+': 0.95, 'AA': 0.9, 'AA-': 0.85,
        'A+': 0.8, 'A': 0.75, 'A-': 0.7,
        'BBB+': 0.65, 'BBB': 0.6, 'BBB-': 0.55
    }
    
    # 计算各项得分
    ytm_score = min(ytm / 10, 1.0)  # 假设10%收益率为满分
    duration_score = 1.0 - (duration / 10)  # 久期越短得分越高
    convexity_score = min(convexity / 0.5, 1.0)  # 凸性越大越好
    credit_score = credit_scores.get(credit_rating, 0.5)
    liquidity_score = min(liquidity, 1.0)
    
    # 计算总分
    total_score = (
        ytm_score * weights['ytm'] +
        duration_score * weights['duration'] +
        convexity_score * weights['convexity'] +
        credit_score * weights['credit'] +
        liquidity_score * weights['liquidity']
    )
    
    # 生成投资建议
    if total_score >= 0.8:
        advice = "强烈推荐：各项指标优秀，建议重点配置"
    elif total_score >= 0.6:
        advice = "建议购买：整体表现良好，可以适量配置"
    elif total_score >= 0.4:
        advice = "中性评级：关注风险因素，谨慎配置"
    else:
        advice = "不建议购买：风险较高，建议规避"
    
    return total_score, advice


def calculate_bond_allocation(
    period: str,
    risk_preference: str,
    available_bonds: List[Dict]
) -> Dict[str, float]:
    """
    根据经济周期和风险偏好计算债券配置
    
    Args:
        period: 经济周期阶段
        risk_preference: 风险偏好
        available_bonds: 可选债券列表，每个债券包含基本信息
    
    Returns:
        Dict[str, float]: 债券配置权重
    """
    # 风险偏好系数
    risk_factors = {
        'conservative': 0.7,
        'moderate': 1.0,
        'aggressive': 1.3
    }
    
    risk_factor = risk_factors.get(risk_preference, 1.0)
    
    # 评估每个债券
    bond_scores = {}
    for bond in available_bonds:
        score, _ = analyze_bond_metrics(
            bond['ytm'],
            bond['duration'],
            bond['convexity'],
            bond['credit_rating'],
            bond['liquidity']
        )
        bond_scores[bond['code']] = score
    
    # 根据经济周期调整配置策略
    if period == '上升':
        # 上升期：降低债券配置，选择短久期品种
        max_duration = 3.0
        min_credit_rating = 'AA'
    elif period == '高点':
        # 高点期：适度配置，选择中等久期
        max_duration = 5.0
        min_credit_rating = 'AA+'
    elif period == '下降':
        # 下降期：增加配置，选择长久期品种
        max_duration = 7.0
        min_credit_rating = 'AA-'
    elif period == '低点':
        # 低点期：积极配置，可以适当降低信用等级要求
        max_duration = 10.0
        min_credit_rating = 'A+'
    else:
        # 未知期：保持中性配置
        max_duration = 5.0
        min_credit_rating = 'AA'
    
    # 筛选符合条件的债券
    eligible_bonds = {
        code: score for code, score in bond_scores.items()
        if available_bonds[code]['duration'] <= max_duration and
        available_bonds[code]['credit_rating'] >= min_credit_rating
    }
    
    # 计算权重
    total_score = sum(eligible_bonds.values())
    if total_score == 0:
        return {}
    
    weights = {
        code: (score / total_score) * risk_factor
        for code, score in eligible_bonds.items()
    }
    
    return weights


def get_investment_suggestions(
    period: str,
    risk_preference: str,
    available_bonds: List[Dict],
    current_portfolio: Optional[Dict[str, float]] = None
) -> Dict[str, Dict[str, float]]:
    """
    获取投资建议
    
    Args:
        period: 经济周期阶段
        risk_preference: 风险偏好
        available_bonds: 可选债券列表
        current_portfolio: 当前持仓情况（可选）
    
    Returns:
        Dict: 包含指数和债券的配置建议
    """
    # 获取指数配置建议
    index_weights = calculate_index_weights(period, risk_preference)
    
    # 获取债券配置建议
    bond_weights = calculate_bond_allocation(period, risk_preference, available_bonds)
    
    result = {
        'index_allocation': index_weights,
        'bond_allocation': bond_weights
    }
    
    # 如果提供了当前持仓，计算调整建议
    if current_portfolio:
        adjustments = {}
        for asset, target_weight in {**index_weights, **bond_weights}.items():
            current_weight = current_portfolio.get(asset, 0.0)
            diff = target_weight - current_weight
            if abs(diff) >= 0.05:  # 差异超过5%才建议调整
                result[f'{asset}_adjustment'] = {
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'adjustment': diff
                }
    
    return result


