"""涨跌幅计算、数据标准化"""

import pandas as pd
import numpy as np


def calc_change_pct(df: pd.DataFrame, days: int) -> float:
    """计算 N 日涨跌幅百分比"""
    if df is None or df.empty or len(df) < 2:
        return np.nan
    close_col = "close" if "close" in df.columns else None
    if close_col is None:
        return np.nan
    recent = df[close_col].dropna()
    if len(recent) < 2:
        return np.nan
    current = recent.iloc[-1]
    idx = max(0, len(recent) - days - 1)
    base = recent.iloc[idx]
    if base == 0:
        return np.nan
    return round((current - base) / base * 100, 2)


def get_latest_price(df: pd.DataFrame) -> dict:
    """获取最新价格信息"""
    if df is None or df.empty:
        return {"close": None, "volume": None, "change_1d": None}
    close_col = "close" if "close" in df.columns else None
    vol_col = "volume" if "volume" in df.columns else None
    if close_col is None:
        return {"close": None, "volume": None, "change_1d": None}

    latest_close = df[close_col].iloc[-1]
    volume = df[vol_col].iloc[-1] if vol_col and len(df) > 0 else None
    change_1d = calc_change_pct(df, 1)

    return {
        "close": round(float(latest_close), 2) if pd.notna(latest_close) else None,
        "volume": int(volume) if pd.notna(volume) else None,
        "change_1d": change_1d,
    }


def build_overview_row(symbol: str, name: str, tier: str, exchange: str,
                       df: pd.DataFrame) -> dict:
    """构建总览表的一行数据"""
    price_info = get_latest_price(df)
    return {
        "梯队": tier,
        "品种": name,
        "代码": symbol,
        "交易所": exchange,
        "最新价": price_info["close"],
        "日涨跌%": price_info["change_1d"],
        "4日涨跌%": calc_change_pct(df, 4),
        "半月涨跌%": calc_change_pct(df, 10),
        "成交量": price_info["volume"],
    }


def get_sparkline_data(df: pd.DataFrame, n: int = 15) -> list:
    """获取迷你走势图数据（最近 N 天收盘价）"""
    if df is None or df.empty:
        return []
    close_col = "close" if "close" in df.columns else None
    if close_col is None:
        return []
    data = df[close_col].dropna().tail(n).tolist()
    return [float(x) for x in data]


def build_heatmap_data(overview_rows: list) -> pd.DataFrame:
    """构建热力图数据"""
    if not overview_rows:
        return pd.DataFrame()
    df = pd.DataFrame(overview_rows)
    return df[["品种", "4日涨跌%", "半月涨跌%"]].dropna()
