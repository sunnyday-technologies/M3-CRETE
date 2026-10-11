# AI-Assisted BOM Purchasing Guide

## How It Works

1. **Configure your build** in the [BOM Viewer](https://bom.m3-crete.com/bom/):
   - Select your **model variant** (M3 / M3-2 / M3-4)
   - Check **I have this** on parts you already own (they'll be excluded)
   - Toggle **Buy / Print / CNC** on each fabricated part
   - Click a **supplier card** to mark it as preferred (click again to deselect)

2. **Export JSON** — your selections are embedded in the export

3. **Paste into your AI assistant** with the prompt below

---

## Prompt Template

Copy this prompt, fill in your zip code and strategy, attach the exported JSON.

```
I have a BOM (Bill of Materials) JSON export for the M3-CRETE open-source
concrete 3D printer motion system. My selections are already embedded in
the export — build method (buy/print/cnc) and preferred suppliers are
marked per part.

PURCHASE STRATEGY (pick one):
→ LOWEST QUOTED COST — Cheapest total from current quotes. Use bulk
  pricing, suggest substitutes where substitute_ok is true, consolidate by
  supplier for shipping.
→ SHORTEST VERIFIED LEAD TIME — Prioritize Amazon Prime and fast US
  shippers. Minimize number of suppliers. Target: everything within 1 week.
→ BALANCED REVIEW — Balance cost and lead time. US-stocked suppliers,
  1-2 week delivery target, reasonable prices. State the weighting you used.
→ HIGHEST DOCUMENTED SPECIFICATION FIT — Prefer suppliers that publish
  datasheets and exact MPNs (e.g. McMaster-Carr, Gates, igus). Exact MPN
  matches.

MY DETAILS:
- Zip code: [YOUR ZIP CODE]
- Purchase strategy: [LOWEST QUOTED COST / SHORTEST VERIFIED LEAD TIME /
  BALANCED REVIEW / HIGHEST DOCUMENTED SPECIFICATION FIT]

RULES:
1. Skip parts where "exclude_from_kit" is true OR "user_excluded" is true.
   These are either outside project scope or parts the user already owns.
2. If "user_build_method" is set on a part, use that (buy/print/cnc).
   If not set, use the default "mfg_type".
3. If "user_preferred_supplier" or "is_preferred" is set, use that
   supplier. Otherwise pick the best match for the purchase strategy.
4. If "substitute_ok" is false, match the EXACT MPN — no substitutions.
5. Use MPN and SKU fields for exact product matching where available.
6. Consolidate orders by supplier. Note free shipping thresholds.

OUTPUT:
- Table grouped by supplier: part, qty, unit price, line total, lead time,
  lead time source, URL
- Lead time is what the supplier page states for that listing: in stock /
  ships in X days, a backorder date, or a stated lead time. Lead time source
  names where it came from: supplier page stock status, stated lead time, or
  backorder notice. If the page does not state it, write "not stated" for the
  lead time and "—" for the source. Never estimate, infer, or guess a lead time.
- Supplier subtotal + estimated shipping per supplier
- Grand total: parts + shipping + estimated tax
- Under the totals: "Longest lead: <part>, <lead time>". This is the
  critical-path part for the build. Compare stated lead times only, using the
  upper end of any range. If any lines are "not stated", add a line
  "Lead time not stated: <N> lines". If none are stated, write
  "Longest lead: not stated".
- Flag any line whose stated lead time exceeds the selected strategy's
  delivery window: 1 week for SHORTEST VERIFIED LEAD TIME, 2 weeks (the top
  of 1-2 weeks) for BALANCED REVIEW. LOWEST QUOTED COST and HIGHEST
  DOCUMENTED SPECIFICATION FIT have no window.
  For each flagged line where substitute_ok is true, suggest a substitute
  with its own stated lead time and source. Where substitute_ok is false,
  say so and keep the exact MPN.
- Flag any out-of-stock, discontinued, or significantly changed prices
```

---

## Strategy Guide

| Strategy | Best For | Trade-off |
|----------|----------|-----------|
| **Lowest quoted cost** | Comparing currently available quotes | May increase lead time, supplier count, duties, returns, and quality-verification burden |
| **Shortest verified lead time** | Schedule-sensitive research procurement | Requires live inventory and delivery confirmation; quoted speed is not guaranteed |
| **Balanced review** | Comparing cost, evidence, support, and lead time | Buyer must define and document the weighting |
| **Highest documented specification fit** | Evidence-focused component selection | Higher price does not establish quality, life, compatibility, or project suitability |

### Cost boundary

No verified all-in cost range is provided. Re-price the current BOM for the exact model, location, fabrication plan, and supplier set. Include shipping, tax, duties, returns, spares, tools, fabrication, engineering, professional electrical/control work, guarding, facility work, commissioning, material-delivery equipment, testing, maintenance, and exclusions. Any generated total is a dated planning estimate, not a quote or sale price.

---

## Tips

- **Best results with**: Claude (web search + long context), ChatGPT with browsing, Perplexity
- **Full BOM JSON**: ~15KB — fits within any major model's context window
- **Re-run monthly**: Prices change. Re-export and re-run before ordering.
- **Consolidation**: Amazon Prime covers ~40% of items with free shipping

## Disclaimer

Supplier listings are community-contributed reference information, not endorsements. Prices, availability, and specifications may change. Verify all details before purchasing.
