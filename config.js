// ============================================================
// BOM Viewer Configuration
// Static-JSON BOM viewer (bom.m3-crete.com/bom/). Loads bom/data.json,
// renders by category, links to GitHub for supplier-suggestion issues.
// No backend, no auth, no PII — safe to commit.
// ============================================================

const BOM_CONFIG = {
  // GitHub repo — supplier suggestions via Issues, BOM data in bom/data.json
  GITHUB_REPO_OWNER: 'sunnyday-technologies',
  GITHUB_REPO_NAME: 'M3-CRETE',

  // Display settings
  PROJECT_TITLE: 'Concrete 3D Printer BOM',
  PROJECT_SUBTITLE: 'Open-Source Hardware | Quad-Z Self-Tramming | Dual-Y Belt-Pinion',

  BUILD_SPECS: {
    'Build Volume': '2000 x 1000 x 1000mm (2 m³)',
    'Form Factor': 'Modular Splice — Pallet-Shippable (48 x 40 in)',
    'Frame': 'C-beam 40x80 1m (single SKU, dust-resistant)',
    'Motion': 'Belts (X/Y) + Lead Screws (Z) + V-Wheels',
    'Z Config': '4x Tr8x2 Lead Screw (Auto-Tram)',
    'Controller': 'BTT Kraken + RPi 5',
    'Motors': 'NEMA23 8mm Shaft (StallGuard)',
    'Sourcing': 'Primarily US Suppliers',
    'Variants': 'M3-1 (1m\u00B3) \u2190 M3-2 (2m\u00B3, default)'
  },

  // Category display order (must match category names in the database)
  CATEGORY_ORDER: [
    'Frame & Structure - Aluminum Extrusions',
    'Frame Hardware & Brackets',
    'X-Axis Motion System',
    'Dual Y-Axis Motion System',
    'Quad Z-Axis System (Self-Tramming)',
    'Electronics & Control System',
    'Fasteners & Hardware',
    'Optional Upgrades',
    'Frame - Reinforcement',
    'Frame - Extrusions',
    'Motion - Plates',
    '3D-Printed Structural',
    // Last: reference only, not in the kit. Pumping and extrusion are a
    // separate, related project.
    'Concrete Extrusion System'
  ],

  // ── Model Variants ─────────────────────────────────
  // M3-2 is the base model (DB quantities). M3-1 downgrades. M3-4 (2000 x 2000 x 1000) was discontinued
  // 2026-10-13: its Y-gantry rails carry the Y belt inside the C-channel, so they can't take the centered 2040 splice.
  DEFAULT_MODEL: 'M3-2',
  MODEL_VARIANTS: {
    'M3-1': {
      label: 'M3-1 (1 m\u00B3)',
      volume: '1000 x 1000 x 1000mm (1 m\u00B3)',
      overrides: {
        // Frame — all members are single-SKU C-beam 40x80 1m. No splice
        // needed at 1m³ (X-rails don't need pairing). 12 pieces + spares.
        'C-beam 40\u00D780 \u00D7 1000 mm \u2014 Frame Member (SDT Standard)': { qty: 13, note: 'Single-SKU frame: 4 Z-posts + 1 top Y + 1 bot Y + 2 mid Y + 2 top X + 2 mid X + 1 X-gantry. +1 spare.' },
        'T-Slot Drop-In Nuts M5 (20-Series)': { qty: 2, unit: 'packs of 100', note: 'Fewer joints' },
        // X-axis motion (shorter travel). Belt keys must match bom/data.json names
        // exactly. Rule (owner, 2026-10-13): Y loop = 2 x rail length; X = one beam-length strand.
        'GT2 Timing Belt 6mm (X-axis, 1x 2m fixed strand)': { qty: 1, name: 'GT2 Timing Belt 6mm (X-axis, 1x 1m fixed strand)', note: 'X: one 1 m fixed strand for the 1 m X beam' },
        // Wiring (shorter X run)
        'Cable Drag Chain (Sealed)': { qty: 3, unit: 'meters total (X: 1.5m + Y: 1.3m)', note: 'Shorter X-axis drag chain' },
        'Shielded Motor Cable - Flex-Rated (18AWG 4C)': { qty: 15, unit: 'meters (1 spool)', note: 'Shorter X-axis run' },
        // No 2 m spans at 1m³, so no centered 2040 inserts (id 65), end L-brackets (id 85) or connector bars (id 5)
        'X-Direction Internal Reinforcement (centered 2040 insert)': { qty: 0, note: 'Not needed: M3-1 has no spliced 2 m members' },
        '2040 Insert End L-Brackets (purchased or printed)': { qty: 0, note: 'No 2040 inserts on M3-1' },
        'Straight Line Internal Connectors (20-Series)': { qty: 0, note: 'No splice joints on M3-1' }
      }
    },
    'M3-2': {
      label: 'M3-2 (2 m\u00B3, default)',
      volume: '2000 x 1000 x 1000mm (2 m\u00B3)',
      overrides: {}  // Base model — DB quantities are M3-2
    }
  }
};
