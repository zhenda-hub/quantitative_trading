"""标准口径 GDP 同比数据

与 jin10 日历口径（GDP年率报告, 已停在 2025-09）并存，互不影响：
- 美国 / 德国 / 欧元区19: FRED 实际GDP（季调、链式、SNA2008）→ 自算同比
- 中国: 国家统计局季度「累计」同比（口径与其余三条不同, 列名已标注）

输出: datas/processed/gdps/std_gdp_growth.csv
列: date, usa, germany, euro19, china_cumulative
"""
from __future__ import annotations

import csv
import io
import re
import urllib.request
from pathlib import Path

import akshare as ak
import pandas as pd
from loguru import logger

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
FRED_SERIES = {
    "usa": "GDPC1",
    "germany": "CLVMNACSCAB1GQDE",
    "euro19": "CLVMNACSCAB1GQEA19",
}
OUTPUT = Path("datas/processed/gdps/std_gdp_growth.csv")


def fetch_fred_level(series_id: str, timeout: int = 30, retry: int = 3):
    """取 FRED 实际 GDP 水平值（季调、链式、SNA2008）

    Args:
        series_id: FRED series id, 如 GDPC1
        timeout: 单次请求超时秒数
        retry: 重试次数

    Returns:
        pd.Series(index=date, values=level), 失败返回 None
    """
    last_error = None
    for attempt in range(1, retry + 1):
        try:
            request = urllib.request.Request(
                FRED_URL.format(sid=series_id), headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8", "ignore")
            rows = list(csv.reader(io.StringIO(text)))[1:]
            df = pd.DataFrame(rows, columns=["date", "value"])
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            series = df.dropna().set_index("date")["value"].sort_index()
            logger.info(
                f"FRED {series_id}: {len(series)} 个季度, 最新 {series.index[-1].date()}"
            )
            return series
        except Exception as error:  # noqa: BLE001 - 网络异常类型多样
            last_error = error
            logger.warning(f"FRED {series_id} 第 {attempt}/{retry} 次失败: {error}")
    logger.error(f"FRED {series_id} 最终失败: {last_error}")
    return None


def quarter_label_to_date(label: str):
    """把 '2026年第1-3季度' 这类标签转成该季度首日

    Examples:
        '2026年第1季度'   -> 2026-01-01
        '2026年第1-3季度' -> 2026-07-01
    """
    digits = re.findall(r"\d+", str(label))
    if len(digits) < 2:
        return pd.NaT
    year, quarter = int(digits[0]), int(digits[-1])
    month_map = {1: 1, 2: 4, 3: 7, 4: 10}
    if quarter not in month_map:
        return pd.NaT
    return pd.Timestamp(year=year, month=month_map[quarter], day=1)


def fetch_china_cumulative(retry: int = 3):
    """取国家统计局季度 GDP 累计同比（%）

    注意: 这是「年初至今累计同比」, 与单季同比不同; Q1 两者相同, 之后分叉。

    Returns:
        pd.Series(index=date, values=累计同比 %), 失败返回 None
    """
    last_error = None
    for attempt in range(1, retry + 1):
        try:
            raw = ak.macro_china_gdp()
            df = raw[["季度", "国内生产总值-同比增长"]].copy()
            df["date"] = df["季度"].map(quarter_label_to_date)
            df["value"] = pd.to_numeric(df["国内生产总值-同比增长"], errors="coerce")
            df = df.dropna(subset=["date", "value"])
            series = df.set_index("date")["value"].sort_index()
            logger.info(
                f"中国统计局: {len(series)} 个季度, 最新 {series.index[-1].date()}"
            )
            return series
        except Exception as error:  # noqa: BLE001
            last_error = error
            logger.warning(f"中国 GDP 第 {attempt}/{retry} 次失败: {error}")
    logger.error(f"中国 GDP 最终失败: {last_error}")
    return None


def build_std_gdp(output: Path = OUTPUT) -> Path | None:
    """抓取并合并标准口径 GDP 同比, 写出 csv

    Returns:
        输出路径, 全部失败时返回 None
    """
    frames = {}

    for name, series_id in FRED_SERIES.items():
        level = fetch_fred_level(series_id)
        if level is None or len(level) < 5:
            logger.warning(f"{name} 数据不足, 跳过")
            continue
        # 同比: 本期 / 去年同期 - 1
        yoy = (level / level.shift(4) - 1) * 100
        frames[name] = yoy.dropna().round(2)

    china = fetch_china_cumulative()
    if china is not None:
        frames["china_cumulative"] = china.round(2)

    if not frames:
        logger.error("全部数据源失败, 未生成文件")
        return None

    merged = pd.concat(frames, axis=1).sort_index()
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

    set_log("gdp_std.log")
    build_std_gdp()
