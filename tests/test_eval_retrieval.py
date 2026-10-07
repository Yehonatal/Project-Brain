"""Retrieval evaluation benchmark measuring Recall@k and MRR across dual FTS5 index."""

import unittest
from pathlib import Path
from brain.config import CONFIG
from brain.db.repository import BrainRepository
from brain.indexer.scanner import IncrementalScanner

EVAL_BENCHMARK = [
    {
        "query": "Project Brain",
        "expected_substring": "Project Brain",
        "category": "intent",
    },
    {
        "query": "sqlite3",
        "expected_substring": "sqlite3",
        "category": "trigram_symbol",
    },
    {
        "query": "gemini cli",
        "expected_substring": "gemini",
        "category": "natural_language",
    },
    {
        "query": "antigravity",
        "expected_substring": "antigravity",
        "category": "domain_keyword",
    },
    {
        "query": "chmod +x",
        "expected_substring": "chmod",
        "category": "trigram_command",
    },
    {
        "query": "React Vite",
        "expected_substring": "React",
        "category": "tech_stack",
    },
    {
        "query": "MCP server",
        "expected_substring": "MCP",
        "category": "protocol",
    },
    {
        "query": "Rule Distiller",
        "expected_substring": "Rule",
        "category": "feature",
    },
]

class TestRetrievalEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = BrainRepository(CONFIG.db_path)
        scanner = IncrementalScanner(cls.repo, CONFIG)
        scanner.scan_all(force=True)

    def test_benchmark_recall_and_mrr(self):
        hits_at_1 = 0
        hits_at_3 = 0
        reciprocal_ranks = []

        print("\n=== RETRIEVAL BENCHMARK EVALUATION ===")
        for item in EVAL_BENCHMARK:
            query = item["query"]
            expected = item["expected_substring"].lower()
            results = self.repo.search_episodes(query, limit=5)

            found_rank = None
            for idx, r in enumerate(results):
                haystack = (r["title"] + " " + r["intent"] + " " + (r.get("resolution") or "") + " " + " ".join(r["commands_run"])).lower()
                if expected in haystack:
                    found_rank = idx + 1
                    break

            if found_rank == 1:
                hits_at_1 += 1
            if found_rank and found_rank <= 3:
                hits_at_3 += 1

            if found_rank:
                rr = 1.0 / found_rank
                reciprocal_ranks.append(rr)
                print(f"✓ [{item['category']}] '{query}' -> Hit at Rank {found_rank} (Score: {results[found_rank-1]['score']})")
            else:
                reciprocal_ranks.append(0.0)
                print(f"✗ [{item['category']}] '{query}' -> Miss")

        total = len(EVAL_BENCHMARK)
        recall_at_1 = hits_at_1 / total
        recall_at_3 = hits_at_3 / total
        mrr = sum(reciprocal_ranks) / total

        print(f"\n--- Benchmark Results ---")
        print(f"Recall@1: {recall_at_1 * 100:.1f}%")
        print(f"Recall@3: {recall_at_3 * 100:.1f}%")
        print(f"Mean Reciprocal Rank (MRR): {mrr:.3f}")
        print("======================================\n")

        self.assertGreaterEqual(recall_at_3, 0.70, "Recall@3 should be at least 70%")

if __name__ == "__main__":
    unittest.main()
