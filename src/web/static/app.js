const ROUTE_COLORS = [
  "#dc2626",
  "#9333ea",
  "#0284c7",
  "#0d9488",
  "#d97706",
  "#db2777",
];
const NODE_COLORS = {
  depot: "#2563eb",
  restaurant: "#ea580c",
  house: "#16a34a",
  intersection: "#64748b",
};

const state = {
  mapId: "sample_11",
  nodes: [],
  edges: [],
  nodePos: {},
  courierStart: "D0",
  selectedRest: "",
  selectedHouse: "",
  placeMode: false,
  orders: [],
  orderSeq: 1,
  plan: null,
  visibleSteps: 0,
  playing: false,
  animFrame: null,
};

const el = (id) => document.getElementById(id);

function setStatus(msg) {
  el("status-msg").textContent = msg;
}

function clearPlan() {
  stopAnimation();
  state.plan = null;
  state.visibleSteps = 0;
  el("itinerary-box").classList.add("hidden");
  updatePlaybackButtons();
  renderMap();
}

function updatePlaybackButtons() {
  const hasPlan = Boolean(state.plan && state.plan.steps.length > 0);
  el("btn-prev").disabled = !hasPlan || state.visibleSteps <= 0;
  el("btn-next").disabled =
    !hasPlan || state.visibleSteps >= state.plan.steps.length;
  el("btn-play").disabled = !hasPlan;
  el("btn-reset-route").disabled = !hasPlan;
  el("btn-play").textContent = state.playing ? "Pause" : "Play";
}

async function loadMap(endpoint, method = "GET") {
  const res = await fetch(endpoint, {
    method,
    headers: { "Content-Type": "application/json" },
    body: method === "POST" ? JSON.stringify({}) : undefined,
  });
  const data = await res.json();
  state.mapId = data.map_id;
  state.nodes = data.nodes;
  state.edges = data.edges;
  state.orders = [];
  state.orderSeq = 1;
  state.courierStart = "D0";
  state.selectedRest = "";
  state.selectedHouse = "";
  populateControls();
  renderOrders();
  clearPlan();
  setStatus(
    `Loaded ${data.nodes.length} nodes (${data.map_id}). Choose a starting location and add orders.`,
  );
}

function sortById(a, b) {
  return a.id.localeCompare(b.id, undefined, { numeric: true });
}

function updateSelectedPairPreview() {
  const restLabel = state.selectedRest || "-";
  const houseLabel = state.selectedHouse || "-";
  el("selected-rest-tag").textContent = restLabel;
  el("selected-house-tag").textContent = houseLabel;
  el("preview-rest-id").textContent = restLabel;
  el("preview-house-id").textContent = houseLabel;
}

function renderNodePickers() {
  const sortedNodes = [...state.nodes].sort(sortById);
  const restaurants = sortedNodes.filter((n) => n.type === "restaurant");
  const houses = sortedNodes.filter((n) => n.type === "house");

  if (!restaurants.some((r) => r.id === state.selectedRest)) {
    state.selectedRest = restaurants.length ? restaurants[0].id : "";
  }
  if (!houses.some((h) => h.id === state.selectedHouse)) {
    state.selectedHouse = houses.length ? houses[0].id : "";
  }

  const restContainer = el("rest-picker");
  restContainer.innerHTML = "";
  restaurants.forEach((node) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `node-chip rest ${node.id === state.selectedRest ? "active" : ""}`;
    btn.textContent = node.id;
    btn.title = node.label || node.id;
    btn.addEventListener("click", () => {
      state.selectedRest = node.id;
      renderNodePickers();
      setStatus(`Selected pickup restaurant ${node.id}.`);
    });
    restContainer.appendChild(btn);
  });

  const houseContainer = el("house-picker");
  houseContainer.innerHTML = "";
  houses.forEach((node) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `node-chip house ${node.id === state.selectedHouse ? "active" : ""}`;
    btn.textContent = node.id;
    btn.title = node.label || node.id;
    btn.addEventListener("click", () => {
      state.selectedHouse = node.id;
      renderNodePickers();
      setStatus(`Selected customer house ${node.id}.`);
    });
    houseContainer.appendChild(btn);
  });

  updateSelectedPairPreview();
}

function populateControls() {
  const allNodes = [...state.nodes].sort(sortById);
  const startSel = el("courier-start");
  startSel.innerHTML = allNodes
    .map((n) => `<option value="${n.id}">${n.id} (${n.type})</option>`)
    .join("");
  startSel.value = state.courierStart;

  renderNodePickers();
}

