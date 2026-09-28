"""
UDO AI Knowledge & Grounding Module
Provides catalog retrieval and context injection for Vertex AI / Gemini.
Follows GEMINI.md directives: No emojis in source code, comments, or output.
"""

import os
import json
import re
from typing import List, Dict, Any

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "udo_catalog_index.json")

class UdoCatalogKnowledge:
    def __init__(self, data_file: str = DATA_PATH):
        self.products: List[Dict[str, Any]] = []
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    self.products = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load catalog index: {e}")

    def retrieve_context(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        """
        Semantic keyword scoring against product catalog.
        Finds the most relevant products based on query tokens.
        """
        if not self.products:
            return []

        tokens = [t.lower() for t in re.findall(r"[\w\d\.\-]+", query) if len(t) > 1]
        if not tokens:
            return self.products[:top_k]

        scored_products = []
        for p in self.products:
            score = 0
            name_val = str(p.get("name") or "").lower()
            brand_val = str(p.get("brand") or "").lower()
            mat_raw = p.get("material")
            mat_val = (" ".join(mat_raw) if isinstance(mat_raw, list) else str(mat_raw or "")).lower()
            proc_raw = p.get("process")
            proc_val = (" ".join(proc_raw) if isinstance(proc_raw, list) else str(proc_raw or "")).lower()
            std_raw = p.get("standards")
            std_val = (" ".join(std_raw) if isinstance(std_raw, list) else str(std_raw or "")).lower()
            snippet_val = str(p.get("snippet") or "").lower()

            p_text = f"{name_val} {brand_val} {mat_val} {proc_val} {std_val} {snippet_val}"
            
            for token in tokens:
                if token in p_text:
                    if token in name_val:
                        score += 5
                    elif token in brand_val:
                        score += 4
                    elif token in mat_val or token in proc_val:
                        score += 3
                    else:
                        score += 1

            if score > 0:
                scored_products.append((score, p))

        scored_products.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_products[:top_k]]

    def format_context_for_prompt(self, products: List[Dict[str, Any]]) -> str:
        """
        Format retrieved products into clean prompt text for Gemini.
        """
        lines = []
        for p in products:
            std_str = ", ".join(p.get("standards", [])) if p.get("standards") else "N/A"
            lines.append(
                f"- SKU: {p.get('sku')} | Brand: {p.get('brand')} | Name: {p.get('name')} | "
                f"Process: {p.get('process')} | Material: {p.get('material')} | Standard: {std_str} | Info: {p.get('snippet')}"
            )
        return "\n".join(lines)
