"""行业信号回测：把「信号」变成可验证的规则

背景：docs/signals.md 记录了三类候选信号（短期反转 / 均线能量 / RS 平滑）
和它们的外部依据。本模块用现有 496 个行业日线做统一回测，回答一个具体问题：

    扣掉交易成本后，这些信号能不能跑赢「等权持有全部行业」和沪深300？

回测设定（尽量贴近可执行的 ETF 轮动）：
- 调仓日：每 N 个交易日一次（默认 20 日，即月频），当日收盘出信号
- 建仓：次一交易日按等权买入排名前 top_n 的行业
- 成本：单边 0.05%（ETF 佣金 + 冲击），按换手率计提
- 过滤：成交额 60 日均 > MIN_AMOUNT（流动性），且收盘价 > MA60（趋势未破坏）
- 出场：三种规则分别回测（见 EXIT_RULES）

用法：python -m utils.signal_backtest
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

HIST_DIR = Path("datas/raw/n_indexes/industry_hist")
BENCHMARK_FILE = Path("datas/raw/indexes/ak_index_global_hist_em_沪深300.csv")

WARMUP = 130            # 前 130 个交易日只算指标、不交易
MIN_AMOUNT = 1e8        # 成交额 60 日均下限（1 亿元）
COST_ONE_WAY = 0.0005   # 单边成本 0.05%
TOP_N = 5
REBAL = 20              # 默认 20 个交易日调仓一次


@dataclass
class Panels:
    """回测需要的数据面板（日期 × 行业）"""

    close: pd.DataFrame
    amount: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    benchmark: pd.Series

    def eligible(self) -> pd.DataFrame:
        """可交易掩码：流动性够 + 长期趋势未破坏"""
        amount_ok = self.amount.rolling(60, min_periods=20).mean() > MIN_AMOUNT
        trend_ok = self.close > self.close.rolling(60, min_periods=20).mean()
        return amount_ok & trend_ok


def load_panels() -> Panels:
    """读全部行业日线与沪深300基准"""
    fields = {"收盘": "close", "成交额": "amount", "最高": "high", "最低": "low"}
    collected: dict[str, dict[str, pd.Series]] = {k: {} for k in fields.values()}

    for path in sorted(HIST_DIR.glob("*.csv")):
        df = pd.read_csv(path)
        if "日期" not in df.columns or len(df) < 200:
            continue
        name = path.stem.split("_", 1)[-1]
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        df = df.dropna(subset=["日期"]).drop_duplicates("日期").set_index("日期")
        for raw, alias in fields.items():
            if raw in df.columns:
                collected[alias][name] = pd.to_numeric(df[raw], errors="coerce")

    close = pd.DataFrame(collected["close"]).sort_index().ffill()
    if close.empty:
        raise RuntimeError(f"{HIST_DIR} 下没有可用日线，先跑 utils.industry_hist")

    amount = pd.DataFrame(collected["amount"]).reindex(close.index).ffill()
    high = pd.DataFrame(collected["high"]).reindex(close.index).ffill()
    low = pd.DataFrame(collected["low"]).reindex(close.index).ffill()

    benchmark = _load_benchmark().reindex(close.index).ffill()

    logger.info(
        f"面板: {close.shape[0]} 交易日 × {close.shape[1]} 行业 | "
        f"{close.index[0].date()} ~ {close.index[-1].date()}"
    )
    return Panels(close, amount, high, low, benchmark)


def _load_benchmark() -> pd.Series:
    """沪深300 收盘价序列"""
    df = pd.read_csv(BENCHMARK_FILE)
    date_col = next((c for c in df.columns if "日期" in c), df.columns[0])
    price_col = next((c for c in ("收盘", "最新价", "close") if c in df.columns), None)
    if price_col is None:  # 老格式最后一列常是涨跌幅，取"最新价"兜底
        price_col = df.columns[4]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    series = (
        df.dropna(subset=[date_col])
        .drop_duplicates(date_col)
        .set_index(date_col)[price_col]
        .astype(float)
        .sort_index()
    )
    return series


# ---------------------------------------------------------------- 信号构造

def signal_reversal(panels: Panels, window: int = 5) -> pd.DataFrame:
    """短期反转：过去 window 日收益取负，跌得多的排前面"""
    return -(panels.close / panels.close.shift(window) - 1)


def signal_ma_energy(panels: Panels, window: int = 20) -> pd.DataFrame:
    """均线能量：MA20 连续同向变动的期数（上涨为正、下跌为负）"""
    ma = panels.close.rolling(window, min_periods=window).mean()
    energy = pd.DataFrame(np.nan, index=ma.index, columns=ma.columns)
    for col in ma.columns:
        sign = np.sign(ma[col].diff())
        # 方向不变的连续段计数：方向一变就开新组
        run = sign.groupby(sign.ne(sign.shift()).cumsum()).cumcount() + 1
        energy[col] = (run * sign).fillna(0.0).where(ma[col].notna())
    return energy


def signal_rs_ema(panels: Panels, window: int = 20, smooth: int = 7) -> pd.DataFrame:
    """相对强弱：行业 window 日涨幅 − 沪深300 涨幅，再 EMA 平滑"""
    bench = panels.benchmark
    bench_ret = bench / bench.shift(window) - 1
    industry_ret = panels.close / panels.close.shift(window) - 1
    raw = industry_ret.sub(bench_ret, axis=0)
    return raw.ewm(span=smooth, adjust=False, min_periods=smooth).mean()


# ---------------------------------------------------------------- 回测引擎

@dataclass
class Strategy:
    name: str
    signal: pd.DataFrame
    rebal: int = REBAL
    top_n: int = TOP_N
    exit_rule: str = "hold"          # hold | ma20 | atr2
    use_filter: bool = True          # 是否用「流动性 + 趋势」过滤
    notes: str = ""
    result: dict = field(default_factory=dict)


def _atr14(panels: Panels) -> pd.DataFrame:
    """ATR14：真实波幅（最高−最低、|最高−昨收|、|最低−昨收| 三者取大）的 14 日均值"""
    prev_close = panels.close.shift(1)
    true_range = np.maximum(
        np.maximum(panels.high - panels.low, (panels.high - prev_close).abs()),
        (panels.low - prev_close).abs(),
    )
    return pd.DataFrame(true_range, index=panels.close.index, columns=panels.close.columns).rolling(
        14, min_periods=10
    ).mean()


def run(strategy: Strategy, panels: Panels) -> dict:
    """逐日推进的组合回测，返回绩效字典"""
    close = panels.close
    dates = close.index
    daily_ret = close.pct_change().fillna(0.0)
    eligible = panels.eligible()
    atr = _atr14(panels) if strategy.exit_rule == "atr2" else None
    ma20 = close.rolling(20, min_periods=20).mean() if strategy.exit_rule == "ma20" else None

    weights = pd.Series(0.0, index=close.columns)
    peak_price: dict[str, float] = {}
    nav, turnovers = [1.0], []
    held_days = 0

    for i in range(WARMUP, len(dates) - 1):
        date = dates[i]
        today_close = close.loc[date]

        # 1) 出场检查（当日收盘判断，次日生效 → 用当日收益近似，不做未来函数）
        if strategy.exit_rule != "hold" and len(weights[weights > 0]):
            for code in list(weights[weights > 0].index):
                price = today_close.get(code, np.nan)
                if pd.isna(price):
                    continue
                peak_price[code] = max(peak_price.get(code, price), price)
                if strategy.exit_rule == "ma20":
                    ma = ma20.loc[date, code]
                    if pd.notna(ma) and price < ma:
                        weights[code] = 0.0
                else:
                    a = atr.loc[date, code]
                    if pd.notna(a) and price < peak_price[code] - 2 * a:
                        weights[code] = 0.0

        # 2) 调仓
        cost = 0.0
        if i % strategy.rebal == 0:
            scores = strategy.signal.loc[date]
            if strategy.use_filter:
                ok = eligible.loc[date].reindex(scores.index).fillna(False)
            else:
                ok = pd.Series(True, index=scores.index)
            candidates = scores[ok & scores.notna()].nlargest(strategy.top_n)
            target = pd.Series(0.0, index=close.columns)
            if len(candidates):
                target[candidates.index] = 1.0 / len(candidates)

            turnover = (target - weights).abs().sum() / 2
            cost = 2 * turnover * COST_ONE_WAY
            turnovers.append(turnover)
            weights = target
            for code in weights[weights > 0].index:
                peak_price[code] = today_close.get(code, np.nan)

        if len(weights[weights > 0]):
            held_days += 1

        # 3) 次日收益（T 日出信号、T+1 持有 → 用下一日收益，无未来函数）
        next_ret = daily_ret.iloc[i + 1]
        port_ret = float((weights * next_ret).sum()) - cost
        nav.append(nav[-1] * (1 + port_ret))

    return _metrics(pd.Series(nav, index=dates[WARMUP:]), turnovers, held_days, strategy.rebal)


def run_equal_weight(panels: Panels) -> dict:
    """基准一：等权持有全部 496 个行业（不做任何筛选）"""
    daily_ret = panels.close.pct_change().iloc[WARMUP + 1:]
    nav = (1 + daily_ret.mean(axis=1).fillna(0)).cumprod()
    return _metrics(nav, [0.0], len(nav), REBAL)


def run_benchmark(panels: Panels) -> dict:
    """基准二：沪深300 买入持有"""
    bench = panels.benchmark.iloc[WARMUP + 1:]
    nav = (bench / bench.iloc[0]).dropna()
    return _metrics(nav, [0.0], len(nav), REBAL)


def _metrics(nav: pd.Series, turnovers: list[float], held_days: int, rebal: int) -> dict:
    """由净值序列算绩效指标"""
    if len(nav) < 20:
        return {}

    nav = nav.dropna()
    ret = nav.pct_change().dropna()
    years = len(nav) / 252
    total = nav.iloc[-1] / nav.iloc[0] - 1
    annual = (1 + total) ** (1 / years) - 1 if years > 0 else np.nan
    vol = ret.std() * np.sqrt(252)
    sharpe = (annual - 0.02) / vol if vol > 0 else np.nan       # 无风险利率 2%
    drawdown = nav / nav.cummax() - 1
    max_dd = drawdown.min()
    calmar = annual / abs(max_dd) if max_dd else np.nan

    monthly = (1 + ret).resample("ME").prod() - 1
    win_rate = (monthly > 0).mean() if len(monthly) else np.nan
    turnover_per_year = np.mean(turnovers) * 252 / rebal if turnovers and rebal else 0

    return {
        "累计收益": round(total * 100, 1),
        "年化收益": round(annual * 100, 1),
        "年化波动": round(vol * 100, 1),
        "夏普": round(sharpe, 2),
        "最大回撤": round(max_dd * 100, 1),
        "Calmar": round(calmar, 2),
        "月度胜率": round(win_rate * 100, 0),
        "年换手": round(turnover_per_year, 1),
        "持仓占比": round(held_days / max(len(nav), 1) * 100, 0),
    }


def build_strategies(panels: Panels) -> list[Strategy]:
    """待测策略清单"""
    rev5 = signal_reversal(panels, 5)
    rev20 = signal_reversal(panels, 20)
    energy = signal_ma_energy(panels, 20)
    rs = signal_rs_ema(panels, 20, 7)

    return [
        Strategy("反转5日_周频", rev5, rebal=5, notes="每5日调仓，持有到下次调仓"),
        Strategy("反转20日_月频", rev20, rebal=20, notes="20日反转，月频"),
        Strategy("反转5日_月频", rev5, rebal=20, notes="信号用5日，月频调仓"),
        Strategy("均线能量_月频", energy, rebal=20, notes="MA20 连续上涨期数"),
        Strategy("RS平滑_月频", rs, rebal=20, notes="EMA(RS20, 7)"),
        Strategy("反转20日_MA20止损", rev20, rebal=20, exit_rule="ma20", notes="跌破MA20出场"),
        Strategy("反转20日_ATR2止损", rev20, rebal=20, exit_rule="atr2", notes="2×ATR 移动止损"),
    ]


def sweep(panels: Panels) -> pd.DataFrame:
    """参数扫描：三个信号 × 持仓数 × 调仓频率，看结果稳不稳定

    单组结果（5 只持仓）噪声很大，必须看参数敏感性：
    如果只有某一组好看、邻域全崩，那就是过拟合。
    """
    signals = {
        "反转5日": signal_reversal(panels, 5),
        "反转20日": signal_reversal(panels, 20),
        "均线能量": signal_ma_energy(panels, 20),
        "RS平滑": signal_rs_ema(panels, 20, 7),
        # 随机对照：分数与任何信息无关，用来判断「是信号无效」还是「过滤条件本身拖后腿」
        "随机对照": pd.DataFrame(
            np.random.default_rng(42).random(panels.close.shape),
            index=panels.close.index,
            columns=panels.close.columns,
        ),
    }
    rows = []
    for name, sig in signals.items():
        for top_n in (5, 10, 20):
            for rebal in (5, 10, 20, 60):
                result = run(Strategy(name, sig, rebal=rebal, top_n=top_n), panels)
                if result:
                    rows.append({"信号": name, "持仓数": top_n, "调仓日": rebal, "过滤": "是", **result})

    # 去掉「趋势/流动性」过滤，隔离过滤条件的贡献
    for name, sig in signals.items():
        for top_n in (20,):
            result = run(
                Strategy(name, sig, rebal=20, top_n=top_n, use_filter=False), panels
            )
            if result:
                rows.append({"信号": name, "持仓数": top_n, "调仓日": 20, "过滤": "否", **result})
    return pd.DataFrame(rows)


def report_sweep(table: pd.DataFrame, panels: Panels) -> pd.DataFrame:
    """打印扫描结果：每个信号的最好/最差，以及与基准的对比"""
    base_ew = run_equal_weight(panels)["年化收益"]
    base_hs = run_benchmark(panels)["年化收益"]
    logger.info(f"基准: 等权全行业 {base_ew}% | 沪深300 {base_hs}%")

    logger.info("=== 参数扫描（每组 12 种组合）===")
    for name, group in table[table["过滤"] == "是"].groupby("信号"):
        best = group.loc[group["年化收益"].idxmax()]
        worst = group.loc[group["年化收益"].idxmin()]
        median = group["年化收益"].median()
        logger.info(
            f"{name:<8} 中位数 {median:>6.1f}% | 最佳 {best['年化收益']:>6.1f}% "
            f"(持仓{int(best['持仓数'])}/调仓{int(best['调仓日'])}日) | "
            f"最差 {worst['年化收益']:>6.1f}% | 跑赢等权 {int((group['年化收益'] > base_ew).sum())}/12"
        )

    logger.info("=== 过滤条件的作用（持仓20/调仓20日）===")
    for name, group in table.groupby("信号"):
        row_on = group[(group["过滤"] == "是") & (group["持仓数"] == 20) & (group["调仓日"] == 20)]
        row_off = group[group["过滤"] == "否"]
        if len(row_on) and len(row_off):
            logger.info(
                f"{name:<8} 有过滤 {row_on['年化收益'].iloc[0]:>6.1f}% | "
                f"无过滤 {row_off['年化收益'].iloc[0]:>6.1f}%"
            )
    return table


def run_all(panels: Panels) -> pd.DataFrame:
    """跑全部策略并打印对比表"""
    rows = []
    for strategy in build_strategies(panels):
        result = run(strategy, panels)
        if not result:
            logger.warning(f"{strategy.name}: 样本不足，跳过")
            continue
        rows.append({"策略": strategy.name, **result, "说明": strategy.notes})
        logger.info(f"{strategy.name} 完成: 年化 {result['年化收益']}% / 夏普 {result['夏普']}")

    for name, func in (("等权全行业", run_equal_weight), ("沪深300", run_benchmark)):
        result = func(panels)
        rows.append({"策略": name, **result, "说明": "基准"})

    table = pd.DataFrame(rows)
    logger.info("=== 回测结果（默认成本：单边 0.05%）===")
    for _, row in table.iterrows():
        logger.info(
            f"{row['策略']:<18} 年化 {row['年化收益']:>6.1f}% | 夏普 {row['夏普']:>5.2f} | "
            f"回撤 {row['最大回撤']:>6.1f}% | 月度胜率 {row['月度胜率']:>3.0f}% | "
            f"年换手 {row['年换手']:>4.1f} | 持仓 {row['持仓占比']:>3.0f}%"
        )
    return table


def main():
    import argparse

    from utils.set_log import set_log

    parser = argparse.ArgumentParser(description="行业信号回测")
    parser.add_argument("--sweep", action="store_true", help="跑参数扫描（信号×持仓数×调仓频率）")
    args = parser.parse_args()

    set_log("signal_backtest.log")
    panels = load_panels()
    out = Path("datas/processed/n_indexes/signal_backtest.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.sweep:
        table = report_sweep(sweep(panels), panels)
        out = out.with_name("signal_backtest_sweep.csv")
    else:
        table = run_all(panels)

    table.to_csv(out, index=False, encoding="utf-8-sig")
    logger.info(f"结果已写入 {out}")
    return table


if __name__ == "__main__":
    main()