function computeSvgPositions() {
  const xs = state.nodes.map((n) => n.x);
  const ys = state.nodes.map((n) => n.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const width = 820;
  const height = 560;
  const padX = 70;
  const padY = 55;
  const spanX = Math.max(1, maxX - minX);
  const spanY = Math.max(1, maxY - minY);

  state.nodePos = {};
  for (const node of state.nodes) {
    const sx = padX + ((node.x - minX) / spanX) * (width - 2 * padX);
    const sy = padY + ((maxY - node.y) / spanY) * (height - 2 * padY);
    state.nodePos[node.id] = { x: sx, y: sy };
  }
}

function svgEl(tag, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) {
    node.setAttribute(k, String(v));
  }
  return node;
}

function renderMap(courierXY = null) {
  const svg = el("city-svg");
  svg.innerHTML = "";
  if (!state.nodes.length) return;
  computeSvgPositions();

  const isDense = state.nodes.length > 25;
  const defs = svgEl("defs");

  const oneWayMarker = svgEl("marker", {
    id: "arrow-oneway",
    viewBox: "0 0 10 10",
    refX: "8",
    refY: "5",
    markerWidth: "6",
    markerHeight: "6",
    orient: "auto-start-reverse",
  });
  oneWayMarker.appendChild(
    svgEl("path", { d: "M 0 1 L 10 5 L 0 9 z", fill: "#f59e0b" }),
  );
  defs.appendChild(oneWayMarker);

  ROUTE_COLORS.forEach((color, idx) => {
    const marker = svgEl("marker", {
      id: `arrow-route-${idx}`,
      viewBox: "0 0 10 10",
      refX: "8",
      refY: "5",
      markerWidth: "6.5",
      markerHeight: "6.5",
      orient: "auto",
    });
    marker.appendChild(
      svgEl("path", { d: "M 0 1 L 10 5 L 0 9 z", fill: color }),
    );
    defs.appendChild(marker);
  });
  svg.appendChild(defs);

  // Base road network layer
  const edgeLayer = svgEl("g");
  for (const edge of state.edges) {
    const p1 = state.nodePos[edge.source];
    const p2 = state.nodePos[edge.target];
    if (edge.bidirectional) {
      edgeLayer.appendChild(
        svgEl("line", {
          x1: p1.x,
          y1: p1.y,
          x2: p2.x,
          y2: p2.y,
          stroke: "#cbd5e1",
          "stroke-width": isDense ? "1.6" : "3",
        }),
      );
    } else {
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const len = Math.hypot(dx, dy) || 1;
      const shrink = isDense ? 11 : 22;
      const x2 = p2.x - (dx / len) * shrink;
      const y2 = p2.y - (dy / len) * shrink;
      edgeLayer.appendChild(
        svgEl("line", {
          x1: p1.x,
          y1: p1.y,
          x2,
          y2,
          stroke: "#f59e0b",
          "stroke-width": isDense ? "1.6" : "2.6",
          "stroke-dasharray": "5,4",
          "marker-end": "url(#arrow-oneway)",
        }),
      );
    }

    const mx = (p1.x + p2.x) / 2;
    const my = (p1.y + p2.y) / 2;
    const bg = svgEl("rect", {
      x: mx - (isDense ? 8 : 11),
      y: my - (isDense ? 7 : 9),
      width: isDense ? 16 : 22,
      height: isDense ? 14 : 18,
      rx: 4,
      fill: edge.bidirectional ? "#ffffff" : "#fef3c7",
      stroke: edge.bidirectional ? "#e2e8f0" : "#f59e0b",
      "stroke-width": "0.8",
    });
    const txt = svgEl("text", {
      x: mx,
      y: my + (isDense ? 3 : 4),
      "text-anchor": "middle",
      "font-size": isDense ? "9" : "11",
      fill: edge.bidirectional ? "#334155" : "#b45309",
      "font-weight": "600",
    });
    txt.textContent = String(edge.weight);
    edgeLayer.appendChild(bg);
    edgeLayer.appendChild(txt);
  }
  svg.appendChild(edgeLayer);

  // Active route steps layer
  const routeLayer = svgEl("g");
  if (state.plan && state.visibleSteps > 0) {
    for (let sIdx = 0; sIdx < state.visibleSteps; sIdx += 1) {
      const step = state.plan.steps[sIdx];
      const colorIdx = sIdx % ROUTE_COLORS.length;
      const color = ROUTE_COLORS[colorIdx];
      const isCurrent = sIdx === state.visibleSteps - 1;
      const offsetSign = sIdx % 2 === 0 ? 1 : -1;

      for (let i = 0; i < step.path.length - 1; i += 1) {
        const p1 = state.nodePos[step.path[i]];
        const p2 = state.nodePos[step.path[i + 1]];
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const len = Math.hypot(dx, dy) || 1;
        const ux = dx / len;
        const uy = dy / len;
        const nx = -uy * 6 * offsetSign;
        const ny = ux * 6 * offsetSign;
        const shrink = isDense ? 12 : 24;

        routeLayer.appendChild(
          svgEl("line", {
            x1: p1.x + ux * shrink + nx,
            y1: p1.y + uy * shrink + ny,
            x2: p2.x - ux * shrink + nx,
            y2: p2.y - uy * shrink + ny,
            stroke: color,
            "stroke-width": isCurrent ? "4" : "2.5",
            "stroke-opacity": isCurrent ? "1" : "0.55",
            "marker-end": `url(#arrow-route-${colorIdx})`,
          }),
        );
      }
    }
  }
  svg.appendChild(routeLayer);

  // Map nodes layer
  const nodeLayer = svgEl("g");
  for (const node of state.nodes) {
    const pos = state.nodePos[node.id];
    const isStart = node.id === state.courierStart;
    const isMinor = isDense && node.type === "intersection" && !isStart;
    const radius = isMinor ? 6 : isDense ? 14 : 21;

    const g = svgEl("g", { class: "node-group" });
    if (isStart) {
      g.appendChild(
        svgEl("circle", {
          cx: pos.x,
          cy: pos.y,
          r: radius + 6,
          fill: "none",
          stroke: "#2563eb",
          "stroke-width": "3",
          "stroke-dasharray": "4,3",
        }),
      );
    }

    g.appendChild(
      svgEl("circle", {
        cx: pos.x,
        cy: pos.y,
        r: radius,
        fill: NODE_COLORS[node.type] || "#64748b",
        stroke: "#ffffff",
        "stroke-width": isMinor ? "1.2" : "2.5",
      }),
    );

    if (!isMinor) {
      const label = svgEl("text", {
        x: pos.x,
        y: pos.y + 4,
        "text-anchor": "middle",
        fill: "#ffffff",
        "font-size": isDense ? "10" : "12",
        "font-weight": "700",
      });
      label.textContent = node.id;
      g.appendChild(label);
    }

    if (isStart) {
      const badge = svgEl("text", {
        x: pos.x,
        y: pos.y - radius - 9,
        "text-anchor": "middle",
        fill: "#1d4ed8",
        "font-size": "10",
        "font-weight": "800",
      });
      badge.textContent = "COURIER";
      g.appendChild(badge);
    }

    g.addEventListener("click", () => handleNodeClick(node));
    nodeLayer.appendChild(g);
  }
  svg.appendChild(nodeLayer);

  // Moving courier marker during step animation
  if (courierXY) {
    svg.appendChild(
      svgEl("circle", {
        cx: courierXY.x,
        cy: courierXY.y,
        r: 9,
        fill: "#1d4ed8",
        stroke: "#ffffff",
        "stroke-width": "2.5",
      }),
    );
  }
}

