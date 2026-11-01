import time
from core.live_retrievers import LiveEvidenceRetriever
from core.rag_store import LiveVectorRAG
from core.llm_client import MultiModalLLMClient
from core.database import LiveAuditDatabase

class FactVerificationAgentPipeline:
    """
    3-Agent Autonomous Verification Engine:
      Agent 1 (Planner & Decomposer): Splits viral input into atomic sub-claims & search queries.
      Agent 2 (Multi-Tool Retriever & Self-Corrector): Queries live PIB/News RSS, Wikipedia, GDELT, and DDG.
      Agent 3 (Forensic Fact-Auditor): Cross-examines evidence, assigns verdict, cites URLs, and creates Hindi/English summaries.
    """

    def __init__(self, db: LiveAuditDatabase, rag: LiveVectorRAG):
        self.db = db
        self.rag = rag

    def run_verification(self, claim_text: str, status_callback=None) -> dict:
        trace = []
        t0 = time.time()

        def log_step(agent_name: str, action: str, detail: str):
            elapsed = f"{time.time() - t0:.2f}s"
            entry = {"time": elapsed, "agent": agent_name, "action": action, "detail": detail}
            trace.append(entry)
            if status_callback:
                status_callback(entry)

        # --- STEP 1: AGENT 1 (CLAIM DECOMPOSER & QUERY PLANNER) ---
        log_step("Agent 1: Claim Decomposer", "Decomposing viral claim", f"Analyzing input: '{claim_text[:100]}...'")
        planner_sys = (
            "You are Agent 1 (Claim Decomposer & Query Planner). Break the user's claim into 1 to 3 verifiable "
            "atomic sub-claims, extract key named entities (people, ministries, schemes, places), and generate "
            "2 concise search queries optimized for news and official government registries. "
            "Return JSON with keys: 'sub_claims' (list of strings), 'entities' (list of strings), 'search_queries' (list of strings)."
        )
        try:
            plan_data, model_used = MultiModalLLMClient.generate_json(planner_sys, claim_text)
            sub_claims = plan_data.get("sub_claims", [claim_text])[:3]
            entities = plan_data.get("entities", [])[:6]
            queries = plan_data.get("search_queries", [claim_text])[:2]
            log_step("Agent 1: Claim Decomposer", f"Planned via {model_used}", f"Extracted {len(sub_claims)} sub-claims & {len(queries)} targeted queries: {queries}")
        except Exception as e:
            sub_claims = [claim_text]
            entities = [w for w in claim_text.split() if len(w) > 4][:5]
            queries = [claim_text, f"{claim_text} PIB fact check India"]
            log_step("Agent 1: Claim Decomposer", "Heuristic Fallback Planner", f"LLM unreachable ({e}); generated direct queries: {queries}")

        # --- STEP 2: AGENT 2 (AUTONOMOUS MULTI-REGISTRY TOOL EXECUTOR) ---
        raw_evidence = []
        for q in queries:
            log_step("Agent 2: Live Registry Retriever", "Querying Google News & PIB RSS", f"Search query: '{q}'")
            raw_evidence.extend(LiveEvidenceRetriever.search_google_news_rss_live(q, max_results=5))

            log_step("Agent 2: Live Registry Retriever", "Querying DuckDuckGo Live Web", f"Search query: '{q}'")
            raw_evidence.extend(LiveEvidenceRetriever.search_duckduckgo_live(q, max_results=4))

        primary_entity_query = " ".join(entities[:3]) if entities else claim_text[:60]
        log_step("Agent 2: Live Registry Retriever", "Querying Wikipedia & GDELT Registries", f"Entity lookup: '{primary_entity_query}'")
        raw_evidence.extend(LiveEvidenceRetriever.search_wikipedia_live(primary_entity_query, max_results=3))
        raw_evidence.extend(LiveEvidenceRetriever.search_gdelt_live(primary_entity_query, max_results=3))

        # Self-Correction Loop if initial retrieval is sparse
        if len(raw_evidence) < 3:
            broad_query = " ".join([w for w in claim_text.split() if len(w) > 3][:5])
            log_step("Agent 2: Self-Correction Loop", "Sparse evidence detected -> Broadening query", f"Retrying with broadened keywords: '{broad_query}'")
            raw_evidence.extend(LiveEvidenceRetriever.search_google_news_rss_live(broad_query, max_results=6))
            raw_evidence.extend(LiveEvidenceRetriever.search_wikipedia_live(broad_query, max_results=3))

        # Index into Live SQLite + Vector RAG & rank top matches
        self.rag.ingest_documents(raw_evidence)
        ranked_evidence = self.rag.retrieve_relevant(claim_text, candidate_docs=raw_evidence, top_k=8)
        log_step("Agent 2: Vector RAG Ranker", "Indexed & ranked live evidence", f"Retrieved {len(ranked_evidence)} high-relevance records from {len(raw_evidence)} raw hits.")

        # --- STEP 3: AGENT 3 (FORENSIC FACT-AUDITOR & GUARDRAILED SYNTHESIZER) ---
        log_step("Agent 3: Forensic Fact-Auditor", "Cross-referencing claim against live evidence", "Synthesizing verdict, confidence score, and bilingual citizen explainer.")
        evidence_context = "\n\n".join([
            f"[Source {i+1}] Title: {d['title']}\nSummary: {d['summary']}\nURL: {d['url']}\nRegistry: {d['source_name']} ({d['published_at']})"
            for i, d in enumerate(ranked_evidence)
        ])

        auditor_sys = (
            "You are Agent 3 (Forensic Fact-Auditor). Evaluate the user's claim strictly using the provided Live Evidence Records. "
            "Do not hallucinate URLs. Cite only URLs present in the evidence list. "
            "Return strictly valid JSON with these exact keys:\n"
            "- 'verdict': One of ['VERIFIED TRUE', 'FALSE / DEBUNKED', 'MISLEADING / ALTERED', 'UNVERIFIED / INSUFFICIENT EVIDENCE']\n"
            "- 'confidence': Integer from 0 to 100\n"
            "- 'explanation_en': Clear, factual 3-4 sentence explanation in English citing specific sources.\n"
            "- 'explanation_hi': Clear 2-3 sentence explanation in Hindi (Devanagari script) for citizen accessibility.\n"
            "- 'sub_claim_verdicts': List of objects [{'sub_claim': str, 'status': str, 'reason': str}]\n"
            "- 'key_entities': List of 3 to 6 key entity strings involved."
        )
        auditor_user = f"CLAIM TO AUDIT:\n{claim_text}\n\nATOMIC SUB-CLAIMS:\n{sub_claims}\n\nLIVE EVIDENCE RECORDS:\n{evidence_context}"

        try:
            audit_json, auditor_model = MultiModalLLMClient.generate_json(auditor_sys, auditor_user)
            log_step("Agent 3: Forensic Fact-Auditor", f"Audit finalized via {auditor_model}", f"Verdict: {audit_json.get('verdict')} ({audit_json.get('confidence')}% confidence)")
        except Exception as e:
            log_step("Agent 3: Forensic Fact-Auditor", "Deterministic Evidence Fallback", f"LLM API unavailable ({e}); returning ranked live evidence summary.")
            top_titles = "; ".join([d["title"] for d in ranked_evidence[:3]]) if ranked_evidence else "No matching records."
            audit_json = {
                "verdict": "UNVERIFIED / INSUFFICIENT EVIDENCE",
                "confidence": 55 if ranked_evidence else 20,
                "explanation_en": f"Live evidence retrieved {len(ranked_evidence)} matching records from public registries ({top_titles}). Configure GEMINI_API_KEY or GROQ_API_KEY in .env for full neural cross-examination.",
                "explanation_hi": "लाइव सार्वजनिक रजिस्ट्री से साक्ष्य प्राप्त किए गए हैं। विस्तृत एआई विश्लेषण के लिए अपनी एपीआई कुंजी (.env) जांचें।",
                "sub_claim_verdicts": [{"sub_claim": sc, "status": "EVIDENCE RETRIEVED", "reason": "Matched against live feeds."} for sc in sub_claims],
                "key_entities": entities
            }

        result = {
            "claim_text": claim_text,
            "verdict": audit_json.get("verdict", "UNVERIFIED / INSUFFICIENT EVIDENCE"),
            "confidence": int(audit_json.get("confidence", 50)),
            "explanation_en": audit_json.get("explanation_en", ""),
            "explanation_hi": audit_json.get("explanation_hi", ""),
            "sub_claims": audit_json.get("sub_claim_verdicts", []),
            "entities": audit_json.get("key_entities", entities),
            "sources": ranked_evidence,
            "agent_trace": trace
        }

        self.db.save_claim_audit(claim_text, result)
        return result
