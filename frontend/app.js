// Sentiment Standings — data wiring for the almanac league table.
// Reads the same-origin FastAPI JSON endpoints; no framework, no build.

const board = document.getElementById("board");
const standings = document.querySelector(".standings");
const limitSelect = document.getElementById("limit");
const runDateEl = document.getElementById("run-date");
const rowTemplate = document.getElementById("row-template");

const MAX_ABS = 0.6;      // score magnitude that fills half the gauge
const THIN_COVERAGE = 10; // fewer articles than this reads as low confidence

let openTicker = null;    // only one drill-down open at a time

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

const fmtScore = (s) => (s >= 0 ? "+" : "−") + Math.abs(s).toFixed(2);
const toneOf = (label) =>
  label === "bullish" ? "bull" : label === "bearish" ? "bear" : "neutral";

function formatDate(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return "—";
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

// ---- Board -------------------------------------------------------------

function renderBoard(picks) {
  board.replaceChildren();
  openTicker = null;

  if (!picks.length) {
    showNotice("No picks yet.", "Run the daily job to populate the standings.");
    return;
  }

  runDateEl.textContent = formatDate(picks[0].time);

  picks.forEach((p, i) => board.appendChild(buildRow(p, i + 1)));
  standings.setAttribute("aria-busy", "false");
}

function buildRow(p, rank) {
  const row = rowTemplate.content.firstElementChild.cloneNode(true);
  const tone = toneOf(p.label);
  const thin = p.articles < THIN_COVERAGE;

  row.dataset.ticker = p.ticker;
  if (rank <= 3) row.classList.add("row--top");
  if (thin) row.classList.add("row--thin");
  row.setAttribute("aria-label", `${p.ticker}, rank ${rank}, ${p.label}, net score ${fmtScore(p.score)}, ${p.articles} articles`);

  row.querySelector(".rank").textContent = rank;
  row.querySelector(".ticker").textContent = p.ticker;

  const tag = row.querySelector(".label-tag");
  tag.textContent = p.label;
  tag.classList.add(`label-tag--${p.label}`);

  // Sentiment gauge: deflect from centre, right = bull, left = bear.
  const fill = row.querySelector(".gauge__fill");
  const halfPct = Math.min(50, (Math.abs(p.score) / MAX_ABS) * 50);
  fill.classList.add(`gauge__fill--${tone}`);
  fill.style.width = `${halfPct}%`;                                  // magnitude
  requestAnimationFrame(() => { fill.style.transform = "scaleX(1)"; }); // settle

  const score = row.querySelector(".score");
  score.textContent = fmtScore(p.score);
  score.classList.add(`score--${tone}`);

  // Form bar: stacked pos | neu | neg from the per-article counts.
  buildFormBar(row.querySelector(".form"), p);

  const cov = row.querySelector(".cov");
  cov.innerHTML = thin
    ? `${p.articles}<small>thin coverage</small>`
    : `${p.articles}<small>articles</small>`;
  if (thin) cov.classList.add("cov--thin");

  row.addEventListener("click", () => toggleDetail(row, p));
  row.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleDetail(row, p); }
  });
  return row;
}

function buildFormBar(el, p) {
  const total = (p.pos || 0) + (p.neu || 0) + (p.neg || 0);
  el.replaceChildren();
  el.setAttribute("aria-label", `Form: ${p.pos || 0} bullish, ${p.neu || 0} neutral, ${p.neg || 0} bearish articles`);
  if (!total) return;
  const segs = [
    ["pos", p.pos || 0, "bullish"],
    ["neu", p.neu || 0, "neutral"],
    ["neg", p.neg || 0, "bearish"],
  ];
  for (const [cls, n, word] of segs) {
    if (!n) continue;
    const seg = document.createElement("span");
    seg.className = `form__seg form__seg--${cls}`;
    seg.style.width = `${(n / total) * 100}%`;
    seg.title = `${n} ${word} ${n === 1 ? "article" : "articles"}`;
    el.appendChild(seg);
  }
}

// ---- Drill-down --------------------------------------------------------

async function toggleDetail(row, p) {
  const existing = row.nextElementSibling;
  const isOpen = existing && existing.classList.contains("detail");

  // Close any open detail first (only one at a time).
  document.querySelectorAll(".detail").forEach((d) => d.remove());
  document.querySelectorAll('.row[aria-expanded="true"]').forEach((r) => r.setAttribute("aria-expanded", "false"));

  if (isOpen && openTicker === p.ticker) { openTicker = null; return; }

  row.setAttribute("aria-expanded", "true");
  openTicker = p.ticker;

  const detail = document.createElement("div");
  detail.className = "detail";
  detail.innerHTML = `<div class="detail__inner"><p class="notice">Loading ${p.ticker} coverage…</p></div>`;
  row.after(detail);

  try {
    const articles = await fetchJSON(`/tickers/${encodeURIComponent(p.ticker)}/articles`);
    if (openTicker !== p.ticker) return; // user moved on while loading
    renderDetail(detail, p, articles);
  } catch (err) {
    detail.querySelector(".detail__inner").innerHTML =
      `<p class="notice"><strong>Couldn't load ${p.ticker}.</strong>${err.message}</p>`;
  }
}

