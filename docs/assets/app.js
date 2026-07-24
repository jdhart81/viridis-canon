const state = {
  catalog: null,
  records: [],
  graph: null,
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

function graphRecordText(record) {
  return [
    record.title,
    record.abstract,
    record.summary,
    record.path,
    record.lean_module,
    record.status,
    record.tier,
    ...(record.tags || []),
  ]
    .join(" ")
    .toLowerCase();
}

function graphLabel(value, limit = 28) {
  return value.length > limit ? `${value.slice(0, limit - 1)}…` : value;
}

function renderResearchGraph(records) {
  const svg = byId("research-graph");
  const namespace = "http://www.w3.org/2000/svg";
  const root = document.createElementNS(namespace, "g");
  const edgeLayer = document.createElementNS(namespace, "g");
  const nodeLayer = document.createElementNS(namespace, "g");
  root.append(edgeLayer, nodeLayer);
  svg.replaceChildren(root);

  const centers = {
    spine: { x: 290, y: 350 },
    flagship: { x: 620, y: 135 },
    "working-corpus": { x: 875, y: 420 },
  };
  const labels = {
    spine: "Verified spine",
    flagship: "Flagships",
    "working-corpus": "Working corpus",
  };
  const nodes = new Map();
  const elements = new Map();
  const edges = [];
  const seenEdges = new Set();

  function addEdge(source, target, type) {
    if (!source || !target || source === target) return;
    const key = [source, target].sort().join("|") + `|${type}`;
    if (seenEdges.has(key)) return;
    seenEdges.add(key);
    edges.push({ source, target, type });
  }

  Object.entries(centers).forEach(([tier, center]) => {
    const id = `tier:${tier}`;
    nodes.set(id, {
      id,
      kind: "hub",
      tier,
      title: labels[tier],
      text: tier,
      x: center.x,
      y: center.y,
    });
  });

  Object.keys(centers).forEach((tier) => {
    const group = records
      .filter((record) => record.tier === tier)
      .sort((left, right) => left.title.localeCompare(right.title));
    const ringCapacity = 16;
    group.forEach((record, index) => {
      const ring = Math.floor(index / ringCapacity);
      const offset = ring * ringCapacity;
      const ringSize = Math.min(ringCapacity, group.length - offset);
      const slot = index - offset;
      const angle = -Math.PI / 2 + (slot * Math.PI * 2) / ringSize + ring * 0.24;
      const radius = 86 + ring * 66;
      const center = centers[tier];
      nodes.set(record.record_id, {
        id: record.record_id,
        kind: "record",
        tier,
        status: record.status,
        title: record.title,
        text: graphRecordText(record),
        record,
        x: Math.max(34, Math.min(1166, center.x + Math.cos(angle) * radius)),
        y: Math.max(100, Math.min(670, center.y + Math.sin(angle) * radius)),
      });
      addEdge(`tier:${tier}`, record.record_id, "tier");
    });
  });

  const modules = new Map();
  records.forEach((record) => {
    if (record.lean_module) modules.set(record.lean_module, record.record_id);
    modules.set(record.path.replace(/\.lean$/i, ""), record.record_id);
    modules.set(record.path.split("/").pop().replace(/\.lean$/i, ""), record.record_id);
  });
  records.forEach((record) => {
    (record.imports || []).forEach((imported) => {
      String(imported)
        .split(/\s+/)
        .forEach((module) => {
          const target = modules.get(module) || modules.get(module.split(".").pop());
          if (target) addEdge(record.record_id, target, "import");
        });
    });
  });

  const ignoredTags = new Set([
    "verified",
    "working",
    "quarantined",
    "spine",
    "flagship",
    "working-corpus",
    "lean4",
  ]);
  const recordsByTag = new Map();
  records.forEach((record) => {
    (record.tags || []).forEach((tag) => {
      if (ignoredTags.has(tag)) return;
      const tagged = recordsByTag.get(tag) || [];
      tagged.push(record.record_id);
      recordsByTag.set(tag, tagged);
    });
  });
  let topicEdges = 0;
  [...recordsByTag.keys()].sort().forEach((tag) => {
    const tagged = recordsByTag.get(tag);
    for (let index = 1; index < tagged.length && topicEdges < 42; index += 1) {
      addEdge(tagged[index - 1], tagged[index], "topic");
      topicEdges += 1;
    }
  });

  const lineElements = edges.map((edge) => {
    const line = document.createElementNS(namespace, "line");
    line.setAttribute("class", `graph-edge ${edge.type}`);
    edgeLayer.append(line);
    return { ...edge, line };
  });

  nodes.forEach((node) => {
    const group = document.createElementNS(namespace, "g");
    group.setAttribute(
      "class",
      `graph-node ${node.kind} ${node.tier || ""} ${node.status || ""}`
    );
    group.setAttribute("role", "button");
    group.setAttribute("tabindex", "0");
    group.setAttribute("aria-label", node.title);
    group.dataset.nodeId = node.id;

    const circle = document.createElementNS(namespace, "circle");
    circle.setAttribute("r", node.kind === "hub" ? "16" : node.tier === "flagship" ? "10" : "7");
    const tooltip = document.createElementNS(namespace, "title");
    tooltip.textContent =
      node.kind === "hub"
        ? `${node.title} — select to isolate this collection`
        : `${node.title}\n${node.record.abstract || node.record.summary}`;
    circle.append(tooltip);

    const text = document.createElementNS(namespace, "text");
    text.setAttribute("y", node.kind === "hub" ? "-25" : "-13");
    text.textContent = graphLabel(node.title, node.kind === "hub" ? 34 : 28);
    group.append(circle, text);

    let pointer = null;
    group.addEventListener("pointerdown", (event) => {
      event.stopPropagation();
      pointer = event.pointerId;
      group.setPointerCapture(pointer);
      group.dataset.dragged = "";
    });
    group.addEventListener("pointermove", (event) => {
      if (pointer === null) return;
      group.dataset.dragged = "1";
      const point = svg.createSVGPoint();
      point.x = event.clientX;
      point.y = event.clientY;
      const local = point.matrixTransform(root.getScreenCTM().inverse());
      node.x = local.x;
      node.y = local.y;
      updateGraphGeometry();
    });
    group.addEventListener("pointerup", () => {
      pointer = null;
      window.setTimeout(() => {
        group.dataset.dragged = "";
      }, 0);
    });

    function activate() {
      if (group.dataset.dragged) return;
      if (node.kind === "record") {
        openRecord(node.record);
      } else {
        const search = byId("graph-search");
        search.value = node.tier;
        filterResearchGraph(node.tier);
      }
    }
    group.addEventListener("click", activate);
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activate();
      }
    });
    nodeLayer.append(group);
    elements.set(node.id, group);
  });

  function updateGraphGeometry() {
    lineElements.forEach((edge) => {
      const source = nodes.get(edge.source);
      const target = nodes.get(edge.target);
      edge.line.setAttribute("x1", source.x);
      edge.line.setAttribute("y1", source.y);
      edge.line.setAttribute("x2", target.x);
      edge.line.setAttribute("y2", target.y);
    });
    nodes.forEach((node) => {
      elements.get(node.id).setAttribute("transform", `translate(${node.x} ${node.y})`);
    });
  }

  let view = { x: 0, y: 0, width: 1200, height: 720 };
  function applyView() {
    svg.setAttribute(
      "viewBox",
      `${view.x} ${view.y} ${view.width} ${view.height}`
    );
  }
  svg.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      const factor = event.deltaY > 0 ? 1.12 : 0.88;
      const width = Math.max(520, Math.min(2100, view.width * factor));
      const height = (width * 720) / 1200;
      view.x += (view.width - width) / 2;
      view.y += (view.height - height) / 2;
      view.width = width;
      view.height = height;
      applyView();
    },
    { passive: false }
  );

  state.graph = {
    nodes,
    elements,
    reset() {
      view = { x: 0, y: 0, width: 1200, height: 720 };
      applyView();
    },
  };
  updateGraphGeometry();
  applyView();
  byId("graph-status").textContent = `${records.length} records · ${edges.length} relationships`;
}

