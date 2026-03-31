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
    'Frame': 'V-Slot 2080 / 2040 (Dust Resistant)',
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
        // Frame — no splice needed, fewer extrusions
        '2080 V-Slot Aluminum Extrusion (1200mm)': { qty: 7, note: 'No splice — single-piece X-rails at 1200mm' },
        '2040 V-Slot Aluminum Extrusion (1000mm)': { qty: 8, note: 'Fewer cross braces (no X-extension)' },
        'Straight Line Internal Connectors (20-Series)': { qty: 0, note: 'Not needed — all extrusions single-piece' },
        'Heavy Duty Corner Brackets (20-Series)': { qty: 32 },
        'T-Slot Drop-In Nuts M5 (20-Series)': { qty: 3, unit: 'packs of 100' },
        // X-axis motion (shorter travel)
        'GT2 Timing Belt 10mm (Reinforced)': { qty: 5, note: 'X-axis belt: ~3m for 1m travel' },
        // Wiring (shorter X run)
        'Cable Drag Chain (Sealed)': { qty: 3, unit: 'meters total (X: 1.5m + Y: 1.3m)', note: 'Shorter X-axis drag chain' },
        'Shielded Motor Cable - Flex-Rated (18AWG 4C)': { qty: 15, unit: 'meters (1 spool)', note: 'Shorter X-axis run' },
        // Reinforcement not needed at 1m span
        'Frame Stiffener — Long Span Reinforcement': { qty: 0, note: 'Not required — 1m spans have adequate stiffness without reinforcement' }
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
        // Frame
        '2080 V-Slot Aluminum Extrusion (1200mm)': { qty: 14, note: 'Modular: splice 2\u00D71200mm for 2.4m rails on both axes. All sections pallet-shippable.' },
        '2040 V-Slot Aluminum Extrusion (1000mm)': { qty: 14, note: 'Additional cross braces for full-size frame' },
        'Straight Line Internal Connectors (20-Series)': { qty: 28, note: '4 connectors per splice joint \u00D7 7 spliced 2080 rails' },
        'T-Slot Drop-In Nuts M5 (20-Series)': { qty: 6, unit: 'packs of 100' },
        'Heavy Duty Corner Brackets (20-Series)': { qty: 48 },
        'Carbon Fiber Stiffener Bar (2080 Rail)': { qty: 7, note: 'Recommended for 2m spans' },
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
