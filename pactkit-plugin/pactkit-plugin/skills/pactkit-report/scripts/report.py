import abc, re, os, sys, json, datetime, argparse, subprocess, shutil, ast
from collections import deque
from dataclasses import dataclass
from pathlib import Path

def nl(): return chr(10)
#!/usr/bin/env python3
"""PactKit Report Skill — Interactive HTML from .mmd files.

STORY-slim-090: Single-file D3 force-directed HTML reports.
STORY-slim-094: Unified aggregated dashboard with Tab switching + audit data.
"""
import argparse
import html as _html_mod
import json
import re
import urllib.request
from pathlib import Path


# --- MMD Parser (R1) ---


def _parse_mmd(mmd_content):
    """Parse a Mermaid .mmd file into {nodes, edges, groups}.

    Supports graph TD/LR and classDiagram formats.
    """
    lines = mmd_content.strip().splitlines()
    if not lines:
        return {'nodes': [], 'edges': [], 'groups': []}

    first = lines[0].strip().lower()
    if first.startswith('classdiagram'):
        return _parse_class_diagram(lines)
    return _parse_graph_td(lines)


def _parse_graph_td(lines):
    """Parse graph TD/LR format."""
    nodes = {}  # id -> {id, label, group?, href?}
    edges = []
    groups = []
    hrefs = {}  # node_id -> href from click lines
    link_styles = {}  # edge_index -> style

    current_group = None
    edge_index = 0

    # Regex patterns
    # Node: A["label"] or A["label with spaces"]
    re_node = re.compile(r'^\s*(\w+)\["([^"]+)"\]')
    # Edge: A --> B  or  A -->|label| B  or  A -.-> B  or  A -.->\|label\| B
    re_edge = re.compile(r'^\s*(\w+)\s+(-->|-.->)(?:\|([^|]*)\|)?\s*(\w+)')
    # Click: click nodeId href "path"
    re_click = re.compile(r'^\s*click\s+(\w+)\s+href\s+"([^"]+)"')
    # Subgraph: subgraph "Name" or subgraph Name
    re_subgraph = re.compile(r'^\s*subgraph\s+"?([^"]+?)"?\s*$')
    # linkStyle N stroke:red...
    re_linkstyle = re.compile(r'^\s*linkStyle\s+(\d+)\s+.*stroke\s*:\s*red')

    for line in lines:
        stripped = line.strip()

        # Skip header
        if stripped.lower().startswith('graph '):
            continue

        # Subgraph start
        m = re_subgraph.match(stripped)
        if m:
            current_group = m.group(1).strip()
            if current_group not in groups:
                groups.append(current_group)
            continue

        # Subgraph end
        if stripped == 'end':
            current_group = None
            continue

        # Click href
        m = re_click.match(stripped)
        if m:
            hrefs[m.group(1)] = m.group(2)
            continue

        # linkStyle
        m = re_linkstyle.match(stripped)
        if m:
            link_styles[int(m.group(1))] = 'violation'
            continue

        # Node definition
        m = re_node.match(stripped)
        if m:
            nid, label = m.group(1), m.group(2)
            if nid not in nodes:
                nodes[nid] = {'id': nid, 'label': label}
            else:
                nodes[nid]['label'] = label
            if current_group:
                nodes[nid]['group'] = current_group
            continue

        # Edge
        m = re_edge.match(stripped)
        if m:
            src, arrow, label, dst = m.group(1), m.group(2), m.group(3), m.group(4)
            edge = {'source': src, 'target': dst}
            if label:
                edge['label'] = label
            if arrow == '-.->':
                edge['style'] = 'dashed'
            # Ensure nodes exist
            if src not in nodes:
                nodes[src] = {'id': src, 'label': src}
            if dst not in nodes:
                nodes[dst] = {'id': dst, 'label': dst}
            if current_group:
                if 'group' not in nodes[src]:
                    nodes[src]['group'] = current_group
                if 'group' not in nodes[dst]:
                    nodes[dst]['group'] = current_group
            edges.append(edge)
            edge_index += 1
            continue

        # Style lines (ignored) or NOTE lines (ignored)

    # Apply click hrefs
    for nid, href in hrefs.items():
        if nid in nodes:
            nodes[nid]['href'] = href

    # Apply linkStyle overrides
    for idx, style in link_styles.items():
        if idx < len(edges):
            edges[idx]['style'] = style

    return {'nodes': list(nodes.values()), 'edges': edges, 'groups': groups}


def _parse_class_diagram(lines):
    """Parse classDiagram format."""
    nodes = {}
    edges = []

    # Regex patterns
    re_class = re.compile(r'^\s*class\s+(\w+)')
    re_member = re.compile(r'^\s+([+\-#])(\w+)')
    re_inherit = re.compile(r'^\s*(\w+)\s+<\|--\s+(\w+)')
    re_assoc = re.compile(r'^\s*(\w+)\s+-->\s+(\w+)')

    current_class = None
    current_members = []

    for line in lines:
        stripped = line.strip()
        if stripped.lower() == 'classdiagram':
            continue

        # Class definition start
        m = re_class.match(stripped)
        if m:
            # Flush previous class
            if current_class and current_class in nodes:
                nodes[current_class]['members'] = current_members
            current_class = m.group(1)
            current_members = []
            if current_class not in nodes:
                nodes[current_class] = {'id': current_class, 'label': current_class}
            continue

        # Class member
        m = re_member.match(line)  # Use original line for indentation
        if m and current_class:
            current_members.append(line.strip())
            continue

        # Closing brace
        if stripped == '}' and current_class:
            nodes[current_class]['members'] = current_members
            current_class = None
            current_members = []
            continue

        # Inheritance: Base <|-- Derived
        m = re_inherit.match(stripped)
        if m:
            base, derived = m.group(1), m.group(2)
            if base not in nodes:
                nodes[base] = {'id': base, 'label': base}
            if derived not in nodes:
                nodes[derived] = {'id': derived, 'label': derived}
            edges.append({'source': base, 'target': derived, 'label': 'extends', 'style': 'dashed'})
            continue

        # Association: A --> B
        m = re_assoc.match(stripped)
        if m:
            src, dst = m.group(1), m.group(2)
            if src not in nodes:
                nodes[src] = {'id': src, 'label': src}
            if dst not in nodes:
                nodes[dst] = {'id': dst, 'label': dst}
            edges.append({'source': src, 'target': dst})
            continue

    # Flush last class
    if current_class and current_class in nodes:
        nodes[current_class]['members'] = current_members

    return {'nodes': list(nodes.values()), 'edges': edges, 'groups': []}


