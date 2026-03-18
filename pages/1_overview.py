"""全品种总览 — 核心页面（并行加载 + 新闻预览 + 数据导出）"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from config import (AKSHARE_SYMBOLS, YFINANCE_SYMBOLS, TOP_METRICS,
                    TIER_GROUPS, AUTO_REFRESH_DEFAULT_MS, TIERS,
                    COLOR_SCHEMES, COLORS, ALERT_THRESHOLD_PCT,
                    TRADING_SESSIONS)
from data.akshare_client import get_daily_kline
from data.yfinance_client import get_daily_data
from data.data_processor import build_overview_row, build_heatmap_data, get_sparkline_data
from components.metrics import render_top_metrics
from components.tables import render_overview_table
from components.charts import create_heatmap, create_sparkline

# --- 侧边栏 ---
with st.sidebar:
    st.header("刷新设置")
    auto_refresh = st.toggle("自动刷新", value=True)
    refresh_interval = st.select_slider(
        "刷新间隔",
        options=[60, 120, 300, 600],
        value=300,
        format_func=lambda x: f"{x // 60} 分钟",
    )
    if auto_refresh:
        st_autorefresh(interval=refresh_interval * 1000, key="overview_refresh")

    st.divider()

    # 颜色方案切换
    st.header("显示设置")
    scheme_name = st.selectbox("涨跌颜色方案", list(COLOR_SCHEMES.keys()), index=0)
    st.session_state["color_scheme"] = COLOR_SCHEMES[scheme_name]
    colors = COLOR_SCHEMES[scheme_name]

    st.divider()
    st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 标题 ---
st.title("大宗商品期货监控")
st.caption("中东局势升级 — 原油及石化产业链品种实时追踪")


# --- 并行加载数据 ---
def _fetch_one(sym: str) -> tuple:
    """获取单品种数据，返回 (symbol, dataframe)"""
    if sym in YFINANCE_SYMBOLS:
        return sym, get_daily_data(sym)
    elif sym in AKSHARE_SYMBOLS:
        return sym, get_daily_kline(sym)
    return sym, None


with st.spinner("正在并行加载数据..."):
    all_symbols = list(AKSHARE_SYMBOLS.keys()) + list(YFINANCE_SYMBOLS.keys())
    all_data = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch_one, sym): sym for sym in all_symbols}
        for future in as_completed(futures):
            sym, df = future.result()
            if df is not None:
                all_data[sym] = df

    # 顶部指标品种数据
    top_data = {}
    top_config = {}
    for sym in TOP_METRICS:
        if sym in all_data:
            top_data[sym] = all_data[sym]
            top_config[sym] = YFINANCE_SYMBOLS.get(sym) or AKSHARE_SYMBOLS.get(sym, {})

# --- 数据源状态指示器 ---
with st.sidebar:
    st.divider()
    st.header("数据源状态")
    akshare_loaded = [s for s in AKSHARE_SYMBOLS
                      if s in all_data and not all_data[s].empty]
    yfinance_loaded = [s for s in YFINANCE_SYMBOLS
                       if s in all_data and not all_data[s].empty]
    akshare_ok = len(akshare_loaded) > 0
    yfinance_ok = len(yfinance_loaded) > 0

    st.markdown(
        f"{'🟢' if akshare_ok else '🔴'} AKShare (中国期货) "
        f"— {len(akshare_loaded)}/{len(AKSHARE_SYMBOLS)}"
    )
    st.markdown(
        f"{'🟢' if yfinance_ok else '🔴'} yfinance (国际期货) "
        f"— {len(yfinance_loaded)}/{len(YFINANCE_SYMBOLS)}"
    )
    if not yfinance_ok:
        st.warning("yfinance 无法连接，国际品种数据不可用。可能需要科学上网。")

# --- 顶部指标卡 ---
render_top_metrics(top_data, top_config)

st.divider()

# --- 全品种汇总表 ---
st.subheader("全品种涨跌一览")

overview_rows = []
for tier_id in ["T1", "T2", "T3"]:
    group = TIER_GROUPS[tier_id]
    for sym in group["akshare"]:
        cfg = AKSHARE_SYMBOLS[sym]
        row = build_overview_row(sym, cfg["name"], tier_id, cfg["exchange"],
                                 all_data.get(sym))
        overview_rows.append(row)
    for sym in group["yfinance"]:
        cfg = YFINANCE_SYMBOLS[sym]
        row = build_overview_row(sym, cfg["name"], tier_id, cfg["exchange"],
                                 all_data.get(sym))
        overview_rows.append(row)

render_overview_table(overview_rows)

# --- 价格预警 ---
alerts = [r for r in overview_rows
          if r["日涨跌%"] is not None and abs(r["日涨跌%"]) >= ALERT_THRESHOLD_PCT]
if alerts:
    for a in alerts:
        direction = "涨" if a["日涨跌%"] > 0 else "跌"
        st.toast(f"⚠️ {a['品种']} 日{direction}幅 {a['日涨跌%']:+.2f}% 超过阈值 {ALERT_THRESHOLD_PCT}%")

# --- 数据导出 ---
if overview_rows:
    export_df = pd.DataFrame(overview_rows)
    csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="导出汇总数据 (CSV)",
        data=csv_data,
        file_name=f"commodity_overview_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

st.divider()

# --- 迷你走势图 ---
st.subheader("近两周走势一览")
_SPARK_COLS = 6
spark_items = []
for row in overview_rows:
    sym = row["代码"]
    df = all_data.get(sym)
    spark_data = get_sparkline_data(df, 15)
    if spark_data:
        spark_items.append((sym, row["品种"], spark_data))

for batch_start in range(0, len(spark_items), _SPARK_COLS):
    batch = spark_items[batch_start:batch_start + _SPARK_COLS]
    cols = st.columns(_SPARK_COLS)
    for j, (sym, name, data) in enumerate(batch):
        with cols[j]:
            fig = create_sparkline(data)
            st.plotly_chart(fig, use_container_width=True, key=f"spark_{sym}")
            st.caption(name)

st.divider()

# --- 热力图 ---
st.subheader("涨跌幅热力图")
heatmap_df = build_heatmap_data(overview_rows)
if not heatmap_df.empty:
    fig = create_heatmap(heatmap_df,
                         color_up=colors["up"], color_down=colors["down"])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("数据不足，无法生成热力图")

st.divider()

# --- 最新资讯预览 ---
st.subheader("最新相关资讯")
try:
    from data.news_client import get_news
    news_df = get_news(limit=5)
    if not news_df.empty:
        for _, row in news_df.iterrows():
            time_str = str(row.get("时间", ""))
            title = str(row.get("标题", ""))
            st.markdown(f"- `{time_str}` **{title}**")
        st.caption("更多资讯请前往「实时资讯」页面 →")
    else:
        st.caption("暂无相关资讯")
except Exception:
    st.caption("资讯模块加载失败，请前往「实时资讯」页面查看")
