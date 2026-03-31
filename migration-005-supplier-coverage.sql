-- ============================================================
-- Migration 005: Supplier Coverage + Data Corrections
-- M3-CRETE BOM — 2026-03-31
--
-- Fixes identified during BOM audit:
-- 1. Add Amazon supplier options for GT2 pulleys, drag chains, steppers
-- 2. Add Bulkman3D/MakerStore as suppliers for gantry/carriage plates
-- 3. Remove OpenBuilds (closed May 2025)
-- 4. Add 3D Printing USA + RatRig as extrusion suppliers
-- 5. Add reinforcement options (aluminum tube, CF bar) to BOM
-- 6. Clean up pump system references (external commercial only)
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 1. ADD AMAZON SUPPLIER OPTIONS (closes the export gap)
-- ────────────────────────────────────────────────────────────

-- GT2 Pulleys — X-axis (part 11)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, sku, approved)
VALUES (11, 'Amazon', 'https://www.amazon.com/BEMONOC-2GT-Timing-Pulley-printer/dp/B01CL24CAI',
        'BEMONOC 5-pack GT2 20T 8mm bore 10mm width', 'B01CL24CAI', true);

-- GT2 Pulleys — Y-axis (part 16)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, sku, approved)
VALUES (16, 'Amazon', 'https://www.amazon.com/BEMONOC-2GT-Timing-Pulley-printer/dp/B01CL24CAI',
        'BEMONOC 5-pack GT2 20T 8mm bore 10mm width — same as X-axis', 'B01CL24CAI', true);

-- GT2 Pulleys — Z-axis (part 21)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, sku, approved)
VALUES (21, 'Amazon', 'https://www.amazon.com/BEMONOC-2GT-Timing-Pulley-printer/dp/B01CL24CAI',
        'BEMONOC 5-pack GT2 20T 8mm bore 10mm width — same as X/Y', 'B01CL24CAI', true);

-- Sealed Drag Chain (part 30)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, sku, approved)
VALUES (30, 'Amazon', 'https://www.amazon.com/uxcell-Plastic-Cable-Carrier-Chain/dp/B01LXNJ7NI',
        'uxcell R55 25x50mm enclosed drag chain 1M — buy 4 units', 'B01LXNJ7NI', true);

-- NEMA23 Stepper — X-axis (part 9)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, sku, approved)
VALUES (9, 'Amazon', 'https://www.amazon.com/STEPPERONLINE-Stepper-Bipolar-57x57x113mm-Engraving/dp/B0CG58KY17',
        'STEPPERONLINE 23HS45-4204S1 3Nm 4.2A 8mm shaft', 'B0CG58KY17', true);

-- NEMA23 Stepper — Y-axis (part 14)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, sku, approved)
VALUES (14, 'Amazon', 'https://www.amazon.com/STEPPERONLINE-Stepper-Bipolar-57x57x113mm-Engraving/dp/B0CG58KY17',
        'STEPPERONLINE 23HS45-4204S1 3Nm 4.2A 8mm shaft — same as X', 'B0CG58KY17', true);

-- NEMA23 Stepper — Z-axis (part 19)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, sku, approved)
VALUES (19, 'Amazon', 'https://www.amazon.com/STEPPERONLINE-Stepper-Bipolar-57x57x113mm-Engraving/dp/B0CG58KY17',
        'STEPPERONLINE 23HS45-4204S1 3Nm 4.2A 8mm shaft — same as X/Y', 'B0CG58KY17', true);


-- ────────────────────────────────────────────────────────────
-- 2. ADD BULKMAN3D / MAKERSTORE FOR GANTRY PLATES
-- ────────────────────────────────────────────────────────────

-- X-Axis Carriage Plate (part 13)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (13, 'Bulkman3D', 'https://bulkman3d.com/product/vs80-1/',
        'V-Slot Gantry Bundle Universal 20-80mm — includes plate + 6 wheels + 3 eccentric spacers + hardware', true);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (13, 'MakerStore USA', 'https://makerstore.cc/product/v-slot-gantry-bundle-2/',
        'V-Slot Gantry Bundle — ships from US warehouse', true);

-- Y-Axis Gantry Plates (part 18)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (18, 'Bulkman3D', 'https://bulkman3d.com/product/vs80-1/',
        'V-Slot Gantry Bundle Universal 20-80mm — 2 needed for dual-Y gantry', true);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (18, 'MakerStore USA', 'https://makerstore.cc/product/v-slot-gantry-bundle-2/',
        'V-Slot Gantry Bundle — ships from US warehouse', true);

-- Z-Axis Carriage Plates (part 23)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (23, 'Bulkman3D', 'https://bulkman3d.com/product/vs80-1/',
        'V-Slot Gantry Bundle Universal — 4 needed for quad-Z carriages', true);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (23, 'MakerStore USA', 'https://makerstore.cc/product/v-slot-gantry-bundle-2/',
        'V-Slot Gantry Bundle — ships from US warehouse', true);

-- Z-Axis Motor Mounts (part 24)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (24, 'Bulkman3D', 'https://bulkman3d.com/product/pl0008-2/',
        'NEMA23 Motor Mount Plate 6061 aluminum — 4-pack, L96.5 x W60 x T3mm', true);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (24, 'MakerStore USA', 'https://makerstore.cc/',
        'NEMA23 motor mount plate — check MakerStore catalog', true);

-- Extruder Mounting Bracket (part 55)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (55, 'Bulkman3D', 'https://bulkman3d.com/product/vs80-1/',
        'Universal gantry plate — adapt for extruder mount with 1" NPT boss', true);


