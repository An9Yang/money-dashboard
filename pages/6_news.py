"""实时资讯 — 财联社电报（大宗商品相关）"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from data.news_client import get_news, DEFAULT_KEYWORDS

st.set_page_config(page_title="实时资讯", page_icon="📰", layout="wide")
st.title("实时资讯")
st.caption("财联社电报 — 大宗商品及能源相关资讯实时追踪")

# --- 侧边栏：自定义关键词 + 自动刷新 ---
with st.sidebar:
    st.header("刷新设置")
    auto_refresh = st.toggle("自动刷新", value=True)
    refresh_interval = st.select_slider(
        "刷新间隔",
        options=[30, 60, 120, 300],
        value=60,
        format_func=lambda x: f"{x} 秒" if x < 60 else f"{x // 60} 分钟",
    )
    if auto_refresh:
        st_autorefresh(interval=refresh_interval * 1000, key="news_refresh")
    st.caption(f"最后刷新: {datetime.now().strftime('%H:%M:%S')}")

    st.divider()
    st.header("关键词过滤")
    use_custom = st.toggle("自定义关键词", value=False)
    if use_custom:
        custom_input = st.text_area(
            "输入关键词（每行一个）",
            value="\n".join(DEFAULT_KEYWORDS),
            height=200,
        )
        keywords = [k.strip() for k in custom_input.strip().split("\n") if k.strip()]
    else:
        keywords = DEFAULT_KEYWORDS

    st.divider()
    st.caption(f"当前过滤关键词: {len(keywords)} 个")
    limit = st.slider("显示条数", min_value=10, max_value=100, value=30, step=10)

# --- 加载新闻 ---
with st.spinner("正在获取最新资讯..."):
    news_df = get_news(keywords=keywords, limit=limit)

if news_df.empty:
    st.info("暂无匹配的资讯，请尝试调整关键词")
else:
    st.success(f"共找到 {len(news_df)} 条相关资讯")

    for i, row in news_df.iterrows():
        time_str = str(row.get("时间", ""))
        title = str(row.get("标题", ""))
        content = str(row.get("内容", ""))

        with st.container():
            col_time, col_content = st.columns([1, 5])
            with col_time:
                st.caption(time_str)
            with col_content:
                st.markdown(f"**{title}**")
                if content and content != title and content != "nan":
                    st.caption(content[:200])
            st.divider()
