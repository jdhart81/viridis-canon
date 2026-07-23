const state = {
  catalog: null,
  records: [],
};

const tierOrder = {
  spine: 0,
  flagship: 1,
  "working-corpus": 2,
};

function byId(id) {
  return document.getElementById(id);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function pretty(value) {
  return String(value || "")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function shortDigest(value) {
  return value ? `${value.slice(0, 8)}…${value.slice(-6)}` : "—";
}

function populateMetrics(catalog) {
  const stats = catalog.stats;
  byId("hero-verified").textContent = stats.verified;
  byId("hero-working").textContent = stats.working;
  byId("hero-quarantined").textContent = stats.quarantined;
  byId("catalog-digest").textContent = shortDigest(catalog.catalog_digest);
  byId("metric-records").textContent = stats.records;
  byId("metric-theorems").textContent = stats.theorems_and_lemmas;
  byId("metric-flagships").textContent = stats.flagships;
}

function recordCard(record) {
  const card = element("button", "record-card");
  card.type = "button";
  card.setAttribute("aria-label", `Open details for ${record.title}`);
  card.addEventListener("click", () => openRecord(record));

  const meta = element("div", "record-meta");
  meta.append(
    element("span", `status-pill ${record.status}`, pretty(record.status)),
    element("span", "tier-pill", pretty(record.tier))
  );

  const title = element("h3", "", record.title);
  const summary = element("p", "", record.summary);
  const foot = element("div", "record-foot");
  const digest = element("div");
  digest.append(
    element("span", "", "Record fingerprint"),
    element("code", "", shortDigest(record.digest))
  );
  const declarations = element("div");
  declarations.append(
    element("span", "", "Theorems + lemmas"),
    element("b", "", record.theorem_count + record.lemma_count)
  );
  foot.append(digest, declarations);
  card.append(meta, title, summary, foot);
  return card;
}

function filteredRecords() {
  const query = byId("search").value.trim().toLowerCase();
  const tier = byId("tier-filter").value;
  const status = byId("status-filter").value;
  const sort = byId("sort").value;

  const records = state.records.filter((record) => {
    const haystack = [
      record.title,
      record.summary,
      record.path,
      record.lean_module,
      ...(record.tags || []),
    ]
      .join(" ")
      .toLowerCase();
    return (
      (!query || haystack.includes(query)) &&
      (!tier || record.tier === tier) &&
      (!status || record.status === status)
    );
  });

  records.sort((left, right) => {
    if (sort === "title") return left.title.localeCompare(right.title);
    if (sort === "theorems") {
      const leftCount = left.theorem_count + left.lemma_count;
      const rightCount = right.theorem_count + right.lemma_count;
      return rightCount - leftCount || left.title.localeCompare(right.title);
    }
    return (
      tierOrder[left.tier] - tierOrder[right.tier] ||
      left.title.localeCompare(right.title)
    );
  });
  return records;
}

function renderCatalog() {
  const grid = byId("catalog-grid");
  const records = filteredRecords();
  grid.replaceChildren(...records.map(recordCard));
  byId("result-count").textContent = records.length;
  if (!records.length) {
    const empty = element("div", "catalog-error");
    empty.textContent = "No records match these filters.";
    grid.append(empty);
  }
}

function detailCell(label, value) {
  const cell = element("div");
  cell.append(element("span", "", label), element("strong", "", value || "Not recorded"));
  return cell;
}

function safeSourceUrl(path) {
  const encoded = path.split("/").map(encodeURIComponent).join("/");
  return `https://github.com/jdhart81/viridis-canon/blob/main/${encoded}`;
}

function openRecord(record) {
  const dialog = byId("record-dialog");
  const content = byId("dialog-content");
  const kicker = element("div", "dialog-kicker");
  kicker.append(
    element("span", `status-pill ${record.status}`, pretty(record.status)),
    element("span", "tier-pill", pretty(record.tier))
  );

  const title = element("h2", "dialog-title", record.title);
  title.id = "dialog-title";
  const summary = element("p", "dialog-summary", record.summary);
  const honesty = element("div", "honesty-box", record.caveat);
  const details = element("div", "detail-grid");
  details.append(
    detailCell("Lean module", record.lean_module),
    detailCell("Integrity", pretty(record.integrity)),
    detailCell("Declarations", record.theorem_count + record.lemma_count + record.definition_count),
    detailCell("External validation", pretty(record.external_validation)),
    detailCell("Source path", record.path),
    detailCell("DOI", record.doi || "Not assigned"),
    detailCell(
      "Source encoding",
      record.metadata?.source_decode_replacements
        ? `Warning — ${record.metadata.source_decode_replacements} invalid byte sequence`
        : "UTF-8 clean"
    )
  );

  const sourceDigest = element("div", "digest-block");
  sourceDigest.append(
    element("span", "", "Source SHA-256"),
    element("code", "", record.source_sha256)
  );
  const recordDigest = element("div", "digest-block");
  recordDigest.append(
    element("span", "", "Canonical record digest"),
    element("code", "", record.digest)
  );

  const actions = element("div", "dialog-actions");
  const source = element("a", "", "Inspect source ↗");
  source.href = safeSourceUrl(record.path);
  source.target = "_blank";
  source.rel = "noreferrer";
  actions.append(source);

  if (record.doi && /^10\.5281\/zenodo\.\d+$/.test(record.doi)) {
    const doi = element("a", "secondary", "Open DOI ↗");
    doi.href = `https://doi.org/${record.doi}`;
    doi.target = "_blank";
    doi.rel = "noreferrer";
    actions.append(doi);
  }

  const copy = element("button", "secondary", "Copy record digest");
  copy.type = "button";
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(record.digest);
      copy.textContent = "Digest copied";
    } catch {
      copy.textContent = "Copy unavailable";
    }
  });
  actions.append(copy);

  content.replaceChildren(
    kicker,
    title,
    summary,
    honesty,
    details,
    sourceDigest,
    recordDigest,
    actions
  );
  window.location.hash = `record=${encodeURIComponent(record.record_id)}`;
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
}

