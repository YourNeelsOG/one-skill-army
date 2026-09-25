"""Export the project graph to interchange formats.

GraphML opens in Gephi and yEd; the self-contained HTML is a zero-dependency
force-directed view that runs from a file with no network access: communities
colored and labelled, relations toggleable, INFERRED edges dashed, and a side
panel listing a clicked node's relations. Both read the
same graph dict the engine produces.
"""
import json
from xml.sax.saxutils import escape


def to_graphml(graph):
    "Return a GraphML XML document for the graph (Gephi / yEd compatible)."
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '<key id="rel" for="edge" attr.name="rel" attr.type="string"/>',
        '<key id="confidence" for="edge" attr.name="confidence" '
        'attr.type="string"/>',
        '<graph edgedefault="directed">',
    ]
    for node in graph["nodes"]:
        nid = escape(str(node["id"]), {'"': "&quot;"})
        kind = escape(str(node.get("kind", "")))
        lines.append('<node id="' + nid + '"><data key="kind">' + kind
                     + "</data></node>")
    for i, edge in enumerate(graph["edges"]):
        s = escape(str(edge.get("source", "")), {'"': "&quot;"})
        t = escape(str(edge.get("target", "")), {'"': "&quot;"})
        rel = escape(str(edge.get("rel", "")))
        conf = escape(str(edge.get("confidence", "")))
        lines.append('<edge id="e' + str(i) + '" source="' + s
                     + '" target="' + t + '"><data key="rel">' + rel
                     + '</data><data key="confidence">' + conf
                     + "</data></edge>")
    lines.append("</graph>")
    lines.append("</graphml>")
    return "\n".join(lines)


# Above this many nodes the view opens with only files, modules and packages
# visible; a checkbox shows symbols. Keeps big projects interactive.
HIDE_SYMBOLS_ABOVE = 1500
# Communities are skipped above this size (Louvain pass cost), like context.md.
COMMUNITY_NODE_CAP = 3000

_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>osa graph</title>
<style>
:root{--bg:#111418;--bar:#1a1e24;--line:#2c323b;--text:#d6dae0;--dim:#8a929c}
*{box-sizing:border-box}
body{margin:0;font:13px ui-monospace,SFMono-Regular,Menlo,monospace;
  background:var(--bg);color:var(--text);overflow:hidden}
#bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:6px 10px;
  background:var(--bar);border-bottom:1px solid var(--line)}
#bar input[type=text],#bar select{background:#0d1014;color:var(--text);
  border:1px solid var(--line);padding:3px 6px;font:inherit}
#q{width:220px}
#count{color:var(--dim)}
canvas{display:block;cursor:grab}
#legend,#panel{scrollbar-color:#3a414b transparent;scrollbar-width:thin}
#legend{position:fixed;left:8px;bottom:8px;max-width:300px;max-height:45vh;
  overflow:auto;background:rgba(26,30,36,.92);border:1px solid var(--line);
  padding:8px 10px;line-height:1.7}
#legend h4{margin:4px 0;color:var(--dim);font-weight:normal}
.sw{display:inline-block;width:18px;height:0;border-top:3px solid;
  vertical-align:middle;margin-right:6px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;
  vertical-align:middle;margin-right:6px}
#panel{position:fixed;right:0;top:40px;bottom:0;width:min(380px,100vw);
  overflow:auto;background:rgba(26,30,36,.97);border-left:1px solid var(--line);
  padding:10px 12px}
#panel h3{margin:0 0 4px;word-break:break-all}
#panel .loc{color:var(--dim);margin-bottom:8px}
#panel .grp{margin-top:8px;color:var(--dim)}
#panel a{color:var(--text);cursor:pointer;display:block;word-break:break-all;
  padding-left:10px}
#panel a:hover{text-decoration:underline}
#tip{position:fixed;display:none;background:#222831;border:1px solid #444;
  padding:3px 7px;pointer-events:none;max-width:420px;word-break:break-all}
</style></head><body>
<div id="bar"><b>osa graph</b><span id="count"></span>
<input id="q" type="text" placeholder="search, Enter to focus">
<label>color <select id="colorby"><option value="c">community</option>
<option value="kind">kind</option></select></label>
<label><input type="checkbox" id="symbols"> symbols</label>
<span id="count2"></span></div>
<canvas id="c"></canvas>
<div id="legend"></div>
<div id="panel" hidden></div>
<div id="tip"></div>
<script>
const DATA = __DATA__;
const REL_COLORS = {defines:"#6b7280",contains:"#4b5563",imports:"#22c55e",
  calls:"#3b82f6",inherits:"#a855f7",method_of:"#94a3b8",links_to:"#eab308",
  references:"#f97316"};
