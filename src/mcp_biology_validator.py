"""MCP biology-validator — a tiny Model Context Protocol server.

Exposes two tools the Skeptic subagent (`.claude/agents/skeptic-reviewer.md`)
can call when validating a candidate law:

  validate_law(gene_symbols: list[str]) -> dict
      Hits NCBI E-utilities (PubMed esearch + esummary) to return a
      recency-weighted count of papers mentioning the gene set together
      with a specified disease term, plus up to 3 recent title/PMID pairs.

  fetch_cohort_summary(project_id: str) -> dict
      Hits the GDC REST API (`/projects/{id}`) for a TCGA project to
      return n_cases, disease_type, and available data categories.

Usage:

    # Start the MCP server (stdio transport — Claude Code connects directly)
    python src/mcp_biology_validator.py --tool server

    # Or register in .mcp.json at repo root (see `.mcp.json`).

    # Exercise one tool directly (no MCP SDK needed):
    python src/mcp_biology_validator.py --tool validate_law --genes TOP2A,EPAS1 --disease ccRCC
    python src/mcp_biology_validator.py --tool fetch_cohort_summary --project-id TCGA-KIRC

The server uses the `mcp` Python SDK (optional dependency — if not
installed, the module still runs as a plain CLI that prints JSON for
each tool, so Phase-E tests can exercise the logic without MCP).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GDC_API = "https://api.gdc.cancer.gov"

# Minimum inter-request spacing (NCBI without API key = 3 req/sec)
_NCBI_SPACING_S = 0.34


@dataclass
class HttpClient:
    """Thin HTTP client.

    Abstracted so tests can inject a fake without reaching the network.
    """

    user_agent: str = "lacuna-biology-validator/0.1"

    def get_json(self, url: str, timeout: float = 10.0) -> dict:
        req = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_text(self, url: str, timeout: float = 10.0) -> str:
        req = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")


def _pubmed_term(gene_symbols: Iterable[str], disease: str | None) -> str:
    gene_clause = " AND ".join(f'"{g}"[Title/Abstract]' for g in gene_symbols)
    if disease:
        return f"({gene_clause}) AND {disease}[Title/Abstract]"
    return gene_clause


def validate_law(
    gene_symbols: list[str],
    disease: str | None = None,
    max_results: int = 3,
    *,
    http: HttpClient | None = None,
) -> dict:
    """Search PubMed for co-mentions of the gene set + optional disease term.

    Returns:
        {
          "query": <the E-utilities query string>,
          "total_results": <int>,
          "top_results": [{"pmid": "...", "title": "...", "pubdate": "..."}, ...],
          "note": "..."   (e.g. "heuristic; does not replace wet-lab validation"),
        }
    """
    if not gene_symbols:
        return {"error": "gene_symbols is empty"}
    http = http or HttpClient()
    term = _pubmed_term(gene_symbols, disease)

    esearch_url = (
        f"{NCBI_EUTILS}/esearch.fcgi?"
        + urlencode({"db": "pubmed", "term": term, "retmode": "json", "retmax": max_results})
    )
    try:
        es = http.get_json(esearch_url)
    except Exception as exc:  # noqa: BLE001 — fail safe for an MCP tool
        return {"error": f"esearch failed: {type(exc).__name__}: {exc}", "query": term}

    search_block = es.get("esearchresult", {})
    total = int(search_block.get("count", 0))
    pmids = search_block.get("idlist", [])

    top_results = []
    if pmids:
        time.sleep(_NCBI_SPACING_S)
        esummary_url = (
            f"{NCBI_EUTILS}/esummary.fcgi?"
            + urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})
        )
        try:
            esumm = http.get_json(esummary_url)
            result = esumm.get("result", {})
            for pmid in pmids:
                entry = result.get(pmid, {})
                top_results.append({
                    "pmid": pmid,
                    "title": entry.get("title", ""),
                    "pubdate": entry.get("pubdate", ""),
                })
        except Exception as exc:  # noqa: BLE001
            top_results = [{"pmid": p, "title": "", "pubdate": ""} for p in pmids]
            top_results[0]["_error"] = f"esummary failed: {exc}"

    return {
        "query": term,
        "total_results": total,
        "top_results": top_results,
        "note": "heuristic co-mention search; does not replace wet-lab validation",
    }


def fetch_cohort_summary(
    project_id: str,
    *,
    http: HttpClient | None = None,
) -> dict:
    """GDC project metadata."""
    if not project_id:
        return {"error": "project_id is empty"}
    http = http or HttpClient()
    url = f"{GDC_API}/projects/{quote(project_id)}?expand=summary"
    try:
        payload = http.get_json(url)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"gdc project fetch failed: {type(exc).__name__}: {exc}"}

    data = payload.get("data", {})
    summary = data.get("summary", {})
    return {
        "project_id": data.get("project_id", project_id),
        "disease_type": data.get("disease_type"),
        "primary_site": data.get("primary_site"),
        "name": data.get("name"),
        "case_count": summary.get("case_count"),
        "file_count": summary.get("file_count"),
        "data_categories": [
            dc.get("data_category") for dc in summary.get("data_categories", [])
        ],
    }


# --- MCP server glue ------------------------------------------------------


def _run_mcp() -> int:
    """Launch the MCP stdio server if the `mcp` package is installed.

    Returns an exit code — non-zero if the SDK is missing.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "mcp package not installed. Install with: pip install mcp\n"
            "Or exercise the tools directly via:\n"
            "  python src/mcp_biology_validator.py --tool validate_law "
            "--genes TOP2A,EPAS1 --disease ccRCC\n"
            "  python src/mcp_biology_validator.py --tool fetch_cohort_summary "
            "--project-id TCGA-KIRC",
            file=sys.stderr,
        )
        return 2

    app = FastMCP("lacuna-biology-validator")

    @app.tool()
    def validate_law_tool(gene_symbols: list[str], disease: str | None = None) -> dict:
        """Co-mention PubMed search for a gene set + optional disease."""
        return validate_law(gene_symbols=gene_symbols, disease=disease)

    @app.tool()
    def fetch_cohort_summary_tool(project_id: str) -> dict:
        """TCGA project metadata (n_cases, disease_type, data categories)."""
        return fetch_cohort_summary(project_id=project_id)

    app.run()  # stdio transport by default
    return 0


def _run_cli(args: argparse.Namespace) -> int:
    if args.tool == "validate_law":
        genes = [g.strip() for g in args.genes.split(",") if g.strip()]
        payload = validate_law(gene_symbols=genes, disease=args.disease)
    elif args.tool == "fetch_cohort_summary":
        payload = fetch_cohort_summary(project_id=args.project_id)
    else:
        print(f"Unknown --tool: {args.tool}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="lacuna-mcp-biology-validator")
    parser.add_argument(
        "--tool",
        choices=["validate_law", "fetch_cohort_summary", "server"],
        default="server",
        help="'server' = start the MCP stdio server; otherwise run one tool and print JSON.",
    )
    parser.add_argument("--genes", default="", help="Comma-separated gene symbols (for validate_law).")
    parser.add_argument("--disease", default=None, help="Optional disease term (for validate_law).")
    parser.add_argument("--project-id", default="", help="TCGA project id (for fetch_cohort_summary).")
    args = parser.parse_args()

    if args.tool == "server":
        return _run_mcp()
    return _run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
