"""品种对比 — 多品种叠加走势 + 相关性矩阵 + 价差分析"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import AKSHARE_SYMBOLS, YFINANCE_SYMBOLS, TIER_GROUPS
from data.akshare_client import get_daily_kline
from data.yfinance_client import get_daily_data
from data.data_processor import (normalize_prices, calc_correlation_matrix,
                                  calc_spread)
from components.charts import (create_comparison_chart, create_correlation_heatmap,
                                create_spread_chart)

st.title("品种对比分析")
st.caption("多品种叠加走势、相关性矩阵、价差监控")

# 构建所有品种选项
all_options = {}
for sym, cfg in AKSHARE_SYMBOLS.items():
    all_options[f"{cfg['name']} ({sym})"] = (sym, "akshare")
for sym, cfg in YFINANCE_SYMBOLS.items():
    if cfg.get("tier") != "FX":
        all_options[f"{cfg['name']} ({sym})"] = (sym, "yfinance")

# --- 品种选择 ---
st.subheader("选择对比品种")

# 快捷选择
preset_col1, preset_col2, preset_col3 = st.columns(3)
with preset_col1:
    if st.button("T1 能源品种", use_container_width=True):
        st.session_state["compare_default"] = [
            k for k, (sym, _) in all_options.items()
            if sym in TIER_GROUPS["T1"]["akshare"] + TIER_GROUPS["T1"]["yfinance"]
        ]
with preset_col2:
    if st.button("内外盘原油", use_container_width=True):
        st.session_state["compare_default"] = [
            k for k, (sym, _) in all_options.items()
            if sym in ["SC0", "CL=F", "BZ=F"]
        ]
with preset_col3:
    if st.button("避险资产", use_container_width=True):
        st.session_state["compare_default"] = [
            k for k, (sym, _) in all_options.items()
            if sym in ["AU0", "AG0"]
        ]

default_sel = st.session_state.get("compare_default", [])
selected = st.multiselect(
    "选择品种（2-8个）", list(all_options.keys()),
    default=default_sel[:8],
    max_selections=8,
)

if len(selected) < 2:
    st.info("请至少选择 2 个品种进行对比")
    st.stop()

# --- 参数 ---
col_param1, col_param2 = st.columns(2)
with col_param1:
    period_days = st.select_slider(
        "对比周期",
        options=[15, 30, 60, 90, 120],
        value=60,
        format_func=lambda x: f"{x} 天",
    )
with col_param2:
    corr_window = st.select_slider(
        "相关性窗口",
        options=[10, 20, 30, 60],
        value=20,
        format_func=lambda x: f"{x} 天",
    )


# --- 加载数据 ---
def _fetch(sym, src):
    if src == "akshare":
        return sym, get_daily_kline(sym, recent_n=max(period_days, 120))
    else:
        return sym, get_daily_data(sym)


with st.spinner("正在加载对比数据..."):
    syms = [(all_options[s][0], all_options[s][1]) for s in selected]
    data = {}
    names_map = {}
    for s in selected:
        sym, src = all_options[s]
        names_map[sym] = s.split(" (")[0]  # 品种名

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch, sym, src): sym
                   for sym, src in syms}
        for f in as_completed(futures):
            sym, df = f.result()
            if df is not None and not df.empty:
                data[sym] = df

st.divider()

# --- 走势对比（归一化） ---
st.subheader("归一化走势对比")
st.caption("以选定周期第一天为基准，显示各品种涨跌幅百分比变化")
norm_df = normalize_prices(data, names_map, recent_n=period_days)
if not norm_df.empty:
    fig = create_comparison_chart(norm_df, title=f"近 {period_days} 天走势对比（归一化%）")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("数据不足，无法生成对比图")

st.divider()

# --- 相关性矩阵 ---
st.subheader("收益率相关性矩阵")
st.caption(f"基于近 {corr_window} 个交易日日收益率计算")
corr_df = calc_correlation_matrix(data, names_map, window=corr_window)
if not corr_df.empty:
    fig = create_correlation_heatmap(corr_df)
    st.plotly_chart(fig, use_container_width=True)

    # 导出相关性数据
    csv = corr_df.to_csv().encode("utf-8-sig")
    st.download_button("导出相关性矩阵 (CSV)", csv,
                       file_name="correlation_matrix.csv", mime="text/csv")
else:
    st.info("数据不足，无法计算相关性矩阵")

st.divider()

# --- 价差分析 ---
st.subheader("价差分析")
if len(selected) >= 2:
    sp_col1, sp_col2, sp_col3 = st.columns([2, 2, 1])
    sym_options = {s.split(" (")[0]: all_options[s][0] for s in selected}
    names = list(sym_options.keys())

    with sp_col1:
        spread_a = st.selectbox("品种 A", names, index=0)
    with sp_col2:
        spread_b = st.selectbox("品种 B", names,
                                index=min(1, len(names) - 1))
    with sp_col3:
        spread_ratio = st.number_input("系数", value=1.0, step=0.1,
                                       format="%.2f")

    if spread_a != spread_b:
        sym_a = sym_options[spread_a]
        sym_b = sym_options[spread_b]
        df_a = data.get(sym_a)
        df_b = data.get(sym_b)
        if df_a is not None and df_b is not None:
            # 确定日期列
            dcol_a = "date" if "date" in df_a.columns else df_a.columns[0]
            dcol_b = "date" if "date" in df_b.columns else df_b.columns[0]
            spread_df = calc_spread(df_a, df_b, dcol_a, dcol_b, ratio=spread_ratio)
            if not spread_df.empty:
                title = f"{spread_a} - {spread_b}"
                if spread_ratio != 1.0:
                    title += f" x {spread_ratio}"
                fig = create_spread_chart(spread_df, title=f"价差: {title}")
                st.plotly_chart(fig, use_container_width=True)

                # 价差统计
                sp = spread_df["spread"]
                stat_cols = st.columns(4)
                with stat_cols[0]:
                    st.metric("当前价差", f"{sp.iloc[-1]:.2f}")
                with stat_cols[1]:
                    st.metric("均值", f"{sp.mean():.2f}")
                with stat_cols[2]:
                    st.metric("最大", f"{sp.max():.2f}")
                with stat_cols[3]:
                    st.metric("最小", f"{sp.min():.2f}")
            else:
                st.info("无法计算价差（日期无重叠）")
    else:
        st.info("请选择两个不同的品种")
