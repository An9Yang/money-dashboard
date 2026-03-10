"""AKShare 数据获取客户端（带缓存，失败不缓存）"""

import streamlit as st
import akshare as ak
import pandas as pd
from config import CACHE_TTL


@st.cache_data(ttl=CACHE_TTL["daily"])
def _fetch_daily_kline(symbol: str, recent_n: int = 120) -> pd.DataFrame:
    """内部：获取日K线，失败时抛异常（不会被缓存）"""
    df = ak.futures_zh_daily_sina(symbol=symbol)
    if df is None or df.empty:
        raise ValueError(f"{symbol} 返回空数据")
    df.columns = [c.lower() for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df.tail(recent_n).reset_index(drop=True)


def get_daily_kline(symbol: str, recent_n: int = 120) -> pd.DataFrame:
    """获取日K线数据（主力连续合约）"""
    try:
        return _fetch_daily_kline(symbol, recent_n)
    except Exception as e:
        st.warning(f"获取 {symbol} 日K线失败: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL["minute"])
def _fetch_minute_kline(symbol: str, period: str = "60") -> pd.DataFrame:
    """内部：获取分钟K线，失败时抛异常（不会被缓存）"""
    df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
    if df is None or df.empty:
        raise ValueError(f"{symbol} 返回空数据")
    df.columns = [c.lower() for c in df.columns]
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").reset_index(drop=True)
    return df


def get_minute_kline(symbol: str, period: str = "60") -> pd.DataFrame:
    """获取分钟K线数据（1/5/15/30/60分钟）"""
    try:
        return _fetch_minute_kline(symbol, period)
    except Exception as e:
        st.warning(f"获取 {symbol} {period}分钟K线失败: {e}")
        return pd.DataFrame()


def get_daily_kline_batch(symbols: list, recent_n: int = 120) -> dict:
    """批量获取日K线数据"""
    result = {}
    for symbol in symbols:
        result[symbol] = get_daily_kline(symbol, recent_n)
    return result
