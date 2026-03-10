"""yfinance 数据获取客户端（带缓存，失败不缓存，自动重试）"""

import time
import streamlit as st
import yfinance as yf
import pandas as pd
from config import CACHE_TTL

_MAX_RETRIES = 3


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns from yfinance and normalize to lowercase."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df.columns = [str(c).lower().strip() for c in df.columns]
    if "adj close" in df.columns:
        df = df.rename(columns={"adj close": "adj_close"})
    # 确保 OHLCV 列为数值类型
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _fetch_with_retry(symbol: str, period: str, interval: str) -> pd.DataFrame:
    """带重试的 yfinance 数据获取"""
    last_err = None
    for attempt in range(_MAX_RETRIES):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            last_err = e
        if attempt < _MAX_RETRIES - 1:
            time.sleep(1)
    raise ValueError(f"{symbol} 在 {_MAX_RETRIES} 次尝试后仍失败: {last_err or '返回空数据'}")


@st.cache_data(ttl=CACHE_TTL["yfinance"])
def _fetch_daily_data(symbol: str, period: str = "3mo") -> pd.DataFrame:
    """内部：获取日线，失败时抛异常（不会被缓存）"""
    df = _fetch_with_retry(symbol, period, "1d")
    df = df.reset_index()
    df = _flatten_columns(df)
    return df


def get_daily_data(symbol: str, period: str = "3mo") -> pd.DataFrame:
    """获取单品种日线数据"""
    try:
        return _fetch_daily_data(symbol, period)
    except Exception as e:
        st.warning(f"获取 {symbol} 日线失败: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL["yfinance"])
def _fetch_hourly_data(symbol: str, period: str = "5d") -> pd.DataFrame:
    """内部：获取小时线，失败时抛异常（不会被缓存）"""
    df = _fetch_with_retry(symbol, period, "1h")
    df = df.reset_index()
    df = _flatten_columns(df)
    if "datetime" not in df.columns and "date" not in df.columns:
        first_col = df.columns[0]
        if pd.api.types.is_datetime64_any_dtype(df[first_col]):
            df = df.rename(columns={first_col: "datetime"})
    return df


def get_hourly_data(symbol: str, period: str = "5d") -> pd.DataFrame:
    """获取小时线数据"""
    try:
        return _fetch_hourly_data(symbol, period)
    except Exception as e:
        st.warning(f"获取 {symbol} 小时线失败: {e}")
        return pd.DataFrame()


def get_daily_batch(symbols: list, period: str = "3mo") -> dict:
    """批量获取日线数据"""
    result = {}
    for symbol in symbols:
        result[symbol] = get_daily_data(symbol, period)
    return result