function handleNodeClick(node) {
  if (state.placeMode) {
    state.courierStart = node.id;
    el("courier-start").value = node.id;
    state.placeMode = false;
    el("btn-place-d0").classList.remove("active-mode");
    el("btn-place-d0").textContent = "Pick on Map";
    clearPlan();
    setStatus(`Courier starting location set to ${node.id}.`);
    return;
  }

  if (node.type === "restaurant") {
    state.selectedRest = node.id;
    renderNodePickers();
    setStatus(`Selected pickup restaurant ${node.id}.`);
  } else if (node.type === "house") {
    state.selectedHouse = node.id;
    renderNodePickers();
    setStatus(`Selected customer house ${node.id}.`);
  }
}

function renderOrders() {
  const list = el("orders-list");
  list.innerHTML = "";
  if (!state.orders.length) {
    const emptyLi = document.createElement("li");
    emptyLi.className = "orders-empty";
    emptyLi.textContent =
      "No orders added yet. Pick a restaurant and house above.";
    list.appendChild(emptyLi);
    return;
  }

  const prioText = { 1: "P1 High", 2: "P2 Normal", 3: "P3 Low" };
  state.orders.forEach((order, index) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="order-meta">
        <strong>${order.order_id}</strong>
        <span>${order.restaurant_id} &rarr; ${order.customer_id}</span>
        <span class="prio-pill p${order.priority}">${prioText[order.priority] || `P${order.priority}`}</span>
      </div>
      <button class="order-remove-btn" type="button" title="Remove order">&times;</button>
    `;
    li.querySelector("button").addEventListener("click", () => {
      state.orders.splice(index, 1);
      renderOrders();
      clearPlan();
    });
    list.appendChild(li);
  });
}

function addOrder(restaurantId, houseId, priority, qty = 1) {
  if (!restaurantId || !houseId) {
    setStatus("Please select both a restaurant and a customer house.");
    return;
  }
  const safeQty = Math.max(1, Math.min(5, Number(qty) || 1));
  for (let i = 0; i < safeQty; i += 1) {
    state.orders.push({
      order_id: `ORD-${state.orderSeq++}`,
      restaurant_id: restaurantId,
      customer_id: houseId,
      priority: Number(priority),
    });
  }
  renderOrders();
  clearPlan();
  setStatus(
    `Added ${safeQty} order${safeQty > 1 ? "s" : ""} (${restaurantId} -> ${houseId}).`,
  );
}

function renderItinerary() {
  if (!state.plan) return;
  el("itinerary-box").classList.remove("hidden");
  el("total-time-badge").textContent =
    `Optimized: ${state.plan.total_time.toFixed(1)} min`;
  el("baseline-badge").textContent =
    `Unoptimized: ${state.plan.unoptimized_time.toFixed(1)} min`;
  const saved = state.plan.time_saved;
  const pct = state.plan.savings_percent;
  el("saved-badge").textContent =
    saved > 0
      ? `Time Saved: ${saved.toFixed(1)} min (${pct.toFixed(1)}%)`
      : "Time Saved: 0.0 min";

  const container = el("itinerary-steps");
  container.innerHTML = "";
  state.plan.steps.forEach((step, idx) => {
    const div = document.createElement("div");
    div.className = `step-card ${idx + 1 === state.visibleSteps ? "active" : ""}`;
    const tag = step.action === "pickup" ? "PICKUP" : "DELIVER";
    div.innerHTML = `
      <strong>${step.step}. [${tag}] ${step.order_id}</strong><br />
      ${step.path.join(" &rarr; ")} (${step.travel_time.toFixed(1)} min)
    `;
    div.addEventListener("click", () => {
      stopAnimation();
      state.visibleSteps = idx + 1;
      renderMap();
      renderItinerary();
      updatePlaybackButtons();
    });
    container.appendChild(div);
  });
}

async function optimizeAndPlay() {
  if (!state.orders.length) {
    setStatus("Please add at least one order before calculating a route.");
    return;
  }
  const payload = {
    map_id: state.mapId,
    courier_start: state.courierStart,
    urgency_penalty: Number(el("urgency-penalty").value),
    orders: state.orders,
  };
  const res = await fetch("/api/optimize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    setStatus(`Error: ${data.error}`);
    return;
  }

  state.plan = data;
  state.visibleSteps = 0;
  renderItinerary();
  updatePlaybackButtons();
  setStatus(
    `Best route found (${data.total_time.toFixed(1)} min). Playing step-by-step animation...`,
  );
  startAnimation();
}

function stopAnimation() {
  state.playing = false;
  if (state.animFrame) {
    cancelAnimationFrame(state.animFrame);
    state.animFrame = null;
  }
}

function startAnimation() {
  if (!state.plan || !state.plan.steps.length) return;
  if (state.visibleSteps >= state.plan.steps.length) {
    state.visibleSteps = 0;
  }
  state.playing = true;
  updatePlaybackButtons();
  animateNextStep();
}

function animateNextStep() {
  if (!state.playing || !state.plan) return;
  if (state.visibleSteps >= state.plan.steps.length) {
    state.playing = false;
    renderMap();
    renderItinerary();
    updatePlaybackButtons();
    setStatus(
      `All ${state.plan.steps.length} delivery steps completed in ${state.plan.total_time.toFixed(1)} min.`,
    );
    return;
  }

  const nextIdx = state.visibleSteps;
  const step = state.plan.steps[nextIdx];
  state.visibleSteps = nextIdx + 1;
  renderItinerary();
  updatePlaybackButtons();

  const points = step.path.map((id) => state.nodePos[id]);
  if (points.length <= 1) {
    renderMap(points[0]);
    setTimeout(() => animateNextStep(), 450);
    return;
  }

  let seg = 0;
  let progress = 0;
  const speed = 0.045;

  function frame() {
    if (!state.playing) return;
    progress += speed;
    if (progress >= 1) {
      seg += 1;
      progress = 0;
    }
    if (seg >= points.length - 1) {
      renderMap(points[points.length - 1]);
      setTimeout(() => animateNextStep(), 350);
      return;
    }
    const pA = points[seg];
    const pB = points[seg + 1];
    renderMap({
      x: pA.x + (pB.x - pA.x) * progress,
      y: pA.y + (pB.y - pA.y) * progress,
    });
    state.animFrame = requestAnimationFrame(frame);
  }
  state.animFrame = requestAnimationFrame(frame);
}

function drawBenchmarkChart(svgId, rows, xKey, y1Key, y2Key, y1Label, y2Label) {
  const svg = el(svgId);
  svg.innerHTML = "";
  const W = 460;
  const H = 260;
  const pad = { top: 24, right: 20, bottom: 38, left: 52 };
  const maxX = Math.max(...rows.map((r) => r[xKey]));
  const minX = Math.min(...rows.map((r) => r[xKey]));
  const maxY =
    Math.max(...rows.flatMap((r) => [r[y1Key], r[y2Key]])) * 1.1 || 1;

  const toX = (val) =>
    pad.left +
    ((val - minX) / Math.max(1, maxX - minX)) * (W - pad.left - pad.right);
  const toY = (val) =>
    H - pad.bottom - (val / maxY) * (H - pad.top - pad.bottom);

  svg.appendChild(
    svgEl("line", {
      x1: pad.left,
      y1: pad.top,
      x2: pad.left,
      y2: H - pad.bottom,
      stroke: "#94a3b8",
    }),
  );
  svg.appendChild(
    svgEl("line", {
      x1: pad.left,
      y1: H - pad.bottom,
      x2: W - pad.right,
      y2: H - pad.bottom,
      stroke: "#94a3b8",
    }),
  );

  const plotSeries = (key, color) => {
    const pts = rows.map((r) => `${toX(r[xKey])},${toY(r[key])}`).join(" ");
    svg.appendChild(
      svgEl("polyline", {
        points: pts,
        fill: "none",
        stroke: color,
        "stroke-width": "2.5",
      }),
    );
    for (const r of rows) {
      svg.appendChild(
        svgEl("circle", {
          cx: toX(r[xKey]),
          cy: toY(r[key]),
          r: 4,
          fill: color,
        }),
      );
    }
  };

  plotSeries(y1Key, "#16a34a");
  plotSeries(y2Key, "#dc2626");

  const legend1 = svgEl("text", {
    x: pad.left + 12,
    y: 18,
    "font-size": "11",
    fill: "#16a34a",
    "font-weight": "700",
  });
  legend1.textContent = y1Label;
  const legend2 = svgEl("text", {
    x: pad.left + 170,
    y: 18,
    "font-size": "11",
    fill: "#dc2626",
    "font-weight": "700",
  });
  legend2.textContent = y2Label;
  const xAxisTxt = svgEl("text", {
    x: W / 2,
    y: H - 8,
    "text-anchor": "middle",
    "font-size": "11",
    fill: "#475569",
  });
  xAxisTxt.textContent = `${xKey.toUpperCase()} (max=${maxX})`;
  const yAxisTxt = svgEl("text", {
    x: pad.left - 6,
    y: pad.top + 8,
    "text-anchor": "end",
    "font-size": "10",
    fill: "#475569",
  });
  yAxisTxt.textContent = `${maxY.toFixed(0)}ms`;

  svg.appendChild(legend1);
  svg.appendChild(legend2);
  svg.appendChild(xAxisTxt);
  svg.appendChild(yAxisTxt);
}

async function runLiveBenchmark() {
  el("btn-run-bench").disabled = true;
  el("btn-run-bench").textContent = "Running...";
  const res = await fetch("/api/benchmark");
  const data = await res.json();
  drawBenchmarkChart(
    "bench-pq-svg",
    data.priority_queue,
    "n",
    "minheap_ms",
    "linear_ms",
    "MinHeap O(log N)",
    "Linear O(N)",
  );
  drawBenchmarkChart(
    "bench-graph-svg",
    data.dijkstra,
    "v",
    "minheap_ms",
    "naive_ms",
    "MinHeap O((V+E)logV)",
    "Naive O(V^2)",
  );
  el("btn-run-bench").disabled = false;
  el("btn-run-bench").textContent = "Run Benchmark";
}

function bindEvents() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".tab-btn")
        .forEach((b) => b.classList.remove("active"));
      document
        .querySelectorAll(".tab-panel")
        .forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      el(`tab-${btn.dataset.tab}`).classList.add("active");
    });
  });

  el("btn-sample-map").addEventListener("click", () =>
    loadMap("/api/map/sample", "GET"),
  );
  el("btn-random-map").addEventListener("click", () =>
    loadMap("/api/map/random", "POST"),
  );

  el("courier-start").addEventListener("change", (e) => {
    state.courierStart = e.target.value;
    clearPlan();
    setStatus(`Courier starting location set to ${state.courierStart}.`);
  });

  el("btn-place-d0").addEventListener("click", () => {
    state.placeMode = !state.placeMode;
    el("btn-place-d0").classList.toggle("active-mode", state.placeMode);
    el("btn-place-d0").textContent = state.placeMode
      ? "Click Map Node..."
      : "Pick on Map";
    if (state.placeMode) {
      setStatus(
        "Click any node on the map to set the courier starting location.",
      );
    }
  });

  el("btn-add-order").addEventListener("click", () => {
    addOrder(
      state.selectedRest,
      state.selectedHouse,
      el("order-prio").value,
      Number(el("order-qty").value),
    );
  });

  el("btn-clear-orders").addEventListener("click", () => {
    state.orders = [];
    renderOrders();
    clearPlan();
    setStatus("All orders cleared.");
  });

  el("btn-preset-r2").addEventListener("click", () => {
    const hasR2 = state.nodes.some((n) => n.id === "R2");
    const restId = hasR2 ? "R2" : state.selectedRest;
    const hasH1 = state.nodes.some((n) => n.id === "H1");
    const hasH4 = state.nodes.some((n) => n.id === "H4");
    const firstHouse = hasH1 ? "H1" : state.selectedHouse;
    const secondHouse = hasH4 ? "H4" : "H2";

    addOrder(restId, firstHouse, 1, 1);
    addOrder(restId, secondHouse, 2, 1);
    setStatus(
      `Loaded sample batch from ${restId} to ${firstHouse} and ${secondHouse}. Click Calculate Best Route.`,
    );
  });

  el("urgency-penalty").addEventListener("input", (e) => {
    el("penalty-val").textContent = `${Number(e.target.value).toFixed(1)} min`;
  });

  el("btn-optimize").addEventListener("click", optimizeAndPlay);

  el("btn-play").addEventListener("click", () => {
    if (state.playing) {
      stopAnimation();
      updatePlaybackButtons();
    } else {
      startAnimation();
    }
  });

  el("btn-prev").addEventListener("click", () => {
    stopAnimation();
    state.visibleSteps = Math.max(0, state.visibleSteps - 1);
    renderMap();
    renderItinerary();
    updatePlaybackButtons();
  });

  el("btn-next").addEventListener("click", () => {
    stopAnimation();
    if (state.plan) {
      state.visibleSteps = Math.min(
        state.plan.steps.length,
        state.visibleSteps + 1,
      );
      renderMap();
      renderItinerary();
      updatePlaybackButtons();
    }
  });

  el("btn-reset-route").addEventListener("click", () => {
    stopAnimation();
    state.visibleSteps = 0;
    renderMap();
    renderItinerary();
    updatePlaybackButtons();
  });

  el("btn-run-bench").addEventListener("click", runLiveBenchmark);

  const syncFullscreenBtn = () => {
    const isFs = Boolean(document.fullscreenElement);
    el("fullscreen-label").textContent = isFs
      ? "Exit Fullscreen"
      : "Fullscreen";
    el("btn-fullscreen").classList.toggle("is-fullscreen", isFs);
  };

  el("btn-fullscreen").addEventListener("click", async () => {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen();
    } else {
      await document.exitFullscreen();
    }
  });
  document.addEventListener("fullscreenchange", syncFullscreenBtn);
}

bindEvents();
loadMap("/api/map/sample", "GET");
