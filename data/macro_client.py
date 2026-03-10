"""宏观指标数据获取（PPI/CPI/PMI，失败不缓存）"""

import streamlit as st
import akshare as ak
import pandas as pd
import requests
from config import CACHE_TTL

# 缩短 akshare 底层 HTTP 超时，避免在 Cloud 上长时间挂起
_TIMEOUT = 15  # 秒
_original_get = requests.Session.get


def _patched_get(self, *args, **kwargs):
    kwargs.setdefault("timeout", _TIMEOUT)
    return _original_get(self, *args, **kwargs)


requests.Session.get = _patched_get


@st.cache_data(ttl=CACHE_TTL["macro"])
def _fetch_ppi() -> pd.DataFrame:
    df = ak.macro_china_ppi_yearly()
    if df is None or df.empty:
        raise ValueError("PPI 返回空数据")
    df = df.rename(columns={"日期": "date", "今值": "value", "预测值": "forecast", "前值": "previous"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def get_ppi() -> pd.DataFrame:
    """获取 PPI 数据"""
    try:
        return _fetch_ppi()
    except Exception as e:
        st.warning(f"获取 PPI 数据失败: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL["macro"])
def _fetch_cpi() -> pd.DataFrame:
    df = ak.macro_china_cpi_yearly()
    if df is None or df.empty:
        raise ValueError("CPI 返回空数据")
    df = df.rename(columns={"日期": "date", "今值": "value", "预测值": "forecast", "前值": "previous"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def get_cpi() -> pd.DataFrame:
    """获取 CPI 数据"""
    try:
        return _fetch_cpi()
    except Exception as e:
        st.warning(f"获取 CPI 数据失败: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL["macro"])
def _fetch_pmi() -> pd.DataFrame:
    df = ak.macro_china_pmi()
    if df is None or df.empty:
        raise ValueError("PMI 返回空数据")
    df = df.rename(columns={"月份": "date", "制造业-指数": "value"})
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = df["date"].str.replace("年", "-").str.replace("月份", "-01")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def get_pmi() -> pd.DataFrame:
    """获取 PMI 数据"""
    try:
        return _fetch_pmi()
    except Exception as e:
        st.warning(f"获取 PMI 数据失败: {e}")
        return pd.DataFrame()
