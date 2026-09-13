#!/usr/bin/env python3
"""osa-map helper for the One Skill Army pack.

Run inside a project. Maintains .osa/graph/manifest.jsonl as a sha256
baseline of the working tree and reports which files changed since the
last index, so the agent re-verifies only those instead of rescanning.
--update rewrites the manifest; --html renders a self-contained
force-directed graph.html from nodes.jsonl + edges.jsonl. No args prints
the stale report. Source code stays the source of truth: this tool only
flags what to re-check.
"""
import argparse
import hashlib
import json
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".osa", ".venv", "venv", "__pycache__",
             "dist", "build", ".next"}
SKIP_NAME_PREFIX = (".env",)
MAX_BYTES = 2_000_000
GRAPH_DIR = Path(".osa") / "graph"


def scan(root):
    "Yield (relative posix path, Path) for indexable files under root."
    stack = [root]
    while stack:
        d = stack.pop()
        for entry in sorted(d.iterdir()):
            if entry.is_dir():
                if entry.name not in SKIP_DIRS:
                    stack.append(entry)
                continue
            if not entry.is_file() or entry.name.startswith(SKIP_NAME_PREFIX):
                continue
            try:
                if entry.stat().st_size > MAX_BYTES:
                    continue
                with entry.open("rb") as fh:
                    if b"\0" in fh.read(8192):
                        continue
            except OSError:
                continue
            yield entry.relative_to(root).as_posix(), entry


def load_manifest():
    "Return {path: entry} from the manifest, or None when not indexed yet."
    mf = GRAPH_DIR / "manifest.jsonl"
    if not mf.is_file():
        return None
    out = {}
    for line in mf.read_text().splitlines():
        line = line.strip()
        if line:
            entry = json.loads(line)
            out[entry["path"]] = entry
    return out


def snapshot():
    "Hash every indexable file in the current project."
    out = {}
    for rel, p in scan(Path(".")):
        data = p.read_bytes()
        out[rel] = {"path": rel, "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data)}
    return out


def write_manifest():
    "Replace the manifest with a fresh snapshot."
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(e, sort_keys=True) for e in snapshot().values()]
    (GRAPH_DIR / "manifest.jsonl").write_text("\n".join(lines) + "\n")


def report():
    "Print the machine-readable stale report plus one human summary line."
    old = load_manifest()
    if old is None:
        print("osa-map: no .osa/graph/manifest.jsonl yet; "
              "run again with --update to index this project")
        return
    cur = snapshot()
    added = sorted(set(cur) - set(old))
    deleted = sorted(set(old) - set(cur))
    modified = sorted(p for p in set(cur) & set(old)
                      if cur[p]["sha256"] != old[p]["sha256"])
    print("OSA-GRAPH-STALE")
    for p in added:
        print("ADDED", p)
    for p in modified:
        print("MODIFIED", p)
    for p in deleted:
        print("DELETED", p)
    print("END")
    if not (added or modified or deleted):
        print("osa-map: no changes")
    else:
        print(f"osa-map: {len(added)} added, {len(modified)} modified, "
              f"{len(deleted)} deleted")


def read_jsonl(name):
    "Read a .osa/graph JSONL file, tolerating a missing file."
    path = GRAPH_DIR / name
    if not path.is_file():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>osa-map</title>
