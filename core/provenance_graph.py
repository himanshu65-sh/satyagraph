import json
import math

class ProvenanceGraphBuilder:
    """
    Builds an accessible, interactive 3D Perspective Provenance Knowledge Graph
    with 3D Lit-Sphere shading, animated evidence particles, 3D/2D camera morphing,
    keyboard navigation, High-Contrast accessibility mode, and a live Node Inspector.
    """

    @staticmethod
    def build_interactive_html(claim_result: dict) -> str:
        verdict = str(claim_result.get("verdict", "UNVERIFIED")).upper()
        confidence = int(claim_result.get("confidence", 50))
        claim_text = str(claim_result.get("claim_text", "Unverified Claim"))

        if "TRUE" in verdict and "FALSE" not in verdict:
            claim_color = "#10b981"
            claim_glow = "rgba(16, 185, 129, 0.55)"
            verdict_badge_bg = "#064e3b"
            verdict_badge_fg = "#6ee7b7"
        elif "FALSE" in verdict or "DEBUNK" in verdict or "FAKE" in verdict:
            claim_color = "#ef4444"
            claim_glow = "rgba(239, 68, 68, 0.55)"
            verdict_badge_bg = "#7f1d1d"
            verdict_badge_fg = "#fca5a5"
        else:
            claim_color = "#f59e0b"
            claim_glow = "rgba(245, 158, 11, 0.55)"
            verdict_badge_bg = "#78350f"
            verdict_badge_fg = "#fde68a"

        nodes = []
        edges = []

        # 1. Root Claim Node at 3D Center (0, 0, 0)
        short_claim = claim_text if len(claim_text) <= 46 else claim_text[:43] + "..."
        nodes.append({
            "id": "ROOT_CLAIM",
            "group": "CLAIM",
            "icon": "🛡️",
            "type_label": "ROOT CLAIM UNDER AUDIT",
            "label": f"🛡️ {short_claim}",
            "full_title": claim_text,
            "status": f"{verdict} ({confidence}% Confidence)",
            "details": claim_result.get("explanation_en", "Audited via SatyaGraph 3-Agent Pipeline."),
            "details_hi": claim_result.get("explanation_hi", ""),
            "url": "",
            "relevance": f"{confidence}% Confidence",
            "color": claim_color,
            "glow": claim_glow,
            "radius": 28,
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        })

        # 2. Sub-Claim Nodes (Inner Upper 3D Ring)
        sub_claims = claim_result.get("sub_claims", [])[:4]
        for idx, sc in enumerate(sub_claims):
            sc_id = f"SUB_{idx}"
            sc_text = str(sc.get("sub_claim", f"Sub-claim {idx+1}"))
            sc_status = str(sc.get("status", "CHECKED")).upper()
            sc_reason = str(sc.get("reason", ""))
            sc_short = sc_text if len(sc_text) <= 30 else sc_text[:27] + "..."

            if "TRUE" in sc_status or "SUPPORTED" in sc_status:
                sc_col = "#14b8a6"
            elif "FALSE" in sc_status or "CONTRADICT" in sc_status or "REFUTED" in sc_status:
                sc_col = "#f43f5e"
            else:
                sc_col = "#eab308"

            angle = (2 * math.pi * idx) / max(1, len(sub_claims)) + 0.4
            nodes.append({
                "id": sc_id,
                "group": "SUBCLAIM",
                "icon": "🧩",
                "type_label": "ATOMIC SUB-CLAIM",
                "label": f"🧩 {sc_short}",
                "full_title": sc_text,
                "status": sc_status,
                "details": sc_reason or "Evaluated by Agent 3 against retrieved public evidence.",
                "details_hi": "",
                "url": "",
                "relevance": sc_status,
                "color": sc_col,
                "glow": "rgba(20, 184, 166, 0.4)",
                "radius": 17,
                "x": 135.0 * math.cos(angle),
                "y": -75.0 + 25.0 * math.sin(angle * 2),
                "z": 135.0 * math.sin(angle)
            })
            edges.append({
                "from": "ROOT_CLAIM",
                "to": sc_id,
                "label": "decomposed into",
                "color": "#64748b",
                "particle_color": sc_col,
                "dashed": True
            })

        # 3. Extracted Entity Nodes (Mid 3D Orbital Shell)
        entities = claim_result.get("entities", [])[:6]
        for idx, entity in enumerate(entities):
            ent_id = f"ENT_{idx}"
            ent_str = str(entity)
            angle = (2 * math.pi * idx) / max(1, len(entities))
            nodes.append({
                "id": ent_id,
                "group": "ENTITY",
                "icon": "🔷",
                "type_label": "EXTRACTED NAMED ENTITY",
                "label": f"🔷 {ent_str[:26]}",
                "full_title": ent_str,
                "status": "KEY ENTITY / SEARCH ANCHOR",
                "details": "Named entity extracted by Agent 1 to query live civic and news registries.",
                "details_hi": "",
                "url": "",
                "relevance": "Primary Search Anchor",
                "color": "#818cf8",
                "glow": "rgba(129, 140, 248, 0.45)",
                "radius": 19,
                "x": 175.0 * math.cos(angle),
                "y": 35.0 * math.sin(angle * 1.5),
                "z": 175.0 * math.sin(angle)
            })
            edges.append({
                "from": "ROOT_CLAIM",
                "to": ent_id,
                "label": "mentions entity",
                "color": "#818cf8",
                "particle_color": "#a5b4fc",
                "dashed": False
            })

        # 4. Live Evidence Registry Sources (Outer 3D Orbital Shell)
        sources = claim_result.get("sources", [])[:6]
        for idx, src in enumerate(sources):
            src_id = f"SRC_{idx}"
            src_name = str(src.get("source_name", "Live Registry"))
            src_title = str(src.get("title", "Verified Document"))
            src_summary = str(src.get("summary", "Fetched live from public endpoint."))
            src_url = str(src.get("url", "#"))
            src_pub = str(src.get("published_at", "Live"))
            src_rel = str(src.get("relevance_score", "N/A"))

            short_src = f"[{src_name[:12]}] {src_title[:22]}..."
            angle = (2 * math.pi * idx) / max(1, len(sources)) + 0.28
            z_offset = 255.0 * math.sin(angle)
            y_offset = 70.0 * ((-1) ** idx)

            nodes.append({
                "id": src_id,
                "group": "SOURCE",
                "icon": "🏛️",
                "type_label": f"LIVE REGISTRY ({src_name.upper()})",
                "label": f"🏛️ {short_src}",
                "full_title": src_title,
                "status": f"Published: {src_pub}",
                "details": src_summary[:280] + ("..." if len(src_summary) > 280 else ""),
                "details_hi": "",
                "url": src_url,
                "relevance": f"Vector Score: {src_rel}",
                "color": "#38bdf8",
                "glow": "rgba(56, 189, 248, 0.5)",
                "radius": 21,
                "x": 255.0 * math.cos(angle),
                "y": y_offset,
                "z": z_offset
            })
            edges.append({
                "from": "ROOT_CLAIM",
                "to": src_id,
                "label": "cross-referenced",
                "color": "#0284c7",
                "particle_color": "#38bdf8",
                "dashed": False
            })

            # Connect matching entities to this live source
            haystack = f"{src_title} {src_summary}".lower()
            for e_idx, entity in enumerate(entities):
                if str(entity).lower() in haystack:
                    edges.append({
                        "from": f"ENT_{e_idx}",
                        "to": src_id,
                        "label": "verified in",
                        "color": "#475569",
                        "particle_color": "#7dd3fc",
                        "dashed": False
                    })

        graph_payload = json.dumps({
            "nodes": nodes,
            "edges": edges,
            "verdict": verdict,
            "confidence": confidence
        })

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        background: radial-gradient(circle at 35% 30%, #0f172a 0%, #090d16 60%, #050811 100%);
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        overflow: hidden;
        height: 100vh;
        width: 100vw;
        display: flex;
        flex-direction: column;
        border: 1px solid #1e293b;
        border-radius: 14px;
    }}

    /* Top Accessible Control Bar (HUD) */
    .hud-topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
        padding: 9px 14px;
        background: rgba(15, 23, 42, 0.94);
        border-bottom: 1px solid rgba(56, 189, 248, 0.25);
        z-index: 10;
    }}
    .hud-title {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.88rem;
        font-weight: 700;
        color: #e2e8f0;
    }}
    .verdict-pill {{
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        background: {verdict_badge_bg};
        color: {verdict_badge_fg};
        border: 1px solid currentColor;
    }}
    .hud-controls {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
    }}
    .hud-btn {{
        background: #1e293b;
        color: #e2e8f0;
        border: 1px solid #475569;
        padding: 5px 10px;
        border-radius: 7px;
        font-size: 0.76rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;
    }}
    .hud-btn:hover, .hud-btn:focus {{
        background: #334155;
        border-color: #38bdf8;
        color: #ffffff;
        outline: 2px solid rgba(56, 189, 248, 0.4);
    }}
    .hud-btn.active {{
        background: rgba(56, 189, 248, 0.2);
        border-color: #38bdf8;
        color: #7dd3fc;
    }}

    /* Main Workspace: 3D Viewport + Accessible Inspector Sidebar */
    .workspace {{
        display: flex;
        flex: 1;
        min-height: 0;
        position: relative;
    }}
    .canvas-wrap {{
        flex: 1;
        position: relative;
        min-width: 0;
        cursor: grab;
    }}
    .canvas-wrap:active {{
        cursor: grabbing;
    }}
    canvas {{
        display: block;
        width: 100%;
        height: 100%;
    }}

    /* Floating Legend & Help Overlay */
    .legend-bar {{
        position: absolute;
        bottom: 10px;
        left: 12px;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid #334155;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 0.74rem;
        color: #cbd5e1;
        pointer-events: none;
    }}
    .legend-item {{
        display: flex;
        align-items: center;
        gap: 5px;
    }}
    .dot {{
        width: 9px;
        height: 9px;
        border-radius: 50%;
        display: inline-block;
    }}

    /* Accessible Right-Hand Node Inspector Panel */
    .inspector {{
        width: 305px;
        background: rgba(15, 23, 42, 0.96);
        border-left: 1px solid #334155;
        padding: 12px 14px;
        display: flex;
        flex-direction: column;
        gap: 9px;
        overflow-y: auto;
    }}
    .inspector-header {{
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        color: #38bdf8;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .node-type-badge {{
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.71rem;
        font-weight: 700;
        background: #1e293b;
        color: #7dd3fc;
        border: 1px solid #334155;
    }}
    .inspector-title {{
        font-size: 0.93rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.38;
        word-break: break-word;
    }}
    .inspector-meta {{
        font-size: 0.78rem;
        color: #94a3b8;
        background: #090d16;
        padding: 7px 10px;
        border-radius: 8px;
        border: 1px solid #1e293b;
        line-height: 1.45;
    }}
    .inspector-desc {{
        font-size: 0.83rem;
        color: #e2e8f0;
        line-height: 1.5;
        background: rgba(30, 41, 59, 0.55);
        padding: 8px 10px;
        border-radius: 8px;
        border-left: 3px solid #38bdf8;
    }}
    .source-link-btn {{
        display: inline-block;
        text-align: center;
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%);
        color: #ffffff !important;
        text-decoration: none;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-top: 2px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }}
    .source-link-btn:hover {{
        opacity: 0.92;
    }}
    .nav-pills {{
        margin-top: auto;
        padding-top: 8px;
        border-top: 1px solid #1e293b;
        display: flex;
        justify-content: space-between;
        gap: 6px;
    }}

    /* High-Contrast / Large Text Accessibility Mode */
    body.a11y-mode .inspector-title {{ font-size: 1.05rem; }}
    body.a11y-mode .inspector-desc {{ font-size: 0.92rem; background: #000000; border: 1px solid #ffffff; }}
    body.a11y-mode .hud-btn {{ font-size: 0.84rem; border-color: #ffffff; }}
</style>
</head>
<body>
    <!-- Top Accessible Control Bar -->
    <div class="hud-topbar" role="toolbar" aria-label="3D Knowledge Graph Controls">
        <div class="hud-title">
            <span>🌐 3D Provenance &amp; Entity Orbit</span>
            <span class="verdict-pill">{verdict} ({confidence}%)</span>
        </div>
        <div class="hud-controls">
            <button id="btnMode" class="hud-btn active" onclick="toggleDimensionMode()" title="Switch between 3D Perspective Orbit and 2D Flat Map">🌐 3D Orbit Mode</button>
            <button id="btnRotate" class="hud-btn active" onclick="toggleAutoRotate()" title="Toggle 3D Auto-Rotation">🔄 Auto-Spin: ON</button>
            <button class="hud-btn" onclick="zoomCamera(1.18)" title="Zoom In">+</button>
            <button class="hud-btn" onclick="zoomCamera(0.84)" title="Zoom Out">&minus;</button>
            <button class="hud-btn" onclick="resetCamera()" title="Reset 3D Camera">🎯 Reset</button>
            <button id="btnA11y" class="hud-btn" onclick="toggleA11y()" title="Toggle High-Contrast Large Text Mode">♿ Accessible Mode</button>
        </div>
    </div>

    <!-- Main 3D Canvas + Accessible Side Inspector -->
    <div class="workspace">
        <div class="canvas-wrap" id="canvasContainer">
            <canvas id="graphCanvas" tabindex="0" aria-label="Interactive 3D Provenance Graph. Use arrow keys or mouse drag to rotate, Tab or Next/Prev buttons to inspect nodes."></canvas>
            <div class="legend-bar">
                <span class="legend-item"><span class="dot" style="background:{claim_color};"></span> 🛡️ Root Claim</span>
                <span class="legend-item"><span class="dot" style="background:#14b8a6;"></span> 🧩 Sub-Claim</span>
                <span class="legend-item"><span class="dot" style="background:#818cf8;"></span> 🔷 Named Entity</span>
                <span class="legend-item"><span class="dot" style="background:#38bdf8;"></span> 🏛️ Live Registry</span>
                <span class="legend-item" style="color:#94a3b8;">| Drag to rotate 3D &bull; Click node to inspect</span>
            </div>
        </div>

        <aside class="inspector" aria-live="polite">
            <div class="inspector-header">
                <span>🔎 Forensic Node Inspector</span>
                <span id="nodeCounter" style="color:#94a3b8;">1 / {len(nodes)}</span>
            </div>
            <div><span class="node-type-badge" id="inspType">ROOT CLAIM</span></div>
            <div class="inspector-title" id="inspTitle"></div>
            <div class="inspector-meta" id="inspMeta"></div>
            <div class="inspector-desc" id="inspDesc"></div>
            <div class="inspector-desc" id="inspDescHi" style="display:none; border-left-color:#10b981;"></div>
            <a id="inspLink" class="source-link-btn" href="#" target="_blank" rel="noopener noreferrer" style="display:none;">🔗 Open Verified Registry Source ↗</a>

            <div class="nav-pills">
                <button class="hud-btn" style="flex:1;" onclick="stepNode(-1)">◀ Prev Node</button>
                <button class="hud-btn" style="flex:1;" onclick="stepNode(1)">Next Node ▶</button>
            </div>
        </aside>
    </div>

<script>
const DATA = {graph_payload};
const nodes = DATA.nodes;
const edges = DATA.edges;

const canvas = document.getElementById("graphCanvas");
const ctx = canvas.getContext("2d");

let width = 800, height = 500;
let rotY = 0.35;
let rotX = 0.22;
let zoom = 1.0;
let is3D = true;
let autoRotate = true;
let a11yMode = false;
let selectedIdx = 0;
let hoveredIdx = -1;

let isDragging = false;
let draggedNodeIdx = -1;
let lastMouseX = 0, lastMouseY = 0;
let tick = 0;
let currentRenderOrder = [];

// Save 2D target positions for smooth 2D/3D transition
nodes.forEach((n, i) => {{
    n.x3d = n.x;
    n.y3d = n.y;
    n.z3d = n.z;
    if (n.group === "CLAIM") {{
        n.x2d = 0; n.y2d = 0;
    }} else if (n.group === "SUBCLAIM") {{
        n.x2d = -185; n.y2d = (i - 2.0) * 75;
    }} else if (n.group === "ENTITY") {{
        n.x2d = 0; n.y2d = ((i % 6) - 2.5) * 72;
    }} else {{
        n.x2d = 200; n.y2d = ((i % 6) - 2.5) * 72;
    }}
}});

function resizeCanvas() {{
    const rect = canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    width = rect.width;
    height = rect.height;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}}
window.addEventListener("resize", resizeCanvas);
resizeCanvas();

function selectNode(idx) {{
    if (idx < 0) idx = nodes.length - 1;
    if (idx >= nodes.length) idx = 0;
    selectedIdx = idx;
    const n = nodes[selectedIdx];
    document.getElementById("nodeCounter").textContent = (selectedIdx + 1) + " / " + nodes.length;
    document.getElementById("inspType").textContent = n.icon + " " + n.type_label;
    document.getElementById("inspTitle").textContent = n.full_title;
    document.getElementById("inspMeta").innerHTML = "<b>Status:</b> " + n.status + "<br><b>Role / Metric:</b> " + n.relevance;
    document.getElementById("inspDesc").textContent = n.details;

    const hiBox = document.getElementById("inspDescHi");
    if (n.details_hi) {{
        hiBox.style.display = "block";
        hiBox.textContent = "🇮🇳 " + n.details_hi;
    }} else {{
        hiBox.style.display = "none";
    }}

    const linkBtn = document.getElementById("inspLink");
    if (n.url && n.url.startsWith("http")) {{
        linkBtn.style.display = "inline-block";
        linkBtn.href = n.url;
    }} else {{
        linkBtn.style.display = "none";
    }}
}}

function stepNode(delta) {{
    selectNode(selectedIdx + delta);
}}

function toggleDimensionMode() {{
    is3D = !is3D;
    const btn = document.getElementById("btnMode");
    btn.textContent = is3D ? "🌐 3D Orbit Mode" : "🗺️ 2D Flat Map";
    btn.classList.toggle("active", is3D);
}}

function toggleAutoRotate() {{
    autoRotate = !autoRotate;
    const btn = document.getElementById("btnRotate");
    btn.textContent = autoRotate ? "🔄 Auto-Spin: ON" : "⏸️ Auto-Spin: OFF";
    btn.classList.toggle("active", autoRotate);
}}

function toggleA11y() {{
    a11yMode = !a11yMode;
    document.body.classList.toggle("a11y-mode", a11yMode);
    const btn = document.getElementById("btnA11y");
    btn.classList.toggle("active", a11yMode);
    if (a11yMode) autoRotate = false;
    document.getElementById("btnRotate").textContent = autoRotate ? "🔄 Auto-Spin: ON" : "⏸️ Auto-Spin: OFF";
    document.getElementById("btnRotate").classList.toggle("active", autoRotate);
}}

function zoomCamera(factor) {{
    zoom = Math.max(0.55, Math.min(2.2, zoom * factor));
}}

function resetCamera() {{
    rotY = 0.35;
    rotX = 0.22;
    zoom = 1.0;
}}

function project3D(x, y, z) {{
    const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
    const cosX = Math.cos(rotX), sinX = Math.sin(rotX);

    const x1 = x * cosY - z * sinY;
    const z1 = z * cosY + x * sinY;
    const y2 = y * cosX - z1 * sinX;
    const z2 = z1 * cosX + y * sinX;

    const fov = 560;
    const scale = (fov / Math.max(120, fov + z2)) * zoom;
    return {{
        sx: width / 2 + x1 * scale,
        sy: height / 2 + y2 * scale,
        scale: scale,
        depth: z2
    }};
}}

function draw3DOrbitalRings() {{
    if (!is3D) return;
    const radii = [145, 250];
    radii.forEach((r, idx) => {{
        ctx.beginPath();
        const steps = 64;
        for (let i = 0; i <= steps; i++) {{
            const a = (i / steps) * Math.PI * 2;
            const px = r * Math.cos(a);
            const pz = r * Math.sin(a);
            const py = idx === 0 ? -20 : 25;
            const p = project3D(px, py, pz);
            if (i === 0) ctx.moveTo(p.sx, p.sy);
            else ctx.lineTo(p.sx, p.sy);
        }}
        ctx.strokeStyle = idx === 0 ? "rgba(129, 140, 248, 0.14)" : "rgba(56, 189, 248, 0.14)";
        ctx.lineWidth = 1.2;
        ctx.stroke();
    }});
}}

function shadeColor(hex, percent) {{
    let num = parseInt(hex.replace("#", ""), 16),
        amt = Math.round(2.55 * percent),
        R = (num >> 16) + amt,
        G = (num >> 8 & 0x00FF) + amt,
        B = (num & 0x0000FF) + amt;
    return "#" + (
        0x1000000 +
        (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
        (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
        (B < 255 ? (B < 1 ? 0 : B) : 255)
    ).toString(16).slice(1);
}}

function render() {{
    tick += 0.014;
    if (autoRotate && is3D && !isDragging) {{
        rotY += 0.0045;
    }}

    ctx.clearRect(0, 0, width, height);
    draw3DOrbitalRings();

    // Compute projected coordinates for all nodes
    const projected = nodes.map((n, idx) => {{
        if (is3D) {{
            n.x += (n.x3d - n.x) * 0.12;
            n.y += (n.y3d - n.y) * 0.12;
            n.z += (n.z3d - n.z) * 0.12;
            return {{ ...project3D(n.x, n.y, n.z), idx }};
        }} else {{
            n.x += (n.x2d - n.x) * 0.15;
            n.y += (n.y2d - n.y) * 0.15;
            n.z += (0 - n.z) * 0.15;
            return {{
                sx: width / 2 + n.x * zoom,
                sy: height / 2 + n.y * zoom,
                scale: zoom,
                depth: 0,
                idx
            }};
        }}
    }});

    const selId = nodes[selectedIdx].id;

    // Draw Edges + Animated 3D Data Particles
    edges.forEach((e, eIdx) => {{
        const fromIdx = nodes.findIndex(n => n.id === e.from);
        const toIdx = nodes.findIndex(n => n.id === e.to);
        if (fromIdx < 0 || toIdx < 0) return;

        const p1 = projected[fromIdx];
        const p2 = projected[toIdx];
        const isHighlighted = (e.from === selId || e.to === selId);

        ctx.save();
        ctx.beginPath();
        if (e.dashed) ctx.setLineDash([5, 5]);
        ctx.moveTo(p1.sx, p1.sy);
        ctx.lineTo(p2.sx, p2.sy);
        ctx.strokeStyle = isHighlighted ? "#38bdf8" : "rgba(100, 116, 139, 0.38)";
        ctx.lineWidth = isHighlighted ? 2.4 : 1.3;
        ctx.stroke();
        ctx.restore();

        // Directional flowing photon particle along the edge
        if (!a11yMode) {{
            const t = ((tick * 0.75 + eIdx * 0.19) % 1);
            const px = p1.sx + (p2.sx - p1.sx) * t;
            const py = p1.sy + (p2.sy - p1.sy) * t;
            ctx.beginPath();
            ctx.arc(px, py, isHighlighted ? 3.4 : 2.2, 0, Math.PI * 2);
            ctx.fillStyle = isHighlighted ? "#7dd3fc" : e.particle_color;
            ctx.fill();
        }}
    }});

    // Sort nodes back-to-front by 3D depth (Painter's Algorithm)
    const sorted = [...projected].sort((a, b) => b.depth - a.depth);
    currentRenderOrder = sorted.map(s => s.idx).reverse();

    sorted.forEach(p => {{
        const n = nodes[p.idx];
        const isSelected = (p.idx === selectedIdx);
        const isHovered = (p.idx === hoveredIdx);
        const r = Math.max(10, n.radius * p.scale * (isSelected ? 1.18 : 1.0));

        // 1. Outer 3D Glow Halo
        ctx.save();
        if (isSelected || isHovered || n.group === "CLAIM") {{
            const halo = ctx.createRadialGradient(p.sx, p.sy, r * 0.4, p.sx, p.sy, r * 2.3);
            halo.addColorStop(0, n.glow);
            halo.addColorStop(1, "rgba(0,0,0,0)");
            ctx.fillStyle = halo;
            ctx.beginPath();
            ctx.arc(p.sx, p.sy, r * 2.3, 0, Math.PI * 2);
            ctx.fill();
        }}

        // 2. 3D Lit Sphere with Specular Highlight
        const grad = ctx.createRadialGradient(
            p.sx - r * 0.35,
            p.sy - r * 0.35,
            r * 0.1,
            p.sx,
            p.sy,
            r
        );
        grad.addColorStop(0, "#ffffff");
        grad.addColorStop(0.22, shadeColor(n.color, 25));
        grad.addColorStop(0.72, n.color);
        grad.addColorStop(1, shadeColor(n.color, -42));

        ctx.beginPath();
        ctx.arc(p.sx, p.sy, r, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();

        // Selection ring
        if (isSelected) {{
            ctx.lineWidth = 2.8;
            ctx.strokeStyle = "#ffffff";
            ctx.stroke();
        }}
        ctx.restore();

        // 3. Crisp Accessible Pill Label Below Sphere
        const fontSize = Math.max(10, Math.round((a11yMode ? 13.5 : 11.5) * Math.pow(p.scale, 0.35)));
        ctx.font = `600 ${{fontSize}}px -apple-system, BlinkMacSystemFont, sans-serif`;
        const textWidth = ctx.measureText(n.label).width;
        const padX = 8, padY = 4;
        const boxW = textWidth + padX * 2;
        const boxH = fontSize + padY * 2;
        const boxX = p.sx - boxW / 2;
        const boxY = p.sy + r + 6;

        ctx.fillStyle = isSelected ? "rgba(2, 132, 199, 0.95)" : "rgba(15, 23, 42, 0.88)";
        ctx.strokeStyle = isSelected ? "#ffffff" : "rgba(148, 163, 184, 0.35)";
        ctx.lineWidth = isSelected ? 1.8 : 1;
        ctx.beginPath();
        ctx.roundRect(boxX, boxY, boxW, boxH, 6);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = "#f8fafc";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(n.label, p.sx, boxY + boxH / 2);

        n._screenX = p.sx;
        n._screenY = p.sy;
        n._screenR = r + 10;
    }});

    requestAnimationFrame(render);
}}

// Check front-most 3D spheres first when clicking
function findNodeAt(mx, my) {{
    const order = currentRenderOrder.length ? currentRenderOrder : nodes.map((_, i) => i);
    for (let k = 0; k < order.length; k++) {{
        const i = order[k];
        const n = nodes[i];
        const dx = mx - (n._screenX || 0);
        const dy = my - (n._screenY || 0);
        if (Math.hypot(dx, dy) <= (n._screenR || 22)) return i;
    }}
    return -1;
}}

canvas.addEventListener("mousedown", e => {{
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const hit = findNodeAt(mx, my);
    isDragging = true;
    lastMouseX = mx;
    lastMouseY = my;
    if (hit >= 0) {{
        draggedNodeIdx = hit;
        selectNode(hit);
    }} else {{
        draggedNodeIdx = -1;
    }}
}});

window.addEventListener("mousemove", e => {{
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (!isDragging) {{
        hoveredIdx = findNodeAt(mx, my);
        canvas.style.cursor = hoveredIdx >= 0 ? "pointer" : "grab";
        return;
    }}

    const dx = mx - lastMouseX;
    const dy = my - lastMouseY;
    lastMouseX = mx;
    lastMouseY = my;

    if (draggedNodeIdx >= 0 && !is3D) {{
        nodes[draggedNodeIdx].x2d += dx / zoom;
        nodes[draggedNodeIdx].y2d += dy / zoom;
    }} else {{
        rotY += dx * 0.007;
        rotX = Math.max(-1.1, Math.min(1.1, rotX + dy * 0.007));
    }}
}});

window.addEventListener("mouseup", () => {{
    isDragging = false;
    draggedNodeIdx = -1;
}});

canvas.addEventListener("wheel", e => {{
    e.preventDefault();
    zoomCamera(e.deltaY < 0 ? 1.08 : 0.92);
}}, {{ passive: false }});

// Keyboard Accessibility (Arrow keys rotate, Brackets/Enter cycle nodes)
canvas.addEventListener("keydown", e => {{
    if (e.key === "ArrowLeft") rotY -= 0.08;
    else if (e.key === "ArrowRight") rotY += 0.08;
    else if (e.key === "ArrowUp") rotX = Math.max(-1.1, rotX - 0.08);
    else if (e.key === "ArrowDown") rotX = Math.min(1.1, rotX + 0.08);
    else if (e.key === "]" || e.key === "Enter") stepNode(1);
    else if (e.key === "[") stepNode(-1);
}});

selectNode(0);
requestAnimationFrame(render);
</script>
</body>
</html>"""