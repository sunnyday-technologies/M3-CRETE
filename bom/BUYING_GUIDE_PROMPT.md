# AI-Assisted BOM Purchasing Guide

Export the BOM as JSON from [m3-crete.com/bom](https://m3-crete.com/bom) using the **Export JSON** button, then paste the following prompt into your AI assistant (Claude, ChatGPT, Gemini, etc.) along with the JSON file.

---

## Prompt Template

```
I have a Bill of Materials (BOM) for an open-source concrete 3D printer
motion system (M3-CRETE). The attached JSON was exported from the
project's interactive BOM viewer.

Please help me build a complete buy list with the following requirements:

1. **Scope**: Include all parts where "exclude_from_kit" is false.
   Skip any parts where "exclude_from_kit" is true (these are
   informational only — the concrete pump system is outside project scope).

2. **Pricing**: For each part, search for the current lowest price from
   the suppliers listed. Use the MPN (manufacturer part number) and SKU
   fields when available for exact product matching. Where no MPN exists,
   use the part name and description to find the closest match.

3. **Substitutions**: If "substitute_ok" is false, match the exact MPN.
   If "substitute_ok" is true, you may suggest cheaper equivalents that
   meet the specifications in the description.

4. **Shipping**: My zip code is [YOUR ZIP CODE]. Consolidate orders by
   supplier to minimize shipping costs. Note free shipping thresholds.
   Estimate shipping for each supplier.

5. **Output format**: Produce a table grouped by supplier with:
   - Part name, quantity, unit price, line total
   - Direct product URL (clickable)
   - Supplier subtotal + estimated shipping per supplier
   - Grand total with estimated tax for my state

6. **Model variant**: I am building the [M3 / M3-2 / M3-4] variant.
   Use the quantities shown in the JSON (they reflect the selected model).

7. **Print vs. Buy**: For parts with mfg_type "print" or "cnc", I want
   to [BUY manufactured versions / 3D PRINT them myself / decide per part].
   If buying, look for CNC aluminum or laser-cut steel options from
   SendCutSend or similar services.

Optional: If you find a significantly cheaper alternative for any part
that still meets the engineering requirements in the description, flag
it as a suggestion with the price difference noted.
```

---

## Tips

- **Best results with**: Claude (web search + long context), ChatGPT with browsing, Perplexity
- **Token budget**: The full BOM JSON is ~15KB — well within context limits for all major models
- **Accuracy**: AI pricing is point-in-time. Verify final prices at checkout before purchasing.
- **Consolidation**: Most items are available on Amazon Prime. Consolidating there saves ~$50-100 in shipping vs. ordering from each specialty supplier individually.

## Disclaimer

Supplier listings are community-contributed reference information, not endorsements. Prices, availability, and specifications may change. Verify all details before purchasing.
