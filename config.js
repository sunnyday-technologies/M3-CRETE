// ============================================================
// BOM Viewer Configuration
// Update these values for your Supabase project and GitHub repo.
// This file is safe to commit — the anon key is a public key.
// All security is enforced via Supabase RLS policies.
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
    'Motion': 'Belt + V-Groove Wheels',
    'Z Config': '4x Belt-Driven (Auto-Tram)',
    'Controller': 'BTT Kraken + RPi 5',
    'Motors': 'NEMA23 8mm Shaft (StallGuard)',
    'Sourcing': 'Primarily US Suppliers',
    'Variants': 'M3-1 (1m\u00B3) \u2190 M3-2 (2m\u00B3, default) \u2192 M3-4 (4m\u00B3)'
  },

  // Category display order (must match category names in the database)
  CATEGORY_ORDER: [
    'Frame & Structure - Aluminum Extrusions',
    'Frame Hardware & Brackets',
    'X-Axis Motion System',
    'Dual Y-Axis Motion System',
    'Quad Z-Axis System (Self-Tramming)',
    'Electronics & Control System',
    'Concrete Extrusion System',
    'Fasteners & Hardware',
    'Optional Upgrades'
  ],

  // ── Model Variants ─────────────────────────────────
  // M3-2 is the base model (DB quantities). M3-1 downgrades, M3-4 upgrades.
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
        // X-axis motion (shorter travel)
        'GT2 Timing Belt 10mm (Reinforced)': { qty: 5, note: 'X-axis belt: ~3m for 1m travel' },
        // Wiring (shorter X run)
        'Cable Drag Chain (Sealed)': { qty: 3, unit: 'meters total (X: 1.5m + Y: 1.3m)', note: 'Shorter X-axis drag chain' },
        'Shielded Motor Cable - Flex-Rated (18AWG 4C)': { qty: 15, unit: 'meters (1 spool)', note: 'Shorter X-axis run' },
        // Reinforcement not needed — C-beam is stiffer than 2080 by design
        'Frame Stiffener \u2014 Long Span Reinforcement': { qty: 0, note: 'Not required \u2014 C-beam cross-section is stiff enough without reinforcement at 1m spans' }
      }
    },
    'M3-2': {
      label: 'M3-2 (2 m\u00B3, default)',
      volume: '2000 x 1000 x 1000mm (2 m\u00B3)',
      overrides: {}  // Base model — DB quantities are M3-2
    },
    'M3-4': {
      label: 'M3-4 (4 m\u00B3)',
      volume: '2000 x 2000 x 1000mm (4 m\u00B3)',
      overrides: {
        // Frame — 4 m\u00B3 variant needs spliced X AND Y at 2m span
        'C-beam 40\u00D780 \u00D7 1000 mm \u2014 Frame Member (SDT Standard)': { qty: 26, note: 'Y-axis also needs pairing: 4 Z-posts + 6 top Y (3L + 3R split at 1m) + 4 bot Y (split) + 4 mid Y + 4 top X + 2 mid X + 2 X-gantry (spliced). +2 spares.' },
        'T-Slot Drop-In Nuts M5 (20-Series)': { qty: 5, unit: 'packs of 100' },
        // X+Y motion (both double)
        'V-Groove Delrin Wheels (Polycarbonate)': { qty: 12, note: 'More wheels for longer X-travel' },
        'V-Groove Wheels (Polycarbonate)': { qty: 24, note: 'More wheels for longer Y-travel' },
        'Eccentric Spacers (V-Slot)': { qty: 40 },
        // Belts (both axes double)
        'GT2 Timing Belt 10mm (Reinforced)': { qty: 12, note: 'X+Y belts: ~5m per axis side for 2m travel' },
        // Wiring (both axes longer)
        'Cable Drag Chain (Sealed)': { qty: 5, unit: 'meters total (X: 2.5m + Y: 2.5m)', note: 'Both axes longer drag chain' },
        'Shielded Motor Cable - Flex-Rated (18AWG 4C)': { qty: 25, unit: 'meters (2 spools)', note: 'Longer runs to X+Y motors' },
        'Power Wire \u2014 12AWG Silicone (Red + Black)': { qty: 3, unit: 'meters each color (6m total)', note: 'Longer PSU-to-board run' },
        'Distribution Wire \u2014 18AWG (Red + Black)': { qty: 10, unit: 'meters total (5m each color)', note: 'Longer branch distribution' },
        'Cable Sleeving, Labels & Tie Kit': { qty: 2, unit: 'kits', note: 'More cable to manage' },
        'Frame Stiffener — Long Span Reinforcement': { qty: 8, note: 'Both X and Y axes have 2m+ spans — 2 bars per rail' }
      }
    }
  }
};
