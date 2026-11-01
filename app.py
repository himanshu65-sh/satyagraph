import requests
import streamlit as st
import streamlit.components.v1 as components
from core.config import Config
from core.database import LiveAuditDatabase
from core.live_retrievers import LiveEvidenceRetriever
from core.rag_store import LiveVectorRAG
from core.agent_pipeline import FactVerificationAgentPipeline
from core.media_forensics import DeepfakeForensicsEngine
from core.provenance_graph import ProvenanceGraphBuilder
from core.llm_client import MultiModalLLMClient
from ui.styles import CUSTOM_CSS, render_verdict_banner, format_report_html

st.set_page_config(
    page_title="SatyaGraph | Real-Time Civic Fact & Deepfake Auditor",
    page_icon="🛡️",
    layout="wide"
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

@st.cache_resource
def init_engines():
    db = LiveAuditDatabase()
    rag = LiveVectorRAG(db)
    pipeline = FactVerificationAgentPipeline(db, rag)
    return db, rag, pipeline

db, rag, pipeline = init_engines()

# Hero Header
st.markdown("""
<div class="main-header">
    <h2 style="margin:0; color:#f8fafc;">🛡️ SatyaGraph: Real-Time Agentic Fact-Verification & Deepfake Audit Engine</h2>
    <p style="margin:0.35rem 0 0 0; color:#cbd5e1; font-size:0.96rem;">
        Forge Buildathon &bull; Theme 1: Civic Pulse, Digital Governance & Public Information (Problem #4)
    </p>
    <div class="badge-row">
        <span class="cyber-badge">⚡ 3-Agent Autonomous RAG</span>
        <span class="cyber-badge">🔬 OpenCV Face-ROI + ELA Deepfake Lab</span>
        <span class="cyber-badge">🔁 Dual-LLM Failover (Gemini 3.5 Flash Lite + Groq Llama-3.3-70B)</span>
        <span class="cyber-badge">✅ 100% Live Registries (Zero Mock Data)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Live Telemetry, Failover Toggle & Feed Sync
with st.sidebar:
    st.subheader("⚡ Live System Telemetry")
    gemini_ok = MultiModalLLMClient._is_valid_key(Config.GEMINI_API_KEY)
    groq_ok = MultiModalLLMClient._is_valid_key(Config.GROQ_API_KEY)

    st.write(f"**Primary LLM (Gemini 3.5 Flash Lite):** {'🟢 Active' if gemini_ok else '🟡 Set in .env'}")
    st.write(f"**Failover LLM (Groq Llama-3.3-70B):** {'🟢 Standby' if groq_ok else '⚪ Add in .env'}")

    # Live Failover Simulation Toggle for Judges Demo
    force_failover = st.toggle(
        "🔁 Simulate Groq Failover Mode",
        value=False,
        help="Turn this ON during judging to demonstrate automatic failover to Groq Llama-3.3-70B without editing .env!"
    )
    Config.FORCE_GROQ_FAILOVER = force_failover
    if force_failover:
        if groq_ok:
            st.info("⚡ Failover Mode Active: Routing reasoning to **Groq Llama-3.3-70B**.")
        else:
            st.warning("⚠️ Add GROQ_API_KEY in `.env` to use Groq Failover mode.")

    st.divider()
    selected_feed_label = st.selectbox("📡 Select Live Civic Feed Stream:", list(Config.LIVE_FEEDS.keys()))
    if st.button("🔄 Pull Live Feed & Index to Vector RAG", use_container_width=True):
        with st.spinner("Connecting to live RSS endpoint & indexing into SQLite/Vector store..."):
            feed_url = Config.LIVE_FEEDS[selected_feed_label]
            live_docs = LiveEvidenceRetriever.fetch_live_rss_stream(feed_url, selected_feed_label, max_items=15)
            rag.ingest_documents(live_docs)
            st.session_state["live_feed_items"] = live_docs
            st.success(f"Ingested {len(live_docs)} live items into RAG index!")

    indexed_count = len(db.get_all_live_documents(limit=500))
    audits_count = len(db.get_recent_claim_audits(limit=500))
    media_count = len(db.get_recent_media_audits(limit=500))

    c_m1, c_m2 = st.columns(2)
    c_m1.metric("Indexed Docs", indexed_count)
    c_m2.metric("Claim Audits", audits_count)
    st.metric("Deepfake Media Audits Logged", media_count)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 1. Live Claim & Feed Verification",
    "🖼️ 2. Multimodal Deepfake & ELA Lab",
    "🕸️ 3. 3D Provenance Graph & Live DB",
    "🧠 4. Architecture & Responsible AI"
])

# --- TAB 1: LIVE CLAIM & FEED VERIFICATION ---
with tab1:
    col_feed, col_audit = st.columns([1, 1.38], gap="large")

    with col_feed:
        st.subheader("📡 Live Civic & Fact-Check Stream")
        st.caption("Click 'Audit This Live Headline' on any live item fetched in real time, or paste any viral rumor on the right.")
        if "live_feed_items" not in st.session_state:
            default_label = list(Config.LIVE_FEEDS.keys())[0]
            st.session_state["live_feed_items"] = LiveEvidenceRetriever.fetch_live_rss_stream(
                Config.LIVE_FEEDS[default_label], default_label, max_items=8
            )
            rag.ingest_documents(st.session_state["live_feed_items"])

        for idx, item in enumerate(st.session_state.get("live_feed_items", [])[:8]):
            with st.container(border=True):
                st.markdown(f"**{item['title']}**")
                st.caption(f"🕒 {item['published_at']} | 🔗 [Open Live Source]({item['url']})")
                if st.button("Audit This Live Headline ➡️", key=f"feed_btn_{idx}", use_container_width=True):
                    st.session_state["claim_input_val"] = item["title"]

    with col_audit:
        st.subheader("🤖 Multi-Agent Claim Cross-Verifier")

        # 1-Click Quick-Test Presets for Fast Live Demo
        st.caption("⚡ **Quick-Load Test Cases for Live Demo:**")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            if st.button("🎓 Fake ₹5k Scheme", use_container_width=True):
                st.session_state["claim_input_val"] = (
                    "Government of India has announced a new ₹5,000 monthly direct bank transfer "
                    "for all college students under PM Digital Yuva Scheme."
                )
        with p_col2:
            if st.button("🏦 Fake RBI Alert", use_container_width=True):
                st.session_state["claim_input_val"] = (
                    "Reserve Bank of India (RBI) has ordered all public sector banks to freeze "
                    "savings accounts that do not link PAN with Ration Card by midnight."
                )
        with p_col3:
            if st.button("🛰️ Verify ISRO / PIB", use_container_width=True):
                st.session_state["claim_input_val"] = (
                    "ISRO and Government of India have approved Chandrayaan-4 and Bharatiya "
                    "Antariksh Station missions in official cabinet decisions."
                )

        default_claim = st.session_state.get(
            "claim_input_val",
            "Government of India has announced a new ₹5,000 monthly direct bank transfer for all college students under PM Digital Yuva Scheme."
        )
        claim_query = st.text_area("Paste a viral WhatsApp forward, social post, or news claim:", value=default_claim, height=110)

        if st.button("🚀 Run Autonomous 3-Agent Audit", type="primary", use_container_width=True):
            if not claim_query.strip():
                st.warning("Please enter a claim to verify.")
            else:
                trace_box = st.expander("⚙️ Live Agent Execution & Tool Trace", expanded=True)
                trace_placeholder = trace_box.empty()
                rendered_steps = []

                def on_step(step_dict):
                    rendered_steps.append(
                        f'<div class="trace-step">[{step_dict["time"]}] <b>{step_dict["agent"]}</b> &rarr; {step_dict["action"]}: {step_dict["detail"]}</div>'
                    )
                    trace_placeholder.markdown("".join(rendered_steps), unsafe_allow_html=True)

                with st.spinner("Running Agent 1 (Planner) -> Agent 2 (Live Registry Search & Self-Correction) -> Agent 3 (Forensic Auditor)..."):
                    audit_res = pipeline.run_verification(claim_query.strip(), status_callback=on_step)
                    st.session_state["latest_audit"] = audit_res

        if "latest_audit" in st.session_state:
            res = st.session_state["latest_audit"]
            st.markdown(render_verdict_banner(res["verdict"], res["confidence"]), unsafe_allow_html=True)

            st.markdown("#### 🇬🇧 English Forensic Explanation")
            st.markdown(format_report_html(res["explanation_en"], is_hindi=False), unsafe_allow_html=True)

            st.markdown("#### 🇮🇳 क्षेत्रीय भाषा सारांश (Hindi Citizen Explainer)")
            st.markdown(format_report_html(res["explanation_hi"], is_hindi=True), unsafe_allow_html=True)

            if res.get("sub_claims"):
                st.markdown("#### 🧩 Atomic Sub-Claim Breakdown")
                for sc in res["sub_claims"]:
                    st.markdown(f"- **{sc.get('sub_claim', '')}** — `{sc.get('status', '')}`: {sc.get('reason', '')}")

            st.markdown("#### 📚 Live Cross-Referenced Evidence & Provenance Links")
            for s_idx, src in enumerate(res.get("sources", [])[:6]):
                st.markdown(
                    f'<div class="source-card">'
                    f'{s_idx+1}. <a href="{src["url"]}" target="_blank">{src["title"]}</a><br>'
                    f'<span style="color:#94a3b8; font-size:0.84rem;">'
                    f'🏛️ Registry: <b>{src["source_name"]}</b> &nbsp;|&nbsp; 🕒 {src.get("published_at", "Live")} &nbsp;|&nbsp; 🎯 Vector Relevance: <b>{src.get("relevance_score", "N/A")}</b>'
                    f'</span></div>',
                    unsafe_allow_html=True
                )

            # One-Click Bilingual WhatsApp Share Card
            with st.expander("📤 Generate Bilingual Citizen Fact-Check Share Card (WhatsApp / Telegram Ready)"):
                top_url = res["sources"][0]["url"] if res.get("sources") else "https://pib.gov.in"
                share_card_text = (
                    f"🛡️ *SATYAGRAPH CIVIC FACT-CHECK ALERT* 🛡️\n\n"
                    f"📌 *Claim:* {res['claim_text']}\n"
                    f"⚖️ *Verdict:* *{res['verdict']}* (Confidence: {res['confidence']}%)\n\n"
                    f"🇬🇧 *Summary:* {res['explanation_en']}\n\n"
                    f"🇮🇳 *हिंदी सारांश:* {res['explanation_hi']}\n\n"
                    f"🔗 *Primary Verified Registry:* {top_url}\n"
                    f"✅ *Verified via SatyaGraph Live Multi-Agent Engine*"
                )
                st.code(share_card_text, language="markdown")
                st.download_button(
                    label="📥 Download Official Fact-Check Bulletin (.txt)",
                    data=share_card_text.encode("utf-8"),
                    file_name="satyagraph_factcheck_bulletin.txt",
                    mime="text/plain",
                    use_container_width=True
                )

# --- TAB 2: MULTIMODAL DEEPFAKE & ELA FORENSICS LAB ---
with tab2:
    st.subheader("🖼️ Multimodal Synthetic Media, Face-Swap & Splice Forensics Lab")
    st.write(
        "Upload any suspicious image or paste a live image URL to execute **OpenCV Haar-Cascade Face-ROI Isolation**, "
        "**CLAHE Error Level Analysis (ELA)**, **CIE-LAB Skin-Tone Seam & 2D-FFT Checks**, and **Gemini 3.5 Flash Lite Vision Forensics**."
    )

    col_up1, col_up2 = st.columns(2)
    with col_up1:
        uploaded_file = st.file_uploader("Upload Image (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
    with col_up2:
        img_url_input = st.text_input("Or paste a direct live image URL to inspect:")

    image_bytes_to_audit = None
    image_name = "uploaded_media.jpg"

    if uploaded_file is not None:
        image_bytes_to_audit = uploaded_file.read()
        image_name = uploaded_file.name
    elif img_url_input.strip():
        try:
            r_img = requests.get(img_url_input.strip(), headers=Config.HEADERS, timeout=10)
            r_img.raise_for_status()
            image_bytes_to_audit = r_img.content
            image_name = img_url_input.strip().split("/")[-1][:40] or "remote_image.jpg"
        except Exception as e:
            st.error(f"Could not fetch image from URL: {e}")

    if image_bytes_to_audit and st.button("🔬 Run Pixel ELA, Face-ROI & Deepfake Vision Audit", type="primary", use_container_width=True):
        with st.spinner("Executing OpenCV Face-ROI seam scan, CLAHE ELA heatmap, and zoomed Vision pass..."):
            forensic_res = DeepfakeForensicsEngine.audit_image(image_bytes_to_audit, image_name, db)
            st.session_state["latest_forensic"] = forensic_res

    if "latest_forensic" in st.session_state:
        f_res = st.session_state["latest_forensic"]
        st.markdown(render_verdict_banner(f_res["verdict"], int(f_res["risk_score"])), unsafe_allow_html=True)

        img_c1, img_c2 = st.columns(2)
        with img_c1:
            st.image(f_res["original_image"], caption=f"Original Media ({f_res['metadata']['resolution']})", use_container_width=True)
        with img_c2:
            st.image(
                f_res["ela_image"],
                caption="CLAHE-Enhanced ELA Heatmap (Cyan = Detected Face Box | Magenta = Inner Face-Swap Mask Zone)",
                use_container_width=True
            )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Composite Manipulation Risk", f"{f_res['risk_score']}%")
        m2.metric("ELA / Face-Seam Anomaly", f"{f_res['ela_score']}/100")
        m3.metric("High-Freq Laplacian Var", f"{f_res['noise_variance']}")
        m4.metric("EXIF Metadata Present", "Yes" if f_res["metadata"]["exif_present"] else "Stripped / No")

        # Visual Risk Gauges
        g1, g2 = st.columns(2)
        with g1:
            st.progress(min(100, int(f_res["risk_score"])), text=f"Composite Manipulation Risk Gauge: {f_res['risk_score']}%")
        with g2:
            st.progress(min(100, int(f_res["ela_score"])), text=f"Localized ELA & Face-Seam Anomaly: {f_res['ela_score']}/100")

        st.markdown(f"**Cryptographic SHA-256 Provenance Fingerprint:** `{f_res['sha256_hash']}`")
        if f_res["metadata"]["suspicious_flags"]:
            st.warning("**Forensic Metadata & Face-ROI Flags:** " + " | ".join(f_res["metadata"]["suspicious_flags"]))

        st.markdown("#### 🤖 Multimodal Vision Forensic Report")
        st.markdown(format_report_html(f_res["vision_report"], is_hindi=False), unsafe_allow_html=True)

# --- TAB 3: PROVENANCE GRAPH & LIVE SQLITE REGISTRY ---
with tab3:
    st.subheader("🕸️ 3D Interactive Claim-to-Registry Provenance Knowledge Graph")
    if "latest_audit" in st.session_state:
        audit_data = st.session_state["latest_audit"]
        graph_html = ProvenanceGraphBuilder.build_interactive_html(audit_data)
        components.html(graph_html, height=540, scrolling=False)

        with st.expander("♿ Accessible Provenance Summary Table (Screen-Reader & Keyboard Friendly)"):
            rows = [
                {
                    "Node Type": "🛡️ Root Claim",
                    "Label / Entity": audit_data["claim_text"],
                    "Status / Registry": audit_data["verdict"],
                    "Confidence / Relevance": f"{audit_data['confidence']}%",
                    "Live URL": "N/A"
                }
            ]
            for sc in audit_data.get("sub_claims", []):
                rows.append({
                    "Node Type": "🧩 Sub-Claim",
                    "Label / Entity": sc.get("sub_claim", ""),
                    "Status / Registry": sc.get("status", ""),
                    "Confidence / Relevance": sc.get("reason", ""),
                    "Live URL": "N/A"
                })
            for src in audit_data.get("sources", [])[:6]:
                rows.append({
                    "Node Type": "🏛️ Live Registry",
                    "Label / Entity": src.get("title", ""),
                    "Status / Registry": src.get("source_name", ""),
                    "Confidence / Relevance": str(src.get("relevance_score", "N/A")),
                    "Live URL": src.get("url", "")
                })
            st.dataframe(rows, use_container_width=True)
    else:
        st.info("Run a claim audit in Tab 1 to generate its interactive 3D entity-and-provenance knowledge graph.")

    st.divider()
    st.subheader("🗄️ Live SQLite Public Accountability Registry (`satyagraph_live.db`)")
    col_db1, col_db2 = st.columns(2)
    with col_db1:
        st.markdown("##### Recent Live Claim Audits")
        recent_claims = db.get_recent_claim_audits(limit=10)
        if recent_claims:
            st.dataframe(
                [
                    {
                        "ID": r["id"],
                        "Timestamp (UTC)": r["created_at"][:19],
                        "Claim": r["claim_text"][:65],
                        "Verdict": r["verdict"],
                        "Confidence": f"{r['confidence']}%"
                    }
                    for r in recent_claims
                ],
                use_container_width=True
            )
        else:
            st.caption("No claim audits recorded yet.")

    with col_db2:
        st.markdown("##### Recent Multimodal Media Audits")
        recent_media = db.get_recent_media_audits(limit=10)
        if recent_media:
            st.dataframe(
                [
                    {
                        "ID": r["id"],
                        "Timestamp (UTC)": r["created_at"][:19],
                        "File": r["filename"],
                        "Risk Score": f"{r['ela_score']}%",
                        "Verdict": r["authenticity_verdict"]
                    }
                    for r in recent_media
                ],
                use_container_width=True
            )
        else:
            st.caption("No media audits recorded yet.")

# --- TAB 4: HOW THE AI WORKS & RESPONSIBLE AI ---
with tab4:
    st.subheader("🧠 How SatyaGraph Works (System Architecture)")
    st.markdown("""
    1. **Agent 1 — Atomic Claim Decomposer & Planner:** Parses noisy social media forwards into atomic, testable sub-claims, extracts named entities, and formulates targeted search queries.
    2. **Agent 2 — Autonomous Multi-Registry Retriever & Self-Correction Loop:** Queries live public feeds in parallel (**PIB & Google News RSS, DuckDuckGo Live Web Index, Wikipedia REST Knowledge API, and GDELT 2.0 Global Media API**). If initial evidence is sparse, Agent 2 automatically broadens its query parameters and retries.
    3. **Live Hybrid Vector RAG (`LiveVectorRAG`):** Ingests all live-fetched articles into an active SQLite table (`live_documents`) and computes **TF-IDF + Cosine Similarity** embeddings on the fly to rank the top 8 evidence passages.
    4. **Agent 3 — Forensic Fact-Auditor & Bilingual Explainer:** Cross-examines the atomic sub-claims strictly against retrieved URLs, enforces source attribution guardrails, and outputs both English and Hindi explanations.
    5. **OpenCV Face-ROI + CLAHE ELA + Vision Deepfake Forensics:** Isolates faces via Haar Cascades to compare inner-face Laplacian sharpness, CIE-LAB skin-tone boundary shifts, and 2D-FFT high-frequency energy against outer head regions, fused with **Gemini 3.5 Flash Lite Vision** on a zoomed face crop.
    6. **Dual-LLM High Availability:** Automatically fails over from **Gemini 3.5 Flash Lite** to **Groq Llama-3.3-70B** if primary APIs rate-limit during live judging.
    """)

    st.subheader("⚖️ Responsible AI, Limitations & Privacy Guardrails")
    st.markdown("""
    - **Zero Hallucinated Citations:** Agent 3 is strictly constrained to cite only URLs returned by Agent 2's live retrievers. If evidence is missing, it defaults to `UNVERIFIED / INSUFFICIENT EVIDENCE` rather than guessing.
    - **Algorithmic Humility on Deepfakes:** Heavy WhatsApp/Telegram recompression can alter pixel error levels. Therefore, SatyaGraph fuses mathematical Face-ROI metrics with neural Vision inspection and provides visual heatmaps for human-in-the-loop review.
    - **Privacy & Data Governance:** Citizen images are processed in-memory; only cryptographic SHA-256 hashes and structured audit logs are persisted in SQLite.
    """)