-- ────────────────────────────────────────────────────────────
-- 3. REMOVE OPENBUILDS (closed May 2025)
-- ────────────────────────────────────────────────────────────

-- OpenBuilds is no longer in business. Remove all supplier options.
-- Note: No OpenBuilds entries exist in the current schema seed,
-- but this ensures any manually-added entries are cleaned up.
DELETE FROM supplier_options WHERE supplier_name ILIKE '%openbuilds%';


-- ────────────────────────────────────────────────────────────
-- 4. ADD 3D PRINTING USA + RATRIG AS EXTRUSION SUPPLIERS
-- ────────────────────────────────────────────────────────────

-- 2080 V-Slot 1200mm (part 1)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (1, '3D Printing USA', 'https://3dprintingusa.com/collections/aluminum-extrusion-v-slot',
        '2080 V-Slot up to 2.5m lengths — no splicing needed for M3-1. US stock.', true);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (1, 'RatRig', 'https://us.ratrig.com/catalogsearch/result/?q=v-slot+2080',
        '2080 V-Slot custom cut-to-length. US/Canada store available.', true);

-- 2040 V-Slot 1200mm (part 2)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (2, '3D Printing USA', 'https://3dprintingusa.com/collections/aluminum-extrusion-v-slot',
        '2040 V-Slot — US stock', true);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (2, 'RatRig', 'https://us.ratrig.com/catalogsearch/result/?q=v-slot+2040',
        '2040 V-Slot custom cut-to-length', true);

-- 2040 V-Slot 1000mm (part 3)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (3, '3D Printing USA', 'https://3dprintingusa.com/collections/aluminum-extrusion-v-slot',
        '2040 V-Slot 1000mm — US stock', true);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES (3, 'RatRig', 'https://us.ratrig.com/catalogsearch/result/?q=v-slot+2040',
        '2040 V-Slot custom cut-to-length', true);


-- ────────────────────────────────────────────────────────────
-- 5. ADD REINFORCEMENT OPTIONS
-- ────────────────────────────────────────────────────────────

-- Add a new part for frame reinforcement (required at 2m+ spans)
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame & Structure - Aluminum Extrusions',
        'Frame Stiffener — Long Span Reinforcement',
        'Required for X-axis spans exceeding 1.5m (M3-2 and M3-4). Bond to the 80mm face of 2080 V-Slot with structural adhesive (Loctite EA 9430 or equivalent) + clamp cure. Two reinforcement bars per 2080 rail, utilizing the flat areas between V-grooves. Aluminum rectangular tube recommended for best stiffness-to-weight with zero galvanic corrosion risk. Carbon fiber flat bar is lighter but more expensive. Steel tube NOT recommended — galvanic corrosion with aluminum causes warping from residual stresses. M3-1 (1m spans): not required. Future: purpose-built I-beam stiffener profile with precision-drilled mounting holes (Sunnyday accessory, in development).',
        4, 'bars (1.2m each, trim to rail length)', 'buy', 15);

INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon', 'https://www.amazon.com/s?k=aluminum+rectangular+tube+1x2+inch+6063',
   'Aluminum rectangular tube 25x50x2mm (1"x2") 6063-T5 — cut to 1200mm. ~$8/m', true),
  (currval('parts_id_seq'), 'Amazon', 'https://www.amazon.com/KARBXON-Carbon-Pultruded-Planes-Drones-Projects/dp/B09Q7V4FLY',
   'KARBXON CF flat bar 20x4mm x 1m pultruded — lightweight alternative. ~$12/m', true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',
   'Aluminum rectangular tube 6063-T52 — precision stock, various sizes', true),
  (currval('parts_id_seq'), 'Metals Depot', 'https://www.metalsdepot.com/',
   'Aluminum rectangular tube — cut to length, ships from Kentucky', true);


-- ────────────────────────────────────────────────────────────
-- 6. PUMP SYSTEM — CLEAN UP REFERENCES
-- ────────────────────────────────────────────────────────────
-- Keep pump parts as informational/reference only.
-- Ensure exclude_from_kit = true and descriptions reference
-- commercial sources without naming specific development plans.

UPDATE parts SET
  exclude_from_kit = true,
  description = 'REFERENCE ONLY — not included in M3-CRETE motion system kit. The concrete extrusion system operates at high pressure and requires commercial-grade components. Proven options include progressive cavity pump systems from established manufacturers. Contact Sunnyday Technologies for current recommendations. High-pressure pump development is tracked separately.'
WHERE id = 44;  -- Progressive Cavity Pump

UPDATE parts SET
  description = 'Mounts extruder pipe to X-axis carriage plate. Standard 1" Male NPT threaded pipe connection. Lightweight — printhead target is 1.5kg. This is the only extrusion-system part in the M3-CRETE motion system kit. Hose, nozzle, and hopper are pump-specific — source from your pump manufacturer or contact Sunnyday Technologies for recommendations.'
WHERE id = 55;  -- Extruder Mounting Bracket


-- ────────────────────────────────────────────────────────────
-- 7. MODEL VARIANT OVERRIDE — Reinforcement stiffener
-- ────────────────────────────────────────────────────────────
-- M3-1: qty 0 (not needed at 1m span)
-- M3-2: qty 4 (2 per spliced X-rail)
-- M3-4: qty 8 (2 per spliced rail on both axes)
-- Note: These overrides are applied in config.js MODEL_VARIANTS,
-- not in the database. The DB default (qty 4) is for M3-2.
