#!/usr/bin/env python3
"""Generate a weekday Jason Alpha Daily report with public market data."""
from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"
HEADERS = {"User-Agent": "Mozilla/5.0 JasonAlphaDaily/1.0"}

MARKETS = [
    ("S&P 500", "^GSPC", "number"), ("Nasdaq", "^IXIC", "number"),
    ("Dow Jones", "^DJI", "number"), ("US 10Y", "^TNX", "yield"),
    ("DXY", "DX-Y.NYB", "number"), ("VIX", "^VIX", "number"),
    ("WTI", "CL=F", "usd"), ("Gold", "GC=F", "usd"),
    ("USD/CNH", "CNH=X", "fx"),
]
CHINA = [("上证指数", "000001.SS"), ("深证成指", "399001.SZ"), ("创业板指", "399006.SZ"), ("科创综指", "000680.SS")]
SECTORS = [("信息技术", "XLK"), ("工业", "XLI"), ("金融", "XLF"), ("通信服务", "XLC"), ("医疗", "XLV"), ("必需消费", "XLP"), ("能源", "XLE")]


def fetch_chart(symbol: str, range_: str = "5d") -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='')}?range={range_}&interval=1d&events=div%2Csplits"
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=20) as response:
        return json.load(response)["chart"]["result"][0]


def quote_row(symbol: str) -> dict:
    chart = fetch_chart(symbol)
    meta = chart["meta"]
    closes = [v for v in chart["indicators"]["quote"][0]["close"] if v is not None]
    value = float(closes[-1] if closes else meta.get("regularMarketPrice", 0))
    previous = float(closes[-2] if len(closes) > 1 else meta.get("chartPreviousClose", value))
    change = ((value / previous) - 1) * 100 if previous else 0
    return {"value": value, "previous": previous, "change": change}


def fmt(value: float, kind: str) -> str:
    if kind == "yield": return f"{value / 10:.3f}%"
    if kind == "usd": return f"${value:,.2f}"
    if kind == "fx": return f"{value:.4f}"
    return f"{value:,.2f}"


def signed(value: float) -> str:
    return f"{value:+.2f}%"


def color(value: float, positive_green: bool = True) -> str:
    good = value >= 0 if positive_green else value <= 0
    return "green" if good else "red"


def safe_quotes(rows):
    result = {}
    for label, symbol, *rest in rows:
        try:
            result[label] = quote_row(symbol)
        except Exception as exc:
            print(f"warning: {symbol}: {exc}")
        time.sleep(0.3)
    return result


def latest_report() -> dict:
    index_path = DATA / "index.json"
    dates = json.loads(index_path.read_text("utf-8")) if index_path.exists() else []
    if dates:
        return json.loads((DATA / f"{dates[0]}.json").read_text("utf-8"))
    return json.loads((ROOT / "sample_data_v1.0.json").read_text("utf-8"))


