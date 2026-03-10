"""Plotly 图表构建器（K线、热力图、迷你图等）"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def create_candlestick(df: pd.DataFrame, title: str = "",
                       date_col: str = "date") -> go.Figure:
    """创建 K 线图"""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5,
                          xref="paper", yref="paper", showarrow=False,
                          font=dict(size=20, color="gray"))
        return fig

    fig = go.Figure()

    # K线
    fig.add_trace(go.Candlestick(
        x=df[date_col] if date_col in df.columns else df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="K线",
        increasing_line_color="#FF4B4B",
        decreasing_line_color="#00C853",
        increasing_fillcolor="#FF4B4B",
        decreasing_fillcolor="#00C853",
    ))

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="价格",
        template="plotly_dark",
        height=450,
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=20, t=50, b=30),
    )
    return fig


def create_volume_bar(df: pd.DataFrame, date_col: str = "date") -> go.Figure:
    """创建成交量柱状图"""
    if df is None or df.empty:
        return go.Figure()

    vol_col = "volume" if "volume" in df.columns else "hold"
    if vol_col not in df.columns:
        return go.Figure()

    colors = []
    for i in range(len(df)):
        if i == 0:
            colors.append("#888888")
        elif df["close"].iloc[i] >= df["close"].iloc[i - 1]:
            colors.append("#FF4B4B")
        else:
            colors.append("#00C853")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[date_col] if date_col in df.columns else df.index,
        y=df[vol_col],
        marker_color=colors,
        name="成交量",
    ))
    fig.update_layout(
        title="成交量",
        template="plotly_dark",
        height=200,
        margin=dict(l=50, r=20, t=40, b=30),
        xaxis_title="",
        yaxis_title="",
    )
    return fig


def create_heatmap(df: pd.DataFrame) -> go.Figure:
    """创建涨跌幅热力图"""
    if df is None or df.empty:
        return go.Figure()

    categories = df["品种"].tolist()
    z_data = []
    text_data = []
    periods = ["4日涨跌%", "半月涨跌%"]

    for period in periods:
        row = df[period].tolist()
        z_data.append(row)
        text_data.append([f"{v:.2f}%" if pd.notna(v) else "N/A" for v in row])

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=categories,
        y=["4日涨跌%", "半月涨跌%"],
        text=text_data,
        texttemplate="%{text}",
        textfont={"size": 12},
        colorscale=[
            [0, "#00C853"],
            [0.5, "#333333"],
            [1, "#FF4B4B"],
        ],
        zmid=0,
        colorbar=dict(title="涨跌%"),
    ))

    fig.update_layout(
        title="全品种涨跌幅热力图",
        template="plotly_dark",
        height=250,
        margin=dict(l=80, r=20, t=50, b=50),
        xaxis=dict(tickangle=-45),
    )
    return fig


def create_sparkline(data: list, color: str = "#4B9DFF") -> go.Figure:
    """创建迷你走势图"""
    if not data:
        return go.Figure()

    if len(data) >= 2:
        color = "#FF4B4B" if data[-1] >= data[0] else "#00C853"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=data,
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=f"rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))}, 0.1)",
    ))
    fig.update_layout(
        height=40,
        width=120,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def create_line_chart(df: pd.DataFrame, x_col: str, y_col: str,
                      title: str = "", color: str = "#4B9DFF") -> go.Figure:
    """创建折线图（用于宏观指标）"""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5,
                          xref="paper", yref="paper", showarrow=False,
                          font=dict(size=20, color="gray"))
        return fig

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=4),
    ))
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=400,
        margin=dict(l=50, r=20, t=50, b=30),
    )
    return fig