const KIND_COLORS = {file:"#9ca3af",module:"#22c55e",package:"#16a34a",
  function:"#3b82f6",method:"#60a5fa",class:"#a855f7",struct:"#a855f7",
  interface:"#c084fc",trait:"#c084fc",heading:"#eab308",table:"#f97316",
  view:"#fb923c"};
const STRUCTURAL = new Set(["file","module","package"]);
const relColor = r => REL_COLORS[r] || "#ec4899";  // manual edges: pink
const commColor = c => "hsl(" + ((c * 137.5) % 360) + ",62%,58%)";

const nodes = DATA.nodes.map((n, i) => {
  // Seed positions by community on a ring so the layout settles fast.
  const a = (n.c * 2.399) % (2 * Math.PI), r = 160 + (n.c % 7) * 40;
  const j = (i * 7919) % 97;
  return Object.assign({}, n, {x: 600 + Math.cos(a) * r + j,
    y: 400 + Math.sin(a) * r + (j * 3) % 61, vx: 0, vy: 0, show: true});
});
const links = DATA.edges.map(e => Object.assign({}, e, {show: true}));
const adj = nodes.map(() => []);
links.forEach((l, i) => { adj[l.s].push(i); adj[l.t].push(i); });

const canvas = document.getElementById("c"), ctx = canvas.getContext("2d");
const tip = document.getElementById("tip"), panel = document.getElementById("panel");
const q = document.getElementById("q"), colorby = document.getElementById("colorby");
const symbols = document.getElementById("symbols");
let W = 1200, H = 800, alpha = 1, k = 1, ox = 0, oy = 0, dirty = true;
let selected = -1, hover = -1;
const relOn = {}, confOn = {E: true, I: true};
links.forEach(l => { relOn[l.rel] = true; });
symbols.checked = !DATA.hideSymbols;

function resize() {
  // The bar wraps on narrow screens: keep the side panel below it.
  const barH = document.getElementById("bar").offsetHeight;
  panel.style.top = barH + "px";
  canvas.width = innerWidth;
  canvas.height = innerHeight - barH;
  W = canvas.width / k; H = canvas.height / k; dirty = true;
}
addEventListener("resize", resize);

// Physics: grid-bucketed repulsion (only nearby nodes push), springs along
// visible links, a weak pull to the centre, and a cooling factor so the
// simulation stops instead of burning CPU forever.
function tick() {
  const grid = new Map();
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    if (!n.show) continue;
    const key = Math.floor(n.x / CELL) + "," + Math.floor(n.y / CELL);
    let bucket = grid.get(key);
    if (!bucket) { bucket = []; grid.set(key, bucket); }
    bucket.push(i);
  }
  for (const [key, bucket] of grid) {
    const [gx, gy] = key.split(",").map(Number);
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      const other = grid.get((gx + dx) + "," + (gy + dy));
      if (!other) continue;
      for (const i of bucket) for (const j of other) {
        if (j <= i) continue;
        const a = nodes[i], b = nodes[j];
        const ddx = a.x - b.x, ddy = a.y - b.y;
        const d2 = ddx * ddx + ddy * ddy + 25, d = Math.sqrt(d2);
        const f = REPEL * alpha / d2;
        a.vx += ddx / d * f; a.vy += ddy / d * f;
        b.vx -= ddx / d * f; b.vy -= ddy / d * f;
      }
    }
  }
  for (const l of links) {
    if (!l.show) continue;
    const a = nodes[l.s], b = nodes[l.t];
    const ddx = b.x - a.x, ddy = b.y - a.y;
    const d = Math.sqrt(ddx * ddx + ddy * ddy) + 0.01;
    const f = (d - LINK_LEN) * SPRING * alpha;
    a.vx += ddx / d * f; a.vy += ddy / d * f;
    b.vx -= ddx / d * f; b.vy -= ddy / d * f;
  }
  for (const n of nodes) {
    if (!n.show) continue;
    n.vx += (W / 2 - n.x) * GRAVITY * alpha;
    n.vy += (H / 2 - n.y) * GRAVITY * alpha;
    n.vx = Math.max(-MAX_V, Math.min(MAX_V, n.vx * DAMP));
    n.vy = Math.max(-MAX_V, Math.min(MAX_V, n.vy * DAMP));
    n.x += n.vx; n.y += n.vy;
  }
  alpha *= ALPHA_DECAY;
}
const CELL = 110, REPEL = 900, SPRING = 0.03, LINK_LEN = 55, GRAVITY = 0.006;
const DAMP = 0.8, MAX_V = 40, ALPHA_DECAY = 0.985, ALPHA_MIN = 0.02;

