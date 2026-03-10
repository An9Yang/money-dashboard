"""品种定义、代码映射、梯队分组配置"""

# 梯队定义
TIERS = {
    "T1": {"name": "能源直接冲击", "color": "#FF4B4B", "emoji": "T1"},
    "T2": {"name": "石化产业链传导", "color": "#FFA500", "emoji": "T2"},
    "T3": {"name": "避险 & 间接影响", "color": "#4B9DFF", "emoji": "T3"},
}

# AKShare 品种配置
AKSHARE_SYMBOLS = {
    # 第一梯队：能源直接冲击
    "SC0": {"name": "原油 SC", "exchange": "INE", "tier": "T1"},
    "FU0": {"name": "燃料油 FU", "exchange": "SHFE", "tier": "T1"},
    "PG0": {"name": "液化石油气 PG", "exchange": "DCE", "tier": "T1"},
    # 第二梯队：石化产业链传导
    "MA0": {"name": "甲醇 MA", "exchange": "CZCE", "tier": "T2"},
    "EB0": {"name": "苯乙烯 EB", "exchange": "DCE", "tier": "T2"},
    "TA0": {"name": "PTA", "exchange": "CZCE", "tier": "T2"},
    "EG0": {"name": "乙二醇 EG", "exchange": "DCE", "tier": "T2"},
    "PP0": {"name": "聚丙烯 PP", "exchange": "DCE", "tier": "T2"},
    "L0": {"name": "LLDPE", "exchange": "DCE", "tier": "T2"},
    "V0": {"name": "PVC", "exchange": "DCE", "tier": "T2"},
    "BU0": {"name": "沥青 BU", "exchange": "SHFE", "tier": "T2"},
    # 第三梯队：避险 & 间接影响
    "AU0": {"name": "黄金 AU", "exchange": "SHFE", "tier": "T3"},
    "AG0": {"name": "白银 AG", "exchange": "SHFE", "tier": "T3"},
    "NR0": {"name": "20号胶 NR", "exchange": "SHFE", "tier": "T3"},
}

# yfinance 品种配置
YFINANCE_SYMBOLS = {
    "CL=F": {"name": "WTI 原油", "exchange": "NYMEX", "tier": "T1"},
    "BZ=F": {"name": "布伦特原油", "exchange": "ICE", "tier": "T1"},
    "NG=F": {"name": "天然气", "exchange": "NYMEX", "tier": "T1"},
}

# 顶部指标卡显示品种
TOP_METRICS = ["CL=F", "BZ=F", "SC0", "AU0"]

# 梯队品种分组
TIER_GROUPS = {
    "T1": {
        "akshare": ["SC0", "FU0", "PG0"],
        "yfinance": ["CL=F", "BZ=F", "NG=F"],
    },
    "T2": {
        "akshare": ["MA0", "EB0", "TA0", "EG0", "PP0", "L0", "V0", "BU0"],
        "yfinance": [],
    },
    "T3": {
        "akshare": ["AU0", "AG0", "NR0"],
        "yfinance": [],
    },
}

# 缓存 TTL（秒）
CACHE_TTL = {
    "daily": 300,       # 日K线 5分钟
    "minute": 120,      # 分钟K线 2分钟
    "yfinance": 300,    # yfinance 5分钟
    "realtime": 60,     # 实时报价 1分钟
    "macro": 3600,      # 宏观指标 1小时
}

# 自动刷新默认间隔（毫秒）
AUTO_REFRESH_DEFAULT_MS = 300_000  # 5分钟

# 涨跌幅颜色
COLORS = {
    "up": "#FF4B4B",     # 红色（涨）
    "down": "#00C853",   # 绿色（跌）
    "flat": "#888888",   # 灰色（平）
}
