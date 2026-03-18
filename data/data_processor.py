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


def get_oi_data(df: pd.DataFrame, date_col: str = "date", n: int = 60) -> pd.DataFrame:
    """获取持仓量数据（最近 N 日）"""
    if df is None or df.empty or "hold" not in df.columns:
        return pd.DataFrame()
    cols = [date_col, "hold"] if date_col in df.columns else ["hold"]
    result = df[cols].tail(n).copy()
    result["hold"] = pd.to_numeric(result["hold"], errors="coerce")
    if date_col in result.columns:
        result["hold_change"] = result["hold"].diff()
    return result


def calc_spread(df1: pd.DataFrame, df2: pd.DataFrame,
                date_col1: str = "date", date_col2: str = "date",
                ratio: float = 1.0) -> pd.DataFrame:
    """计算两品种价差 (df1.close - df2.close * ratio)"""
    if df1 is None or df1.empty or df2 is None or df2.empty:
        return pd.DataFrame()
    s1 = df1[[date_col1, "close"]].copy().rename(columns={date_col1: "date", "close": "close1"})
    s2 = df2[[date_col2, "close"]].copy().rename(columns={date_col2: "date", "close": "close2"})
    s1["date"] = pd.to_datetime(s1["date"]).dt.date
    s2["date"] = pd.to_datetime(s2["date"]).dt.date
    merged = pd.merge(s1, s2, on="date", how="inner")
    merged["spread"] = merged["close1"] - merged["close2"] * ratio
    merged["date"] = pd.to_datetime(merged["date"])
    return merged


def calc_correlation_matrix(data_dict: dict, names_map: dict,
                            window: int = 20) -> pd.DataFrame:
    """计算品种间收益率相关性矩阵"""
    returns = {}
    for sym, df in data_dict.items():
        if df is not None and not df.empty and "close" in df.columns:
            name = names_map.get(sym, sym)
            close = pd.to_numeric(df["close"], errors="coerce").dropna()
            if len(close) >= window:
                returns[name] = close.pct_change().tail(window)
    if len(returns) < 2:
        return pd.DataFrame()
    ret_df = pd.DataFrame(returns)
    return ret_df.corr().round(2)


def normalize_prices(data_dict: dict, names_map: dict,
                     recent_n: int = 60) -> pd.DataFrame:
    """将多品种价格归一化为百分比变化（基准=第一天）用于叠加对比"""
    result = {}
    for sym, df in data_dict.items():
        if df is not None and not df.empty and "close" in df.columns:
            name = names_map.get(sym, sym)
            close = pd.to_numeric(df["close"], errors="coerce").dropna().tail(recent_n)
            if len(close) >= 2:
                base = close.iloc[0]
                if base != 0:
                    result[name] = ((close / base - 1) * 100).values
    if not result:
        return pd.DataFrame()
    max_len = max(len(v) for v in result.values())
    aligned = {}
    for name, vals in result.items():
        if len(vals) < max_len:
            aligned[name] = list(vals) + [np.nan] * (max_len - len(vals))
        else:
            aligned[name] = list(vals)
    return pd.DataFrame(aligned)
