const briefing = document.querySelector("#briefing");
const dateSelect = document.querySelector("#dateSelect");
const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
const cls = value => ["green", "red", "amber", "sector-up", "sector-down"].includes(value) ? value : "";
const money = value => escapeHtml(value);

function render(data) {
  const { meta, executive, scores, portfolio, breadth, drawdown } = data;
  document.title = `${meta.title}｜${meta.date}`;
  briefing.innerHTML = `
    <header class="topbar"><div class="brand"><div class="mark" aria-hidden="true">JA</div><div><h1>${escapeHtml(meta.brand)}</h1><div class="subtitle">${escapeHtml(meta.subtitle)}</div></div></div><div class="datebox"><div class="date">${escapeHtml(meta.date)}</div><div class="cutoff">${escapeHtml(meta.cutoff)}</div></div></header>
    <section class="hero"><div><h2>${escapeHtml(executive.headline)}</h2><p>${escapeHtml(executive.summary)}</p></div><div class="status"><span class="pill">MARKET STATUS</span><div class="signal">${escapeHtml(executive.status_cn)} <small>${escapeHtml(executive.status_en)}</small></div></div></section>
    <section class="cards">
      ${card("牛市健康度", `${scores.market_health}<span class="unit"> /10</span>`, scores.market_health_note, scores.market_health_class)}
      ${card("机会指数", `${scores.opportunity}<span class="unit"> /100</span>`, scores.opportunity_note, scores.opportunity_class)}
      ${card("股票当前市值", `¥${money(portfolio.market_value_fmt)}`, portfolio.return_pct_fmt, portfolio.return_class)}
      ${card("浮动盈利", `¥${money(portfolio.profit_fmt)}`, `累计投入 ¥${money(portfolio.invested_fmt)}`, portfolio.return_class)}
      <div class="card"><div class="label">${escapeHtml(portfolio.milestone_label)}</div><div class="value">${escapeHtml(portfolio.milestone_progress_fmt)}</div><div class="progress"><span style="width:${Math.max(0,Math.min(100,Number(portfolio.milestone_progress)))}%"></span></div><div class="delta">差 ¥${money(portfolio.milestone_gap_fmt)}</div></div>
    </section>
    <div class="layout"><section class="panel"><h3>全球市场概览</h3><div class="marketgrid">${data.global_markets.map(metric).join("")}</div></section>
      <section class="panel"><h3>Market Breadth & Sector Leadership</h3><div class="hint">${escapeHtml(breadth.summary)}</div><div class="bars">${breadth.sectors.map(sector => `<div class="barrow"><span>${escapeHtml(sector.name)}</span><div class="bar"><span class="${cls(sector.bar_class)}" style="width:${Math.max(0,Math.min(100,Number(sector.bar_width)))}%"></span></div><b class="${cls(sector.change_class)}">${escapeHtml(sector.change)}</b></div>`).join("")}</div></section></div>
    <div class="layout"><section class="panel"><h3>Market Health Dashboard</h3><div class="health"><div class="gauge" style="background:conic-gradient(var(--green) 0 ${Math.max(0,Math.min(100,Number(scores.market_health_pct)))}%,#E8EDF5 ${Math.max(0,Math.min(100,Number(scores.market_health_pct)))}%)"><div class="num">${escapeHtml(scores.market_health)}<small>综合健康度</small></div></div><div class="checks">${data.health_checks.map(item => `<div class="check"><b>${escapeHtml(item.name)}</b><span class="${cls(item.status_class)}">${escapeHtml(item.status)}</span></div>`).join("")}</div></div></section>
      <section class="panel"><h3>回调机会提醒</h3><div class="hint">${escapeHtml(drawdown.summary)}</div><table><tbody>${drawdown.levels.map(row => `<tr><td>${escapeHtml(row.range)}</td><td class="${cls(row.status_class)}">${escapeHtml(row.status)}</td><td>${escapeHtml(row.action)}</td></tr>`).join("")}</tbody></table></section></div>
    <div class="split3">${listPanel("美国宏观政策", data.macro)}${listPanel("AI / 科技 / SpaceX", data.technology)}${listPanel("未来5-20个交易日", data.outlook)}</div>
    <div class="layout"><section class="panel"><h3>中国市场与政策</h3><table><tbody>${data.china_markets.map(item => `<tr><td class="ticker">${escapeHtml(item.name)}</td><td>${escapeHtml(item.value)}</td><td class="${cls(item.change_class)}">${escapeHtml(item.change)}</td></tr>`).join("")}</tbody></table><div class="hint" style="margin-top:8px">${escapeHtml(data.china_summary)}</div></section>
      <section class="panel"><h3>长期投资仪表盘</h3><div class="marketgrid">${data.long_term_dashboard.map(item => `<div class="metric"><div class="n">${escapeHtml(item.name)}</div><div class="v ${cls(item.value_class)}">${escapeHtml(item.value)}</div></div>`).join("")}</div></section></div>
    <section class="panel action" style="margin-top:12px"><h3>Action Center · 今日行动</h3><div class="actiongrid">${data.actions.map(item => `<div class="act"><strong class="${cls(item.title_class)}">${escapeHtml(item.title)}</strong><span>${escapeHtml(item.detail)}</span></div>`).join("")}</div></section>
    <footer class="footer"><div>公开行情数据：Yahoo Finance · 仅供信息参考，不构成投资建议</div><div>固定模板 V1.0 · 工作日 10:00 更新</div></footer>`;
}

function card(label, value, delta, deltaClass) { return `<div class="card"><div class="label">${escapeHtml(label)}</div><div class="value">${value}</div><div class="delta ${cls(deltaClass)}">${escapeHtml(delta)}</div></div>`; }
function metric(item) { return `<div class="metric"><div class="n">${escapeHtml(item.name)}</div><div class="v">${escapeHtml(item.value)}</div><div class="c ${cls(item.change_class)}">${escapeHtml(item.change)}</div></div>`; }
function listPanel(title, items) { return `<section class="panel"><h3>${escapeHtml(title)}</h3><div class="list">${items.map(item => `<div class="item"><b>${escapeHtml(item.name)}</b><span class="${cls(item.value_class)}">${escapeHtml(item.value)}</span></div>`).join("")}</div></section>`; }

function loadDate(date) {
  briefing.setAttribute("aria-busy", "true");
  try {
    const data = window.__BRIEFINGS__?.reports?.[date];
    if (!data) throw new Error("briefing not found");
    render(data);
    history.replaceState(null, "", `?date=${encodeURIComponent(date)}`);
  } catch {
    briefing.innerHTML = `<div class="loading">该日期的简报暂不可用，请选择其他日期。</div>`;
  } finally { briefing.removeAttribute("aria-busy"); }
}

const dates = window.__BRIEFINGS__?.dates || [];
const requested = new URLSearchParams(location.search).get("date");
const selected = dates.includes(requested) ? requested : dates[0];
dateSelect.innerHTML = dates.map(date => `<option value="${escapeHtml(date)}" ${date === selected ? "selected" : ""}>${escapeHtml(date)}</option>`).join("");
dateSelect.addEventListener("change", event => loadDate(event.target.value));
document.querySelector("#printButton").addEventListener("click", () => window.print());
loadDate(selected);
