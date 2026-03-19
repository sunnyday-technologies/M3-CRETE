-- ============================================================
-- Concrete 3D Printer BOM — Supabase Schema
-- M3-CRETE  |  M3-1: 1000 x 1000 x 1000mm (1 m³) build volume
-- V-Slot frame  |  Pallet-shippable (48 x 40 in)
-- Future variants: M3-2 (1×2×1m), M3-4 (2×2×1m) — scale by adding longer extrusions
--
-- Run this in the Supabase SQL Editor to set up the database.
-- All migrations (001-005) are baked into this file.
-- ============================================================

-- 1. TABLES
-- ----------------------------------------------------------

CREATE TABLE parts (
  id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  category       TEXT    NOT NULL,
  name           TEXT    NOT NULL,
  description    TEXT,
  qty            INTEGER NOT NULL DEFAULT 1,
  unit           TEXT    NOT NULL DEFAULT 'pieces',
  mfg_type       TEXT    NOT NULL CHECK (mfg_type IN ('buy', 'print', 'cnc')),
  sort_order     INTEGER NOT NULL DEFAULT 0,
  mpn            TEXT,                          -- Manufacturer Part Number (agent-readable)
  substitute_ok  BOOLEAN NOT NULL DEFAULT true, -- false = exact match required
  exclude_from_kit BOOLEAN NOT NULL DEFAULT false -- true = informational only, not in purchasable kit
);