function closeDialog() {
  const dialog = byId("record-dialog");
  if (dialog.open && typeof dialog.close === "function") dialog.close();
  else dialog.removeAttribute("open");
  if (window.location.hash.startsWith("#record=")) {
    history.replaceState(null, "", window.location.pathname + window.location.search);
  }
}

function bindControls() {
  ["search", "tier-filter", "status-filter", "sort"].forEach((id) => {
    byId(id).addEventListener(id === "search" ? "input" : "change", renderCatalog);
  });
  byId("reset-filters").addEventListener("click", () => {
    byId("search").value = "";
    byId("tier-filter").value = "";
    byId("status-filter").value = "";
    byId("sort").value = "prominence";
    renderCatalog();
  });
  byId("dialog-close").addEventListener("click", closeDialog);
  byId("record-dialog").addEventListener("click", (event) => {
    if (event.target === byId("record-dialog")) closeDialog();
  });
  byId("record-dialog").addEventListener("cancel", (event) => {
    event.preventDefault();
    closeDialog();
  });
}

async function init() {
  bindControls();
  try {
    const response = await fetch("./data/catalog.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`catalog request failed: ${response.status}`);
    state.catalog = await response.json();
    state.records = state.catalog.records || [];
    populateMetrics(state.catalog);
    renderCatalog();

    if (window.location.hash.startsWith("#record=")) {
      const recordId = decodeURIComponent(window.location.hash.slice("#record=".length));
      const record = state.records.find((item) => item.record_id === recordId);
      if (record) openRecord(record);
    }
  } catch (error) {
    console.error(error);
    byId("catalog-error").hidden = false;
  }
}

document.addEventListener("DOMContentLoaded", init);
