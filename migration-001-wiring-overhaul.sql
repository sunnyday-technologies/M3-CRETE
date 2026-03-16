-- ============================================================
-- Migration 001: Remove Endstop Switches, Replace Wiring Kit
-- with detailed wiring line items. Update Progressive Cavity
-- Pump with concrete-specific suppliers.
-- ============================================================

-- 1. DELETE Mechanical Endstop Switches (using StallGuard sensorless homing)
DELETE FROM supplier_options
WHERE part_id IN (
  SELECT id FROM parts
  WHERE name = 'Mechanical Endstop Switches'
    AND category = 'Electronics & Control System'
);
DELETE FROM parts
WHERE name = 'Mechanical Endstop Switches'
  AND category = 'Electronics & Control System';

-- 2. DELETE old "Wiring Kit & Cable Management" (too vague)
DELETE FROM supplier_options
WHERE part_id IN (
  SELECT id FROM parts
  WHERE name = 'Wiring Kit & Cable Management'
    AND category = 'Electronics & Control System'
);
DELETE FROM parts
WHERE name = 'Wiring Kit & Cable Management'
  AND category = 'Electronics & Control System';

-- 3. INSERT detailed wiring line items
-- Using sort_order 100+ to place them after existing electronics parts

-- ── Stepper Motor Cable — Flex-Rated Shielded ──────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Shielded Motor Cable - Flex-Rated (18AWG 4C)',
        '4-conductor 18AWG, foil shield + drain, silicone jacket, continuous-flex drag-chain-rated. For X, Y, and extruder motors on moving axes. Critical for reliable StallGuard sensorless homing.',
        15, 'meters (1 spool)', 'buy', 100);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'igus',          'https://www.igus.com',     'chainflex CF211 — premium drag-chain-rated, best reliability', true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',       '18AWG 4C shielded silicone flex cable — verify flex rating',  true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',     'Continuous-flex shielded cable (catalog: multi-conductor)',    true);

-- ── Stepper Motor Cable — Static Shielded ──────────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Shielded Motor Cable - Static (18AWG 4C)',
        '4-conductor 18AWG, foil shield + drain, PVC jacket, UL2464. For 4 stationary Z-axis motors. Shield drain connects at controller end only (star ground).',
        10, 'meters (1 spool)', 'buy', 110);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key',      'https://digikey.com',  'Alpha Wire or Belden UL2464 shielded 4C 18AWG',  true),
  (currval('parts_id_seq'), 'Amazon',         'https://amazon.com',   '18AWG 4C foil-shielded cable',                   true),
  (currval('parts_id_seq'), 'McMaster-Carr',  'https://mcmaster.com', 'Shielded multi-conductor cable',                 true);

-- ── GX16-4 Aviation Connector Sets ─────────────────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'GX16-4 Aviation Connector Sets',
        'Quick-disconnect for all 8 stepper motors. IP65 when mated — critical for concrete dust protection. Panel-mount female socket + inline male plug per set. Apply dielectric grease at assembly.',
        10, 'sets (8 needed + 2 spare)', 'buy', 120);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',       'GX16-4 male-inline + female-panel set',       true),
  (currval('parts_id_seq'), 'Digi-Key',      'https://digikey.com',      'Amphenol equivalent circular connectors',     true);

-- ── Power Wiring (12AWG + 18AWG) ───────────────────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Power Wire — 12AWG Silicone (Red + Black)',
        'PSU 24V output to BTT Kraken main power input. 12AWG handles 25A max draw at 600W/24V. Silicone jacket for heat resistance inside enclosure. Also used for E-stop contactor power loop.',
        2, 'meters each color (4m total)', 'buy', 130);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',       '12AWG silicone stranded wire (red + black)',          true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',     '12AWG stranded hookup wire',                         true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Distribution Wire — 18AWG (Red + Black)',
        '24V branch distribution, accessory power, E-stop signal loop. For internal control panel wiring between terminal blocks, buck converter, and accessories.',
        6, 'meters total (3m each color)', 'buy', 135);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',       '18AWG silicone hookup wire assortment',      true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com',     '18AWG stranded hookup wire',                 true);

