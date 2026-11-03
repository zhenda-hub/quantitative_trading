"""行业估值自算（PE/PB）

数据来源：
- 行业成分股：ak.stock_board_industry_cons_em(symbol=板块名) —— 含个股 PE(动态)/PB
- 个股市值：datas/raw/stocks/ef_沪深A股.csv —— 总市值/流通市值（用于加权）

计算口径：
- PE 中位数：剔除 PE<=0（亏损）与缺失后的中位数，对极值稳健
- PE 加权：Σ流通市值 / Σ(流通市值 / PE) —— 等价于「流通市值 / 成分股合计盈利」
- PB 同法；另记录负 PE 占比（行业整体亏损面）

输出：datas/processed/n_indexes/industry_valuation.csv
     （按 (日期, 板块代码) 去重后追加，需要多次运行才能积累历史分位）
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import akshare as ak
import pandas as pd
from loguru import logger

OUTPUT = Path("datas/processed/n_indexes/industry_valuation.csv")
STOCK_SNAPSHOT = Path("datas/raw/stocks/ef_沪深A股.csv")

PE_LIMIT = 500.0     # 超过视为异常，不参与加权（中位数天然稳健）
WORKERS = 4          # 并发数（过高容易被限流）
CALL_TIMEOUT = 40    # 单个接口超时（秒）
RETRY = 2


def _call_with_timeout(fn, timeout=CALL_TIMEOUT):
    """在守护线程里执行，超时返回 None（防止 akshare 卡死整轮）"""
    box = {}

    def worker():
        try:
            box["value"] = fn()
        except Exception as error:  # noqa: BLE001
            box["error"] = error

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None, "timeout"
    if "error" in box:
        return None, f"{type(box['error']).__name__}: {box['error']}"
    return box.get("value"), None


def load_stock_market_cap() -> pd.DataFrame:
    """读个股快照，取 代码 -> 流通市值/总市值"""
    df = pd.read_csv(STOCK_SNAPSHOT, dtype={"股票代码": str})
    df["股票代码"] = df["股票代码"].astype(str).str.zfill(6)
    for column in ("流通市值", "总市值"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df[["股票代码", "流通市值", "总市值"]].dropna(subset=["流通市值"])


def compute_one(industry: str, industry_code: str, cap: pd.DataFrame) -> dict | None:
    """计算单个行业的估值指标"""
    members = None
    for attempt in range(1, RETRY + 1):
        members, error = _call_with_timeout(
            lambda: ak.stock_board_industry_cons_em(symbol=industry)
        )
        if members is not None and len(members):
            break
        if attempt == RETRY:
            logger.warning(f"[{industry}] 成分股获取失败: {error or '空数据'}")
            return None

    df = members.copy()
    df["代码"] = df["代码"].astype(str).str.zfill(6)
    df["市盈率-动态"] = pd.to_numeric(df["市盈率-动态"], errors="coerce")
    df["市净率"] = pd.to_numeric(df["市净率"], errors="coerce")
    df = df.merge(cap, left_on="代码", right_on="股票代码", how="left")

    total = len(df)
    pe = df["市盈率-动态"]
    pb = df["市净率"]
    weight = df["流通市值"]

    pe_valid = pe[(pe > 0) & (pe <= PE_LIMIT)]
    pb_valid = pb[(pb > 0) & (pb <= PE_LIMIT)]
    negative_pe = int((pe <= 0).sum())

    # 加权 PE = Σ流通市值 / Σ(流通市值/PE)，只用 PE 有效的成分股
    mask = pe.notna() & weight.notna() & (pe > 0) & (pe <= PE_LIMIT)
    pe_weighted = (
        weight[mask].sum() / (weight[mask] / pe[mask]).sum()
        if mask.any() and (weight[mask] / pe[mask]).sum() > 0
        else None
    )

    mask_pb = pb.notna() & weight.notna() & (pb > 0) & (pb <= PE_LIMIT)
    pb_weighted = (
        weight[mask_pb].sum() / (weight[mask_pb] / pb[mask_pb]).sum()
        if mask_pb.any() and (weight[mask_pb] / pb[mask_pb]).sum() > 0
        else None
    )

    return {
        "板块代码": industry_code,
        "板块名称": industry,
        "成分数": total,
        "PE有效数": int(pe_valid.notna().sum()),
        "PE中位数": round(float(pe_valid.median()), 2) if len(pe_valid) else None,
        "PE加权": round(float(pe_weighted), 2) if pe_weighted else None,
        "PB中位数": round(float(pb_valid.median()), 2) if len(pb_valid) else None,
        "PB加权": round(float(pb_weighted), 2) if pb_weighted else None,
        "负PE占比": round(negative_pe / total * 100, 1) if total else None,
    }


def build_industry_valuation(output: Path = OUTPUT) -> Path | None:
    """抓全部行业成分股并计算估值，按日期追加去重后落盘"""
    industries, error = _call_with_timeout(ak.stock_board_industry_name_em, timeout=60)
    if industries is None:
        logger.error(f"行业列表获取失败: {error}")
        return None

    pairs = list(zip(industries["板块名称"].astype(str), industries["板块代码"].astype(str)))
    logger.info(f"行业数: {len(pairs)}，并发 {WORKERS}，预计 {len(pairs) * 1.2 / WORKERS / 60:.1f} 分钟")

    cap = load_stock_market_cap()
    logger.info(f"个股市值快照: {len(cap)} 行")

    rows, failed = [], []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(compute_one, name, code, cap): name for name, code in pairs
        }
        for index, future in enumerate(as_completed(futures), start=1):
            name = futures[future]
            try:
                result = future.result()
            except Exception as error:  # noqa: BLE001
                failed.append(name)
                logger.warning(f"[{name}] 计算异常: {error}")
                continue
            if result is None:
                failed.append(name)
                continue
            rows.append(result)
            if index % 100 == 0:
                logger.info(f"进度 {index}/{len(pairs)}，成功 {len(rows)}，失败 {len(failed)}")

    if not rows:
        logger.error("没有任何行业计算成功")
        return None

    today = date.today().isoformat()
    result = pd.DataFrame(rows)
    result.insert(0, "日期", today)

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        history = pd.read_csv(output, dtype={"板块代码": str})
        merged = pd.concat([history, result], ignore_index=True)
    else:
        merged = result
    merged = merged.drop_duplicates(subset=["日期", "板块代码"], keep="last")
    merged = merged.sort_values(["日期", "板块代码"])
    merged.to_csv(output, index=False)

    logger.info(
        f"{output} 已更新: 本次 {len(result)} 个行业（失败 {len(failed)}），"
        f"累计 {len(merged)} 行 / {merged['日期'].nunique()} 个交易日"
    )
    if failed:
        logger.warning(f"失败行业 {len(failed)} 个: {', '.join(failed[:10])}{' …' if len(failed) > 10 else ''}")
    return output


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("industry_valuation.log")
    build_industry_valuation()
