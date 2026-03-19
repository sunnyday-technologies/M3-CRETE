// ============================================================
// BOM Viewer Configuration
// Update these values for your Supabase project and GitHub repo.
// This file is safe to commit — the anon key is a public key.
// All security is enforced via Supabase RLS policies.
// ============================================================

const BOM_CONFIG = {
  // Supabase project credentials (from Project Settings > API)
  SUPABASE_URL: 'https://ykgdqfygshgrjmtniued.supabase.co',
  SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlrZ2RxZnlnc2hncmptdG5pdWVkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM2OTU3MjIsImV4cCI6MjA4OTI3MTcyMn0.WJ7qSPsHmUoGPmcSXwEZPBvoeSx1G7ric2KN0utvmdM',

  // GitHub repo for contributor verification
  // Contributors = collaborators on this repo (checked via GitHub API)
  GITHUB_REPO_OWNER: 'sunnyday-technologies',
  GITHUB_REPO_NAME: 'M3-CRETE',

  // Display settings
  PROJECT_TITLE: 'Concrete 3D Printer BOM',
  PROJECT_SUBTITLE: 'Open-Source Hardware | Quad-Z Self-Tramming | Dual-Y Belt-Pinion',

  BUILD_SPECS: {
    'Build Volume': '1000 x 1000 x 1000mm (1 m³)',
    'Form Factor': 'Pallet-Shippable (48 x 40 in)',
    'Frame': 'V-Slot 2080 / 2040 (Dust Resistant)',
    'Motion': 'Belt + V-Groove Wheels',
    'Z Config': '4x Belt-Driven (Auto-Tram)',
    'Controller': 'BTT Kraken + RPi 5',
    'Motors': 'NEMA23 8mm Shaft (StallGuard)',
    'Sourcing': 'Primarily US Suppliers',
    'Variants': 'M3 (1m\u00B3) \u2192 M3-2 (2m\u00B3) \u2192 M3-4 (4m\u00B3)'
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
  // M3-1 is the base model (DB quantities). Larger models override qty/unit/name.
  DEFAULT_MODEL: 'M3',
  MODEL_VARIANTS: {
    'M3': {
      label: 'M3 (1 m\u00B3)',
      volume: '1000 x 1000 x 1000mm (1 m\u00B3)',
      overrides: {}
    },
    'M3-2': {
      label: 'M3-2 (2 m\u00B3)',
      volume: '2000 x 1000 x 1000mm (2 m\u00B3)',
      overrides: {
        // Frame — modular: order more 1200mm sections, splice with inline connectors for 2m X-travel
        '2080 V-Slot Aluminum Extrusion (1200mm)': { qty: 11, note: 'Modular: splice 2\u00D71200mm for 2.4m X-rails. All sections pallet-shippable.' },
        '2040 V-Slot Aluminum Extrusion (1000mm)': { qty: 12, note: 'Additional cross braces for longer X frame' },
        'T-Slot Drop-In Nuts M5 (20-Series)': { qty: 5, unit: 'packs of 100' },
        'Heavy Duty Corner Brackets (20-Series)': { qty: 40 },
        // Splice connectors for joined extrusions (M3 base doesn't need these)
        'Straight Line Internal Connectors (20-Series)': { qty: 12, note: '4 connectors per splice joint \u00D7 3 spliced rails' },
        // X-axis motion (doubles — only 1 motor, simpler than extending Y)
        'V-Groove Delrin Wheels (Polycarbonate)': { qty: 12, note: 'More wheels for longer X-travel' },
        'Eccentric Spacers (V-Slot)': { qty: 40 },
        // Belts (X doubles, Y unchanged)
        'GT2 Timing Belt 10mm (Reinforced)': { qty: 8, note: 'X-axis belt: ~5m for 2m travel' },
        // Wiring (longer X run — single motor, simpler)
        'Cable Drag Chain (Sealed)': { qty: 4, unit: 'meters total (X: 2.5m + Y: 1.3m)', note: 'Longer X-axis drag chain' },
        'Shielded Motor Cable - Flex-Rated (18AWG 4C)': { qty: 20, unit: 'meters (1 spool)', note: 'Longer run to X motor on extended gantry' },
        'Power Wire \u2014 12AWG Silicone (Red + Black)': { qty: 3, unit: 'meters each color (6m total)', note: 'Longer PSU-to-board run' },
        'Distribution Wire \u2014 18AWG (Red + Black)': { qty: 8, unit: 'meters total (4m each color)', note: 'Longer branch distribution' },
        'Cable Sleeving, Labels & Tie Kit': { qty: 2, unit: 'kits', note: 'More cable to manage' }
      }
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
        'Cable Sleeving, Labels & Tie Kit': { qty: 2, unit: 'kits', note: 'More cable to manage' }
      }
    }
  }
};