CREATE TABLE supplier_options (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  part_id       BIGINT       NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  supplier_name TEXT         NOT NULL,
  product_url   TEXT,
  notes         TEXT,
  step_url      TEXT,
  sku           TEXT,                  -- Supplier-specific SKU/ASIN (agent-readable)
  submitted_by  UUID         REFERENCES auth.users(id),
  approved      BOOLEAN      NOT NULL DEFAULT false,
  approved_by   UUID         REFERENCES auth.users(id),
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE maintainers (
  user_id         UUID PRIMARY KEY REFERENCES auth.users(id),
  github_username TEXT NOT NULL,
  added_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. INDEXES
-- ----------------------------------------------------------

CREATE INDEX idx_supplier_options_part_id  ON supplier_options(part_id);
CREATE INDEX idx_supplier_options_approved ON supplier_options(approved) WHERE approved = true;
CREATE INDEX idx_parts_category            ON parts(category);

-- 3. ROW LEVEL SECURITY
-- ----------------------------------------------------------

ALTER TABLE parts            ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintainers      ENABLE ROW LEVEL SECURITY;

CREATE POLICY "parts_read" ON parts
  FOR SELECT USING (true);

CREATE POLICY "parts_maintainer_insert" ON parts
  FOR INSERT WITH CHECK (
    auth.uid() IN (SELECT user_id FROM maintainers)
  );

CREATE POLICY "parts_maintainer_update" ON parts
  FOR UPDATE USING (
    auth.uid() IN (SELECT user_id FROM maintainers)
  );

CREATE POLICY "supplier_read" ON supplier_options
  FOR SELECT USING (
    approved = true
    OR auth.uid() = submitted_by
    OR auth.uid() IN (SELECT user_id FROM maintainers)
  );

CREATE POLICY "supplier_insert" ON supplier_options
  FOR INSERT WITH CHECK (
    auth.uid() IS NOT NULL
    AND submitted_by = auth.uid()
    AND approved = false
  );

CREATE POLICY "supplier_maintainer_update" ON supplier_options
  FOR UPDATE USING (
    auth.uid() IN (SELECT user_id FROM maintainers)
  );

CREATE POLICY "supplier_maintainer_delete" ON supplier_options
  FOR DELETE USING (
    auth.uid() IN (SELECT user_id FROM maintainers)
  );

CREATE POLICY "maintainers_read" ON maintainers
  FOR SELECT USING (auth.uid() IS NOT NULL);

-- 4. SEED DATA
-- ----------------------------------------------------------
-- All seed supplier_options are pre-approved.
-- Prices intentionally omitted. step_url populated where available.

-- ════════════════════════════════════════════════════════════
-- ██  FRAME & STRUCTURE - ALUMINUM EXTRUSIONS              ██
-- ════════════════════════════════════════════════════════════

-- ── 2080 V-Slot — Travel Rails & Main Frame ─────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame & Structure - Aluminum Extrusions',
        '2080 V-Slot Aluminum Extrusion (1200mm)',
        'Main frame horizontals and gantry beam. V-groove rails on all 4 faces for wheel carriages. 1200mm provides ~1000mm usable travel after carriage clearance. 2080 oriented with 80mm vertical for maximum stiffness (Iy ≈ 33 cm⁴). Deflection ~0.05mm at 1.2m span with 3kg load. Fits within 48-inch pallet dimension. For M3-2/M3-4 variants, scale to 2200mm.',
        7, 'lengths', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',      'https://bulkman3d.com/product/v-slot-2080/',              '2080 V-Slot, cut to length, black or silver anodized',   NULL, true),
  (currval('parts_id_seq'), 'MakerStore USA',  'https://makerstore.cc/product/v-slot-20-x-80mm-4/',      '2080 V-Slot, lengths up to 2650mm',                      NULL, true),
  (currval('parts_id_seq'), 'ZYLtech',         'https://www.zyltech.com/zyltech-2080-t-slot-aluminum-extrusion-pre-cut-length-1000mm/', '2080 pre-cut, 1000-2000mm. NOTE: ZYLtech 2080 is T-slot not V-slot — verify V-groove compatibility or use for structural-only members', NULL, true),
  (currval('parts_id_seq'), 'VXB Bearings',    'https://vxb.com/products/1000mm-black-v-slot-aluminum-extrusion-profile-lin', '2080 V-Slot 1000mm stocked, black anodized', NULL, true);

-- ── 2040 V-Slot — Verticals & Cross Braces ──────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame & Structure - Aluminum Extrusions',
        '2040 V-Slot Aluminum Extrusion (1200mm)',
        'Vertical posts (Z-height). 1200mm gives ~1000mm usable Z travel after motor mount and belt pulley clearance. V-groove rails serve as Z linear guides for belt-driven carriages. Fits within 48-inch pallet dimension (1200mm < 1219mm).',
        4, 'lengths', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',      'https://bulkman3d.com/product/v-slot-2040/',              '2040 V-Slot, cut to length',              NULL, true),
  (currval('parts_id_seq'), 'MakerStore USA',  'https://makerstore.cc/product/v-slot-20-x-40mm/',        '2040 V-Slot, multiple lengths',           NULL, true),
  (currval('parts_id_seq'), 'ZYLtech',         'https://www.zyltech.com/2040-v-groove-extrusion-pre-cut-lengths-300mm-2000mm/', '2040 V-Groove (V-Slot compatible), 300-2000mm', NULL, true);

-- ── 2040 V-Slot — Cross Braces & Supports ───────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame & Structure - Aluminum Extrusions',
        '2040 V-Slot Aluminum Extrusion (1000mm)',
        'Cross braces, cable chain mounts, electronics panel rails, and accessory mounting. 1000mm is the most common pre-cut stock length.',
        8, 'lengths', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',      'https://bulkman3d.com/product/v-slot-2040/',              '2040 V-Slot 1000mm',                      NULL, true),
  (currval('parts_id_seq'), 'ZYLtech',         'https://www.zyltech.com/10x-1m-2040-v-groove-extrusion-bulk-pack/', '10-pack 1000mm V-Groove bulk — best value', NULL, true),
  (currval('parts_id_seq'), 'VXB Bearings',    'https://vxb.com/',                                       '2040 V-Slot 1000mm stocked',              NULL, true);

-- ════════════════════════════════════════════════════════════
-- ██  FRAME HARDWARE & BRACKETS                            ██
-- ════════════════════════════════════════════════════════════

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame Hardware & Brackets', 'Heavy Duty Corner Brackets (20-Series)',
        'Frame corner connections for V-Slot 20-series. Must be 20-series compatible (6mm slot). Printable saves $200+.',
        32, 'pieces', 'print', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',       'https://bulkman3d.com/',       '20-series cast aluminum L-bracket',   true),
  (currval('parts_id_seq'), 'McMaster-Carr',   'https://mcmaster.com',         'Aluminum L-bracket 20mm series',      true),
  (currval('parts_id_seq'), 'Self-Manufacture','',                             '3D Printed ABS/Nylon — STL in repo',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame Hardware & Brackets', 'Straight Line Internal Connectors (20-Series)',
        'Slides into T-slot to splice two extrusions end-to-end for modular frame scaling. Not needed for M3 base model (all extrusions single-piece). For M3-2/M3-4: use 4 connectors per splice joint (one per slot) for maximum rigidity and V-groove alignment. 100mm long, M5 set screws.',
        0, 'pieces (M3-2: 12, M3-4: 28)', 'buy', 15);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   '20-series straight line connector 100mm with M5 screws — 4-pack or 12-pack', true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'PZRT 2020 series straight line connector bracket',                          true),
  (currval('parts_id_seq'), 'Bulkman3D',     'https://bulkman3d.com/','20-series internal joining plate',                                         true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame Hardware & Brackets', 'T-Slot Drop-In Nuts M5 (20-Series)',
        '300 total — M5 is the standard fastener for 20-series V-Slot (6mm slot width). Spring-loaded drop-in style recommended for easier assembly. NOT M6 — M6 is for 40-series only.',
        3, 'packs of 100', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',      'https://bulkman3d.com/',       'M5 spring-loaded T-nut 20-series',    true),
  (currval('parts_id_seq'), 'ZYLtech',        'https://www.zyltech.com/',     'M5 T-nut for 2020/2040/2080',         true),
  (currval('parts_id_seq'), 'McMaster-Carr',  'https://mcmaster.com',         'M5 drop-in nut for 20mm T-slot',      true),
  (currval('parts_id_seq'), 'Amazon',         'https://amazon.com',           'M5 T-nut 100-pack (20-series 6mm slot)', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame Hardware & Brackets', 'Eccentric Spacers (V-Slot)',
        'Required for V-wheel preload adjustment on all motion axes (X, Y, and Z). Each V-wheel carriage uses eccentric spacers on the bottom wheels to tension against the rail. Without these, wheels cannot be properly preloaded and will be loose on the rail.',
        28, 'pieces', 'buy', 25);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',      'https://bulkman3d.com/',       'Eccentric spacer for V-Slot (6mm bore, 10mm OD)', true),
  (currval('parts_id_seq'), 'MakerStore USA', 'https://makerstore.cc/',       'Eccentric spacer — precision ground',              true),
  (currval('parts_id_seq'), 'Amazon',         'https://amazon.com',           'V-Slot eccentric spacer 10-pack',                  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame Hardware & Brackets', 'Adjustable Leveling Feet M16',
        'Critical for leveling on uneven job-site floors. 1000lb-rated per foot. NOTE: M16 thread will not fit directly into 20-series V-Slot — requires printed or CNC base plates to interface with frame.',
        4, 'pieces', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Heavy duty 1000lb swivel leveling foot', true),
  (currval('parts_id_seq'), 'Grainger',      'https://grainger.com', 'Vibration dampening leveling mount',     true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Standard M16 leveling foot',             true);

-- ════════════════════════════════════════════════════════════
-- ██  X-AXIS MOTION SYSTEM                                 ██
-- ════════════════════════════════════════════════════════════

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'NEMA23 Stepper Motor (X-axis, 8mm shaft)',
        'MUST be 8mm shaft variant to match pulleys and couplers. TMC5160 StallGuard for sensorless homing. 3Nm minimum torque recommended.',
        1, 'motor', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US',  'https://www.omc-stepperonline.com', 'NEMA23 3Nm 8mm shaft',              'https://www.omc-stepperonline.com/download', true),
  (currval('parts_id_seq'), 'StepperOnline US',  'https://www.omc-stepperonline.com', 'NEMA23 4.5Nm High Torque 8mm shaft','https://www.omc-stepperonline.com/download', true),
  (currval('parts_id_seq'), 'AutomationDirect',  'https://automationdirect.com',      'NEMA23 3Nm — verify 8mm shaft',     NULL, true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'GT2 Timing Belt 10mm (Reinforced)',
        'X-axis drive belt. ~3m needed for 1m travel (2×1.2m run + tensioner + tails). Buy extra for spares. Gates PowerGrip GT2/GT3 interchangeable at 2mm pitch.',
        5, 'meters', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',      'https://mcmaster.com',              'Gates PowerGrip GT2 10mm',    'https://www.gates.com/us/en', true),
  (currval('parts_id_seq'), 'Amazon',             'https://amazon.com',                'Fiberglass core GT2 10mm',    NULL, true),
  (currval('parts_id_seq'), 'StepperOnline US',   'https://www.omc-stepperonline.com', 'Standard rubber GT2 10mm',    NULL, true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'GT2 Pulley 20-Tooth (8mm Bore)',
        'Drive and idler pulleys — MUST match motor shaft diameter (8mm). Metal recommended for belt tooth engagement under load. Aluminum or steel.',
        4, 'pulleys', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Aluminum 20T 8mm bore GT2',         true),
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'Steel 20T 8mm bore GT2',            true),
  (currval('parts_id_seq'), 'ZYLtech',          'https://www.zyltech.com/',          'GT2 20T pulley — 5mm/6.35mm/8mm bore options', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'V-Groove Delrin Wheels (Polycarbonate)',
        'Dust-resistant, critical for concrete environment. Use Polycarbonate (Xtreme/Solid) for CNC-grade loads, not standard Delrin. Rides on V-Slot extrusion V-groove rails.',
        8, 'wheels', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',      'https://bulkman3d.com/',       'Xtreme Solid V-Wheel (polycarbonate)',  true),
  (currval('parts_id_seq'), 'MakerStore USA', 'https://makerstore.cc/',       'Solid V-Wheel polycarbonate',           true),
  (currval('parts_id_seq'), 'Amazon',         'https://amazon.com',           'V-Slot V-Wheel kit with bearings',      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'X-Axis Carriage Plate Assembly',
        'Carries the 1.5kg printhead. Print saves $70+ with CF-Nylon/ABS. Must be compatible with V-Slot 2080 rail width. Hose is counter-weighted to reduce gantry loading.',
        1, 'assembly', 'print', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum 6061 6mm',           true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed Carbon Fiber Nylon',   true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Water-jet cut steel',             true);

-- ════════════════════════════════════════════════════════════
-- ██  DUAL Y-AXIS MOTION SYSTEM                            ██
-- ════════════════════════════════════════════════════════════

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'NEMA23 Stepper Motor (Y-axis, 8mm shaft)',
        'Dual motors for anti-racking — TMC5160 StallGuard compatible. MUST be 8mm shaft variant. Both Y motors must be identical model for matched steps/mm.',
        2, 'motors', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 3Nm 8mm shaft',              'https://www.omc-stepperonline.com/download', true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 4.5Nm High Torque 8mm shaft','https://www.omc-stepperonline.com/download', true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com',      'NEMA23 3Nm — verify 8mm shaft',     NULL, true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'GT2 Timing Belt 10mm (Reinforced)',
        'Dual Y-axis belts — ~3m each side, 6m total. High load application with gantry beam.',
        8, 'meters', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'Gates PowerGrip GT2 10mm',  true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',                'Fiberglass core GT2 10mm',  true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Standard rubber GT2 10mm',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'GT2 Pulley 20-Tooth (8mm Bore)',
        'Multiple pulleys needed for dual Y system. MUST be 8mm bore to match motor shaft.',
        8, 'pulleys', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Aluminum 20T 8mm bore',     true),
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'Steel 20T 8mm bore',        true),
  (currval('parts_id_seq'), 'ZYLtech',          'https://www.zyltech.com/',          'GT2 20T 8mm bore',          true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'V-Groove Wheels (Polycarbonate)',
        'More wheels = better load distribution on the gantry beam carriages. Polycarbonate (Xtreme/Solid) for heavy gantry loads.',
        16, 'wheels', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',      'https://bulkman3d.com/',  'Xtreme Solid V-Wheel',            true),
  (currval('parts_id_seq'), 'MakerStore USA', 'https://makerstore.cc/',  'Solid V-Wheel polycarbonate',     true),
  (currval('parts_id_seq'), 'Amazon',         'https://amazon.com',      'V-Slot V-Wheel kit with bearings',true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'Y-Axis Gantry Plates',
        'Connects gantry beam to Y-rail carriages. Must span 2080 rail width. Print saves $160+.',
        2, 'plates', 'print', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum 8mm',               true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed CF-Nylon Reinforced', true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Laser cut steel',                true);

-- ════════════════════════════════════════════════════════════
-- ██  QUAD Z-AXIS SYSTEM (BELT-DRIVEN, SELF-TRAMMING)     ██
-- ════════════════════════════════════════════════════════════
-- Belt-driven Z replaces lead screws. Advantages:
-- 1. Zero unique parts — same belts, pulleys, wheels as X/Y
-- 2. ~$50-100 cheaper (no lead screws, nut blocks, couplers, pillow blocks)
-- 3. Belts shed concrete splatters — lead screw threads would seize
-- 4. V-wheels ride 2040 vertical posts — linear guide is built into the frame
-- 5. Faster Z movement (~50mm/s vs ~5mm/s)
-- Note: TR12x3 pitch is NOT self-locking anyway — belt is equivalent

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'NEMA23 Stepper Motor (Z-axis, 8mm shaft)',
        'Four independent motors for auto-tramming via Klipper Z_TILT_ADJUST. 8mm shaft to match pulleys. Belt-driven Z — same motor type as X/Y for full parts commonality.',
        4, 'motors', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 3Nm 8mm shaft',              'https://www.omc-stepperonline.com/download', true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 4.5Nm High Torque 8mm shaft','https://www.omc-stepperonline.com/download', true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com',      'NEMA23 3Nm — verify 8mm shaft',     NULL, true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'GT2 Timing Belt 10mm (Z-axis)',
        'Belt-driven Z — same GT2 10mm belt as X/Y axes. ~3m per Z corner (up + down run + tensioner), 12m total for 4 independent Z drives. Belts shed concrete splatters unlike lead screw threads.',
        12, 'meters', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'Gates PowerGrip GT2 10mm — same as X/Y',  true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',                'Fiberglass core GT2 10mm',                 true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Standard rubber GT2 10mm',                 true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'GT2 Pulley 20-Tooth (8mm Bore, Z-axis)',
        'Drive + idler pulleys for belt Z. Same 8mm bore GT2 pulleys as X/Y — full parts commonality. 2 per Z corner (drive + idler) = 8 total.',
        8, 'pulleys', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Aluminum 20T 8mm bore — same as X/Y',  true),
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'Steel 20T 8mm bore',                    true),
  (currval('parts_id_seq'), 'ZYLtech',          'https://www.zyltech.com/',          'GT2 20T 8mm bore',                      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'V-Groove Wheels (Z-axis Carriages)',
        'V-wheels ride the 2040 vertical post V-grooves — the frame IS the linear guide. 3 wheels per corner carriage (2 fixed + 1 eccentric) × 4 corners = 12 wheels. Same polycarbonate wheels as X/Y.',
        12, 'wheels', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Bulkman3D',      'https://bulkman3d.com/',  'Xtreme Solid V-Wheel — same as X/Y',  true),
  (currval('parts_id_seq'), 'MakerStore USA', 'https://makerstore.cc/',  'Solid V-Wheel polycarbonate',          true),
  (currval('parts_id_seq'), 'Amazon',         'https://amazon.com',      'V-Slot V-Wheel kit with bearings',     true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'Z-Axis Carriage Plates',
        'Connects gantry frame to V-wheel carriages on vertical posts. 4 plates (one per corner). Must mount V-wheels + belt clamp. Print saves $60+.',
        4, 'plates', 'print', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum 6mm',                true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed CF-Nylon Reinforced',  true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Laser cut steel',                 true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'Z-Axis Motor Mounts',
        'Print saves $90 for all 4 mounts. Must interface between NEMA23 face and 2040 V-Slot vertical post. Mounts at top or bottom of verticals.',
        4, 'mounts', 'print', 60);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum mount',   true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed PETG/ABS',  true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Laser cut steel',      true);

-- ════════════════════════════════════════════════════════════
-- ██  ELECTRONICS & CONTROL SYSTEM                         ██
-- ════════════════════════════════════════════════════════════
-- NOTE: Endstop switches REMOVED (StallGuard sensorless homing via TMC5160).
-- NOTE: Vague "Wiring Kit" REPLACED with 13 detailed components below.

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'BTT Kraken Mainboard',
        '8 stepper drivers (TMC5160) — perfect for this build: X + 2×Y + 4×Z + Extruder. StallGuard sensorless homing on all axes.',
        1, 'board', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'Filastruder', 'https://www.filastruder.com', 'BTT Kraken v1.0',       'https://github.com/bigtreetech/Kraken/tree/master/Hardware', true),
  (currval('parts_id_seq'), 'Amazon',      'https://amazon.com',          'BTT Kraken',             NULL, true),
  (currval('parts_id_seq'), 'Filastruder', 'https://www.filastruder.com', 'BTT Octopus Pro (alt)',  'https://github.com/bigtreetech/BIGTREETECH-OCTOPUS-Pro', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Raspberry Pi 5 (8GB RAM)',
        'Runs Klipper firmware. 8GB recommended for large print files.',
        1, 'computer', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Adafruit',          'https://www.adafruit.com', 'RPi 5 8GB',        true),
  (currval('parts_id_seq'), 'Amazon - CanaKit',  'https://amazon.com',       'RPi 5 8GB Kit',    true),
  (currval('parts_id_seq'), 'Adafruit',          'https://www.adafruit.com', 'RPi 4 8GB (alt)',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', '7-inch Touchscreen Display',
        'User interface for printer control via KlipperScreen.',
        1, 'display', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Adafruit', 'https://www.adafruit.com', 'Raspberry Pi 7" Official',    true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',       'Waveshare 7" HDMI',           true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',       'Generic 7" capacitive touch',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Power Supply 24V 600W',
        'MeanWell for reliability. 600W handles 7 NEMA23 steppers + accessories. 24V bus for Kraken + peripherals.',
        1, 'PSU', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Mouser Electronics', 'https://mouser.com', 'MeanWell LRS-600-24',    true),
  (currval('parts_id_seq'), 'Digi-Key',           'https://digikey.com','MeanWell RSP-750-24',    true),
  (currval('parts_id_seq'), 'Amazon',             'https://amazon.com', 'Generic 24V 600W',       true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Emergency Stop Button',
        'Critical safety component. NC (normally-closed) contacts — pressing opens the circuit and kills 24V via contactor.',
        1, 'switch', 'buy', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',         'Mushroom E-stop NC',        true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com', 'Twist-release E-stop NC',   true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',           'Panel mount E-stop NC',     true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Cable Drag Chain (Sealed)',
        'Enclosed/sealed type for concrete dust protection. X-axis: 25x50mm ID, 1.5m. Y-axis: 25x38mm ID, 1.3m. Open-style chains will clog with concrete dust. igus E2 micro series is ideal for dusty environments.',
        3, 'meters total (X: 1.5m + Y: 1.3m)', 'buy', 80);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'igus',            'https://www.igus.com',  'E2 micro sealed drag chain — premium, dust-proof',  'https://www.igus.com/', true),
  (currval('parts_id_seq'), 'McMaster-Carr',   'https://mcmaster.com',  'Heavy duty sealed 35mm cable carrier',              NULL, true),
  (currval('parts_id_seq'), 'Self-Manufacture','',                      '3D Printed parametric sealed chain',                NULL, true);

-- ── Detailed Wiring Components (replaces vague "Wiring Kit") ──

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Shielded Motor Cable - Flex-Rated (18AWG 4C)',
        '4-conductor 18AWG, foil shield + drain, silicone jacket, continuous-flex drag-chain-rated. For X, Y, and extruder motors on moving axes. Critical for reliable StallGuard sensorless homing.',
        15, 'meters (1 spool)', 'buy', 100);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'igus',          'https://www.igus.com',     'chainflex CF211 — premium drag-chain-rated', true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',       '18AWG 4C shielded silicone flex cable',     true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',     'Continuous-flex shielded cable',             true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Shielded Motor Cable - Static (18AWG 4C)',
        '4-conductor 18AWG, foil shield + drain, PVC jacket, UL2464. For 4 stationary Z-axis motors. Shield drain connects at controller end only (star ground).',
        10, 'meters (1 spool)', 'buy', 110);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key',      'https://digikey.com',  'Alpha Wire or Belden UL2464 shielded 4C 18AWG', true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   '18AWG 4C foil-shielded cable',                  true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Shielded multi-conductor cable',                true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'GX16-4 Aviation Connector Sets',
        'Quick-disconnect for all 8 stepper motors. IP65 when mated — critical for concrete dust protection. Panel-mount female + inline male per set. Apply dielectric grease at assembly.',
        10, 'sets (8 needed + 2 spare)', 'buy', 120);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',  'GX16-4 male-inline + female-panel set', true),
  (currval('parts_id_seq'), 'Digi-Key', 'https://digikey.com', 'Amphenol equivalent circular connectors', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Power Wire — 12AWG Silicone (Red + Black)',
        'PSU 24V output to BTT Kraken main power input. 12AWG handles 25A max draw at 600W/24V. Also used for E-stop contactor power loop.',
        2, 'meters each color (4m total)', 'buy', 130);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   '12AWG silicone stranded wire (red + black)', true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', '12AWG stranded hookup wire',                 true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Distribution Wire — 18AWG (Red + Black)',
        '24V branch distribution, accessory power, E-stop signal loop. For internal control panel wiring.',
        6, 'meters total (3m each color)', 'buy', 135);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   '18AWG silicone hookup wire assortment', true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', '18AWG stranded hookup wire',            true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Ferrule Crimping Tool + Assortment Kit',
        'Every stranded wire into a screw terminal MUST have a ferrule — critical in high-vibration concrete printer. Expect to use ~100 ferrules.',
        1, 'kit', 'buy', 140);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon', 'https://amazon.com', 'IWISS or Wirefy ratcheting crimper + ferrule kit', true),
  (currval('parts_id_seq'), 'Amazon', 'https://amazon.com', 'Preciva ferrule crimping set',                     true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'IEC C14 Power Inlet w/ EMI Filter & Fuse',
        'Panel-mount AC inlet with integrated EMI filter, fuse holder (6A slow-blow for 120V), and rocker switch. Single mains entry point.',
        1, 'unit', 'buy', 150);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key', 'https://digikey.com', 'Schaffner or Qualtek IEC inlet w/ filter', true),
  (currval('parts_id_seq'), 'Mouser',   'https://mouser.com',  'TE Connectivity Corcom series',            true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',  'IEC C14 inlet fused + filtered',           true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        '24V Safety Contactor / Relay',
        'E-stop cuts 24V power via this contactor. NC E-stop loop controls the coil. 30A contacts minimum for 600W PSU output.',
        1, 'unit', 'buy', 155);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key',         'https://digikey.com',          'Omron or Schneider 24VDC coil contactor', true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com', 'IDEC or Fuji 24VDC relay',               true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',           '24V DC coil contactor 30A+',             true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        '24V-to-5V DC-DC Buck Converter (5A)',
        'Powers Raspberry Pi 5 and touchscreen from the 24V bus. RPi 5 draws up to 5A with peripherals. Use dedicated converter, NOT Kraken 5V output.',
        1, 'unit', 'buy', 160);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',      'Pololu 5V 5A step-down regulator',   true),
  (currval('parts_id_seq'), 'Digi-Key', 'https://digikey.com',     'Mean Well DDR-30G-5 DIN-rail mount', true),
  (currval('parts_id_seq'), 'Adafruit', 'https://www.adafruit.com','5V 5A buck converter breakout',      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'DIN-Rail Terminal Block Kit + Rail',
        '10-position terminal blocks, end stops, jumper bars, and 0.5m 35mm DIN rail. Star-ground bus bar for all shield drain wires.',
        1, 'kit', 'buy', 165);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key',         'https://digikey.com',          'Phoenix Contact UK series + rail',        true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',           'Dinkle DIN-rail terminal block kit',      true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com', 'DINnector terminal block set',            true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Nylon Cable Gland Assortment',
        'IP68 cable glands for every wire entering the control panel. Prevents concrete dust ingress. Mount on bottom/sides only. Sizes: PG7-PG13.5.',
        1, '50-pack assorted', 'buy', 170);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Nylon cable gland assortment PG7-PG13.5', true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Strain relief cable glands',              true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Snap-On Ferrite Cores (13mm ID)',
        'One per stepper motor cable at the controller end. Suppresses EMI that interferes with StallGuard sensorless homing.',
        8, 'pieces', 'buy', 175);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',  'Snap-on ferrite cores 13mm (8-pack)',    true),
  (currval('parts_id_seq'), 'Digi-Key', 'https://digikey.com', 'Fair-Rite or TDK snap ferrite',          true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Cable Sleeving, Labels & Tie Kit',
        '10m PET braided sleeving (1/2" + 1/4"), 100x UV-resistant cable ties, 30x screw-mount bases, self-laminating wire labels. Label both ends: M1-X, M2-YL, M3-YR, M4-Z1..M7-Z4, M8-EXT.',
        1, 'kit', 'buy', 180);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'PET sleeving + cable tie + label bundle', true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Braided sleeving, nylon ties, markers',   true);

