# AI-Assisted BOM Purchasing Guide

## How It Works

1. **Configure your build** in the [BOM Viewer](https://m3-crete.com/bom):
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
→ LOWEST COST — Cheapest total. Use bulk pricing, suggest substitutes
  where substitute_ok is true, consolidate by supplier for shipping.
→ FASTEST SHIPPING — Prioritize Amazon Prime and fast US shippers.
  Minimize number of suppliers. Everything within 1 week.
→ BEST VALUE — Balance cost and speed. US-stocked suppliers, 1-2 week
  delivery, reasonable prices.
→ MAXIMUM QUALITY — Premium suppliers only (McMaster-Carr, Gates, igus).
  Exact MPN matches, industrial-grade, longest service life.

MY DETAILS:
- Zip code: [YOUR ZIP CODE]
- Purchase strategy: [LOWEST COST / FASTEST SHIPPING / BEST VALUE / MAXIMUM QUALITY]

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
- Table grouped by supplier: part, qty, unit price, line total, URL
- Supplier subtotal + estimated shipping per supplier
- Grand total: parts + shipping + estimated tax
- Flag any out-of-stock, discontinued, or significantly changed prices
```

---

## Strategy Guide

| Strategy | Best For | Trade-off |
|----------|----------|-----------|
| **Lowest Cost** | Budget builds, patient builders | 3-6 week lead time (overseas), more suppliers |
| **Fastest Shipping** | Urgent builds | ~15-25% premium, mostly Amazon Prime |
| **Best Value** | Most builders | US suppliers, 1-2 week delivery, balanced |
| **Maximum Quality** | Production machines | Highest cost, best components, longest life |

### Typical All-In Cost Range (M3 base, excl. concrete pump)

| Strategy | Print plates | Buy CNC plates |
|----------|-------------|----------------|
| Lowest Cost | ~$1,900 – $2,200 | ~$2,400 – $2,700 |
| Best Value | ~$2,200 – $2,600 | ~$2,600 – $3,100 |
| Fastest Shipping | ~$2,400 – $2,800 | ~$2,800 – $3,300 |
| Maximum Quality | ~$2,800 – $3,400 | ~$3,200 – $4,000 |

*Ranges include parts + shipping + tax. Concrete extrusion system not included.*

---

## Tips

- **Best results with**: Claude (web search + long context), ChatGPT with browsing, Perplexity
- **Full BOM JSON**: ~15KB — fits within any major model's context window
- **Re-run monthly**: Prices change. Re-export and re-run before ordering.
- **Consolidation**: Amazon Prime covers ~40% of items with free shipping

## Disclaimer

Supplier listings are community-contributed reference information, not endorsements. Prices, availability, and specifications may change. Verify all details before purchasing.