-- ── Ferrule Crimping Kit ───────────────────────────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Ferrule Crimping Tool + Assortment Kit',
        'Ratcheting crimper + 800-1200 assorted bootlace ferrules (22-10AWG). Every stranded wire into a screw terminal MUST have a ferrule — especially critical in a high-vibration concrete printer. Expect to use ~100 ferrules.',
        1, 'kit', 'buy', 140);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',  'IWISS or Wirefy ratcheting crimper + ferrule kit',  true),
  (currval('parts_id_seq'), 'Amazon',   'https://amazon.com',  'Preciva ferrule crimping set',                      true);

-- ── Control Panel Electrical Components ────────────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'IEC C14 Power Inlet w/ EMI Filter & Fuse',
        'Panel-mount AC inlet with integrated EMI filter, fuse holder (6A slow-blow for 120V), and rocker switch. Single entry point for mains power into the control enclosure.',
        1, 'unit', 'buy', 150);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key',      'https://digikey.com',  'Schaffner or Qualtek IEC inlet w/ filter',   true),
  (currval('parts_id_seq'), 'Mouser',        'https://mouser.com',   'TE Connectivity Corcom series',              true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'IEC C14 inlet fused + filtered',             true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        '24V Safety Contactor / Relay',
        'E-stop cuts 24V power via this contactor. NC E-stop loop controls the coil — when pressed, contactor opens, killing all 24V. 30A contacts minimum for 600W PSU output.',
        1, 'unit', 'buy', 155);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key',         'https://digikey.com',          'Omron or Schneider 24VDC coil contactor',     true),
  (currval('parts_id_seq'), 'AutomationDirect',  'https://automationdirect.com', 'IDEC or Fuji 24VDC relay',                   true),
  (currval('parts_id_seq'), 'Amazon',            'https://amazon.com',           '24V DC coil contactor 30A+',                 true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        '24V-to-5V DC-DC Buck Converter (5A)',
        'Powers Raspberry Pi 5 and 7-inch touchscreen from the 24V bus. RPi 5 draws up to 5A with peripherals. Use a dedicated converter, not the Kraken 5V output.',
        1, 'unit', 'buy', 160);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',    'https://amazon.com',     'Pololu 5V 5A step-down regulator',              true),
  (currval('parts_id_seq'), 'Digi-Key',  'https://digikey.com',    'Mean Well DDR-30G-5 or similar DIN-rail mount', true),
  (currval('parts_id_seq'), 'Adafruit',  'https://www.adafruit.com','5V 5A buck converter breakout',                true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'DIN-Rail Terminal Block Kit + Rail',
        '10-position terminal blocks, end stops, jumper bars, and 0.5m 35mm DIN rail. Star-ground bus bar for all shield drain wires. Clean power distribution inside control panel.',
        1, 'kit', 'buy', 165);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Digi-Key',      'https://digikey.com',  'Phoenix Contact UK series terminal blocks + rail',   true),
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Dinkle DIN-rail terminal block kit',                 true),
  (currval('parts_id_seq'), 'AutomationDirect','https://automationdirect.com', 'DINnector terminal block set',             true);

INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Nylon Cable Gland Assortment',
        'IP68 cable glands for every wire entering the control panel enclosure. Prevents concrete dust ingress. Mount on bottom/sides of enclosure only (never top). Sizes: PG7, PG9, PG11, PG13.5.',
        1, '50-pack assorted', 'buy', 170);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'Nylon cable gland assortment PG7-PG13.5',  true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Strain relief cable glands',               true);

