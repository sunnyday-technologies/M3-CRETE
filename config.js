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
  PROJECT_SUBTITLE: 'Open-Source Hardware | Quad-Z Self-Tramming | Dual-Y | US Sourcing',

  BUILD_SPECS: {
    'Build Volume': '1200 x 1000 x 1000mm',
    'Motion': 'Belt + V-Groove (Dust Resistant)',
    'Z Config': '4x Independent (Auto-Tram)',
    'Controller': 'BTT Kraken + RPi 5',
    'Motors': 'NEMA23 Standard (StallGuard)',
    'Sourcing': '100% US Suppliers'
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
  ]
};
