"""行业动量因子的有效性检验（IC 扫描）

目的：回答「动量分位适合多长持有期」这类问题，而不是拍脑袋。

方法：
1. 读 datas/raw/n_indexes/industry_hist/*.csv，拼成 日期 × 板块 的收盘价面板
2. 每个取样日 t，按 20/60/120 日涨幅的横截面百分位加权算出「动量分位」
3. 用 scipy.stats.spearmanr 计算 动量分位 与 t→t+H 收益 的秩相关（IC）及 p 值
4. 对 H = 5/10/20/40/60/120 交易日：
   - IC 均值、标准差、t 值、p 值（单样本 t 检验，检验 IC 均值是否为 0）
   - IC 显著为负/正的日期占比
   - 强组（动量前 20%）− 弱组（后 20%）的收益差及 t 检验

注意：样本期短（约 810 个交易日）且持有期重叠，t 值偏乐观，仅作方向性参考。

用法：python -m utils.momentum_ic
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats

HIST_DIR = Path("datas/raw/n_indexes/industry_hist")
HORIZONS = (5, 10, 20, 40, 60, 120)
WINDOWS = (20, 60, 120)
WEIGHTS = {20: 0.5, 60: 0.3, 120: 0.2}
SAMPLE_STEP = 5          # 每 N 个交易日取样一次（降低重叠）
MIN_CROSS_SECTION = 100  # 截面上至少这么多个板块才算有效


def load_panel() -> pd.DataFrame:
    """读全部行业日线，拼成 日期 × 板块 的收盘价面板"""
    frames = {}
    for path in sorted(HIST_DIR.glob("*.csv")):
        df = pd.read_csv(path)
        if len(df) < 200 or "收盘" not in df.columns:
            continue
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        df["收盘"] = pd.to_numeric(df["收盘"], errors="coerce")
        series = (
            df.dropna(subset=["日期", "收盘"])
            .drop_duplicates("日期")
            .set_index("日期")["收盘"]
        )
        frames[path.stem.split("_", 1)[1]] = series

    if not frames:
        raise RuntimeError(f"{HIST_DIR} 下没有可用的行业日线，先跑 utils.industry_hist")

    panel = pd.DataFrame(frames).sort_index().ffill()
    logger.info(
        f"面板: {panel.shape[0]} 个交易日 × {panel.shape[1]} 个板块 | "
        f"{panel.index[0].date()} ~ {panel.index[-1].date()}"
    )
    return panel


def scan(panel: pd.DataFrame) -> pd.DataFrame:
    """扫描各持有期的 IC 与强弱组收益差"""
    returns = {w: panel / panel.shift(w) - 1 for w in WINDOWS}
    forward = {h: panel.shift(-h) / panel - 1 for h in HORIZONS}

    lookback = max(WINDOWS) + 1
    dates = panel.index[lookback:-max(HORIZONS) - 1:SAMPLE_STEP]

    rows = []
    for moment in dates:
        score = pd.Series(0.0, index=panel.columns)
        for window, weight in WEIGHTS.items():
            cross_section = returns[window].loc[moment]
            if cross_section.notna().sum() < MIN_CROSS_SECTION:
                score = None
                break
            score += cross_section.rank(pct=True) * 100 * weight
        if score is None:
            continue

        record = {"日期": moment}
        for horizon in HORIZONS:
            future = forward[horizon].loc[moment].reindex(score.index)
            pair = pd.concat([score, future], axis=1, keys=["s", "f"]).dropna()
            if len(pair) < MIN_CROSS_SECTION:
                continue

            ic, p_value = stats.spearmanr(pair["s"], pair["f"])
            record[f"IC{horizon}"] = ic
            record[f"p{horizon}"] = p_value

            high = pair["s"].quantile(0.8)
            low = pair["s"].quantile(0.2)
            record[f"spread{horizon}"] = (
                pair.loc[pair["s"] >= high, "f"].mean()
                - pair.loc[pair["s"] <= low, "f"].mean()
            ) * 100
        rows.append(record)

    return pd.DataFrame(rows)


def summarize(result: pd.DataFrame) -> pd.DataFrame:
    """汇总每个持有期的统计量"""
    out = []
    for horizon in HORIZONS:
        ic = result.get(f"IC{horizon}", pd.Series(dtype=float)).dropna()
        spread = result.get(f"spread{horizon}", pd.Series(dtype=float)).dropna()
        if len(ic) < 10:
            continue

        t_ic, p_ic = stats.ttest_1samp(ic, 0.0)
        # IC 均值的 95% 置信区间
        half = 1.96 * ic.std(ddof=1) / np.sqrt(len(ic))
        t_sp, p_sp = stats.ttest_1samp(spread, 0.0) if len(spread) >= 10 else (np.nan, np.nan)

        out.append({
            "持有期": horizon,
            "样本数": len(ic),
            "IC均值": round(ic.mean(), 4),
            "IC标准差": round(ic.std(ddof=1), 4),
            "IC_t值": round(t_ic, 2),
            "IC_p值": round(p_ic, 4),
            "IC_95%CI下限": round(ic.mean() - half, 4),
            "IC_95%CI上限": round(ic.mean() + half, 4),
            "IC负显著占比%": round((result[f"p{horizon}"] < 0.05).mean() * 100, 1)
            if f"p{horizon}" in result else None,
            "强弱差均值%": round(spread.mean(), 3),
            "强弱差_t值": round(t_sp, 2) if pd.notna(t_sp) else None,
            "强弱差_p值": round(p_sp, 4) if pd.notna(p_sp) else None,
        })
    return pd.DataFrame(out)


def run():
    panel = load_panel()
    result = scan(panel)
    logger.info(f"有效取样日: {len(result)} 个（每 {SAMPLE_STEP} 个交易日取一次）")

    summary = summarize(result)
    if summary.empty:
        logger.error("样本不足，无法给出统计结论")
        return summary

    logger.info("=== 动量分位对各持有期收益的预测力（scipy 秩相关）===")
    for _, row in summary.iterrows():
        significance = (
            "显著" if row["IC_p值"] < 0.05 else "不显著"
        )
        logger.info(
            f"{int(row['持有期']):3d}日 | IC {row['IC均值']:+.4f} "
            f"(95%CI {row['IC_95%CI下限']:+.4f}~{row['IC_95%CI上限']:+.4f}), "
            f"t={row['IC_t值']:+.2f}, p={row['IC_p值']:.4f} [{significance}] | "
            f"强弱差 {row['强弱差均值%']:+.3f}% "
            f"(t={row['强弱差_t值']:+.2f}, p={row['强弱差_p值']:.4f})"
        )
    return summary


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("momentum_ic.log")
    run()
