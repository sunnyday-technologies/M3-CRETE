-- ============================================================
-- Concrete 3D Printer BOM — Supabase Schema
-- Run this in the Supabase SQL Editor to set up the database.
-- ============================================================

-- 1. TABLES
-- ----------------------------------------------------------

CREATE TABLE parts (
  id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  category   TEXT    NOT NULL,
  name       TEXT    NOT NULL,
  description TEXT,
  qty        INTEGER NOT NULL DEFAULT 1,
  unit       TEXT    NOT NULL DEFAULT 'pieces',
  mfg_type   TEXT    NOT NULL CHECK (mfg_type IN ('buy', 'print', 'cnc')),
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE supplier_options (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  part_id       BIGINT       NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  supplier_name TEXT         NOT NULL,
  product_url   TEXT,
  notes         TEXT,
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

-- Parts: public read, maintainer write
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

-- Supplier options: public reads approved, submitters see own pending, maintainers see all
CREATE POLICY "supplier_read" ON supplier_options
  FOR SELECT USING (
    approved = true
    OR auth.uid() = submitted_by
    OR auth.uid() IN (SELECT user_id FROM maintainers)
  );

-- Authenticated users can insert (always unapproved, always as themselves)
CREATE POLICY "supplier_insert" ON supplier_options
  FOR INSERT WITH CHECK (
    auth.uid() IS NOT NULL
    AND submitted_by = auth.uid()
    AND approved = false
  );

-- Maintainers can update (approve) and delete (reject)
CREATE POLICY "supplier_maintainer_update" ON supplier_options
  FOR UPDATE USING (
    auth.uid() IN (SELECT user_id FROM maintainers)
  );

CREATE POLICY "supplier_maintainer_delete" ON supplier_options
  FOR DELETE USING (
    auth.uid() IN (SELECT user_id FROM maintainers)
  );

-- Maintainers table: authenticated can read (for client-side role checks)
CREATE POLICY "maintainers_read" ON maintainers
  FOR SELECT USING (auth.uid() IS NOT NULL);

-- 4. SEED DATA
-- ----------------------------------------------------------
-- All seed supplier_options are pre-approved with no submitter attribution.
-- Prices from the original BOM are intentionally omitted.

-- Helper: we use currval('parts_id_seq') to reference the last-inserted part.

-- ---- Frame & Structure - Aluminum Extrusions ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame & Structure - Aluminum Extrusions', '4040 T-Slot Aluminum Extrusion',
        'Main frame verticals and horizontals', 8, '6ft lengths', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), '8020.net',  'https://8020.net',          '4040 Series 15',  true),
  (currval('parts_id_seq'), 'TNutz',     'https://www.tnutz.com',     '4040 T-slot',     true),
  (currval('parts_id_seq'), 'MiSUMi',    'https://us.misumi-ec.com',  '4040 extrusion',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame & Structure - Aluminum Extrusions', '4020 T-Slot Aluminum Extrusion',
        'Cross bracing, gantry rails, and supports', 10, '6ft lengths', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), '8020.net',  'https://8020.net',          '4020 Series 15',  true),
  (currval('parts_id_seq'), 'TNutz',     'https://www.tnutz.com',     '4020 T-slot',     true),
  (currval('parts_id_seq'), 'MiSUMi',    'https://us.misumi-ec.com',  '4020 extrusion',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame & Structure - Aluminum Extrusions', '2020 T-Slot Aluminum Extrusion',
        'Carriage mounts and accessory rails', 6, '6ft lengths', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), '8020.net', 'https://8020.net',          '2020 Series 15',          true),
  (currval('parts_id_seq'), 'TNutz',    'https://www.tnutz.com',     '2020 T-slot',             true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',        '2020 from US seller',     true);

-- ---- Frame Hardware & Brackets ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame Hardware & Brackets', 'Heavy Duty Corner Brackets',
        'Frame corner connections - printable saves $200+', 32, 'pieces', 'print', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), '8020.net',        'https://8020.net',    'Cast aluminum bracket',   true),
  (currval('parts_id_seq'), 'McMaster-Carr',   'https://mcmaster.com','Steel L-bracket',         true),
  (currval('parts_id_seq'), 'Self-Manufacture','',                    '3D Printed ABS/Nylon',    true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame Hardware & Brackets', 'T-Slot Drop-In Nuts M6',
        '300 total - essential for all frame mounting', 3, 'packs of 100', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), '8020.net',      'https://8020.net',    'Spring-loaded',     true),
  (currval('parts_id_seq'), 'TNutz',         'https://www.tnutz.com','Economy pack',     true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com','Standard',          true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Frame Hardware & Brackets', 'Adjustable Leveling Feet M16',
        'Critical for leveling on uneven floors', 4, 'pieces', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Heavy duty 1000lb',        true),
  (currval('parts_id_seq'), 'Grainger',      'https://grainger.com', 'Vibration dampening',      true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Standard M16',             true);

-- ---- X-Axis Motion System ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'NEMA23 Stepper Motor (X-axis)',
        'Standard stepper - TMC5160 StallGuard for sensorless homing', 1, 'motor', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US',  'https://www.omc-stepperonline.com', 'NEMA23 3Nm',              true),
  (currval('parts_id_seq'), 'StepperOnline US',  'https://www.omc-stepperonline.com', 'NEMA23 4.5Nm High Torque',true),
  (currval('parts_id_seq'), 'AutomationDirect',  'https://automationdirect.com',      'NEMA23 3Nm',              true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'GT2 Timing Belt 10mm (Reinforced)',
        'X-axis drive belt - buy extra for spares', 10, 'meters', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',      'https://mcmaster.com',              'Gates PowerGrip GT2',    true),
  (currval('parts_id_seq'), 'Amazon - US Stock',  'https://amazon.com',                'Fiberglass core GT2',    true),
  (currval('parts_id_seq'), 'StepperOnline US',   'https://www.omc-stepperonline.com', 'Standard rubber GT2',    true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'GT2 Pulley 20-Tooth 8mm Bore',
        'Drive and idler pulleys - metal recommended', 4, 'pulleys', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Aluminum 20T',          true),
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'Steel 20T',             true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                                  '3D Printed reinforced', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'V-Groove Delrin Wheels',
        'Dust-resistant, critical for concrete', 8, 'wheels', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',    'https://amazon.com',         'Xtreme V-wheel',       true),
  (currval('parts_id_seq'), 'RobotDigg', 'https://www.robotdigg.com',  'Delrin wheel kit',     true),
  (currval('parts_id_seq'), 'MiSUMi',   'https://us.misumi-ec.com',   'Polycarbonate',        true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('X-Axis Motion System', 'X-Axis Carriage Plate Assembly',
        'Print saves $70+ with CF-Nylon/ABS', 1, 'assembly', 'print', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum 6061 6mm',           true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed Carbon Fiber Nylon',   true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Water-jet cut steel',             true);

-- ---- Dual Y-Axis Motion System ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'NEMA23 Stepper Motor (Y-axis)',
        'Dual motors for anti-racking - TMC5160 StallGuard compatible', 2, 'motors', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 3Nm',              true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 4.5Nm High Torque',true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com',      'NEMA23 3Nm',              true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'GT2 Timing Belt 10mm (Reinforced)',
        'Dual Y-axis belts - high load application', 12, 'meters', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',     'https://mcmaster.com',              'Gates PowerGrip GT2',  true),
  (currval('parts_id_seq'), 'Amazon - US Stock', 'https://amazon.com',                'Fiberglass core GT2',  true),
  (currval('parts_id_seq'), 'StepperOnline US',  'https://www.omc-stepperonline.com', 'Standard rubber GT2',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'GT2 Pulley 20-Tooth 8mm Bore',
        'Multiple pulleys needed for dual Y system', 8, 'pulleys', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Aluminum 20T',          true),
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'Steel 20T',             true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                                  '3D Printed reinforced', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'V-Groove Delrin Wheels',
        'More wheels = better load distribution', 16, 'wheels', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',    'https://amazon.com',        'Xtreme V-wheel',    true),
  (currval('parts_id_seq'), 'RobotDigg', 'https://www.robotdigg.com', 'Delrin wheel kit',  true),
  (currval('parts_id_seq'), 'MiSUMi',   'https://us.misumi-ec.com',  'Polycarbonate',     true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Dual Y-Axis Motion System', 'Y-Axis Gantry Plates',
        'Ginger G1 style - print saves $160+', 2, 'plates', 'print', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum 8mm',               true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed CF-Nylon Reinforced', true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Laser cut steel',                true);

-- ---- Quad Z-Axis System (Self-Tramming) ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'NEMA23 Stepper Motor (Z-axis)',
        'Four independent motors for auto-tramming via Klipper Z_TILT_ADJUST', 4, 'motors', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 3Nm',              true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 4.5Nm High Torque',true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com',      'NEMA23 3Nm',              true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'TR12x3 Lead Screw 1200mm',
        'Full height Z-axis lead screws', 4, 'screws', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'RobotDigg',    'https://www.robotdigg.com', 'TR12x3 Standard',          true),
  (currval('parts_id_seq'), 'Amazon - US',  'https://amazon.com',        'TR12x3 Anti-backlash',     true),
  (currval('parts_id_seq'), 'Dumpster CNC', 'https://www.dumpstercnc.com','SFU1204 Ball Screw',      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'TR12 Lead Screw Nut Block',
        'Brass for precision, Delrin for cost', 4, 'nut blocks', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'RobotDigg',       'https://www.robotdigg.com', 'Brass anti-backlash nut', true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',        'Delrin POM nut',          true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                          '3D Printed nut housing',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'Flexible Shaft Coupler 8mm-12mm',
        'Motor to lead screw connection', 4, 'couplers', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon - US',      'https://amazon.com',                'Aluminum flex coupler', true),
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'Oldham coupling',       true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Helical beam',          true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'Pillow Block Bearing FL001 (12mm)',
        'Top & bottom supports for each Z screw', 8, 'bearings', 'buy', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com', 'Sealed bearing block',      true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',   'Standard FL001',            true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                     '3D Printed bearing housing',true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Quad Z-Axis System (Self-Tramming)', 'Z-Axis Motor Mounts',
        'Print saves $90 for all 4 mounts', 4, 'mounts', 'print', 60);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum mount',   true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed PETG/ABS',  true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Laser cut steel',      true);

-- ---- Electronics & Control System ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'BTT Kraken Mainboard',
        '8 stepper drivers - perfect for this build', 1, 'board', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Filastruder', 'https://www.filastruder.com', 'BTT Kraken v1.0',       true),
  (currval('parts_id_seq'), 'Amazon',      'https://amazon.com',          'BTT Kraken',             true),
  (currval('parts_id_seq'), 'Filastruder', 'https://www.filastruder.com', 'BTT Octopus Pro (alt)',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Raspberry Pi 5 (8GB RAM)',
        'Runs Klipper firmware', 1, 'computer', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Adafruit',          'https://www.adafruit.com', 'RPi 5 8GB',        true),
  (currval('parts_id_seq'), 'Amazon - CanaKit',  'https://amazon.com',       'RPi 5 8GB',        true),
  (currval('parts_id_seq'), 'Adafruit',          'https://www.adafruit.com', 'RPi 4 8GB (alt)',   true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', '7-inch Touchscreen Display',
        'User interface for printer control', 1, 'display', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Adafruit', 'https://www.adafruit.com', 'Raspberry Pi 7" Official',    true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',       'Waveshare 7" HDMI',           true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',       'Generic 7" capacitive',       true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Power Supply 24V 600W',
        'MeanWell for reliability, generic for budget', 1, 'PSU', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Mouser Electronics', 'https://mouser.com', 'MeanWell LRS-600-24',    true),
  (currval('parts_id_seq'), 'Digi-Key',           'https://digikey.com','MeanWell RSP-750-24',    true),
  (currval('parts_id_seq'), 'Amazon',             'https://amazon.com', 'Generic 24V 600W',       true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Emergency Stop Button',
        'Critical safety component', 1, 'switch', 'buy', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',         'Mushroom E-stop',       true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com', 'Twist-release E-stop',  true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',           'Panel mount E-stop',    true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Mechanical Endstop Switches',
        'X, Y, 4xZ homing + spares', 10, 'switches', 'buy', 60);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key', 'https://digikey.com', 'Omron micro switch',         true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',  'Generic endstop pack',       true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',  'Inductive sensor NPN',       true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Wiring Kit & Cable Management',
        'Power cables, signal wires, cable chain', 1, 'kit', 'buy', 70);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'Complete wire kit',    true),
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',              'DIY bulk wire',        true),
  (currval('parts_id_seq'), 'Amazon',           'https://amazon.com',                'Premium sleeved',      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System', 'Cable Drag Chain',
        'Protects cables during motion', 6, 'meters', 'buy', 80);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon - US',      'https://amazon.com',  '25mm cable chain',             true),
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com','Heavy duty 35mm',              true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                    '3D Printed parametric chain',  true);

-- ---- Concrete Extrusion System ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Progressive Cavity Pump',
        'Core extrusion component', 1, 'pump', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Moyno (Ohio)',     'https://www.moyno.com',    'Moyno 500 EZStrip',       true),
  (currval('parts_id_seq'), 'Graco Industrial', 'https://graco.com',        'PC Pump 500ml/rev',       true),
  (currval('parts_id_seq'), 'Cole-Parmer',      'https://coleparmer.com',   'Peristaltic pump alt',    true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'NEMA23 Motor for Extruder',
        'Drives the pump - needs high torque', 1, 'motor', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 4.5Nm',           true),
  (currval('parts_id_seq'), 'AutomationDirect', 'https://automationdirect.com',      'NEMA23 Geared 10:1',     true),
  (currval('parts_id_seq'), 'StepperOnline US', 'https://www.omc-stepperonline.com', 'NEMA23 3Nm standard',    true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Material Hopper 20-Liter',
        'Material reservoir - PETG food-safe', 1, 'hopper', 'print', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',    'https://mcmaster.com',  'Stainless steel hopper',  true),
  (currval('parts_id_seq'), 'US Plastic Corp',  'https://usplastic.com', 'HDPE funnel 5-gal',       true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                      '3D Printed PETG hopper',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Concrete Nozzle Assembly',
        'Critical for print quality', 1, 'assembly', 'cnc', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local Machine Shop', '', 'Custom machined brass',     true),
  (currval('parts_id_seq'), 'Local Machine Shop', '', 'Stainless steel nozzle',    true),
  (currval('parts_id_seq'), 'SendCutSend',  'https://sendcutsend.com', 'Replaceable tip design', true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Tubing & Quick Fittings',
        'Pump to nozzle material flow', 1, 'kit', 'buy', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',   'https://mcmaster.com',  'Complete tube kit',         true),
  (currval('parts_id_seq'), 'US Plastic Corp', 'https://usplastic.com', 'Food-grade hose set',       true),
  (currval('parts_id_seq'), 'Grainger',        'https://grainger.com',  'Reinforced concrete hose',  true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System', 'Extruder Mounting Bracket',
        'Mounts pump to carriage', 1, 'bracket', 'print', 60);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Local CNC Shop',  '',                        'CNC Aluminum plate',       true),
  (currval('parts_id_seq'), 'Self-Manufacture', '',                        '3D Printed reinforced',    true),
  (currval('parts_id_seq'), 'SendCutSend',     'https://sendcutsend.com', 'Laser cut steel',          true);

-- ---- Fasteners & Hardware ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'M6 Socket Head Cap Screws',
        'Primary structural fasteners', 1, '500pc kit', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',  'Assortment 500pc',          true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',    'Basic set 500pc',           true),
  (currval('parts_id_seq'), 'Bolt Depot',    'https://boltdepot.com', 'Stainless kit 500pc',       true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'M5 Socket Head Cap Screws',
        'Secondary mounting hardware', 1, '500pc kit', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',  'Assortment 500pc',          true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',    'Basic set 500pc',           true),
  (currval('parts_id_seq'), 'Bolt Depot',    'https://boltdepot.com', 'Stainless kit 500pc',       true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'M3 Socket Head Cap Screws',
        'Electronics mounting and small parts', 1, '500pc kit', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',  'Assortment 500pc',      true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',    'Basic set 500pc',       true),
  (currval('parts_id_seq'), 'Digi-Key',      'https://digikey.com',   'Electronics kit',       true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'Washers & Lock Washers Assorted',
        'Prevent loosening from vibration', 1, 'kit', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Complete M3-M8 kit',     true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Basic washer set',       true),
  (currval('parts_id_seq'), 'Grainger',      'https://grainger.com', 'Nord-Lock washers',      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Fasteners & Hardware', 'Heat-Set Inserts M3/M5',
        'Essential for 3D printed parts', 1, '200pc kit', 'buy', 50);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Brass insert kit',       true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Economy inserts',        true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Premium knurled (CNC Kitchen)', true);

-- ---- Optional Upgrades ----

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'Polycarbonate Enclosure Panels',
        'Dust containment for indoor use', 1, 'set', 'buy', 10);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'TAP Plastics',    'https://tapplastics.com', 'Clear polycarbonate sheets',  true),
  (currval('parts_id_seq'), 'US Plastic Corp', 'https://usplastic.com',   'Corrugated plastic',          true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'LED Work Lighting',
        'Work area illumination', 1, 'kit', 'buy', 20);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon', 'https://amazon.com', '24V LED strip 5m',  true),
  (currval('parts_id_seq'), 'Amazon', 'https://amazon.com', 'RGB LED strip',     true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'Camera Module for Monitoring',
        'Remote print monitoring', 1, 'camera', 'buy', 30);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Adafruit', 'https://www.adafruit.com', 'RPi Camera v3',         true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',       'USB Webcam 1080p',      true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Optional Upgrades', 'HEPA Air Filtration',
        'Concrete dust particle capture', 1, 'system', 'buy', 40);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Grainger', 'https://grainger.com', 'HEPA filter box',      true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',   'DIY filter + fan',     true);
