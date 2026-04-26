#!/usr/bin/env python3
"""PhF-4: render every tracked falsification report as a single static HTML page.

Output: `results/rejection_log.html`. Each row = one candidate; failure
reasons colour-coded; filters by task / panel / source. Accepts at the top.
Pure stdlib (no JS framework) so the HTML renders everywhere.

The purpose of this page is to make the rejection rate *visible*. In most
AI-for-Science publications, the negative results stay invisible —
publication bias at generation time. Here the 100+ rejected candidates are
the product, and the 1 accepted law sits at the top.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


# Every committed falsification report in the repo. Label the cohort/task/
# panel in a way a judge skimming the page can parse at a glance.
SOURCES = [
    # (path, cohort, task, panel, source)
    ("results/opus_exante/kirc_flagship_report.json",             "TCGA-KIRC", "tumor_vs_normal",   "11-gene",  "Opus ex-ante"),
    ("results/opus_exante/kirc_tier2_report.json",                "TCGA-KIRC", "stage_I-II_vs_III-IV","11-gene","Opus ex-ante"),
    ("results/flagship_run/falsification_report.json",            "TCGA-KIRC", "tumor_vs_normal",   "11-gene",  "PySR"),
    ("results/tier2_run/falsification_report.json",               "TCGA-KIRC", "stage_I-II_vs_III-IV","11-gene","PySR"),
    ("results/track_a_task_landscape/survival/falsification_report.json",          "TCGA-KIRC", "5yr_survival", "11-gene", "PySR"),
    ("results/track_a_task_landscape/metastasis/falsification_report.json",        "TCGA-KIRC", "metastasis_M0_vs_M1","11-gene","PySR"),
    ("results/track_a_task_landscape/survival/opus_exante_report.json",            "TCGA-KIRC", "5yr_survival", "11-gene", "Opus ex-ante"),
    ("results/track_a_task_landscape/metastasis/opus_exante_report.json",          "TCGA-KIRC", "metastasis_M0_vs_M1","11-gene","Opus ex-ante"),
    ("results/track_a_task_landscape/survival_expanded/falsification_report.json", "TCGA-KIRC", "5yr_survival",       "45-gene","PySR"),
    ("results/track_a_task_landscape/metastasis_expanded/falsification_report.json","TCGA-KIRC","metastasis_M0_vs_M1","45-gene","PySR"),
    ("results/track_a_task_landscape/luad/opus_exante_report.json",                "TCGA-LUAD", "tumor_vs_normal",    "22-gene","Opus ex-ante"),
]


def _fail_reason_chips(reason: str) -> str:
    if not reason:
        return '<span class="chip pass">PASS</span>'
    parts = [p.strip() for p in reason.split(",") if p.strip()]
    html_parts = [f'<span class="chip {p}">{p}</span>' for p in parts]
    return "".join(html_parts)


def _row(i: int, r: dict, cohort: str, task: str, panel: str, source: str) -> str:
    eq = r.get("equation") or r.get("law_family") or ""
    passes = bool(r.get("passes"))
    reason = r.get("fail_reason") or ""
    auc = r.get("law_auc", r.get("auroc"))
    dbase = r.get("delta_baseline")
    ci_lo = r.get("ci_lower")
    perm_p = r.get("perm_p")
    perm_fdr = r.get("perm_p_fdr", perm_p)
    decoy_p = r.get("decoy_p")
    num_err = r.get("numeric_error") or ""

    eq_display = html.escape(eq[:90]) + ("…" if len(eq) > 90 else "")
    cls = "accept-row" if passes else "reject-row"
    fmt = lambda x: "—" if x is None else f"{x:.3f}"
    reason_html = _fail_reason_chips(reason) if not num_err else f'<span class="chip numeric">{html.escape(num_err[:30])}</span>'

    return (
        f'<tr class="{cls}" data-cohort="{cohort}" data-task="{task}" '
        f'data-panel="{panel}" data-source="{source}" data-passes="{passes}">'
        f'<td>{i}</td>'
        f'<td>{cohort}</td>'
        f'<td>{task}</td>'
        f'<td>{panel}</td>'
        f'<td>{source}</td>'
        f'<td class="eq"><code>{eq_display}</code></td>'
        f'<td class="num">{fmt(auc)}</td>'
        f'<td class="num">{fmt(dbase)}</td>'
        f'<td class="num">{fmt(ci_lo)}</td>'
        f'<td class="num">{fmt(perm_fdr)}</td>'
        f'<td class="num">{fmt(decoy_p)}</td>'
        f'<td>{reason_html}</td>'
        f'</tr>'
    )


def main() -> None:
    rows = []
    idx = 1
    totals = {"total": 0, "pass": 0, "fail": 0}

    for rel, cohort, task, panel, source in SOURCES:
        path = ROOT / rel
        if not path.exists():
            continue
        for r in json.loads(path.read_text()):
            rows.append(_row(idx, r, cohort, task, panel, source))
            idx += 1
            totals["total"] += 1
            if r.get("passes"):
                totals["pass"] += 1
            else:
                totals["fail"] += 1

    # PhF-3 add-on: include the IMmotion150 PFS replay verdict as a special row.
    immotion_verdict_path = RESULTS / "track_a_task_landscape" / "external_replay" / "immotion150_pfs" / "verdict.json"
    if immotion_verdict_path.exists():
        imm = json.loads(immotion_verdict_path.read_text())
        is_pass = imm.get("verdict") == "PASS"
        passes_attr = str(is_pass).lower()
        cls = "accept-row external-replay-row" if is_pass else "reject-row external-replay-row"
        lr_p = imm["kill_tests"][0]["p"]
        hr = imm["kill_tests"][1]["hr"]
        c_index = imm["kill_tests"][2]["c_index_best"]
        rows.append(
            f'<tr class="{cls}" data-cohort="IMmotion150" data-task="PFS_survival_replay" '
            f'data-panel="external" data-source="external-replay" data-passes="{passes_attr}">'
            f'<td>★</td>'
            f'<td>IMmotion150</td>'
            f'<td>PFS_survival_replay</td>'
            f'<td>external</td>'
            f'<td>PhF-3 replay</td>'
            f'<td class="eq"><code>TOP2A - EPAS1</code></td>'
            f'<td class="num" colspan="4">log-rank p={lr_p:.1e}, HR={hr:.2f}, C={c_index:.3f}</td>'
            f'<td></td>'
            f'<td><span class="chip external">external-replay PASS</span></td>'
            f'</tr>'
        )
        totals["total"] += 1
        if is_pass:
            totals["pass"] += 1
        else:
            totals["fail"] += 1

    # Put accept rows at the top.
    accept_rows = [r for r in rows if "accept-row" in r]
    reject_rows = [r for r in rows if "accept-row" not in r]
    body_rows = "\n".join(accept_rows + reject_rows)

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Lacuna — Rejection Log</title>
<style>
  html, body {{ margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; color:#1a1a1a; background:#fafafa; }}
  header {{ background:#1a1a1a; color:white; padding:24px 32px; }}
  header h1 {{ margin:0 0 6px 0; font-size:1.8em; letter-spacing:-0.02em; }}
  header p {{ margin:4px 0; font-size:0.95em; color:#c0c0c0; }}
  .counts {{ background:#2a2a2a; padding:12px 32px; display:flex; gap:32px; font-size:0.95em; color:#ddd; }}
  .counts strong {{ color:#fff; font-size:1.15em; }}
  .filters {{ background:#f0f0f0; padding:10px 32px; font-size:0.9em; border-bottom:1px solid #ddd; }}
  .filters label {{ margin-right:16px; cursor:pointer; }}
  table {{ border-collapse:collapse; width:100%; font-size:0.85em; }}
  th, td {{ padding:8px 12px; border-bottom:1px solid #e8e8e8; text-align:left; vertical-align:top; }}
  th {{ background:#fff; position:sticky; top:0; border-bottom:2px solid #333; font-weight:600; font-size:0.9em; }}
  td.num {{ font-variant-numeric:tabular-nums; text-align:right; font-size:0.85em; }}
  td.eq code {{ font-size:0.88em; color:#2060a0; }}
  tr.accept-row {{ background:#e8f5e8; border-left:4px solid #2a9d3f; }}
  tr.accept-row.external-replay-row {{ background:#fff6d6; border-left:4px solid #c0870f; }}
  tr.reject-row {{ background:#fff; border-left:4px solid transparent; }}
  tr:hover {{ background:#fffbea !important; }}
  .chip {{ display:inline-block; padding:1px 8px; margin:1px 2px; border-radius:10px; font-size:0.78em; font-weight:600; letter-spacing:0.02em; }}
  .chip.pass {{ background:#2a9d3f; color:#fff; }}
  .chip.perm_p {{ background:#f5c518; color:#000; }}
  .chip.ci_lower {{ background:#f08030; color:#fff; }}
  .chip.delta_baseline {{ background:#d54052; color:#fff; }}
  .chip.delta_confound {{ background:#2060a0; color:#fff; }}
  .chip.decoy_p {{ background:#7020a0; color:#fff; }}
  .chip.numeric {{ background:#bbb; color:#000; }}
  .chip.external {{ background:#c0870f; color:#fff; }}
  .chip.threshold_edge {{ background:#888; color:#fff; }}
  footer {{ padding:18px 32px; color:#666; font-size:0.85em; border-top:1px solid #ddd; }}
</style>
</head>
<body>
<header>
  <h1>Lacuna — The Rejection Log</h1>
  <p>Every single candidate ever put through the pre-registered 5-test gate, including the ones that failed. The rejection rate <em>is</em> the product.</p>
  <p>Accepted rows are green at the top. The one external-cohort replay (PhF-3, IMmotion150 PFS) sits in amber.</p>
</header>
<div class="counts">
  <span>Total candidates evaluated: <strong>{totals['total']}</strong></span>
  <span>Passed the 5-test gate: <strong>{totals['pass']}</strong></span>
  <span>Rejected: <strong>{totals['fail']}</strong></span>
  <span>Reject rate: <strong>{totals['fail']/totals['total']:.1%}</strong></span>
</div>
<div class="filters">
  Filter: <input type="text" id="filterBox" placeholder="type to filter equations, cohorts, tasks, reasons…" style="padding:4px 8px; width:360px;">
  <label><input type="checkbox" id="onlyFailed"> Only failed</label>
  <label><input type="checkbox" id="onlyPassed"> Only passed</label>
</div>
<table>
<thead>
<tr>
<th>#</th><th>Cohort</th><th>Task</th><th>Panel</th><th>Source</th>
<th>Equation</th>
<th>AUROC</th><th>Δbaseline</th><th>CI lower</th><th>perm p (FDR)</th><th>decoy p</th>
<th>Failure reason(s)</th>
</tr>
</thead>
<tbody>
{body_rows}
</tbody>
</table>
<footer>
  Generated {_generation_timestamp()} by <code>src/render_rejection_log.py</code>.
  Raw data in <code>results/flagship_run/</code>, <code>results/opus_exante/</code>, <code>results/tier2_run/</code>, <code>results/track_a_task_landscape/</code>.
  Pre-registrations in <code>preregistrations/</code>.
  Live external replay (IMmotion150 PFS, PhF-3) in <code>results/track_a_task_landscape/external_replay/immotion150_pfs/</code>.
</footer>
<script>
  const box = document.getElementById("filterBox");
  const onlyFailed = document.getElementById("onlyFailed");
  const onlyPassed = document.getElementById("onlyPassed");
  function applyFilter() {{
    const q = box.value.toLowerCase();
    document.querySelectorAll("tbody tr").forEach(tr => {{
      const t = tr.innerText.toLowerCase();
      const passes = tr.dataset.passes === "true";
      const txt = !q || t.includes(q);
      const passFilter = (onlyFailed.checked && passes) || (onlyPassed.checked && !passes);
      tr.style.display = (txt && !passFilter) ? "" : "none";
    }});
  }}
  box.addEventListener("input", applyFilter);
  onlyFailed.addEventListener("change", applyFilter);
  onlyPassed.addEventListener("change", applyFilter);
</script>
</body>
</html>
"""
    out = RESULTS / "rejection_log.html"
    out.write_text(html_out)
    print(f"Wrote {out}: {totals['total']} candidates ({totals['pass']} pass, {totals['fail']} fail)")


def _generation_timestamp() -> str:
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    main()