-- ── EMI Suppression ────────────────────────────────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Snap-On Ferrite Cores (13mm ID)',
        'One per stepper motor cable at the controller end. Suppresses EMI that interferes with StallGuard sensorless homing. Especially important if using a VFD for the pump — keep VFD cables separated by 150mm minimum.',
        8, 'pieces', 'buy', 175);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',    'https://amazon.com',   'Snap-on ferrite cores 13mm (8-pack or 10-pack)',  true),
  (currval('parts_id_seq'), 'Digi-Key',  'https://digikey.com',  'Fair-Rite or TDK snap ferrite',                   true);

-- ── Cable Labeling & Sleeving ──────────────────────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Electronics & Control System',
        'Cable Sleeving, Labels & Tie Kit',
        '10m PET braided sleeving (1/2" + 1/4"), 100x 8" UV-resistant cable ties, 30x screw-mount bases, self-laminating wire labels. Label both ends of every cable: M1-X, M2-YL, M3-YR, M4-Z1...M7-Z4, M8-EXT, PWR-24V, SIG-ESTOP.',
        1, 'kit', 'buy', 180);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Amazon',        'https://amazon.com',   'PET sleeving + cable tie + label bundle',           true),
  (currval('parts_id_seq'), 'McMaster-Carr', 'https://mcmaster.com', 'Braided sleeving, nylon ties, wire markers',        true);

-- 4. UPDATE Cable Drag Chain description with better specs
UPDATE parts
SET description = 'Enclosed/sealed type for concrete dust protection. X-axis: 25x50mm ID, 1.5m. Y-axis: 25x38mm ID, 1.3m. Open-style chains will clog with concrete dust. igus E2 micro series is ideal for dusty environments.',
    qty = 3,
    unit = 'meters total (X: 1.5m + Y: 1.3m)'
WHERE name = 'Cable Drag Chain'
  AND category = 'Electronics & Control System';

-- ============================================================
-- 5. UPDATE Progressive Cavity Pump — real concrete 3D printing suppliers
-- ============================================================

-- Delete old generic pump supplier options
DELETE FROM supplier_options
WHERE part_id IN (
  SELECT id FROM parts
  WHERE name = 'Progressive Cavity Pump'
    AND category = 'Concrete Extrusion System'
);

-- Update the part description
UPDATE parts
SET description = 'Core extrusion component. Purpose-built concrete 3D printing pumps from MAI or StoneFlower are the proven options. Flow rate 0.7-15 L/min, grain size up to 2-6mm depending on model. If you want a US-sourced stepper-driven pump solution, leave a comment — at 10 commitments we will produce a small batch using NEMA23 + external driver controlled by the Kraken stepper signal for precise volumetric control.'
WHERE name = 'Progressive Cavity Pump'
  AND category = 'Concrete Extrusion System';

-- Insert updated supplier options (no pricing)
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  ((SELECT id FROM parts WHERE name = 'Progressive Cavity Pump' AND category = 'Concrete Extrusion System'),
   'MAI International (Austria)',
   'https://mai.at/en/product-range/3d-printing/mai-2pump-pictor-3d/',
   'MAI 2PUMP PICTOR-3D — purpose-built for concrete 3D printing. 0.7-15.5 L/min, grain up to 2mm, MAI CODUR wear-resistant materials. Industry standard for research and startups.',
   true),
  ((SELECT id FROM parts WHERE name = 'Progressive Cavity Pump' AND category = 'Concrete Extrusion System'),
   'StoneFlower 3D (Germany)',
   'https://www.stoneflower3d.com/store/concrete-3d-printer/',
   'Automated concrete pump — up to 10 L/min, 40 bar, aggregates up to 6mm. Compatible with their mixing print head (2-component). Includes operator training.',
   true),
  ((SELECT id FROM parts WHERE name = 'Progressive Cavity Pump' AND category = 'Concrete Extrusion System'),
   'Community Interest: US-Sourced Stepper Pump',
   '',
   'INTEREST CHECK — stepper-driven progressive cavity pump using NEMA23 + external driver + Kraken stepper signal for precise volumetric control. Need 10 commitments for a small production batch. Leave a comment or submit a supplier suggestion to register interest.',
   true);
