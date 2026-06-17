"""選股宇宙：大型權值股清單（台股 + 美股）。

設計：
  - 預設掃描「大型股為主」——台股以 0050 / 0100 成分代表、美股以 Nasdaq-100 / S&P500
    代表性權值股為主。清單刻意做成可維護常數，方便日後增減或改抓成分股 API。
  - 每檔記錄 (ticker, name, market)。market: "tw" | "us"。
  - ⚠️ 成分股會調整，清單僅為「代表性大型股」起始集合，非即時成分；
    日後可改抓 TWSE / 指數成分 API 自動更新。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Market = Literal["tw", "us"]


@dataclass(frozen=True)
class Stock:
    ticker: str          # 台股為代號（如 "2330"）；美股為 symbol（如 "AAPL"）
    name: str            # 顯示名稱
    market: Market


# ── 台股：0050 / 0100 代表性大型權值股 ───────────────────────────────────
# 名稱為常見簡稱；代號以上市為主。
_TW: list[tuple[str, str]] = [
    ("2330", "台積電"), ("2317", "鴻海"), ("2454", "聯發科"), ("2308", "台達電"),
    ("2382", "廣達"), ("2881", "富邦金"), ("2882", "國泰金"), ("2891", "中信金"),
    ("2412", "中華電"), ("2303", "聯電"), ("3711", "日月光投控"), ("2886", "兆豐金"),
    ("1216", "統一"), ("2884", "玉山金"), ("2885", "元大金"), ("2892", "第一金"),
    ("2357", "華碩"), ("3008", "大立光"), ("2002", "中鋼"), ("3045", "台灣大"),
    ("2880", "華南金"), ("2883", "開發金"), ("2887", "台新金"), ("2890", "永豐金"),
    ("1303", "南亞"), ("1301", "台塑"), ("1326", "台化"), ("2207", "和泰車"),
    ("2379", "瑞昱"), ("3034", "聯詠"), ("2327", "國巨"), ("2345", "智邦"),
    ("4904", "遠傳"), ("2912", "統一超"), ("5871", "中租-KY"), ("2603", "長榮"),
    ("2615", "萬海"), ("2609", "陽明"), ("6505", "台塑化"), ("1101", "台泥"),
    ("2301", "光寶科"), ("3231", "緯創"), ("2376", "技嘉"), ("2356", "英業達"),
    ("3017", "奇鋐"), ("6669", "緯穎"), ("3661", "世芯-KY"), ("2395", "研華"),
    ("2360", "致茂"), ("1590", "亞德客-KY"),
]

# ── 美股：Nasdaq-100 / S&P500 代表性大型權值股 ───────────────────────────
_US: list[tuple[str, str]] = [
    ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "NVIDIA"), ("AMZN", "Amazon"),
    ("GOOGL", "Alphabet"), ("META", "Meta"), ("TSLA", "Tesla"), ("AVGO", "Broadcom"),
    ("BRK-B", "Berkshire Hathaway"), ("JPM", "JPMorgan"), ("V", "Visa"), ("MA", "Mastercard"),
    ("UNH", "UnitedHealth"), ("XOM", "ExxonMobil"), ("JNJ", "Johnson & Johnson"),
    ("PG", "Procter & Gamble"), ("COST", "Costco"), ("HD", "Home Depot"), ("KO", "Coca-Cola"),
    ("PEP", "PepsiCo"), ("ADBE", "Adobe"), ("NFLX", "Netflix"), ("AMD", "AMD"),
    ("CRM", "Salesforce"), ("INTC", "Intel"), ("CSCO", "Cisco"), ("QCOM", "Qualcomm"),
    ("TXN", "Texas Instruments"), ("AMAT", "Applied Materials"), ("MU", "Micron"),
    ("PFE", "Pfizer"), ("MRK", "Merck"), ("ABBV", "AbbVie"), ("CVX", "Chevron"),
    ("WMT", "Walmart"), ("MCD", "McDonald's"), ("DIS", "Disney"), ("VZ", "Verizon"),
    ("T", "AT&T"), ("IBM", "IBM"),
]


def tw_universe() -> list[Stock]:
    return [Stock(t, n, "tw") for t, n in _TW]


def us_universe() -> list[Stock]:
    return [Stock(t, n, "us") for t, n in _US]


def full_universe() -> list[Stock]:
    return tw_universe() + us_universe()