<style>
body{margin:0;font-family:ui-monospace,monospace;background:#111;color:#ddd;overflow:hidden}
#bar{padding:6px 10px;background:#1b1b1b;font-size:13px;border-bottom:1px solid #333}
#q{background:#222;color:#eee;border:1px solid #444;padding:2px 6px;width:200px;margin-left:8px}
#legend span{margin-left:10px;font-size:12px}
#tip{position:fixed;display:none;background:#222;border:1px solid #555;padding:4px 8px;font-size:12px;pointer-events:none;max-width:360px;z-index:2}
canvas{display:block;cursor:grab}
</style>
</head>
<body>
<div id="bar"><b>osa-map</b> <span id="count"></span>
<input id="q" placeholder="filter nodes">
<span id="legend"></span></div>
<canvas id="c"></canvas>
<div id="tip"></div>
<script>
const DATA = __DATA__;
const COLORS = {file:"#8a8a8a",function:"#4da6ff",class:"#b07cff",route:"#ff9f43",
service:"#2ecc71",model:"#ff6b6b",config:"#f1c40f",doc:"#1abc9c"};
const KINDS = Object.keys(COLORS);
const nodes = DATA.nodes.map((n,i)=>({id:n.id,kind:COLORS[n.kind]?n.kind:"file",
label:n.id.split("/").pop(),summary:n.summary||"",x:Math.cos(i)*120+400,
y:Math.sin(i)*120+300,vx:0,vy:0}));
const idx = {}; nodes.forEach((n,i)=>idx[n.id]=i);
DATA.edges.forEach(e=>{ if(!(e.from in idx)){idx[e.from]=nodes.length;
nodes.push({id:e.from,kind:"file",label:e.from.split("/").pop(),summary:"",
x:400+Math.random()*80,y:300+Math.random()*80,vx:0,vy:0});}
if(!(e.to in idx)){idx[e.to]=nodes.length;
nodes.push({id:e.to,kind:"file",label:e.to.split("/").pop(),summary:"",
x:400+Math.random()*80,y:300+Math.random()*80,vx:0,vy:0});}});
const links = DATA.edges.map(e=>({s:idx[e.from],t:idx[e.to],rel:e.rel}));
const canvas = document.getElementById("c"), ctx = canvas.getContext("2d");
const tip = document.getElementById("tip");
function resize(){canvas.width=innerWidth;canvas.height=innerHeight-34;}
addEventListener("resize",resize);resize();
document.getElementById("count").textContent =
nodes.length+" nodes, "+links.length+" edges";
const legend=document.getElementById("legend");
KINDS.forEach(k=>{const s=document.createElement("span");
s.innerHTML='<span style="color:'+COLORS[k]+'">\\u25cf</span> '+k;legend.appendChild(s);});
let drag=-1,hover=null;
function pick(mx,my){let best=-1,bd=200;
nodes.forEach((n,i)=>{const d=(n.x-mx)**2+(n.y-my)**2;if(d<bd){bd=d;best=i;}});
return best;}
canvas.addEventListener("mousedown",e=>{drag=pick(e.clientX,e.clientY-34);});
addEventListener("mouseup",()=>{drag=-1;});
canvas.addEventListener("mousemove",e=>{
if(drag>=0){nodes[drag].x=e.clientX;nodes[drag].y=e.clientY-34;
nodes[drag].vx=0;nodes[drag].vy=0;}
const h=pick(e.clientX,e.clientY-34);
hover=h>=0?nodes[h]:null;
if(hover){tip.style.display="block";tip.style.left=(e.clientX+12)+"px";
tip.style.top=(e.clientY+12)+"px";
tip.innerHTML="<b>"+hover.id+"</b><br>"+hover.summary;}
else tip.style.display="none";});
const q=document.getElementById("q");
function matches(n){return !q.value||n.id.toLowerCase().includes(q.value.toLowerCase());}
function tick(){
for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
const a=nodes[i],b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+100;
const d=Math.sqrt(d2),f=1200/d2;a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;}
links.forEach(l=>{const a=nodes[l.s],b=nodes[l.t];
let dx=b.x-a.x,dy=b.y-a.y;const d=Math.sqrt(dx*dx+dy*dy)+0.01;
const f=(d-90)*0.005;a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;});
nodes.forEach(n=>{n.vx+=(canvas.width/2-n.x)*0.002;
n.vy+=(canvas.height/2-n.y)*0.002;
n.x+=n.vx*=0.85;n.y+=n.vy*=0.85;});}
function draw(){
ctx.clearRect(0,0,canvas.width,canvas.height);
links.forEach(l=>{const a=nodes[l.s],b=nodes[l.t];
ctx.strokeStyle="rgba(255,255,255,0.15)";ctx.beginPath();
ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();});
nodes.forEach(n=>{const dim=!matches(n);
ctx.globalAlpha=dim?0.15:1;
ctx.fillStyle=COLORS[n.kind]||"#8a8a8a";
ctx.beginPath();ctx.arc(n.x,n.y,6,0,7);ctx.fill();
ctx.fillStyle="#ccc";ctx.font="11px monospace";
ctx.fillText(n.label,n.x+9,n.y+4);ctx.globalAlpha=1;});
if(hover&&!matches(hover)){/* still draw hover ring */}
}
function loop(){tick();draw();requestAnimationFrame(loop);}
loop();
</script>
</body>
</html>
"""


def render_html():
    "Write graph.html from nodes + edges, creating implicit edge nodes."
    nodes = read_jsonl("nodes.jsonl")
    edges = read_jsonl("edges.jsonl")
    seen = {n.get("id") for n in nodes}
    for e in edges:
        for end in ("from", "to"):
            if e.get(end) and e[end] not in seen:
                nodes.append({"id": e[end], "kind": "file", "summary": ""})
                seen.add(e[end])
    data = json.dumps({"nodes": nodes, "edges": edges}).replace("</", "<\\/")
    if not nodes:
        html = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<title>osa-map</title></head><body style='background:#111;"
                "color:#ddd;font-family:monospace;padding:2em'>"
                "<h2>osa-map: empty graph</h2>"
                "<p>Record nodes and edges in .osa/graph/nodes.jsonl and "
                "edges.jsonl during tasks, then re-run --html.</p>"
                "</body></html>")
    else:
        html = HTML_TEMPLATE.replace("__DATA__", data)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    (GRAPH_DIR / "graph.html").write_text(html)
    print(f"osa-map: wrote .osa/graph/graph.html "
          f"({len(nodes)} nodes, {len(edges)} edges)")


def main():
    ap = argparse.ArgumentParser(description="osa-map staleness + HTML helper")
    ap.add_argument("--update", action="store_true", help="rewrite the manifest")
    ap.add_argument("--html", action="store_true", help="render graph.html")
    args = ap.parse_args()
    if args.html:
        render_html()
    elif args.update:
        write_manifest()
        print(f"osa-map: manifest updated "
              f"({len(snapshot())} files indexed)")
    else:
        report()


if __name__ == "__main__":
    main()
