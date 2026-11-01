# 🛡️ SatyaGraph: Real-Time Agentic Fact-Verification & Deepfake Audit Engine

Built for **Forge Buildathon — Theme 1: Civic Pulse, Digital Governance & Public Information (Problem #4)**.

## 🚨 Problem Statement
Viral misinformation, fabricated government scheme notifications, and AI-generated deepfakes spread across social platforms faster than manual fact-checking desks can respond. Citizens lack a unified, transparent tool to verify claims against official registries and inspect suspicious media in real time.

## 💡 Solution & USP
**SatyaGraph** is an autonomous 3-agent verification engine and multimodal media forensics lab that operates on **100% live public feeds and databases (zero static/dummy data)**:
1. **3-Agent Autonomous Verification Pipeline:** Decomposes complex viral posts into atomic sub-claims, executes live searches across **PIB/Google News RSS, Wikipedia REST API, GDELT 2.0, and DuckDuckGo**, self-corrects when queries return sparse hits, and synthesizes guardrailed verdicts in **English and Hindi**.
2. **Mathematical + Neural Deepfake Lab:** Combines pixel-level **Error Level Analysis (ELA)** heatmaps, **Laplacian noise variance**, **EXIF software signature auditing**, and **Gemini 2.5 Flash Vision** to detect both spliced manipulations and diffusion deepfakes.
3. **Interactive Provenance Knowledge Graph:** Visualizes how extracted entities map to verified registry URLs using NetworkX and PyVis.
4. **Dual-LLM High Availability:** Automatically fails over from **Gemini 2.5 Flash** to **Groq Llama-3.3-70B** and deterministic RAG if an API rate-limits during live evaluation.

## 🏗️ Architecture Diagram
```text
[Citizen / Journalist Input: Viral Claim or Suspicious Image]
       │
       ├──► [Tab 1: 3-Agent Claim Verification Pipeline]
       │       ├─► Agent 1 (Decomposer): Atomic sub-claims + Entity extraction
       │       ├─► Agent 2 (Tool Executor): Live PIB/News RSS + Wiki REST + GDELT + DDG
       │       ├─► Live Vector RAG: SQLite persistence + TF-IDF Cosine Ranking
       │       └─► Agent 3 (Fact-Auditor): Verdict + URL Attribution + Hindi/English Summary
       │
       ├──► [Tab 2: Multimodal Deepfake Forensics Lab]
       │       ├─► EXIF & AI Software Header Inspector + SHA-256 Fingerprint
       │       ├─► Mathematical Error Level Analysis (ELA) + Laplacian Variance
       │       └─► Gemini 2.5 Flash Multimodal Vision Artifact Auditor
       │
       └──► [Tab 3: Provenance Graph & Live Accountability DB]
               ├─► NetworkX + PyVis Interactive Entity-Source Graph
               └─► Active SQLite Audit Registry (satyagraph_live.db)
```

## ⚙️ Quick Setup
1. Create a virtual environment and install requirements:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add your `GEMINI_API_KEY` (and optional `GROQ_API_KEY`).
3. Run the application:
   ```bash
   streamlit run app.py
   ```
