"""行业轮动榜：动量 + 相对强弱 + 估值分位 + 可买 ETF（合成一张表）

输入（全部是现成文件，不抓数据）：
- datas/raw/n_indexes/industry_hist/{板块代码}_{板块}.csv   行业日线（近 3 年）
- datas/raw/indexes/ak_index_global_hist_em_沪深300.csv     基准
- datas/raw/stocks/ef_行业板块.csv                          当日快照（涨跌幅/换手/PE/成交额）
- datas/reference/industry_etf_map.csv                      行业→Top1 ETF
- datas/processed/n_indexes/industry_pe_cninfo.csv          国证行业 PE 历史（算分位）

输出：datas/processed/n_indexes/industry_rotation.csv

指标口径：
- 20/60/120 日涨幅 = 收盘价 / N 个交易日前收盘 - 1
- RS = 行业涨幅 - 沪深300 同期涨幅（超额收益，单位 pp）
- 动量分位 = 20/60/120 日涨幅百分位排名的加权（0.5 / 0.3 / 0.2）
- PE 分位 = 当前静态 PE 在国证该行业近 3 年历史中的位置
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

HIST_DIR = Path("datas/raw/n_indexes/industry_hist")
BENCHMARK = Path("datas/raw/indexes/ak_index_global_hist_em_沪深300.csv")
BOARD = Path("datas/raw/stocks/ef_行业板块.csv")
ETF_MAP = Path("datas/reference/industry_etf_map.csv")
PE_HIST = Path("datas/processed/n_indexes/industry_pe_cninfo.csv")
OUTPUT = Path("datas/processed/n_indexes/industry_rotation.csv")

WINDOWS = (20, 60, 120)
WEIGHTS = {20: 0.5, 60: 0.3, 120: 0.2}


def load_benchmark() -> pd.Series:
    df = pd.read_csv(BENCHMARK)
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df["最新价"] = pd.to_numeric(df["最新价"], errors="coerce")
    series = df.dropna(subset=["日期", "最新价"]).set_index("日期")["最新价"].sort_index()
    logger.info(f"基准沪深300: {len(series)} 行，最新 {series.index[-1].date()}")
    return series


def momentum_one(path: Path, bench: pd.Series) -> dict | None:
    """读一个行业的历史，算各周期涨幅与 RS"""
    df = pd.read_csv(path)
    if len(df) < max(WINDOWS) + 1:
        return None
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df["收盘"] = pd.to_numeric(df["收盘"], errors="coerce")
    df = df.dropna(subset=["日期", "收盘"]).sort_values("日期")
    if len(df) < max(WINDOWS) + 1:
        return None

    close = df.set_index("日期")["收盘"]
    last_date = close.index[-1]
    code, name = path.stem.split("_", 1)

    result = {"板块代码": code, "板块": name, "K线日期": last_date.date().isoformat()}
    for window in WINDOWS:
        industry_ret = close.iloc[-1] / close.iloc[-1 - window] - 1
        bench_window = bench[bench.index <= last_date].tail(window + 1)
        bench_ret = (
            bench_window.iloc[-1] / bench_window.iloc[0] - 1 if len(bench_window) > window else float("nan")
        )
        result[f"{window}日涨幅"] = round(industry_ret * 100, 2)
        result[f"RS{window}"] = round((industry_ret - bench_ret) * 100, 2)
    return result


def load_pe_percentile() -> dict:
    """国证行业名 → 近3年 PE 分位"""
    if not PE_HIST.exists():
        return {}
    df = pd.read_csv(PE_HIST, dtype={"行业编码": str})
    df["静态市盈率-加权平均"] = pd.to_numeric(df["静态市盈率-加权平均"], errors="coerce")
    df = df[(df["静态市盈率-加权平均"] > 0)].dropna(subset=["静态市盈率-加权平均"])

    mapping = {}
    for (code, name), group in df.groupby(["行业编码", "行业名称"]):
        series = group.sort_values("日期")["静态市盈率-加权平均"].values
        if len(series) < 60:      # 不足 60 期不参与（分位不稳）
            continue
        mapping[name] = round(float((series <= series[-1]).mean() * 100), 1)
    logger.info(f"国证 PE 分位可用行业: {len(mapping)} 个")
    return mapping


def match_pe(board_name: str, pe_map: dict, used: set) -> float | None:
    """把东财板块名匹配到国证行业名（精确 → 包含，取最长公共匹配）"""
    if board_name in pe_map and board_name not in used:
        return pe_map[board_name]

    candidates = [
        (len(name), name)
        for name in pe_map
        if name not in used
        and len(name) >= 2
        and len(board_name) >= 2
        and (name in board_name or board_name in name)
    ]
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return pe_map[candidates[0][1]]


def build(output: Path = OUTPUT) -> pd.DataFrame:
    bench = load_benchmark()

    records = []
    for path in sorted(HIST_DIR.glob("*.csv")):
        row = momentum_one(path, bench)
        if row:
            records.append(row)
    if not records:
        raise RuntimeError(f"{HIST_DIR} 下没有可用的行业历史，先跑 utils.industry_hist")

    momentum = pd.DataFrame(records)
    logger.info(f"动量计算: {len(momentum)} 个行业")

    # 动量分位（各周期涨幅的百分位排名加权）
    score = pd.Series(0.0, index=momentum.index)
    for window in WINDOWS:
        score += momentum[f"{window}日涨幅"].rank(pct=True) * 100 * WEIGHTS[window]
    momentum["动量分位"] = score.round(1)

    # 当日快照
    board = pd.read_csv(BOARD)
    for column in ("涨跌幅", "换手率", "量比", "成交额", "动态市盈率"):
        if column in board.columns:
            board[column] = pd.to_numeric(board[column], errors="coerce")
    board = board.rename(columns={"股票代码": "板块代码", "股票名称": "板块"})
    board["成交额(亿)"] = (board["成交额"] / 1e8).round(1)
    board = board[["板块代码", "涨跌幅", "换手率", "量比", "成交额(亿)", "动态市盈率"]]
    board = board.rename(columns={"涨跌幅": "今日涨幅", "动态市盈率": "动态PE"})

    merged = momentum.merge(board, on="板块代码", how="left")

    # ETF（每板块成交额最大的一只）
    if ETF_MAP.exists():
        etf = pd.read_csv(ETF_MAP, dtype={"板块代码": str})
        etf = etf.dropna(subset=["ETF代码"]).sort_values("成交额(亿)", ascending=False)
        top = etf.drop_duplicates(subset=["板块代码"], keep="first")[["板块代码", "ETF名称", "成交额(亿)"]]
        top = top.rename(columns={"成交额(亿)": "ETF成交额(亿)"})
        merged = merged.merge(top, on="板块代码", how="left")

    # PE 分位（名称匹配，best effort）
    pe_map = load_pe_percentile()
    used = set()
    merged["PE分位"] = [match_pe(name, pe_map, used) for name in merged["板块"]]
    covered = merged["PE分位"].notna().sum()
    logger.info(f"PE 分位匹配: {covered}/{len(merged)} 个行业（{covered / len(merged) * 100:.0f}%）")

    merged = merged.sort_values("动量分位", ascending=False)
    merged.insert(0, "排名", range(1, len(merged) + 1))

    output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output, index=False, encoding="utf-8-sig")
    logger.info(
        f"{output} 已生成: {len(merged)} 行 x {len(merged.columns)} 列 | "
        f"K线日期 {merged['K线日期'].mode().iloc[0]}"
    )
    return merged


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("industry_rotation.log")
    build()