def main() -> None:
    now = datetime.now().astimezone()
    if now.weekday() >= 5 and not os.getenv("FORCE_RUN"):
        print("Weekend: no report generated")
        return

    report = latest_report()
    market = safe_quotes(MARKETS)
    china = safe_quotes([(a, b) for a, b in CHINA])
    sectors = safe_quotes([(a, b) for a, b in SECTORS])
    if len(market) < 6:
        raise RuntimeError("Not enough market data returned; keeping the previous report")

    date = now.strftime("%Y-%m-%d")
    report["meta"].update({"date": date, "cutoff": f"公开市场数据更新于 {now.strftime('%m-%d %H:%M')} · Asia/Shanghai"})
    report["global_markets"] = []
    for label, _, kind in MARKETS:
        row = market.get(label)
        if not row: continue
        change_text = signed(row["change"])
        if label == "US 10Y": change_text = f"{(row['value']-row['previous'])/10:+.3f}pct"
        report["global_markets"].append({"name": label, "value": fmt(row["value"], kind), "change": change_text, "change_class": color(row["change"], label not in {"US 10Y", "DXY", "VIX"})})

    sector_changes = [(name, sectors[name]["change"]) for name, _ in SECTORS if name in sectors]
    leader = max(sector_changes, key=lambda item: item[1]) if sector_changes else ("市场", 0)
    positive = sum(change >= 0 for _, change in sector_changes)
    breadth_ratio = positive / max(1, len(sector_changes))
    report["breadth"] = {"summary": f"{leader[0]}领涨，{positive}/{len(sector_changes)} 个主要板块上涨", "sectors": [{"name": name, "bar_width": min(100, max(8, round(abs(change) * 35))), "bar_class": "sector-up" if change >= 0 else "sector-down", "change": signed(change), "change_class": color(change)} for name, change in sector_changes]}

    try:
        yearly = fetch_chart("^GSPC", "1y")
        closes = [v for v in yearly["indicators"]["quote"][0]["close"] if v is not None]
        drawdown = ((closes[-1] / max(closes)) - 1) * 100
    except Exception:
        drawdown = -1
    vix = market.get("VIX", {}).get("value", 20)
    index_avg = sum(market[name]["change"] for name in ("S&P 500", "Nasdaq", "Dow Jones") if name in market) / 3
    health = max(1, min(10, 5 + index_avg * 0.8 + (breadth_ratio - .5) * 3 + (20 - vix) / 10))
    opportunity = max(0, min(100, 20 + abs(drawdown) * 5 + max(0, vix - 15) * 2))
    health_class = "green" if health >= 6.5 else "amber" if health >= 4.5 else "red"
    opportunity_class = "green" if opportunity >= 65 else "amber" if opportunity >= 35 else "red"
    report["scores"].update({"market_health": round(health, 1), "market_health_pct": round(health * 10), "market_health_class": health_class, "market_health_note": "▲ 风险偏好改善" if index_avg >= 0 else "▼ 风险偏好回落", "opportunity": round(opportunity), "opportunity_class": opportunity_class, "opportunity_note": "回撤机会增加" if opportunity >= 60 else "维持纪律"})
    report["drawdown"]["summary"] = f"S&P 500 距近一年高点回撤 {drawdown:.2f}%"
    active = 0 if drawdown > -5 else 1 if drawdown > -10 else 2 if drawdown > -15 else 3 if drawdown > -20 else 4
    for i, row in enumerate(report["drawdown"]["levels"]):
        row["status"] = "当前区域" if i == active else "未触发"
        row["status_class"] = "green" if i == active else "amber" if i == active + 1 else ""

    report["china_markets"] = [{"name": label, "value": fmt(china[label]["value"], "number"), "change": signed(china[label]["change"]), "change_class": color(china[label]["change"])} for label, _ in CHINA if label in china]
    china_avg = sum(row["change"] for row in china.values()) / max(1, len(china))
    report["china_summary"] = f"A股主要指数平均变动 {china_avg:+.2f}%；关注成交扩散、政策信号与科技板块持续性。"
    direction = "中性偏强" if index_avg > .25 else "中性偏弱" if index_avg < -.25 else "中性"
    report["executive"].update({"headline": f"{leader[0]}领涨，全球风险偏好{'回升' if index_avg >= 0 else '降温'}", "summary": f"美股三大指数平均变动 {index_avg:+.2f}%，VIX {vix:.1f}；当前回撤约 {drawdown:.2f}%，维持分批与不追高纪律。", "status_cn": direction, "status_en": "Neutral+" if index_avg > .25 else "Neutral-" if index_avg < -.25 else "Neutral"})
    report["outlook"][0].update({"value": direction, "value_class": health_class})
    report["health_checks"] = [{"name":"市场宽度","status":f"{positive}/{len(sector_changes)}上涨","status_class":health_class},{"name":"板块扩散","status":"改善" if breadth_ratio >= .6 else "偏弱","status_class":health_class},{"name":"Equal Weight","status":"观察","status_class":"amber"},{"name":"Mag7集中度","status":"持续跟踪","status_class":"amber"},{"name":"小盘股","status":signed(market.get("IWM",{}).get("change",0)),"status_class":"amber"},{"name":"波动率","status":f"VIX {vix:.1f}","status_class":"green" if vix < 20 else "amber"},{"name":"20日趋势","status":"改善" if index_avg >= 0 else "回落","status_class":health_class},{"name":"上涨类型","status":"扩散" if breadth_ratio >= .7 else "结构性","status_class":health_class}]

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / f"{date}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
    dates = sorted({p.stem for p in DATA.glob("20??-??-??.json")}, reverse=True)[:120]
    (DATA / "index.json").write_text(json.dumps(dates, ensure_ascii=False) + "\n", "utf-8")
    reports = {d: json.loads((DATA / f"{d}.json").read_text("utf-8")) for d in dates}
    archive = "window.__BRIEFINGS__=" + json.dumps({"dates": dates, "reports": reports}, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (DATA / "archive.js").write_text(archive, "utf-8")
    print(f"Generated {date} with {len(report['global_markets'])} market series")


if __name__ == "__main__":
    main()
