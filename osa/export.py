"""Export the project graph to interchange formats.

GraphML opens in Gephi and yEd; the self-contained HTML is a zero-dependency
force-directed view that runs from a file with no network access. Both read the
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
        lines.append('<edge id="e' + str(i) + '" source="' + s
                     + '" target="' + t + '"><data key="rel">' + rel
                     + "</data></edge>")
    lines.append("</graph>")
    lines.append("</graphml>")
    return "\n".join(lines)


_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>osa graph</title>
<style>
body{margin:0;font-family:ui-monospace,monospace;background:#111;color:#ddd;overflow:hidden}
#bar{padding:6px 10px;background:#1b1b1b;font-size:13px;border-bottom:1px solid #333}
#q{background:#222;color:#eee;border:1px solid #444;padding:2px 6px;width:200px;margin-left:8px}
canvas{display:block;cursor:grab}
#tip{position:fixed;display:none;background:#222;border:1px solid #555;padding:4px 8px;font-size:12px;pointer-events:none;max-width:360px;z-index:2}
</style></head><body>
<div id="bar"><b>osa graph</b> <span id="count"></span><input id="q" placeholder="filter nodes"></div>
<canvas id="c"></canvas><div id="tip"></div>
<script>
const DATA = __DATA__;
const COLORS = {file:"#8a8a8a",function:"#4da6ff",class:"#b07cff",module:"#2ecc71",heading:"#f1c40f"};
const nodes = DATA.nodes.map((n,i)=>({id:n.id,kind:COLORS[n.kind]?n.kind:"file",
label:String(n.id).split("/").pop(),x:Math.cos(i)*120+400,y:Math.sin(i)*120+300,vx:0,vy:0}));
const idx={}; nodes.forEach((n,i)=>idx[n.id]=i);
const links = DATA.edges.filter(e=>e.source in idx && e.target in idx).map(e=>({s:idx[e.source],t:idx[e.target]}));
const canvas=document.getElementById("c"),ctx=canvas.getContext("2d"),tip=document.getElementById("tip");
function resize(){canvas.width=innerWidth;canvas.height=innerHeight-34;}addEventListener("resize",resize);resize();
document.getElementById("count").textContent=nodes.length+" nodes, "+links.length+" edges";
let drag=-1,hover=null;
function pick(mx,my){let best=-1,bd=200;nodes.forEach((n,i)=>{const d=(n.x-mx)**2+(n.y-my)**2;if(d<bd){bd=d;best=i;}});return best;}
canvas.addEventListener("mousedown",e=>{drag=pick(e.clientX,e.clientY-34);});
addEventListener("mouseup",()=>{drag=-1;});
canvas.addEventListener("mousemove",e=>{if(drag>=0){nodes[drag].x=e.clientX;nodes[drag].y=e.clientY-34;nodes[drag].vx=0;nodes[drag].vy=0;}
const h=pick(e.clientX,e.clientY-34);hover=h>=0?nodes[h]:null;
if(hover){tip.style.display="block";tip.style.left=(e.clientX+12)+"px";tip.style.top=(e.clientY+12)+"px";tip.textContent=hover.id;}else tip.style.display="none";});
const q=document.getElementById("q");
function matches(n){return !q.value||n.id.toLowerCase().includes(q.value.toLowerCase());}
function tick(){for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j];
let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+100,d=Math.sqrt(d2),f=1200/d2;a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;}
links.forEach(l=>{const a=nodes[l.s],b=nodes[l.t];let dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)+0.01,f=(d-90)*0.005;
a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;});
nodes.forEach(n=>{n.vx+=(canvas.width/2-n.x)*0.002;n.vy+=(canvas.height/2-n.y)*0.002;n.x+=n.vx*=0.85;n.y+=n.vy*=0.85;});}
function draw(){ctx.clearRect(0,0,canvas.width,canvas.height);
links.forEach(l=>{const a=nodes[l.s],b=nodes[l.t];ctx.strokeStyle="rgba(255,255,255,0.15)";ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();});
nodes.forEach(n=>{ctx.globalAlpha=matches(n)?1:0.15;ctx.fillStyle=COLORS[n.kind]||"#8a8a8a";
ctx.beginPath();ctx.arc(n.x,n.y,6,0,7);ctx.fill();ctx.fillStyle="#ccc";ctx.font="11px monospace";ctx.fillText(n.label,n.x+9,n.y+4);ctx.globalAlpha=1;});}
function loop(){tick();draw();requestAnimationFrame(loop);}loop();
</script></body></html>"""


def to_html(graph):
    "Return a self-contained force-directed HTML view of the graph."
    data = json.dumps({"nodes": graph["nodes"], "edges": graph["edges"]})
    data = data.replace("</", "<\\/")  # never break out of the script block
    return _HTML.replace("__DATA__", data)