function draw() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.setTransform(k, 0, 0, k, ox, oy);
  const focus = new Set();
  if (selected >= 0) {
    focus.add(selected);
    adj[selected].forEach(li => { focus.add(links[li].s); focus.add(links[li].t); });
  }
  const term = q.value.trim().toLowerCase();
  ctx.lineWidth = 1 / k;
  for (const l of links) {
    if (!l.show) continue;
    const a = nodes[l.s], b = nodes[l.t];
    const lit = selected < 0 || (focus.has(l.s) && focus.has(l.t) &&
      (l.s === selected || l.t === selected));
    ctx.globalAlpha = lit ? (selected < 0 ? 0.45 : 0.95) : 0.06;
    ctx.strokeStyle = relColor(l.rel);
    ctx.setLineDash(l.conf === "I" ? [5 / k, 4 / k] : []);
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
  }
  ctx.setLineDash([]);
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    if (!n.show) continue;
    const match = term && (n.id.toLowerCase().includes(term));
    const lit = (selected < 0 && !term) || focus.has(i) || match;
    ctx.globalAlpha = lit ? 1 : 0.15;
    ctx.fillStyle = colorby.value === "c" ? commColor(n.c)
      : (KIND_COLORS[n.kind] || "#9ca3af");
    const r = (STRUCTURAL.has(n.kind) ? 6 : 4) + Math.min(6, adj[i].length / 6);
    ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, 7); ctx.fill();
    if (i === selected || match) {
      ctx.strokeStyle = "#fff"; ctx.lineWidth = 2 / k; ctx.stroke();
      ctx.lineWidth = 1 / k;
    }
    if (k > 1.3 || focus.has(i) || match || i === hover) {
      ctx.fillStyle = "#d6dae0";
      ctx.font = (11 / k) + "px ui-monospace,monospace";
      ctx.fillText(n.name || n.id, n.x + r + 2 / k, n.y + 4 / k);
    }
  }
  ctx.globalAlpha = 1;
}

function applyFilters() {
  nodes.forEach(n => { n.show = symbols.checked || STRUCTURAL.has(n.kind); });
  let shown = 0;
  links.forEach(l => {
    l.show = relOn[l.rel] && confOn[l.conf] && nodes[l.s].show && nodes[l.t].show;
    if (l.show) shown++;
  });
  document.getElementById("count").textContent = " " +
    nodes.filter(n => n.show).length + "/" + nodes.length + " nodes, " +
    shown + "/" + links.length + " edges";
  alpha = Math.max(alpha, 0.3); dirty = true;
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
}

function legend() {
  const rels = Object.keys(relOn).sort();
  let h = "<h4>relations</h4>";
  for (const r of rels) {
    h += '<label><input type="checkbox" data-rel="' + esc(r) + '"' +
      (relOn[r] ? " checked" : "") + '><span class="sw" style="border-color:' +
      relColor(r) + '"></span>' + esc(r) + "</label><br>";
  }
  h += "<h4>confidence</h4>";
  h += '<label><input type="checkbox" data-conf="E" checked><span class="sw" ' +
    'style="border-color:#ccc"></span>EXTRACTED</label><br>';
  h += '<label><input type="checkbox" data-conf="I" checked><span class="sw" ' +
    'style="border-color:#ccc;border-top-style:dashed"></span>INFERRED</label>';
  if (colorby.value === "c") {
    const sizes = {};
    nodes.forEach(n => { sizes[n.c] = (sizes[n.c] || 0) + 1; });
    const top = Object.keys(sizes).sort((a, b) => sizes[b] - sizes[a]).slice(0, 12);
    h += "<h4>communities</h4>";
    for (const c of top) {
      h += '<span class="dot" style="background:' + commColor(+c) + '"></span>' +
        esc(DATA.labels[c] || c) + " (" + sizes[c] + ")<br>";
    }
  }
  const el = document.getElementById("legend");
  el.innerHTML = h;
  el.querySelectorAll("[data-rel]").forEach(cb => cb.onchange = () => {
    relOn[cb.dataset.rel] = cb.checked; applyFilters(); });
  el.querySelectorAll("[data-conf]").forEach(cb => cb.onchange = () => {
    confOn[cb.dataset.conf] = cb.checked; applyFilters(); });
}

function select(i) {
  selected = i; dirty = true;
  if (i < 0) { panel.hidden = true; return; }
  const n = nodes[i], groups = {};
  for (const li of adj[i]) {
    const l = links[li], out = l.s === i, other = out ? l.t : l.s;
    const key = (out ? "--> " : "<-- ") + l.rel;
    (groups[key] = groups[key] || []).push({other, l});
  }
  let h = "<h3>" + esc(n.id) + "</h3><div class=loc>" + esc(n.kind) + ", " +
    esc((n.path || n.id) + ":" + (n.line || 1)) + ", community " +
    esc(DATA.labels[n.c] || n.c) + "</div>";
  for (const key of Object.keys(groups).sort()) {
    h += '<div class="grp">' + esc(key) + "</div>";
    for (const g of groups[key]) {
      const tag = g.l.conf === "E" ? "[E] " : "[I] ";
      const why = g.l.why ? " (" + g.l.why + ")" : "";
      h += '<a data-i="' + g.other + '">' + tag + esc(nodes[g.other].id) +
        esc(why) + "</a>";
    }
  }
  panel.innerHTML = h; panel.hidden = false;
  panel.querySelectorAll("a").forEach(a => a.onclick = () => {
    const j = +a.dataset.i; center(j); select(j); });
}