-- ════════════════════════════════════════════════════════════
-- ██  CONCRETE EXTRUSION SYSTEM                            ██
-- ════════════════════════════════════════════════════════════

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Progressive Cavity Pump',
        'Core extrusion component. Purpose-built concrete 3D printing pumps from MAI, M-Tec, or StoneFlower are the proven options. Flow rate 0.7-24 L/min, grain size up to 2-6mm depending on model. If you want a US-sourced stepper-driven pump solution, leave a comment — at 10 commitments we will produce a small batch.',
        1, 'pump', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'MAI International (Austria)',
   'https://mai.at/en/product-range/3d-printing/mai-2pump-pictor-3d/',
   'MAI 2PUMP PICTOR-3D — 0.7-15.5 L/min, grain up to 2mm, analog 0-10V control. Industry standard for research and startups.',
   true),
  (currval('parts_id_seq'), 'M-Tec (Germany)',
   'https://m-tec.com/',
   'M-Tec P20 3DCP — 3-24 L/min, grain up to 4mm, Modbus-RTU control. Higher throughput for large-format printing.',
   true),
  (currval('parts_id_seq'), 'StoneFlower 3D (Germany)',
   'https://www.stoneflower3d.com/store/concrete-3d-printer/',
   'Automated concrete pump — up to 10 L/min, 40 bar, aggregates up to 6mm. Includes operator training.',
   true),
  (currval('parts_id_seq'), 'Community Interest: US-Sourced Stepper Pump',
   '',
   'INTEREST CHECK — stepper-driven PC pump using NEMA23 + external driver + Kraken stepper signal. Need 10 commitments for a small production batch.',
   true);

