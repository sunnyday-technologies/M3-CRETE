# AI-Assisted BOM Purchasing Guide

Export the BOM as JSON from [m3-crete.com/bom](https://m3-crete.com/bom) using the **Export JSON** button, then paste the following prompt into your AI assistant (Claude, ChatGPT, Gemini, etc.) along with the JSON file.

---

## Prompt Template

Copy the prompt below, fill in the bracketed fields, and attach your exported BOM JSON.

```
I have a Bill of Materials (BOM) for an open-source concrete 3D printer
motion system (M3-CRETE). The attached JSON was exported from the
project's interactive BOM viewer.

Please help me build a complete buy list with the following requirements:

PURCHASE STRATEGY (pick one):
→ [LOWEST COST] — Minimize total spend. Use cheapest supplier per part,
  bulk pricing tiers, and consolidate orders to reduce shipping. Suggest
  cheaper substitutes where substitute_ok is true.
→ [FASTEST SHIPPING] — Prioritize Amazon Prime, DigiKey, and other
  suppliers with 1-3 day delivery. Minimize the number of suppliers.
  Pay more per part if it means everything arrives within a week.
→ [BEST VALUE] — Balance cost and shipping speed. Prefer US-stocked
  suppliers with reasonable prices. Avoid overseas shipping delays
  but don't overpay for overnight delivery.
→ [MAXIMUM QUALITY] — Use premium suppliers (McMaster-Carr, Gates belts,
  igus drag chain, StepperOnline direct). Prioritize exact MPN matches,
  brand-name components, and industrial-grade options over budget parts.

MY DETAILS:
- Zip code: [YOUR ZIP CODE]
- Model variant: [M3 / M3-2 / M3-4]
- Purchase strategy: [LOWEST COST / FASTEST SHIPPING / BEST VALUE / MAXIMUM QUALITY]
- Print vs. Buy: For parts with mfg_type "print" or "cnc", I want to
  [BUY manufactured versions / 3D PRINT them myself / DECIDE per part]

RULES:
1. Include all parts where "exclude_from_kit" is false. Skip parts where
   "exclude_from_kit" is true (concrete pump system is outside scope).

2. Use the MPN (manufacturer part number) and SKU fields when available
   for exact product matching. Where no MPN exists, use the part name
   and description to find the closest match.

3. If "substitute_ok" is false, match the EXACT MPN — no substitutions.
   If "substitute_ok" is true, follow the purchase strategy above.

4. Consolidate orders by supplier to minimize shipping costs. Note free
   shipping thresholds (e.g., Amazon Prime = free, DigiKey = $6.99
   ground, Adafruit = free over $35).

5. OUTPUT FORMAT — Produce a table grouped by supplier with:
   - Part name, quantity, unit price, line total
   - Direct product URL (clickable)
   - Supplier subtotal + estimated shipping
   - Grand total with estimated tax for my state
   - Summary comparing: parts cost, shipping, tax, all-in total

6. FLAG any parts that are out of stock, discontinued, or where the
   price has changed significantly from what the BOM description implies.

Optional: If you find a significantly cheaper alternative for any part
that still meets the engineering requirements in the description, flag
it as a suggestion with the price difference noted.
```

---

## Strategy Guide

| Strategy | Best For | Trade-off |
|----------|----------|-----------|
| **Lowest Cost** | Budget builds, patient builders | 3-6 week lead time (Bulkman3D sea freight), more suppliers to manage |
| **Fastest Shipping** | Urgent builds, impatient builders | ~15-25% price premium, mostly Amazon |
| **Best Value** | Most builders | Good balance — US suppliers, 1-2 week delivery, reasonable prices |
| **Maximum Quality** | Production machines, reliability-critical | Highest cost but best components, longest service life |

### Typical All-In Cost Range (M3 base, excl. concrete pump)

| Strategy | Estimated Range |
|----------|----------------|
| Lowest Cost (3D print plates) | ~$1,900 – $2,200 |
| Lowest Cost (buy CNC plates) | ~$2,400 – $2,700 |
| Best Value | ~$2,600 – $3,100 |
| Fastest Shipping | ~$2,800 – $3,300 |
| Maximum Quality | ~$3,200 – $4,000 |

*Ranges include parts + shipping + tax. Concrete extrusion system not included — see BOM for pump options.*

---

## Tips

- **Best results with**: Claude (web search + long context), ChatGPT with browsing, Perplexity
- **Token budget**: The full BOM JSON is ~15KB — well within context limits for all major models
- **Accuracy**: AI pricing is point-in-time. Verify final prices at checkout before purchasing.
- **Consolidation**: Most items are available on Amazon Prime. Consolidating there saves ~$50-100 in shipping vs. ordering from each specialty supplier individually.
- **Re-run monthly**: Prices change. Re-export the JSON and re-run the prompt to get updated pricing before you order.

## Disclaimer

Supplier listings are community-contributed reference information, not endorsements. Prices, availability, and specifications may change. Verify all details before purchasing.
