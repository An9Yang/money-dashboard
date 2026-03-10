"""财联社全球资讯获取客户端（带缓存）"""

import streamlit as st
import akshare as ak
import pandas as pd
from config import CACHE_TTL

DEFAULT_KEYWORDS = [
    "原油", "中东", "伊朗", "能源", "石化", "冲突", "制裁",
    "OPEC", "油价", "天然气", "沙特", "俄罗斯", "成品油",
    "LPG", "燃料油", "化工", "甲醇", "PTA", "乙二醇",
]


@st.cache_data(ttl=CACHE_TTL["realtime"])
def _fetch_global_news() -> pd.DataFrame:
    """获取财联社全球资讯原始数据"""
    df = ak.stock_info_global_cls()
    if df is None or df.empty:
        raise ValueError("财联社资讯返回空数据")
    return df


def get_news(keywords: list = None, limit: int = 30) -> pd.DataFrame:
    """获取过滤后的新闻列表"""
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    try:
        df = _fetch_global_news()
    except Exception as e:
        st.warning(f"获取新闻数据失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    # stock_info_global_cls 返回列: 标题, 内容, 发布日期, 发布时间
    # 关键词过滤：标题或内容包含任一关键词
    pattern = "|".join(keywords)
    mask = pd.Series(False, index=df.index)
    for col in ["标题", "内容"]:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.contains(pattern, na=False)

    filtered = df[mask].head(limit).copy()

    # 合并日期+时间为一列
    if "发布日期" in filtered.columns and "发布时间" in filtered.columns:
        filtered["时间"] = filtered["发布日期"].astype(str) + " " + filtered["发布时间"].astype(str)
    elif "发布时间" in filtered.columns:
        filtered["时间"] = filtered["发布时间"].astype(str)

    cols = [c for c in ["时间", "标题", "内容"] if c in filtered.columns]
    return filtered[cols].reset_index(drop=True)