# --- Dashboard HTML Template (CodeFlow-inspired) ---

_DASHBOARD_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>
:root{--bg:#0d1117;--fg:#c9d1d9;--panel:#161b22;--border:#30363d;--accent:#58a6ff;--green:#3fb950;--yellow:#d29922;--orange:#db6d28;--red:#f85149;--muted:#8b949e}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--fg);overflow:hidden;height:100vh}
a{color:var(--accent);text-decoration:none}
/* Layout: 3-column */
#app{display:grid;grid-template-columns:240px 1fr 320px;grid-template-rows:48px 1fr;height:100vh}
#topbar{grid-column:1/-1;display:flex;align-items:center;gap:12px;padding:0 16px;background:var(--panel);border-bottom:1px solid var(--border)}
#topbar .logo{font-weight:700;font-size:15px;color:var(--accent)}
#topbar input{padding:5px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--fg);font-size:13px;width:260px}
#topbar .match{font-size:12px;color:var(--muted);min-width:90px}
#topbar .spacer{flex:1}
.tbtn{padding:4px 12px;border:1px solid var(--border);border-radius:6px;background:var(--panel);color:var(--fg);cursor:pointer;font-size:12px}
.tbtn:hover{border-color:var(--accent)}
.tbtn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
/* Left panel */
#left{background:var(--panel);border-right:1px solid var(--border);overflow-y:auto;padding:16px;font-size:13px}
#left h3{font-size:11px;text-transform:uppercase;color:var(--muted);margin:16px 0 8px;letter-spacing:.5px}
#left h3:first-child{margin-top:0}
.color-legend{display:flex;flex-direction:column;gap:4px}
.color-legend div{display:flex;align-items:center;gap:8px;cursor:pointer;padding:2px 4px;border-radius:4px}
.color-legend div:hover{background:var(--border)}
.color-legend .dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.stat-box{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center}
.stat-box .num{font-size:22px;font-weight:700;color:var(--accent)}
.stat-box .lbl{font-size:10px;color:var(--muted);text-transform:uppercase}
.file-tree{font-size:12px;margin-top:4px}
.file-tree details{margin-left:12px}
.file-tree summary{cursor:pointer;padding:1px 0;user-select:none}
.file-tree summary:hover{color:var(--accent)}
.file-tree .count{color:var(--muted);font-size:11px;float:right}
/* Center: SVG graph */
#center{position:relative;overflow:hidden}
#center svg{width:100%;height:100%;display:block}
.node-circle{cursor:pointer;stroke:#fff;stroke-width:1.5}
.node-label{font-size:10px;fill:var(--fg);pointer-events:none}
.link{stroke:var(--border);stroke-width:1;fill:none;opacity:.6}
.link.violation{stroke:var(--red);stroke-width:2;opacity:1}
.link.dashed{stroke-dasharray:4 2}
.faded{opacity:.08!important}
#center .view-tabs{position:absolute;top:12px;left:50%;transform:translateX(-50%);display:flex;gap:4px;z-index:5}
#center .bottom-bar{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);display:flex;gap:12px;font-size:12px;color:var(--muted);background:var(--panel);padding:4px 16px;border-radius:16px;border:1px solid var(--border)}
/* Right panel */
#right{background:var(--panel);border-left:1px solid var(--border);overflow-y:auto;padding:16px;font-size:13px}
#right .tabs{display:flex;gap:0;border-bottom:1px solid var(--border);margin-bottom:12px}
#right .tab{padding:6px 12px;font-size:12px;cursor:pointer;border-bottom:2px solid transparent;color:var(--muted)}
#right .tab.active{color:var(--accent);border-bottom-color:var(--accent)}
#right h2{font-size:14px;margin-bottom:4px}
#right .filepath{font-size:11px;color:var(--muted);margin-bottom:12px;word-break:break-all}
.section{margin-bottom:16px}
.section-header{display:flex;align-items:center;justify-content:space-between;cursor:pointer;padding:8px 0;border-top:1px solid var(--border)}
.section-header h3{font-size:13px}
.badge{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600}
.badge.critical{background:var(--red);color:#fff}
.badge.high{background:var(--orange);color:#fff}
.badge.medium{background:var(--yellow);color:#000}
.badge.low{background:var(--green);color:#000}
.section-body{font-size:12px;color:var(--muted);padding:4px 0}
.affected-list{list-style:none;padding:0}
.affected-list li{padding:2px 0;display:flex;align-items:center;gap:6px}
.affected-list li::before{content:'';width:8px;height:8px;background:var(--border);display:inline-block}
.conn-count{display:inline-block;background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:1px 8px;font-size:11px;float:right}
.func-row{display:flex;align-items:center;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border)}
.func-name{color:var(--accent);font-size:12px}
.func-tags span{font-size:10px;padding:1px 6px;border-radius:4px;margin-left:4px;background:var(--bg);border:1px solid var(--border)}
.no-select{font-size:12px;color:var(--muted);padding:40px 0;text-align:center}
</style>
</head>
<body>
<div id="app">
<div id="topbar">
  <span class="logo">PACTKIT</span>
  <input id="search" type="text" placeholder="Search files & functions...">
  <span class="match" id="match-count"></span>
  <span class="spacer"></span>
  <button class="tbtn" id="zoom-in" title="Zoom in">+</button>
  <button class="tbtn" id="zoom-out" title="Zoom out">&minus;</button>
  <button class="tbtn" id="zoom-reset" title="Reset">Reset</button>
  <button class="tbtn" id="fullscreen-btn">&#x26F6;</button>
</div>
<div id="left">
  <h3>Color By</h3>
  <div class="color-legend" id="color-legend"></div>
  <h3>Stats</h3>
  <div class="stat-grid" id="stat-grid"></div>
  <h3>Explorer</h3>
  <div class="file-tree" id="file-tree"></div>
</div>
<div id="center">
  <svg id="graph"><defs>
    <marker id="arrow" viewBox="0 0 10 6" refX="18" refY="3" markerWidth="6" markerHeight="5" orient="auto-start-reverse">
      <path d="M0 0L10 3L0 6Z" fill="var(--border)"/>
    </marker>
  </defs></svg>
  <div class="bottom-bar" id="bottom-bar"></div>
</div>
<div id="right">
  <div class="no-select" id="no-select">Click a node to inspect</div>
  <div id="detail-content" style="display:none">
    <h2 id="det-name"></h2>
    <div class="filepath" id="det-path"></div>
    <div class="section" id="sect-blast">
      <div class="section-header"><h3>Blast Radius</h3><span class="badge" id="blast-badge"></span></div>
      <div class="section-body" id="blast-body"></div>
    </div>
    <div class="section" id="sect-conn">
      <div class="section-header"><h3>Connections</h3><span class="conn-count" id="conn-count"></span></div>
      <div class="section-body" id="conn-body"></div>
    </div>
    <div class="section" id="sect-funcs">
      <div class="section-header"><h3>Functions</h3></div>
      <div class="section-body" id="funcs-body"></div>
    </div>
  </div>
</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script>
const DATA=/*GRAPH_JSON*/null;
const OVERLAY=/*OVERLAY_JSON*/null;
const FUNCS=/*FUNCS_JSON*/null;
const nodes=DATA.nodes,edges=DATA.edges,groups=DATA.groups||[];
// Folder-based color
const folders=[...new Set(nodes.map(n=>{const p=n.href||n.label||'';const s=p.split('/');return s.length>1?s.slice(0,-1).join('/'):'/'}))].sort();
const fColor=d3.scaleOrdinal(d3.schemeTableau10).domain(folders);
function getFolder(d){const p=d.href||d.label||'';const s=p.split('/');return s.length>1?s.slice(0,-1).join('/'):'/'}
function nodeColor(d){return fColor(getFolder(d))}
function nodeR(d){const c=edges.filter(e=>(e.source.id||e.source)===d.id||(e.target.id||e.target)===d.id).length;return Math.max(5,Math.min(25,3+c*1.2))}

// --- Left panel: color legend ---
const legend=document.getElementById('color-legend');
folders.forEach(f=>{const d=document.createElement('div');d.innerHTML=`<span class="dot" style="background:${fColor(f)}"></span><span>${f}</span>`;legend.appendChild(d)});

// --- Left panel: stats ---
const sg=document.getElementById('stat-grid');
const nFuncs=FUNCS?FUNCS.length:0;
const nLinks=edges.length;
[[nodes.length,'FILES'],[nFuncs,'FUNCTIONS'],[nLinks,'LINKS'],[0,'UNUSED']].forEach(([n,l])=>{
  const b=document.createElement('div');b.className='stat-box';b.innerHTML=`<div class="num">${n}</div><div class="lbl">${l}</div>`;sg.appendChild(b)});

// --- Left panel: file tree ---
const tree=document.getElementById('file-tree');
const treeData={};
nodes.forEach(n=>{const p=n.href||n.label||n.id;const parts=p.split('/');let cur=treeData;parts.forEach((s,i)=>{if(!cur[s])cur[s]=i===parts.length-1?null:{};if(cur[s]!==null)cur=cur[s]})});
function buildTree(obj,container){
  Object.keys(obj).sort().forEach(k=>{
    if(obj[k]===null){const s=document.createElement('div');s.style.paddingLeft='12px';s.style.fontSize='11px';s.style.cursor='pointer';s.textContent=k;
      s.addEventListener('click',()=>{const nd=nodes.find(n=>(n.href||n.label||n.id).endsWith(k));if(nd)selectNode(nd)});container.appendChild(s)}
    else{const det=document.createElement('details');const sum=document.createElement('summary');const cnt=Object.keys(obj[k]).length+(obj[k]===null?0:Object.values(obj[k]).filter(v=>v===null).length);
      sum.innerHTML=`${k} <span class="count">${cnt}</span>`;det.appendChild(sum);buildTree(obj[k],det);container.appendChild(det)}
  })}
buildTree(treeData,tree);

// --- D3 Force Graph ---
const svgEl=d3.select('#graph');const gEl=svgEl.append('g');
const W=document.getElementById('center').offsetWidth,H=document.getElementById('center').offsetHeight;

const zoom=d3.zoom().scaleExtent([.05,10]).on('zoom',e=>gEl.attr('transform',e.transform));
svgEl.call(zoom);
document.getElementById('zoom-in').onclick=()=>svgEl.transition().call(zoom.scaleBy,1.3);
document.getElementById('zoom-out').onclick=()=>svgEl.transition().call(zoom.scaleBy,.7);
document.getElementById('zoom-reset').onclick=()=>svgEl.transition().call(zoom.transform,d3.zoomIdentity);
document.getElementById('fullscreen-btn').onclick=()=>{if(!document.fullscreenElement)document.documentElement.requestFullscreen();else document.exitFullscreen()};

const sim=d3.forceSimulation(nodes)
  .force('link',d3.forceLink(edges).id(d=>d.id).distance(60))
  .force('charge',d3.forceManyBody().strength(-180))
  .force('center',d3.forceCenter(W/2,H/2))
  .force('collide',d3.forceCollide().radius(d=>nodeR(d)+4));

// Path labels for folders
const folderLabels=gEl.selectAll('.folder-label').data(folders.filter(f=>f!=='/')).join('text')
  .attr('class','node-label').style('font-size','12px').style('fill','var(--muted)').style('opacity',.4).text(d=>d);

const link=gEl.selectAll('.link').data(edges).join('line')
  .attr('class',d=>'link'+(d.style==='dashed'?' dashed':'')+(d.style==='violation'?' violation':''))
  .attr('marker-end','url(#arrow)');

const nodeG=gEl.selectAll('.node-g').data(nodes).join('g').attr('class','node-g');
const circle=nodeG.append('circle').attr('class','node-circle').attr('r',d=>nodeR(d)).attr('fill',nodeColor);
const lbl=nodeG.append('text').attr('class','node-label').attr('dx',d=>nodeR(d)+4).attr('dy',3).text(d=>{const l=d.label||d.id;return l.length>20?l.slice(0,18)+'..':l});

nodeG.call(d3.drag()
  .on('start',(e,d)=>{if(!e.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y})
  .on('drag',(e,d)=>{d.fx=e.x;d.fy=e.y})
  .on('end',(e,d)=>{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null}));

sim.on('tick',()=>{
  link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
  nodeG.attr('transform',d=>`translate(${d.x},${d.y})`);
  // position folder labels at centroid
  folderLabels.each(function(f){const ns=nodes.filter(n=>getFolder(n)===f);if(!ns.length)return;
    const cx=d3.mean(ns,n=>n.x),cy=d3.mean(ns,n=>n.y)-30;d3.select(this).attr('x',cx).attr('y',cy)});
});

// Hover: highlight neighbors
nodeG.on('mouseover',(e,d)=>{
  const nb=new Set();edges.forEach(l=>{const si=l.source.id||l.source,ti=l.target.id||l.target;if(si===d.id)nb.add(ti);if(ti===d.id)nb.add(si)});nb.add(d.id);
  nodeG.classed('faded',n=>!nb.has(n.id));link.classed('faded',l=>(l.source.id||l.source)!==d.id&&(l.target.id||l.target)!==d.id);
}).on('mouseout',()=>{nodeG.classed('faded',false);link.classed('faded',false)});

// Bottom bar
document.getElementById('bottom-bar').innerHTML=`${nodes.length} files &nbsp;&middot;&nbsp; ${edges.length} links`;

// --- Right panel: node detail ---
function selectNode(d){
  document.getElementById('no-select').style.display='none';
  document.getElementById('detail-content').style.display='block';
  document.getElementById('det-name').textContent=d.label||d.id;
  document.getElementById('det-path').textContent=d.href||d.group||'';
  // Blast radius: BFS all reachable
  const fwd={},rev={};edges.forEach(e=>{const s=e.source.id||e.source,t=e.target.id||e.target;(fwd[s]=fwd[s]||[]).push(t);(rev[t]=rev[t]||[]).push(s)});
  const visited=new Set();const q=[d.id];let depth=0;const bfsQ=[[d.id,0]];
  while(bfsQ.length){const[cur,dd]=bfsQ.shift();if(visited.has(cur))continue;visited.add(cur);depth=Math.max(depth,dd);
    (fwd[cur]||[]).concat(rev[cur]||[]).forEach(nb=>{if(!visited.has(nb))bfsQ.push([nb,dd+1])})}
  visited.delete(d.id);const pct=nodes.length>1?Math.round(visited.size/(nodes.length-1)*100):0;
  const cls=pct>60?'critical':pct>30?'high':pct>10?'medium':'low';
  document.getElementById('blast-badge').className='badge '+cls;document.getElementById('blast-badge').textContent=cls.toUpperCase();
  let bhtml=`<div style="margin:8px 0"><strong>Impact</strong> &nbsp; ${visited.size} files (${pct}%)</div>`;
  bhtml+=`<div style="color:var(--muted);font-size:11px;margin-bottom:6px">Changes propagate up to ${depth} levels deep</div>`;
  bhtml+='<div style="font-size:11px;margin-bottom:4px"><strong>Affected Files:</strong></div><ul class="affected-list">';
  [...visited].slice(0,10).forEach(nid=>{const nd=nodes.find(n=>n.id===nid);bhtml+=`<li>${nd?nd.label||nd.id:nid}</li>`});
  if(visited.size>10)bhtml+=`<li style="color:var(--muted)">+${visited.size-10} more files</li>`;
  bhtml+='</ul>';document.getElementById('blast-body').innerHTML=bhtml;
  // Connections
  const conns=edges.filter(e=>(e.source.id||e.source)===d.id||(e.target.id||e.target)===d.id);
  document.getElementById('conn-count').textContent=conns.length;
  let chtml='<div style="font-size:11px">';
  const outgoing=conns.filter(e=>(e.source.id||e.source)===d.id);
  const incoming=conns.filter(e=>(e.target.id||e.target)===d.id);
  chtml+=`<div style="margin-bottom:4px">Imports: ${outgoing.length} &nbsp; Imported by: ${incoming.length}</div>`;
  chtml+='</div>';document.getElementById('conn-body').innerHTML=chtml;
  // Functions (from overlay)
  let fhtml='';
  if(FUNCS&&FUNCS.length){const fileFuncs=FUNCS.filter(f=>d.label&&(f.file||'').includes(d.label));
    if(fileFuncs.length){document.getElementById('sect-funcs').style.display='';
      fileFuncs.slice(0,15).forEach(f=>{const cls=f.complexity>30?'critical':f.complexity>20?'high':f.complexity>10?'medium':'low';
        fhtml+=`<div class="func-row"><span class="func-name">${f.function}</span><div class="func-tags"><span>${f.complexity}</span></div></div>`});
      if(fileFuncs.length>15)fhtml+=`<div style="color:var(--muted);font-size:11px;padding:4px 0">+${fileFuncs.length-15} more</div>`}
    else{document.getElementById('sect-funcs').style.display='none'}}
  else{document.getElementById('sect-funcs').style.display='none'}
  document.getElementById('funcs-body').innerHTML=fhtml||'<span style="color:var(--muted)">No function data</span>';
  // Highlight in graph
  circle.attr('stroke',n=>n.id===d.id?'var(--accent)':'#fff').attr('stroke-width',n=>n.id===d.id?3:1.5);
}
nodeG.on('click',(e,d)=>selectNode(d));

// Search
const searchInput=document.getElementById('search');const matchEl=document.getElementById('match-count');
searchInput.addEventListener('input',()=>{const q=searchInput.value.toLowerCase();
  if(!q){nodeG.classed('faded',false);link.classed('faded',false);matchEl.textContent='';return}
  let c=0;nodeG.classed('faded',d=>{const m=(d.label||d.id).toLowerCase().includes(q);if(m)c++;return!m});
  link.classed('faded',true);matchEl.textContent=`${c} of ${nodes.length}`});
searchInput.addEventListener('keydown',e=>{if(e.key==='Escape'){searchInput.value='';searchInput.dispatchEvent(new Event('input'))}});
</script>
</body>
</html>'''


def _render_html(graph_data, mode='file', project='', overlay=None):
    """Render graph data into a self-contained dashboard HTML string.

    SEC-4: All user-derived labels are HTML-escaped before embedding.
    """
    safe_data = {
        'nodes': [],
        'edges': graph_data.get('edges', []),
        'groups': graph_data.get('groups', []),
    }
    for node in graph_data.get('nodes', []):
        safe_node = dict(node)
        raw_label = node.get('label', node.get('id', ''))
        # Strip Mermaid <br/> tags — SVG text elements don't support HTML
        raw_label = re.sub(r'<br\s*/?>', ' ', raw_label)
        safe_node['label'] = _html_mod.escape(raw_label)
        if 'href' in safe_node:
            safe_node['href'] = _html_mod.escape(safe_node['href'])
        safe_data['nodes'].append(safe_node)

    title = f'{_html_mod.escape(project)} \u2014 {mode} Graph' if project else f'{mode} Graph'

    overlay_data = overlay if overlay else []
    funcs_data = overlay_data if overlay_data and isinstance(overlay_data, list) and overlay_data and 'function' in (overlay_data[0] if overlay_data else {}) else []

    html = _DASHBOARD_TEMPLATE
    html = html.replace('{{TITLE}}', title)
    html = html.replace('/*GRAPH_JSON*/null', json.dumps(safe_data))
    html = html.replace('/*OVERLAY_JSON*/null', json.dumps(overlay_data))
    html = html.replace('/*FUNCS_JSON*/null', json.dumps(funcs_data))
    return html


# --- Overlay Support (R8) ---


def _load_overlay(overlay_path):
    """Load overlay JSON (complexity, blast_radius, or layers)."""
    try:
        data = json.loads(Path(overlay_path).read_text(encoding='utf-8'))
        return data if isinstance(data, list) else []
    except Exception:
        return []


# --- Audit Data Loader (STORY-slim-094 R2) ---


def _load_audit_data(root):
    """Load harness_audit.json if it exists. Returns dict or None."""
    audit_file = Path(root) / 'docs' / 'architecture' / 'governance' / 'harness_audit.json'
    if not audit_file.exists():
        return None
    try:
        return json.loads(audit_file.read_text(encoding='utf-8'))
    except Exception:
        return None


# --- D3 Source Loader (STORY-slim-094 R5) ---

_D3_CDN = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js'


def _get_d3_source():
    """Get D3.js source for inline embedding.

    Tries: 1) local cache 2) CDN download 3) fallback CDN script tag.
    """
    # Try local cache
    cache = Path('/tmp/pactkit_d3.min.js')
    if cache.exists() and cache.stat().st_size > 100000:
        return cache.read_text(encoding='utf-8')
    # Try download
    try:
        resp = urllib.request.urlopen(_D3_CDN, timeout=10)
        src = resp.read().decode('utf-8')
        cache.write_text(src, encoding='utf-8')
        return src
    except Exception:
        pass
    # Fallback: return empty (template will use CDN tag)
    return ''


# --- Unified HTML Renderer (STORY-slim-094 R1-R3, R5) ---


def _render_unified_html(graphs_dict, audit_data, project=''):
    """Render all graphs + audit data into a single unified HTML dashboard.

    Args:
        graphs_dict: {stem: {nodes, edges, groups}} for each .mmd file
        audit_data: dict from harness_audit.json or None
        project: project name for title
    """
    d3_src = _get_d3_source()
    use_inline_d3 = bool(d3_src)

    # Sanitize all graph data
    safe_graphs = {}
    for stem, graph in graphs_dict.items():
        safe = {
            'nodes': [],
            'edges': graph.get('edges', []),
            'groups': graph.get('groups', []),
        }
        for node in graph.get('nodes', []):
            sn = dict(node)
            raw_label = node.get('label', node.get('id', ''))
            raw_label = re.sub(r'<br\s*/?>', ' ', raw_label)
            sn['label'] = _html_mod.escape(raw_label)
            if 'href' in sn:
                sn['href'] = _html_mod.escape(sn['href'])
            safe['nodes'].append(sn)
        safe_graphs[stem] = safe

    tabs = sorted(safe_graphs.keys())
    default_tab = 'code_graph' if 'code_graph' in tabs else tabs[0] if tabs else ''

    # Detect mode per tab
    mode_map = {'class': 'class', 'call': 'call', 'module': 'module', 'workflow': 'workflow'}
    tab_modes = {}
    for t in tabs:
        tab_modes[t] = next((v for k, v in mode_map.items() if k in t.lower()), 'file')

    title = _html_mod.escape(f'{project} — Architecture Dashboard' if project else 'Architecture Dashboard')

    # Build audit panel HTML
    audit_html = _build_audit_panel_html(audit_data)
    hotspots_json = json.dumps(audit_data.get('hotspots', []) if audit_data else [])

    # Build the HTML
    d3_tag = f'<script>{d3_src}</script>' if use_inline_d3 else '<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>'

    tab_buttons = ''.join(
        f'<button class="tbtn view-tab{" active" if t == default_tab else ""}" data-tab="{_html_mod.escape(t)}">'
        f'{_html_mod.escape(t.replace("_", " ").title())}</button>'
        for t in tabs
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#0d1117;--fg:#c9d1d9;--panel:#161b22;--border:#30363d;--accent:#58a6ff;--green:#3fb950;--yellow:#d29922;--orange:#db6d28;--red:#f85149;--muted:#8b949e}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--fg);overflow:hidden;height:100vh}}
a{{color:var(--accent);text-decoration:none}}
#app{{display:grid;grid-template-columns:260px 1fr 320px;grid-template-rows:48px 1fr;height:100vh}}
#topbar{{grid-column:1/-1;display:flex;align-items:center;gap:12px;padding:0 16px;background:var(--panel);border-bottom:1px solid var(--border)}}
#topbar .logo{{font-weight:700;font-size:15px;color:var(--accent)}}
#topbar input{{padding:5px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--fg);font-size:13px;width:220px}}
#topbar .spacer{{flex:1}}
.tbtn{{padding:4px 12px;border:1px solid var(--border);border-radius:6px;background:var(--panel);color:var(--fg);cursor:pointer;font-size:12px}}
.tbtn:hover{{border-color:var(--accent)}}
.tbtn.active{{background:var(--accent);color:#fff;border-color:var(--accent)}}
#left{{background:var(--panel);border-right:1px solid var(--border);overflow-y:auto;padding:16px;font-size:13px}}
#left h3{{font-size:11px;text-transform:uppercase;color:var(--muted);margin:16px 0 8px;letter-spacing:.5px}}
#left h3:first-child{{margin-top:0}}
.score-ring{{width:120px;height:120px;margin:8px auto}}
.score-ring svg{{width:100%;height:100%}}
.layer-bar{{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:12px}}
.layer-bar .bar{{flex:1;height:8px;background:var(--border);border-radius:4px;overflow:hidden}}
.layer-bar .fill{{height:100%;border-radius:4px}}
.stat-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.stat-box{{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center}}
.stat-box .num{{font-size:22px;font-weight:700;color:var(--accent)}}
.stat-box .lbl{{font-size:10px;color:var(--muted);text-transform:uppercase}}
.hotspot-list{{font-size:12px}}.hotspot-item{{padding:6px 0;border-bottom:1px solid var(--border);cursor:pointer}}.hotspot-item:hover{{color:var(--accent)}}
.hotspot-score{{float:right;font-weight:700}}
.ai-ready{{display:inline-block;padding:2px 10px;border-radius:10px;font-weight:700;font-size:12px}}
.ai-ready.yes{{background:var(--green);color:#000}}.ai-ready.no{{background:var(--red);color:#fff}}
.no-audit{{color:var(--muted);font-size:12px;padding:12px 0}}
#center{{position:relative;overflow:hidden}}
#center svg{{width:100%;height:100%;display:block}}
.node-circle{{cursor:pointer;stroke:#fff;stroke-width:1.5}}
.node-label{{font-size:10px;fill:var(--fg);pointer-events:none}}
.link{{stroke:var(--border);stroke-width:1;fill:none;opacity:.6}}
.link.violation{{stroke:var(--red);stroke-width:2;opacity:1}}
.link.dashed{{stroke-dasharray:4 2}}
.faded{{opacity:.08!important}}
#center .view-tabs{{position:absolute;top:12px;left:50%;transform:translateX(-50%);display:flex;gap:4px;z-index:5}}
#center .bottom-bar{{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);display:flex;gap:12px;font-size:12px;color:var(--muted);background:var(--panel);padding:4px 16px;border-radius:16px;border:1px solid var(--border)}}
#right{{background:var(--panel);border-left:1px solid var(--border);overflow-y:auto;padding:16px;font-size:13px}}
#right h2{{font-size:14px;margin-bottom:4px}}
#right .filepath{{font-size:11px;color:var(--muted);margin-bottom:12px;word-break:break-all}}
.section{{margin-bottom:16px}}.section-header{{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-top:1px solid var(--border)}}
.section-header h3{{font-size:13px}}.badge{{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600}}
.badge.critical{{background:var(--red);color:#fff}}.badge.high{{background:var(--orange);color:#fff}}.badge.medium{{background:var(--yellow);color:#000}}.badge.low{{background:var(--green);color:#000}}
.section-body{{font-size:12px;color:var(--muted);padding:4px 0}}
.affected-list{{list-style:none;padding:0}}.affected-list li{{padding:2px 0}}
.no-select{{font-size:12px;color:var(--muted);padding:40px 0;text-align:center}}
</style>
</head>
<body>
<div id="app">
<div id="topbar">
  <span class="logo">PACTKIT</span>
  <input id="search" type="text" placeholder="Search files...">
  <span class="spacer"></span>
  <div class="view-tabs" style="position:static;transform:none">{tab_buttons}</div>
  <span class="spacer"></span>
  <button class="tbtn" id="zoom-reset">Reset</button>
</div>
<div id="left">
{audit_html}
</div>
<div id="center">
  <svg id="graph"><defs>
    <marker id="arrow" viewBox="0 0 10 6" refX="18" refY="3" markerWidth="6" markerHeight="5" orient="auto-start-reverse">
      <path d="M0 0L10 3L0 6Z" fill="var(--border)"/>
    </marker>
  </defs></svg>
  <div class="bottom-bar" id="bottom-bar"></div>
</div>
<div id="right">
  <div class="no-select" id="no-select">Click a node to inspect</div>
  <div id="detail-content" style="display:none">
    <h2 id="det-name"></h2>
    <div class="filepath" id="det-path"></div>
    <div class="section" id="sect-blast">
      <div class="section-header"><h3>Blast Radius</h3><span class="badge" id="blast-badge"></span></div>
      <div class="section-body" id="blast-body"></div>
    </div>
    <div class="section" id="sect-conn">
      <div class="section-header"><h3>Connections</h3><span id="conn-count" style="font-size:12px;color:var(--muted)"></span></div>
      <div class="section-body" id="conn-body"></div>
    </div>
    <div class="section" id="sect-hotspot" style="display:none">
      <div class="section-header"><h3>Hotspot Signals</h3></div>
      <div class="section-body" id="hotspot-body"></div>
    </div>
  </div>
</div>
</div>
{d3_tag}
<script>
const ALL_GRAPHS={json.dumps(safe_graphs)};
const HOTSPOTS={hotspots_json};
const TABS={json.dumps(tabs)};
let currentTab="{_html_mod.escape(default_tab)}";
let sim,nodeG,link,gEl;

function loadGraph(tab){{
  currentTab=tab;
  document.querySelectorAll('.view-tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  const data=ALL_GRAPHS[tab];
  const svgEl=d3.select('#graph');svgEl.selectAll('g').remove();
  if(!data||!data.nodes||data.nodes.length===0){{
    gEl=svgEl.append('g');
    gEl.append('text').attr('x','50%').attr('y','50%').attr('text-anchor','middle')
      .attr('fill','var(--muted)').attr('font-size','14px')
      .text('No data \\u2014 run visualize to populate this graph');
    document.getElementById('bottom-bar').innerHTML='No data';
    nodeG=null;link=null;return;
  }}
  const nodes=data.nodes,edges=data.edges;
  gEl=svgEl.append('g');
  const W=document.getElementById('center').offsetWidth,H=document.getElementById('center').offsetHeight;

  const folders=[...new Set(nodes.map(n=>{{const p=n.href||n.label||'';const s=p.split('/');return s.length>1?s.slice(0,-1).join('/'):'/'}}))]
  const fColor=d3.scaleOrdinal(d3.schemeTableau10).domain(folders);
  function getFolder(d){{const p=d.href||d.label||'';const s=p.split('/');return s.length>1?s.slice(0,-1).join('/'):'/';}}
  function nodeR(d){{const c=edges.filter(e=>(e.source.id||e.source)===d.id||(e.target.id||e.target)===d.id).length;return Math.max(5,Math.min(25,3+c*1.2));}}

  // Hotspot color overlay
  const hsMap={{}};HOTSPOTS.forEach(h=>{{hsMap[h.file]=h}});
  function nodeColor(d){{const label=d.label||d.id;const hs=Object.values(hsMap).find(h=>h.file.endsWith(label));if(hs){{const s=hs.score;return s>30?'var(--red)':s>15?'var(--orange)':s>5?'var(--yellow)':'var(--green)';}}return fColor(getFolder(d));}}

  const zoom=d3.zoom().scaleExtent([.05,10]).on('zoom',e=>gEl.attr('transform',e.transform));
  svgEl.call(zoom);
  document.getElementById('zoom-reset').onclick=()=>svgEl.transition().call(zoom.transform,d3.zoomIdentity);

  sim=d3.forceSimulation(nodes)
    .force('link',d3.forceLink(edges).id(d=>d.id).distance(60))
    .force('charge',d3.forceManyBody().strength(-180))
    .force('center',d3.forceCenter(W/2,H/2))
    .force('collide',d3.forceCollide().radius(d=>nodeR(d)+4));

  link=gEl.selectAll('.link').data(edges).join('line')
    .attr('class',d=>'link'+(d.style==='dashed'?' dashed':'')+(d.style==='violation'?' violation':''))
    .attr('marker-end','url(#arrow)');

  nodeG=gEl.selectAll('.node-g').data(nodes).join('g').attr('class','node-g');
  nodeG.append('circle').attr('class','node-circle').attr('r',d=>nodeR(d)).attr('fill',nodeColor);
  nodeG.append('text').attr('class','node-label').attr('dx',d=>nodeR(d)+4).attr('dy',3)
    .text(d=>{{const l=d.label||d.id;return l.length>20?l.slice(0,18)+'..':l}});

  nodeG.call(d3.drag()
    .on('start',(e,d)=>{{if(!e.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y}})
    .on('drag',(e,d)=>{{d.fx=e.x;d.fy=e.y}})
    .on('end',(e,d)=>{{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null}}));

  sim.on('tick',()=>{{
    link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
    nodeG.attr('transform',d=>`translate(${{d.x}},${{d.y}})`);
  }});

  nodeG.on('mouseover',(e,d)=>{{
    const nb=new Set();edges.forEach(l=>{{const si=l.source.id||l.source,ti=l.target.id||l.target;if(si===d.id)nb.add(ti);if(ti===d.id)nb.add(si)}});nb.add(d.id);
    nodeG.classed('faded',n=>!nb.has(n.id));link.classed('faded',l=>(l.source.id||l.source)!==d.id&&(l.target.id||l.target)!==d.id);
  }}).on('mouseout',()=>{{nodeG.classed('faded',false);link.classed('faded',false)}});

  nodeG.on('click',(e,d)=>selectNode(d,edges,nodes));
  document.getElementById('bottom-bar').innerHTML=`${{nodes.length}} files &middot; ${{edges.length}} links &middot; ${{tab.replace('_',' ')}}`;
}}

function selectNode(d,edges,nodes){{
  document.getElementById('no-select').style.display='none';
  document.getElementById('detail-content').style.display='block';
  document.getElementById('det-name').textContent=d.label||d.id;
  document.getElementById('det-path').textContent=d.href||d.group||'';
  const fwd={{}},rev={{}};edges.forEach(e=>{{const s=e.source.id||e.source,t=e.target.id||e.target;(fwd[s]=fwd[s]||[]).push(t);(rev[t]=rev[t]||[]).push(s)}});
  const visited=new Set(),bfsQ=[[d.id,0]];let depth=0;
  while(bfsQ.length){{const[cur,dd]=bfsQ.shift();if(visited.has(cur))continue;visited.add(cur);depth=Math.max(depth,dd);
    (fwd[cur]||[]).concat(rev[cur]||[]).forEach(nb=>{{if(!visited.has(nb))bfsQ.push([nb,dd+1])}})}}
  visited.delete(d.id);const pct=nodes.length>1?Math.round(visited.size/(nodes.length-1)*100):0;
  const cls=pct>60?'critical':pct>30?'high':pct>10?'medium':'low';
  document.getElementById('blast-badge').className='badge '+cls;document.getElementById('blast-badge').textContent=cls.toUpperCase();
  document.getElementById('blast-body').innerHTML=`<div style="margin:8px 0"><strong>Impact:</strong> ${{visited.size}} files (${{pct}}%)</div><div style="color:var(--muted);font-size:11px">Propagation depth: ${{depth}} levels</div>`;
  const conns=edges.filter(e=>(e.source.id||e.source)===d.id||(e.target.id||e.target)===d.id);
  const outgoing=conns.filter(e=>(e.source.id||e.source)===d.id);
  const incoming=conns.filter(e=>(e.target.id||e.target)===d.id);
  document.getElementById('conn-count').textContent=conns.length+' total';
  document.getElementById('conn-body').innerHTML=`Imports: ${{outgoing.length}} &nbsp; Imported by: ${{incoming.length}}`;
  // Hotspot signals
  const label=d.label||d.id;const hs=HOTSPOTS.find(h=>h.file.endsWith(label));
  const sectHs=document.getElementById('sect-hotspot');const hsBody=document.getElementById('hotspot-body');
  if(hs){{sectHs.style.display='';hsBody.innerHTML=`<div>Composite: <strong>${{hs.score}}</strong></div><div>Complexity: ${{hs.complexity_avg||'-'}}</div><div>Blast: ${{hs.blast_pct||0}}%</div><div>Fan-in: ${{hs.fan_in||0}}</div><div>Test: ${{hs.has_test?'Yes':'No'}}</div><div style="margin-top:4px;color:var(--accent)">${{hs.action||''}}</div>`}}
  else{{sectHs.style.display='none'}}
  if(nodeG)nodeG.selectAll('circle').attr('stroke',n=>n.id===d.id?'var(--accent)':'#fff').attr('stroke-width',n=>n.id===d.id?3:1.5);
}}

// Tab switching
document.querySelectorAll('.view-tab').forEach(b=>b.addEventListener('click',()=>loadGraph(b.dataset.tab)));
// Search
const searchInput=document.getElementById('search');
searchInput.addEventListener('input',()=>{{const q=searchInput.value.toLowerCase();
  if(!q){{if(nodeG){{nodeG.classed('faded',false);link.classed('faded',false)}}return}}
  if(nodeG){{nodeG.classed('faded',d=>!(d.label||d.id).toLowerCase().includes(q));link.classed('faded',true)}}
}});
// Boot
loadGraph(currentTab);
</script>
</body>
</html>'''


def _build_audit_panel_html(audit_data):
    """Build left panel HTML for audit data (R2)."""
    if not audit_data:
        return '<h3>Health</h3><div class="no-audit">Run <code>pactkit audit</code> to generate health data</div>'

    score = audit_data.get('score', 0)
    ready = audit_data.get('ready', False)
    layers = audit_data.get('layers', {})
    hotspots = audit_data.get('hotspots', [])

    # Score ring color
    if score >= 80:
        ring_color = 'var(--green)'
    elif score >= 50:
        ring_color = 'var(--yellow)'
    else:
        ring_color = 'var(--red)'

    # SVG ring
    pct = max(0, min(100, score))
    circumference = 2 * 3.14159 * 45
    dash = circumference * pct / 100
    gap = circumference - dash

    ready_cls = 'yes' if ready else 'no'
    ready_txt = 'YES' if ready else 'NO'

    html = f'''<h3>Harness Score</h3>
<div class="score-ring"><svg viewBox="0 0 120 120">
  <circle cx="60" cy="60" r="45" fill="none" stroke="var(--border)" stroke-width="8"/>
  <circle cx="60" cy="60" r="45" fill="none" stroke="{ring_color}" stroke-width="8"
    stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-linecap="round" transform="rotate(-90 60 60)"/>
  <text x="60" y="55" text-anchor="middle" fill="var(--fg)" font-size="24" font-weight="700">{score}</text>
  <text x="60" y="72" text-anchor="middle" fill="var(--muted)" font-size="10">/100</text>
</svg></div>
<div style="text-align:center;margin-bottom:12px">AI Ready: <span class="ai-ready {ready_cls}">{ready_txt}</span></div>
<h3>Layers</h3>'''

    layer_names = {
        'H1': 'Prompt', 'H2': 'Context', 'H3': 'Process',
        'H4': 'Tools', 'H5': 'Safety', 'H6': 'Observe', 'H7': 'Evolution',
    }
    for key in ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7']:
        layer = layers.get(key, {})
        level = layer.get('level', 0)
        fill_pct = level / 3 * 100
        colors = ['var(--red)', 'var(--orange)', 'var(--yellow)', 'var(--green)']
        color = colors[min(level, 3)]
        name = layer_names.get(key, key)
        html += f'<div class="layer-bar"><span style="width:24px">{key}</span><span style="width:55px;font-size:11px">{_html_mod.escape(name)}</span><div class="bar"><div class="fill" style="width:{fill_pct:.0f}%;background:{color}"></div></div><span style="font-size:11px">L{level}</span></div>\n'

    # Stats (populated by JS from graph data)
    html += '<h3>Stats</h3><div class="stat-grid" id="stat-grid"></div>'

    # Hotspots
    if hotspots:
        html += '<h3>Hotspots</h3><div class="hotspot-list">'
        for h in hotspots[:10]:
            fname = _html_mod.escape(h.get('file', '').split('/')[-1])
            sc = h.get('score', 0)
            html += f'<div class="hotspot-item">{fname}<span class="hotspot-score">{sc}</span></div>'
        html += '</div>'

    return html


# --- Entry Point (STORY-slim-094 R1/R4/R7) ---


def generate(target='.', input_file=None, output_file=None, all_mode=False, overlay_file=None):
    """Generate HTML report from .mmd file(s).

    STORY-slim-094: all_mode now generates a single unified report.html
    instead of N individual .html files.
    """
    if all_mode:
        root = Path(target).resolve()
        graphs_dir = root / 'docs' / 'architecture' / 'graphs'
        if not graphs_dir.is_dir():
            return f'No graphs directory found at {graphs_dir}'

        # HOTFIX-slim-096: Only include core PDCA graphs in --all mode.
        # Focus/reverse/workflow graphs are manual ad-hoc artifacts.
        _CORE_GRAPHS = {'code_graph', 'class_graph', 'call_graph', 'system_design'}

        # Parse core .mmd files, skip empty ones (STORY-slim-095 R3)
        graphs_dict = {}
        for mmd_file in sorted(graphs_dir.glob('*.mmd')):
            if mmd_file.stem not in _CORE_GRAPHS:
                continue
            content = mmd_file.read_text(encoding='utf-8')
            parsed = _parse_mmd(content)
            if parsed.get('nodes'):  # Skip .mmd with 0 nodes
                graphs_dict[mmd_file.stem] = parsed

        if not graphs_dict:
            return 'No .mmd files found'

        # Load audit data (auto-detect)
        audit_data = _load_audit_data(root)

        # Detect project name
        project = root.name

        # Render unified HTML
        html = _render_unified_html(graphs_dict, audit_data, project)
        dest = graphs_dir / 'report.html'
        dest.write_text(html, encoding='utf-8')
        return f'Generated: {dest}'

    if not input_file:
        return 'Error: --input or --all is required'

    # Single file mode (R4: backward compat)
    overlay = _load_overlay(overlay_file) if overlay_file else None

    mmd_path = Path(input_file).resolve()
    if not mmd_path.exists():
        return f'Error: {input_file} not found'

    html_dest = Path(output_file) if output_file else mmd_path.with_suffix('.html')
    _generate_one(mmd_path, html_dest, overlay)
    return f'Generated: {html_dest}'


def _generate_one(mmd_path, html_dest, overlay=None):
    """Generate a single HTML report from a .mmd file."""
    mmd_content = mmd_path.read_text(encoding='utf-8')
    graph = _parse_mmd(mmd_content)

    stem = mmd_path.stem.lower()
    mode_map = {'class': 'class', 'call': 'call', 'module': 'module', 'workflow': 'workflow', 'unified': 'unified'}
    mode = next((v for k, v in mode_map.items() if k in stem), 'file')

    project = ''
    try:
        for parent in mmd_path.parents:
            if parent.name not in ('graphs', 'architecture', 'docs'):
                project = parent.name
                break
    except Exception:
        pass

    html = _render_html(graph, mode=mode, project=project, overlay=overlay)
    html_dest.parent.mkdir(parents=True, exist_ok=True)
    html_dest.write_text(html, encoding='utf-8')


# --- CLI ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PactKit Report — Interactive HTML Dashboard')
    sub = parser.add_subparsers(dest='cmd', required=True)
    p_gen = sub.add_parser('generate', help='Generate HTML report from .mmd')
    p_gen.add_argument('--input', help='Input .mmd file path')
    p_gen.add_argument('--output', help='Output .html file path (default: same name as input)')
    p_gen.add_argument('--all', dest='all_mode', action='store_true', help='Convert all .mmd in docs/architecture/graphs/')
    p_gen.add_argument('--overlay', help='Overlay JSON file (complexity/blast_radius/layers)')

    a = parser.parse_args()
    if a.cmd == 'generate':
        result = generate(input_file=a.input, output_file=a.output, all_mode=a.all_mode, overlay_file=a.overlay)
        if result:
            print(result)