-- ── DIY Stepper-Driven Pump Components ───────────────────

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'NEMA23 Planetary Geared Stepper (10:1) — Pump Drive',
        'Drives the PC pump rotor. 10:1 planetary gearbox provides ~6Nm output torque at low RPM (50-300 RPM). Must be high-torque variant (76mm+ body, 2.8A+). Controlled via Kraken extruder stepper output.',
        1, 'motor + gearbox assembly', 'buy', 15);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US',
   'https://www.omc-stepperonline.com/nema-23-stepper-motor-l-76mm-gear-ratio-10-1-high-precision-planetary-gearbox-23hs30-2804s-hg10',
   '23HS30-2804S-HG10 — 76mm body, 2.8A, 10:1 HG series. 6Nm max output. 15 arc-min backlash.',
   'https://www.omc-stepperonline.com/download', true),
  (currval('parts_id_seq'), 'StepperOnline US',
   'https://www.omc-stepperonline.com/nema-23-stepper-motor-l-76mm-gear-ratio-10-1-mg-series-planetary-gearbox-23hs30-2904s-mg10',
   '23HS30-2904S-MG10 — MG series budget option, 30 arc-min backlash.',
   'https://www.omc-stepperonline.com/download', true),
  (currval('parts_id_seq'), 'Amazon',
   'https://amazon.com',
   'STEPPERONLINE NEMA23 10:1 planetary — also on Amazon Prime.',
   NULL, true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'External Stepper Driver — TMC5160 (48V High Current)',
        'Drives geared pump motor via Kraken STEP/DIR/EN signals. External driver recommended: higher current (6A) and 48V for more torque. SPI enables StallGuard for material blockage alarm.',
        1, 'driver board', 'buy', 16);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'West3D (US)',
   'https://west3d.com/products/tmc5160-pro-48v-stepper-motor-driver-drivers-btt',
   'BTT TMC5160 Pro V1.2 — 48V, external MOSFETs, SPI.',
   'https://github.com/bigtreetech/TMC5160T-Pro', true),
  (currval('parts_id_seq'), 'Amazon',
   'https://amazon.com',
   'BIGTREETECH TMC5160T Pro V1.0 — 48V, SPI/UART.',
   NULL, true),
  (currval('parts_id_seq'), 'Digi-Key',
   'https://digikey.com',
   'Analog Devices TMC5160-BOB evaluation board.',
   NULL, true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'Progressive Cavity Pump Element (Rotor + Stator)',
        'Core pumping element — chrome-plated SS rotor inside elastomer stator. For mortar/concrete with aggregates up to 2-6mm. Stator: Buna Nitrile (NBR) for concrete, EPDM for alkaline. Expect stator replacement every 200-500 hours.',
        1, 'rotor + stator set', 'buy', 17);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Continental Ultra Pumps (Missouri)',
   'https://www.continentalultrapumps.com/store/CP22-progressing-cavity-pump.html',
   'CP22 pump — 0.4-4.9 GPM, 100 PSI, 3/4" NPT, chrome SS rotor, Buna stator. Smallest US-made PC pump. Call 636-456-6006.',
   true),
  (currval('parts_id_seq'), 'Progressive Cavity Parts (US)',
   'https://www.progressivecavityparts.com/',
   'Aftermarket replacement rotors and stators for Moyno, Seepex, Netzsch, Continental.',
   true),
  (currval('parts_id_seq'), 'Seepex (via US distributors)',
   'https://www.seepex.com/en-nam/products/pumps/standard-progressive-cavity-pumps/bn-pump-with-block-design/',
   'BN series — industrial PC pump. US distributors: Tencarva, Edelmann, Cummins-Wagner.',
   true),
  (currval('parts_id_seq'), 'Community Interest: Custom Batch',
   '',
   'INTEREST CHECK — small-batch custom rotor+stator. CNC SS rotor + cast NBR stator. Need 10 commitments.',
   true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'Pump Drive Coupling — Universal Joint + Connecting Rod',
        'Converts motor rotation to rotor orbital motion. PC pump rotors orbit eccentrically — a rigid shaft will break. Use gear-type universal joint or double-cardan joint.',
        1, 'coupling assembly', 'buy', 18);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, step_url, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',
   'https://mcmaster.com',
   'Miniature universal joints + flex couplings. Match bore sizes to motor output and rotor drive shaft.',
   'https://mcmaster.com', true),
  (currval('parts_id_seq'), 'Amazon',
   'https://amazon.com',
   'Stainless steel universal joint couplers (8-14mm bores) + jaw couplings.',
   NULL, true),
  (currval('parts_id_seq'), 'Self-Manufacture',
   '',
   'CNC or metal SLS custom connecting rod. STL files in repo /cad/pump/ directory.',
   NULL, true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'Pump Housing & Bearing Assembly',
        'Encloses rotor/stator and provides bearing support. Must handle axial thrust. If using Continental CP22, housing is included. For DIY: CNC aluminum + sealed bearings.',
        1, 'assembly', 'cnc', 19);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Continental Ultra Pumps',
   'https://www.continentalultrapumps.com/',
   'CP22 housing included with pump purchase.',
   true),
  (currval('parts_id_seq'), 'McMaster-Carr',
   'https://mcmaster.com',
   'DIY: Flanged ball bearings (sealed, SS) + Schedule 40 SS pipe as stator housing.',
   true),
  (currval('parts_id_seq'), 'SendCutSend',
   'https://sendcutsend.com',
   'CNC-machined aluminum end plates and motor mount. Upload DXF/STEP from repo.',
   true),
  (currval('parts_id_seq'), 'Self-Manufacture',
   '',
   '3D printed PETG prototype housing for testing only — concrete slurry is abrasive.',
   true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'NEMA23 Motor for Extruder (Direct Drive Option)',
        'Direct-drive option (no gearbox) for simpler pump setups or peristaltic pump. If building the stepper-driven PC pump, use the "NEMA23 Planetary Geared Stepper (10:1)" instead — the gearbox is essential for PC pump torque.',
        1, 'motor', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 4.5Nm 8mm shaft',        true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com',      'NEMA23 Geared 10:1',            true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 3Nm standard 8mm shaft', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        '48V Power Supply for Pump Driver (Optional)',
        'Only needed if running external TMC5160 pump driver at 48V. Mean Well LRS-200-48 provides dedicated 48V for the geared stepper. Not needed if running pump from Kraken onboard driver at 24V.',
        1, 'PSU', 'buy', 21);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Mouser Electronics', 'https://mouser.com',  'Mean Well LRS-200-48 — 48V 200W enclosed',  true),
  (currval('parts_id_seq'), 'Digi-Key',           'https://digikey.com', 'Mean Well UHP-200-48 — 48V slim profile',   true),
  (currval('parts_id_seq'), 'Amazon',             'https://amazon.com',  'Mean Well 48V PSU — also on Amazon Prime',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Material Hopper 20-Liter',
        'Material reservoir above the pump. HDPE or stainless for concrete compatibility. Printable in PETG for testing.',
        1, 'hopper', 'print', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',  'Stainless steel hopper',  true),
  (currval('parts_id_seq'), 'US Plastic Corp',  'https://usplastic.com', 'HDPE funnel 5-gal',       true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                      '3D Printed PETG hopper',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Concrete Nozzle Assembly',
        'Critical for print quality. Replaceable-tip design recommended for different layer widths (20-40mm).',
        1, 'assembly', 'cnc', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local Machine Shop', '', 'Custom machined brass nozzle',      true),
  (currval('parts_id_seq'), 'Local Machine Shop', '', 'Stainless steel nozzle',            true),
  (currval('parts_id_seq'), 'SendCutSend',  'https://sendcutsend.com', 'Replaceable tip design', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Tubing & Quick Fittings',
        'Pump to nozzle material flow. Reinforced hose rated for concrete slurry. Counter-weighted to reduce gantry loading.',
        1, 'kit', 'buy', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',   'https://mcmaster.com',  'Reinforced concrete-rated hose + fittings', true),
  (currval('parts_id_seq'), 'US Plastic Corp', 'https://usplastic.com', 'Food-grade reinforced hose set',            true),
  (currval('parts_id_seq'), 'Grainger',        'https://grainger.com',  'Industrial reinforced concrete hose',       true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Extruder Mounting Bracket',
        'Mounts nozzle assembly to X-axis carriage. Lightweight — printhead is only 1.5kg target.',
        1, 'bracket', 'print', 60);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum plate',       true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed reinforced',    true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Laser cut steel',          true);

-- ════════════════════════════════════════════════════════════
-- ██  FASTENERS & HARDWARE                                 ██
-- ════════════════════════════════════════════════════════════

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'M5 Socket Head Cap Screws',
        'Primary structural fasteners for 20-series V-Slot frame. M5 is the standard for 6mm slot width.',
        1, '500pc kit', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',  'M5 SHCS assortment 500pc',          true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',    'M5 SHCS basic set 500pc',           true),
  (currval('parts_id_seq'), 'Bolt Depot',    'https://boltdepot.com', 'M5 stainless kit 500pc',            true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'M3 Socket Head Cap Screws',
        'Electronics mounting and small parts.',
        1, '500pc kit', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',  'M3 SHCS assortment 500pc',  true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',    'M3 SHCS basic set 500pc',   true),
  (currval('parts_id_seq'), 'Digi-Key',      'https://digikey.com',   'M3 electronics kit',        true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'Washers & Lock Washers Assorted',
        'Prevent loosening from vibration. Nord-Lock recommended for structural joints.',
        1, 'kit', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Complete M3-M8 kit',     true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Basic washer set',       true),
  (currval('parts_id_seq'), 'Grainger',      'https://grainger.com', 'Nord-Lock washers',      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'Heat-Set Inserts M3/M5',
        'Essential for threaded connections in 3D printed parts.',
        1, '200pc kit', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Brass insert kit M3+M5',              true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Economy inserts M3+M5',               true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Premium knurled (CNC Kitchen style)', true);

-- ════════════════════════════════════════════════════════════
-- ██  OPTIONAL UPGRADES                                    ██
-- ════════════════════════════════════════════════════════════

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'Polycarbonate Enclosure Panels',
        'Dust containment for indoor use. Sized to frame dimensions.',
        1, 'set', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'TAP Plastics',    'https://tapplastics.com', 'Clear polycarbonate sheets — cut to size', true),
  (currval('parts_id_seq'), 'US Plastic Corp', 'https://usplastic.com',   'Corrugated plastic panels',               true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'LED Work Lighting',
        'Work area illumination — 24V LED strips powered from main bus.',
        1, 'kit', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon', 'https://amazon.com', '24V LED strip 5m',  true),
  (currval('parts_id_seq'), 'Amazon', 'https://amazon.com', 'RGB LED strip 24V', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'Camera Module for Monitoring',
        'Remote print monitoring via KlipperScreen or Mainsail.',
        1, 'camera', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Adafruit', 'https://www.adafruit.com', 'RPi Camera v3',         true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',       'USB Webcam 1080p',      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'HEPA Air Filtration',
        'Concrete dust particle capture for indoor operation.',
        1, 'system', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Grainger', 'https://grainger.com', 'HEPA filter box fan unit',  true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',   'DIY HEPA filter + fan',     true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'Carbon Fiber Stiffener Bar (2080 Rail)',
        'Bonds to outer 80mm face of 2080 V-Slot for 20-30% additional stiffness on long spans. Structural epoxy + clamp cure. Only needed if 2m span deflection is a concern.',
        4, 'bars (2m each)', 'buy', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'DragonPlate',   'https://dragonplate.com',  'CF flat bar — various widths and thicknesses', true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',       'Carbon fiber flat bar 20x3mm or 30x3mm',       true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',     'Carbon fiber rectangular bar stock',            true);

-- ════════════════════════════════════════════════════════════
-- ██  MIGRATION 005 — Agent-Readable Metadata               ██
-- ════════════════════════════════════════════════════════════
-- Run this block on existing databases. Safe to re-run (IF NOT EXISTS).
-- New installs already have these columns in the CREATE TABLE above.

ALTER TABLE parts ADD COLUMN IF NOT EXISTS mpn TEXT;
ALTER TABLE parts ADD COLUMN IF NOT EXISTS substitute_ok BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE parts ADD COLUMN IF NOT EXISTS exclude_from_kit BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE supplier_options ADD COLUMN IF NOT EXISTS sku TEXT;

-- Mark the community interest / informational rows as excluded from kit
UPDATE parts SET exclude_from_kit = true
WHERE name ILIKE '%community interest%'
   OR name ILIKE '%interest check%'
   OR (mfg_type = 'buy' AND qty = 0);

-- Seed MPNs for parts with known manufacturer part numbers
UPDATE parts SET mpn = '23HS45-4204S1', substitute_ok = false
WHERE name ILIKE '%NEMA23 Stepper Motor (X-axis%';

UPDATE parts SET mpn = '23HS45-4204S1', substitute_ok = false
WHERE name ILIKE '%NEMA23 Stepper Motor (Y-axis%';

UPDATE parts SET mpn = '23HS45-4204S1', substitute_ok = false
WHERE name ILIKE '%NEMA23 Stepper Motor (Z-axis%';

UPDATE parts SET mpn = '23HS30-2804S-HG10', substitute_ok = false
WHERE name ILIKE '%Planetary Geared Stepper%';

UPDATE parts SET mpn = 'LRS-600-24', substitute_ok = false
WHERE name ILIKE '%Power Supply 24V 600W%';

UPDATE parts SET mpn = 'LRS-200-48', substitute_ok = false
WHERE name ILIKE '%48V Power Supply%';

UPDATE parts SET mpn = 'BIGTREETECH-Kraken-V1.1', substitute_ok = false
WHERE name ILIKE '%BTT Kraken%';

UPDATE parts SET mpn = 'SC1112', substitute_ok = false
WHERE name ILIKE '%Raspberry Pi 5%';

UPDATE parts SET mpn = 'FN9260-6-06'
WHERE name ILIKE '%IEC C14 Power Inlet%';

UPDATE parts SET mpn = 'HSC8-6-4A'
WHERE name ILIKE '%Ferrule Crimping Tool%';

UPDATE parts SET mpn = 'GX16-4'
WHERE name ILIKE '%GX16-4 Aviation%';

-- ════════════════════════════════════════════════════════════
-- ██  MIGRATION 006 — Populate SKUs & Full Product URLs      ██
-- ════════════════════════════════════════════════════════════
-- Adds supplier-specific SKUs (ASINs, DigiKey PNs, Bulkman3D SKUs)
-- and replaces bare domain URLs with actual product page links.
-- Safe to re-run (UPDATE ... WHERE matches are idempotent).

-- ── BTT Kraken — Amazon ASIN ──
UPDATE supplier_options SET sku = 'B0CQX9XJ4W',
  product_url = 'https://www.amazon.com/BIGTREETECH-Control-Onboard-8%C3%97TMC2160-High-Performance/dp/B0CQX9XJ4W'
WHERE supplier_name = 'Amazon'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%BTT Kraken%' LIMIT 1)
  AND notes ILIKE '%BTT Kraken%';

-- ── Raspberry Pi 5 8GB — Amazon ASIN ──
UPDATE supplier_options SET sku = 'B0CK2FCG1K',
  product_url = 'https://www.amazon.com/Raspberry-Pi-8GB-SC1112-Quad-core/dp/B0CK2FCG1K'
WHERE supplier_name ILIKE '%Amazon%CanaKit%'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Raspberry Pi 5%' LIMIT 1);

-- ── MeanWell LRS-600-24 — DigiKey & Mouser SKUs ──
UPDATE supplier_options SET sku = '1866-LRS-600-24-ND',
  product_url = 'https://www.digikey.com/en/products/detail/mean-well-usa-inc/LRS-600-24/16394242'
WHERE supplier_name = 'Digi-Key'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Power Supply 24V 600W%' LIMIT 1);

UPDATE supplier_options SET sku = '709-LRS-600-24',
  product_url = 'https://www.mouser.com/ProductDetail/MEAN-WELL/LRS-600-24'
WHERE supplier_name = 'Mouser Electronics'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Power Supply 24V 600W%' LIMIT 1);

-- ── GX16-4 Connectors — Amazon ASINs ──
UPDATE supplier_options SET sku = 'B07174LCGR',
  product_url = 'https://www.amazon.com/Female-Connector-GX16-4-Silver-Aviation/dp/B07174LCGR'
WHERE supplier_name = 'Amazon'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%GX16-4 Aviation%' LIMIT 1)
  AND notes ILIKE '%male-inline%';

UPDATE supplier_options SET sku = 'B089YT5P3G'
WHERE supplier_name = 'Amazon'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%GX16-4 Aviation%' LIMIT 1)
  AND sku IS NULL;

-- ── Ferrule Crimper — Amazon ASINs ──
UPDATE supplier_options SET sku = 'B00ODSJGSW',
  product_url = 'https://www.amazon.com/IWISS-Self-Adjusting-AWG23-10-End-Sleeves-Ferrule/dp/B00ODSJGSW'
WHERE supplier_name = 'Amazon'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Ferrule Crimping%' LIMIT 1)
  AND notes ILIKE '%IWISS%';

UPDATE supplier_options SET sku = 'B00H950AK4',
  product_url = 'https://www.amazon.com/IWISS-Crimper-Plier-Self-adjustable-Crimping/dp/B00H950AK4'
WHERE supplier_name = 'Amazon'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Ferrule Crimping%' LIMIT 1)
  AND notes ILIKE '%Preciva%';

-- ── IEC C14 Inlet — DigiKey & Mouser ──
UPDATE supplier_options SET sku = 'FN9260-6-06',
  product_url = 'https://www.digikey.com/en/product-highlight/s/schaffner/fn9260-series-power-entry-modules'
WHERE supplier_name = 'Digi-Key'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%IEC C14%' LIMIT 1);

-- ── Bulkman3D V-Wheels — product URLs ──
UPDATE supplier_options SET sku = 'VW02-RS',
  product_url = 'https://bulkman3d.com/product/vk0012/'
WHERE supplier_name = 'Bulkman3D'
  AND part_id IN (SELECT id FROM parts WHERE name ILIKE '%V-Groove%Wheels%' OR name ILIKE '%V-Groove Delrin%');

-- ── Bulkman3D Extrusions — product URLs ──
UPDATE supplier_options SET product_url = 'https://bulkman3d.com/product/v-slot-2080/'
WHERE supplier_name = 'Bulkman3D'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%2080 V-Slot%1200mm%' LIMIT 1)
  AND product_url = 'https://bulkman3d.com/product/v-slot-2080/';

UPDATE supplier_options SET product_url = 'https://bulkman3d.com/product/v-slot-2040/'
WHERE supplier_name = 'Bulkman3D'
  AND part_id IN (SELECT id FROM parts WHERE name ILIKE '%2040 V-Slot%')
  AND product_url = 'https://bulkman3d.com/product/v-slot-2040/';

-- ── Eccentric Spacers — Amazon ASIN ──
UPDATE supplier_options SET sku = 'B01D2FAV44',
  product_url = 'https://www.amazon.com/Eccentric-Spacers-Full-Size-Wheels/dp/B01D2FAV44'
WHERE supplier_name = 'Amazon'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Eccentric Spacers%' LIMIT 1);

-- ── Snap-On Ferrite Cores — Amazon ASIN ──
UPDATE supplier_options SET sku = 'B01N0AV746',
  product_url = 'https://www.amazon.com/Ferrite-Noise-Filter-Cable-3-5mm/dp/B01N0AV746'
WHERE supplier_name = 'Amazon'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Ferrite Cores%' LIMIT 1);

-- ── NEMA23 Stepper Motors — StepperOnline product URLs ──
UPDATE supplier_options SET sku = '23HS45-4204S1',
  product_url = 'https://www.omc-stepperonline.com/nema-23-bipolar-3nm-425oz-in-8mm-diameter-4-2a-57x57x113mm-4-wires-stepper-motor-23hs45-4204s1'
WHERE supplier_name = 'StepperOnline US'
  AND notes ILIKE '%3Nm 8mm%'
  AND product_url = 'https://www.omc-stepperonline.com';

-- ── Planetary Geared Stepper — StepperOnline SKUs ──
UPDATE supplier_options SET sku = '23HS30-2804S-HG10'
WHERE supplier_name = 'StepperOnline US'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Planetary Geared%' LIMIT 1)
  AND notes ILIKE '%HG10%';

UPDATE supplier_options SET sku = '23HS30-2904S-MG10'
WHERE supplier_name = 'StepperOnline US'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%Planetary Geared%' LIMIT 1)
  AND notes ILIKE '%MG10%';

-- ── Continental CP22 Pump ──
UPDATE supplier_options SET sku = 'CP22'
WHERE supplier_name ILIKE '%Continental%'
  AND part_id IN (SELECT id FROM parts WHERE name ILIKE '%Progressive Cavity Pump Element%');

-- ── TMC5160 Pro — West3D ──
UPDATE supplier_options SET sku = 'TMC5160T-Pro-V1.2'
WHERE supplier_name ILIKE '%West3D%'
  AND part_id = (SELECT id FROM parts WHERE name ILIKE '%External Stepper Driver%TMC5160%' LIMIT 1);
