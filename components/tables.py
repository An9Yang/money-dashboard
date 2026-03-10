"""涨跌幅表格（红绿配色）"""

import streamlit as st
import pandas as pd
from config import TIERS


def color_change(val):
    """涨跌幅红绿色阶渲染"""
    if pd.isna(val):
        return "color: #888888"
    if val > 0:
        intensity = min(abs(val) / 5, 1)
        r = int(255 * intensity)
        return f"color: rgb({r}, 75, 75); font-weight: bold"
    elif val < 0:
        intensity = min(abs(val) / 5, 1)
        g = int(200 * intensity)
        return f"color: rgb(0, {g}, 83); font-weight: bold"
    return "color: #888888"


def color_tier(val):
    """梯队颜色标记"""
    if val in TIERS:
        return f"background-color: {TIERS[val]['color']}20; color: {TIERS[val]['color']}; font-weight: bold"
    return ""


def render_overview_table(rows: list):
    """渲染全品种总览表"""
    if not rows:
        st.info("暂无数据")
        return

    df = pd.DataFrame(rows)

    # 格式化显示
    display_df = df.copy()
    for col in ["日涨跌%", "4日涨跌%", "半月涨跌%"]:
        display_df[col] = display_df[col].apply(
            lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"
        )
    display_df["最新价"] = display_df["最新价"].apply(
        lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A"
    )
    display_df["成交量"] = display_df["成交量"].apply(
        lambda x: f"{x:,}" if pd.notna(x) else "N/A"
    )

    # Styled table using st.html (st.markdown unsafe_allow_html broken in 1.55+)
    st.html(_build_html_table(df, display_df))


def _build_html_table(raw_df: pd.DataFrame, display_df: pd.DataFrame) -> str:
    """构建带颜色的 HTML 表格"""
    style = """
    <style>
    .overview-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    .overview-table th {
        background-color: #1E1E1E;
        color: #CCCCCC;
        padding: 8px 12px;
        text-align: left;
        border-bottom: 2px solid #333;
        position: sticky;
        top: 0;
    }
    .overview-table td {
        padding: 6px 12px;
        border-bottom: 1px solid #2A2A2A;
    }
    .overview-table tr:hover {
        background-color: #1A1A2E;
    }
    .up { color: #FF4B4B; font-weight: bold; }
    .down { color: #00C853; font-weight: bold; }
    .flat { color: #888888; }
    .tier-T1 { background-color: #FF4B4B20; color: #FF4B4B; font-weight: bold; padding: 2px 8px; border-radius: 4px; }
    .tier-T2 { background-color: #FFA50020; color: #FFA500; font-weight: bold; padding: 2px 8px; border-radius: 4px; }
    .tier-T3 { background-color: #4B9DFF20; color: #4B9DFF; font-weight: bold; padding: 2px 8px; border-radius: 4px; }
    </style>
    """

    rows_html = ""
    for i in range(len(raw_df)):
        tier = raw_df.iloc[i]["梯队"]
        tier_label = f'<span class="tier-{tier}">{tier}</span>'

        change_cols = ["日涨跌%", "4日涨跌%", "半月涨跌%"]
        cells = [
            f"<td>{tier_label}</td>",
            f"<td>{display_df.iloc[i]['品种']}</td>",
            f"<td><code>{display_df.iloc[i]['代码']}</code></td>",
            f"<td>{display_df.iloc[i]['交易所']}</td>",
            f"<td><b>{display_df.iloc[i]['最新价']}</b></td>",
        ]
        for col in change_cols:
            raw_val = raw_df.iloc[i][col]
            disp_val = display_df.iloc[i][col]
            if pd.notna(raw_val):
                cls = "up" if raw_val > 0 else ("down" if raw_val < 0 else "flat")
            else:
                cls = "flat"
            cells.append(f'<td class="{cls}">{disp_val}</td>')

        cells.append(f"<td>{display_df.iloc[i]['成交量']}</td>")
        rows_html += f"<tr>{''.join(cells)}</tr>\n"

    headers = ["梯队", "品种", "代码", "交易所", "最新价", "日涨跌%", "4日涨跌%", "半月涨跌%", "成交量"]
    header_html = "".join(f"<th>{h}</th>" for h in headers)

    return f"""
    {style}
    <table class="overview-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """


def render_detail_table(df: pd.DataFrame, date_col: str = "date"):
    """渲染逐日涨跌明细表"""
    if df is None or df.empty:
        st.info("暂无数据")
        return

    display = df.copy()
    if date_col in display.columns:
        display[date_col] = pd.to_datetime(display[date_col]).dt.strftime("%Y-%m-%d")

    if "close" in display.columns and len(display) > 1:
        display["日涨跌%"] = display["close"].pct_change() * 100
        display["日涨跌%"] = display["日涨跌%"].apply(
            lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"
        )

    cols_to_show = [c for c in [date_col, "open", "high", "low", "close", "volume", "日涨跌%"]
                    if c in display.columns]
    display = display[cols_to_show].tail(20).iloc[::-1]

    col_map = {date_col: "日期", "open": "开盘", "high": "最高",
               "low": "最低", "close": "收盘", "volume": "成交量"}
    display = display.rename(columns=col_map)
    st.dataframe(display, use_container_width=True, hide_index=True)