function filterResearchGraph(value) {
  if (!state.graph) return;
  const query = value.trim().toLowerCase();
  let matches = 0;
  state.graph.nodes.forEach((node, id) => {
    const match = !query || node.text.includes(query);
    const graphNode = state.graph.elements.get(id);
    graphNode.classList.toggle("dim", Boolean(query) && !match);
    graphNode.classList.toggle(
      "match",
      Boolean(query) && match && node.kind === "record"
    );
    if (match && node.kind === "record") matches += 1;
  });
  byId("graph-status").textContent = query
    ? `${matches} matching records`
    : `${state.records.length} records · connected by tier, imports, and topics`;
}

function resetResearchGraph() {
  byId("graph-search").value = "";
  filterResearchGraph("");
  if (state.graph) state.graph.reset();
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
  const abstract = element("section", "abstract-block");
  abstract.append(
    element("span", "", "Abstract"),
    element("p", "", record.abstract || record.summary)
  );
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
  const sourceUrl = record.source_url || safeSourceUrl(record.path);
  const paperUrl = record.paper_url || sourceUrl;
  const paper = element(
    "a",
    "",
    paperUrl === sourceUrl ? "Read full research artifact ↗" : "Open paper ↗"
  );
  paper.href = paperUrl;
  paper.target = "_blank";
  paper.rel = "noreferrer";
  actions.append(paper);

  const source = element("a", "secondary", "Inspect formal source ↗");
  source.href = sourceUrl;
  source.target = "_blank";
  source.rel = "noreferrer";
  if (sourceUrl !== paperUrl) actions.append(source);

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
    abstract,
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
  byId("graph-search").addEventListener("input", (event) => {
    filterResearchGraph(event.target.value);
  });
  byId("reset-map").addEventListener("click", resetResearchGraph);
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
    renderResearchGraph(state.records);

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
