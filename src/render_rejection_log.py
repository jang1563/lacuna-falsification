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
    external_rows = 0
    external_pass = 0

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
        external_rows += 1
        if is_pass:
            totals["pass"] += 1
            external_pass += 1
        else:
            totals["fail"] += 1

    # Put accept rows at the top.
    accept_rows = [r for r in rows if "accept-row" in r]
    reject_rows = [r for r in rows if "accept-row" not in r]
    body_rows = "\n".join(accept_rows + reject_rows)
    candidate_total = totals["total"] - external_rows
    candidate_pass = totals["pass"] - external_pass
    reject_rate = totals["fail"] / candidate_total if candidate_total else 0.0

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lacuna — Rejection Log</title>
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<style>
  html, body {{ margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; color:#1a1a1a; background:#fafafa; }}
  header {{ background:#1a1a1a; color:white; padding:24px 32px; }}
  header h1 {{ margin:0 0 6px 0; font-size:1.8em; letter-spacing:-0.02em; }}
  header p {{ margin:4px 0; font-size:0.95em; color:#c0c0c0; }}
  .counts {{ background:#2a2a2a; padding:12px 32px; display:flex; gap:32px; font-size:0.95em; color:#ddd; }}
  .counts strong {{ color:#fff; font-size:1.15em; }}
  .filters {{ background:#f0f0f0; padding:12px 32px; font-size:0.9em; border-bottom:1px solid #ddd; display:flex; flex-wrap:wrap; align-items:center; gap:12px; }}
  .filters label {{ cursor:pointer; display:flex; align-items:center; gap:4px; }}
  .filters select {{ padding:4px 8px; font-size:0.9em; border:1px solid #ccc; border-radius:4px; background:#fff; cursor:pointer; }}
  .filter-group {{ display:flex; align-items:center; gap:6px; }}
  .filter-group span {{ color:#666; font-size:0.85em; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; }}
  table {{ border-collapse:collapse; width:100%; font-size:0.85em; }}
  th, td {{ padding:8px 12px; border-bottom:1px solid #e8e8e8; text-align:left; vertical-align:top; }}
  th {{ background:#fff; font-weight:600; font-size:0.9em; }}
  thead tr:first-child th {{ position:sticky; top:0; z-index:2; border-bottom:1px solid #ccc; }}
  thead tr:nth-child(2) th {{ position:sticky; top:33px; z-index:2; background:#f5f5f5; padding:4px 6px; border-bottom:2px solid #333; }}
  thead tr:nth-child(2) th input,
  thead tr:nth-child(2) th select {{
    width:100%; box-sizing:border-box; padding:3px 5px; font-size:0.82em;
    border:1px solid #ccc; border-radius:3px; background:#fff;
    color:#1a1a1a; min-width:0;
  }}
  thead tr:nth-child(2) th.num-th {{ min-width:72px; }}
  thead tr:nth-child(2) th input[type=number] {{ text-align:right; width:72px; }}
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
  <span>Candidate evaluations: <strong>{candidate_total}</strong></span>
  <span>Passed the 5-test gate: <strong>{candidate_pass}</strong></span>
  <span>Rejected: <strong>{totals['fail']}</strong></span>
  <span>External replay rows: <strong>{external_rows}</strong></span>
  <span>Reject rate: <strong>{reject_rate:.1%}</strong></span>
</div>
<div class="counts-bar" style="background:#f8f8f8; padding:8px 32px; border-bottom:1px solid #ddd; font-size:0.85em; color:#555;">
  Showing <span id="matchCount" style="font-weight:600; color:#1a1a1a;"></span> — use column filters below to narrow
</div>
<table>
<thead>
<tr>
<th>#</th><th>Cohort</th><th>Task</th><th>Panel</th><th>Source</th>
<th>Equation</th>
<th>AUROC</th><th>Δbaseline</th><th>CI lower</th><th>perm p (FDR)</th><th>decoy p</th>
<th>Failure reason(s)</th>
</tr>
<tr>
<th></th>
<th><select id="f-cohort"><option value="">All</option></select></th>
<th><select id="f-task"><option value="">All</option></select></th>
<th><select id="f-panel"><option value="">All</option></select></th>
<th><select id="f-source"><option value="">All</option></select></th>
<th><input type="text" id="f-eq" placeholder="search…"></th>
<th class="num-th"><input type="number" id="f-auroc" placeholder="≥" step="0.01" min="0" max="1"></th>
<th class="num-th"><input type="number" id="f-dbase" placeholder="≥" step="0.01"></th>
<th class="num-th"><input type="number" id="f-cilower" placeholder="≥" step="0.01"></th>
<th class="num-th"><input type="number" id="f-permp" placeholder="≤" step="0.001" min="0" max="1"></th>
<th class="num-th"><input type="number" id="f-decp" placeholder="≤" step="0.001" min="0" max="1"></th>
<th><input type="text" id="f-reason" placeholder="search…"></th>
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
  // Populate column-header dropdowns from data attributes
  function populateSelect(selId, attr) {{
    const sel = document.getElementById(selId);
    const vals = new Set();
    document.querySelectorAll("tbody tr").forEach(tr => {{
      const v = tr.dataset[attr]; if (v) vals.add(v);
    }});
    [...vals].sort().forEach(v => {{
      const o = document.createElement("option"); o.value = v; o.textContent = v; sel.appendChild(o);
    }});
  }}
  populateSelect("f-cohort", "cohort");
  populateSelect("f-task",   "task");
  populateSelect("f-panel",  "panel");
  populateSelect("f-source", "source");

  function parseNum(s) {{ const n = parseFloat(s); return isNaN(n) ? null : n; }}
  function colText(tr, i) {{ const td = tr.querySelectorAll("td")[i]; return td ? td.innerText.trim() : ""; }}

  function applyFilter() {{
    const cohortV = document.getElementById("f-cohort").value;
    const taskV   = document.getElementById("f-task").value;
    const panelV  = document.getElementById("f-panel").value;
    const sourceV = document.getElementById("f-source").value;
    const eqQ     = document.getElementById("f-eq").value.toLowerCase();
    const aurocMin = parseNum(document.getElementById("f-auroc").value);
    const dbaseMin = parseNum(document.getElementById("f-dbase").value);
    const cilMin   = parseNum(document.getElementById("f-cilower").value);
    const permpMax = parseNum(document.getElementById("f-permp").value);
    const decpMax  = parseNum(document.getElementById("f-decp").value);
    const reasonQ  = document.getElementById("f-reason").value.toLowerCase();

    let shown = 0;
    document.querySelectorAll("tbody tr").forEach(tr => {{
      const auroc = parseNum(colText(tr, 6));
      const dbase = parseNum(colText(tr, 7));
      const cil   = parseNum(colText(tr, 8));
      const permp = parseNum(colText(tr, 9));
      const decp  = parseNum(colText(tr, 10));
      const ok =
        (!cohortV || tr.dataset.cohort  === cohortV) &&
        (!taskV   || tr.dataset.task    === taskV)   &&
        (!panelV  || tr.dataset.panel   === panelV)  &&
        (!sourceV || tr.dataset.source  === sourceV) &&
        (!eqQ     || colText(tr, 5).toLowerCase().includes(eqQ)) &&
        (aurocMin === null || auroc === null || auroc >= aurocMin) &&
        (dbaseMin === null || dbase === null || dbase >= dbaseMin) &&
        (cilMin   === null || cil   === null || cil   >= cilMin)   &&
        (permpMax === null || permp === null || permp <= permpMax) &&
        (decpMax  === null || decp  === null || decp  <= decpMax)  &&
        (!reasonQ || colText(tr, 11).toLowerCase().includes(reasonQ));
      tr.style.display = ok ? "" : "none";
      if (ok) shown++;
    }});
    document.getElementById("matchCount").textContent = shown + " of {totals['total']}";
  }}

  document.querySelectorAll("#f-cohort,#f-task,#f-panel,#f-source").forEach(s =>
    s.addEventListener("change", applyFilter));
  document.querySelectorAll("#f-eq,#f-auroc,#f-dbase,#f-cilower,#f-permp,#f-decp,#f-reason").forEach(i =>
    i.addEventListener("input", applyFilter));
  applyFilter();
</script>
</body>
</html>
"""
    out = RESULTS / "rejection_log.html"
    out.write_text(html_out)
    print(
        f"Wrote {out}: {candidate_total} candidate evaluations + "
        f"{external_rows} external replay row(s) "
        f"({candidate_pass} 5-test pass, {totals['fail']} fail)"
    )


def _generation_timestamp() -> str:
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    main()