function center(i) {
  const n = nodes[i];
  ox = canvas.width / 2 - n.x * k; oy = canvas.height / 2 - n.y * k; dirty = true;
}

function toWorld(e) {
  const rect = canvas.getBoundingClientRect();
  return [(e.clientX - rect.left - ox) / k, (e.clientY - rect.top - oy) / k];
}

function pick(e) {
  const [x, y] = toWorld(e);
  let best = -1, bd = (10 / k) ** 2;
  nodes.forEach((n, i) => {
    if (!n.show) return;
    const d = (n.x - x) ** 2 + (n.y - y) ** 2;
    if (d < bd) { bd = d; best = i; }
  });
  return best;
}

let drag = -1, panning = null, moved = false;
canvas.addEventListener("mousedown", e => {
  moved = false; drag = pick(e);
  if (drag < 0) panning = [e.clientX - ox, e.clientY - oy];
});
addEventListener("mouseup", () => {
  if (!moved) select(drag);
  drag = -1; panning = null;
});
canvas.addEventListener("mousemove", e => {
  moved = true;
  if (drag >= 0) {
    const [x, y] = toWorld(e);
    Object.assign(nodes[drag], {x, y, vx: 0, vy: 0});
    alpha = Math.max(alpha, 0.2);
  } else if (panning) {
    ox = e.clientX - panning[0]; oy = e.clientY - panning[1];
  }
  const h = pick(e);
  if (h !== hover) { hover = h; }
  if (h >= 0) {
    tip.style.display = "block";
    tip.style.left = Math.min(e.clientX + 12, innerWidth - 300) + "px";
    tip.style.top = (e.clientY + 12) + "px";
    tip.textContent = nodes[h].id;
  } else tip.style.display = "none";
  dirty = true;
});
canvas.addEventListener("wheel", e => {
  e.preventDefault();
  const f = e.deltaY < 0 ? 1.12 : 1 / 1.12;
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  ox = mx - (mx - ox) * f; oy = my - (my - oy) * f; k *= f; dirty = true;
}, {passive: false});
q.addEventListener("input", () => { dirty = true; });
q.addEventListener("keydown", e => {
  if (e.key !== "Enter") return;
  const term = q.value.trim().toLowerCase();
  const i = nodes.findIndex(n => n.show && n.id.toLowerCase().includes(term));
  if (i >= 0) { center(i); select(i); }
});
colorby.onchange = () => { legend(); dirty = true; };
symbols.onchange = applyFilters;

function loop() {
  if (alpha > ALPHA_MIN) { tick(); dirty = true; }
  if (dirty) { draw(); dirty = false; }
  requestAnimationFrame(loop);
}
resize(); applyFilters(); legend(); loop();
</script></body></html>"""


def to_html(graph):
    """Return a self-contained, offline HTML view of the graph.

    Nodes carry their community (color and legend label); edges carry their
    relation (color, toggle) and confidence (INFERRED drawn dashed, with the
    reason shown in the side panel).
    """
    from .analyze import communities
    from .report import community_labels

    nodes = graph["nodes"]
    comm = communities(graph) if len(nodes) <= COMMUNITY_NODE_CAP else {}
    labels = ({str(c): lab for c, lab in community_labels(graph, comm).items()}
              if comm else {"0": "all nodes"})
    index = {n["id"]: i for i, n in enumerate(nodes)}
    data = {
        "nodes": [{"id": n["id"], "kind": n.get("kind", "file"),
                   "name": n.get("name", n["id"]), "path": n.get("path"),
                   "line": n.get("line"), "c": comm.get(n["id"], 0)}
                  for n in nodes],
        "edges": [{"s": index[e["source"]], "t": index[e["target"]],
                   "rel": e.get("rel", ""),
                   "conf": "E" if e.get("confidence", "EXTRACTED")
                   == "EXTRACTED" else "I",
                   "why": e.get("reason")}
                  for e in graph["edges"]
                  if e.get("source") in index and e.get("target") in index],
        "labels": labels,
        "hideSymbols": len(nodes) > HIDE_SYMBOLS_ABOVE,
    }
    text = json.dumps(data)
    text = text.replace("</", "<\\/")  # never break out of the script block
    return _HTML.replace("__DATA__", text)
