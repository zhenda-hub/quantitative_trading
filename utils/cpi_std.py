"""标准口径 CPI 同比数据

各国用「本国最权威的官方口径」，来源逐列标注：

- 美国      : FRED ``CPIAUCSL``（BLS 原始指数, 季调）→ 自算同比
- 欧元区19  : Eurostat HICP 月度同比（COICOP 统一口径）
- 德国      : Eurostat HICP 月度同比（同上）
- 中国/日本/澳大利亚/加拿大: 沿用东财已有合并结果（各国官方口径, 非国际统一库）

输出: datas/processed/cpis/std_cpi_growth.csv
列  : date, usa, euro19, germany, china, japan, australia, canada
"""
from __future__ import annotations

import csv
import io
import json
import urllib.request
from pathlib import Path

import pandas as pd
from loguru import logger

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
FRED_SERIES = {"usa": "CPIAUCSL"}

EUROSTAT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "prc_hicp_manr?format=JSON&lang=EN&freq=M&unit=RCH_A&coicop=CP00&geo={geo}"
)
EUROSTAT_GEO = {"euro19": "EA20", "germany": "DE"}

# 东财已合并结果里沿用的列（这些国家没有收录进 HICP/IFS 的免费月度源）
DONGCAI_PATH = Path("datas/processed/cpis/all_data.csv")
DONGCAI_COLUMNS = ["china", "japan", "australia", "canada"]
# FRED 不可用时, 美国回落到东财口径（日志会告警）
DONGCAI_FALLBACK = ["usa"]

OUTPUT = Path("datas/processed/cpis/std_cpi_growth.csv")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def _fetch(url: str, timeout: int = 30, retry: int = 3, pause: int = 8) -> str:
    """带重试的 GET（FRED 连续请求会限速, 因此需要退避）"""
    import time

    last_error = None
    for attempt in range(1, retry + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", "ignore")
        except Exception as error:  # noqa: BLE001 - 网络异常类型多样
            last_error = error
            logger.warning(f"请求失败 第 {attempt}/{retry} 次: {error}")
            if attempt < retry:
                time.sleep(pause * attempt)
    raise RuntimeError(f"请求最终失败: {last_error}")


def fetch_fred_index(series_id: str):
    """取 FRED 指数序列（月度）

    Returns:
        pd.Series(index=month_start, values=index), 失败返回 None
    """
    try:
        text = _fetch(FRED_URL.format(sid=series_id))
    except RuntimeError as error:
        logger.error(f"FRED {series_id} 获取失败: {error}")
        return None

    rows = list(csv.reader(io.StringIO(text)))[1:]
    df = pd.DataFrame(rows, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    series = df.dropna().set_index("date")["value"].sort_index()
    logger.info(f"FRED {series_id}: {len(series)} 期, 最新 {series.index[-1].date()}")
    return series


def fetch_eurostat_hicp(geo: str, retry: int = 3, pause: int = 8):
    """取 Eurostat HICP 月度同比（%）

    Args:
        geo: 地区代码, 如 EA20 / DE

    Returns:
        pd.Series(index=month_start, values=同比 %), 失败返回 None
    """
    try:
        payload = json.loads(_fetch(EUROSTAT_URL.format(geo=geo), retry=retry, pause=pause))
    except Exception as error:  # noqa: BLE001
        logger.error(f"Eurostat {geo} 获取失败: {error}")
        return None

    periods = payload.get("dimension", {}).get("time", {}).get("category", {}).get("index", {})
    values = payload.get("value", {})
    if not periods or not values:
        logger.error(f"Eurostat {geo} 返回空数据")
        return None

    records = []
    for period, position in periods.items():
        value = values.get(str(position))
        if value is None:
            continue
        records.append({"date": pd.Timestamp(f"{period}-01"), "value": float(value)})

    if not records:
        logger.error(f"Eurostat {geo} 无有效观测值")
        return None

    series = pd.DataFrame(records).set_index("date")["value"].sort_index()
    logger.info(
        f"Eurostat {geo} HICP: {len(series)} 期, 最新 {series.index[-1]:%Y-%m}, "
        f"数据集更新于 {payload.get('updated')}"
    )
    return series


def load_dongcai(china_path: Path = DONGCAI_PATH, columns=None):
    """读取东财合并结果, 只保留需要的列并统一到月初

    Args:
        china_path: 东财合并后的 csv
        columns: 需要的列, 默认主列 + 回落列
    """
    wanted = columns if columns is not None else DONGCAI_COLUMNS + DONGCAI_FALLBACK
    if not china_path.exists():
        logger.warning(f"{china_path} 不存在, 跳过东财列")
        return None

    df = pd.read_csv(china_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

    keep = ["date"] + [c for c in wanted if c in df.columns]
    if len(keep) == 1:
        logger.warning("东财文件里没有可用的列")
        return None

    df = df[keep].dropna(subset=keep[1:], how="all").set_index("date")
    logger.info(f"东财 CPI: {len(df)} 期, 最新 {df.index[-1]:%Y-%m}, 列 {keep[1:]}")
    return df


def build_std_cpi(output: Path = OUTPUT):
    """抓取并合并标准口径 CPI 同比, 写出 csv

    Returns:
        输出路径, 全部失败时返回 None
    """
    frames = {}

    for name, series_id in FRED_SERIES.items():
        index = fetch_fred_index(series_id)
        if index is None or len(index) < 13:
            logger.warning(f"{name} 数据不足, 跳过")
            continue
        # CPI 同比: 本月 / 去年同月 - 1
        frames[name] = ((index / index.shift(12) - 1) * 100).dropna().round(2)

    for name, geo in EUROSTAT_GEO.items():
        series = fetch_eurostat_hicp(geo)
        if series is not None:
            frames[name] = series.round(2)
        import time as _time

        _time.sleep(2)  # 给 Eurostat 留点间隔

    dongcai = load_dongcai()
    if dongcai is not None:
        for column in DONGCAI_COLUMNS:
            if column in dongcai.columns:
                frames[column] = dongcai[column].round(2)
        for column in DONGCAI_FALLBACK:
            if column not in frames and column in dongcai.columns:
                logger.warning(f"{column} 回落到东财口径（对应国际源不可用）")
                frames[column] = dongcai[column].round(2)

    if not frames:
        logger.error("全部数据源失败, 未生成文件")
        return None

    order = ["usa", "euro19", "germany", "china", "japan", "australia", "canada"]
    merged = pd.concat(frames, axis=1).sort_index()
    merged = merged[[c for c in order if c in merged.columns]]
    merged = merged.dropna(how="all")
    merged.index.name = "date"

    output.parent.mkdir(parents=True, exist_ok=True)
    result = merged.reset_index()
    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    result.to_csv(output, index=False)

    logger.info(
        f"{output} 已更新: {len(result)} 行, "
        f"区间 {result['date'].iloc[0]} ~ {result['date'].iloc[-1]}, "
        f"列 {list(result.columns)}"
    )
    return output


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("cpi_std.log")
    build_std_cpi()