function renderDetail(detail, p, articles) {
  const inner = detail.querySelector(".detail__inner");
  inner.replaceChildren();

  const head = document.createElement("div");
  head.className = "detail__head";
  head.innerHTML = `
    <h2 class="detail__title">${p.ticker} · <span class="score--${toneOf(p.label)}">${fmtScore(p.score)}</span> ${p.label}</h2>
    <span class="detail__breakdown">
      <b class="up">${p.pos || 0}</b> bullish ·
      <b class="flat">${p.neu || 0}</b> neutral ·
      <b class="down">${p.neg || 0}</b> bearish
      &nbsp;across ${p.articles} articles
    </span>`;
  inner.appendChild(head);

  if (!articles.length) {
    inner.insertAdjacentHTML("beforeend", `<p class="notice">No articles stored for this run.</p>`);
    return;
  }

  const list = document.createElement("ul");
  list.className = "articles";
  for (const a of articles) {
    const li = document.createElement("li");
    li.className = "article";
    const verdict = a.label || "neutral";
    const conf = a.score != null ? `${Math.round(a.score * 100)}%` : "";
    const link = document.createElement("a");
    link.className = "article__link";
    link.href = a.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = a.title || a.url;
    li.innerHTML = `<span class="article__verdict article__verdict--${verdict}">${verdict}${conf ? ` <span class="article__conf">${conf}</span>` : ""}</span>`;
    const body = document.createElement("span");
    body.appendChild(link);
    li.appendChild(body);
    list.appendChild(li);
  }
  inner.appendChild(list);
}

// ---- States ------------------------------------------------------------

function showSkeleton() {
  standings.setAttribute("aria-busy", "true");
  board.replaceChildren();
  for (let i = 0; i < 8; i++) {
    const s = document.createElement("div");
    s.className = "skeleton";
    board.appendChild(s);
  }
}

function showNotice(title, body, retry) {
  board.replaceChildren();
  const div = document.createElement("div");
  div.className = "notice";
  div.innerHTML = `<strong>${title}</strong>${body || ""}`;
  if (retry) {
    const btn = document.createElement("button");
    btn.textContent = "Try again";
    btn.addEventListener("click", loadBoard);
    div.appendChild(btn);
  }
  board.appendChild(div);
  standings.setAttribute("aria-busy", "false");
}

// ---- Boot --------------------------------------------------------------

async function loadBoard() {
  showSkeleton();
  try {
    const picks = await fetchJSON(`/picks?limit=${encodeURIComponent(limitSelect.value)}`);
    renderBoard(picks);
  } catch (err) {
    showNotice("Couldn't reach the standings.", err.message, true);
  }
}

limitSelect.addEventListener("change", loadBoard);
loadBoard();

// ---- Ticker search -----------------------------------------------------

const searchForm = document.getElementById("search");
const searchInput = document.getElementById("search-input");
const searchPanel = document.getElementById("search-panel");
const searchClear = document.getElementById("search-clear");
const legend = document.querySelector(".legend");

function showStandings() {
  searchPanel.hidden = true;
  standings.style.display = "";
  if (legend) legend.style.display = "";
}

function showResult() {
  standings.style.display = "none";
  if (legend) legend.style.display = "none";
  searchPanel.hidden = false;
}

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const ticker = searchInput.value.trim().toUpperCase(); // tickers are stored uppercase
  if (!ticker) return;

  const detail = searchPanel.querySelector(".detail");
  detail.querySelector(".detail__inner").innerHTML = `<p class="notice">Looking up ${ticker}…</p>`;
  showResult();

  try {
    const data = await fetchJSON(`/tickers/${encodeURIComponent(ticker)}`);
    if (!data) {
      detail.querySelector(".detail__inner").innerHTML =
        `<p class="notice"><strong>No data for ${ticker}.</strong>It isn't in the latest run, or the symbol is unknown.</p>`;
      return;
    }
    // read() returns the sentiment row + a `coverage` list, but no pos/neu/neg
    // counts — derive them from coverage so we can reuse renderDetail().
    const coverage = data.coverage || [];
    const counts = coverage.reduce((c, a) => { c[a.label] = (c[a.label] || 0) + 1; return c; }, {});
    const pick = {
      ticker: data.ticker, score: data.score, label: data.label, articles: data.articles,
      pos: counts.positive || 0, neu: counts.neutral || 0, neg: counts.negative || 0,
    };
    renderDetail(detail, pick, coverage);
  } catch (err) {
    detail.querySelector(".detail__inner").innerHTML =
      `<p class="notice"><strong>Couldn't load ${ticker}.</strong>${err.message}</p>`;
  }
});

searchClear.addEventListener("click", () => { searchInput.value = ""; showStandings(); });
