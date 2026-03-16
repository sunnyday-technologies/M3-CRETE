-- ============================================================
-- Migration 002: Add DIY Stepper-Driven Pump Components
-- Based on StoneFlower design: NEMA23 geared stepper + PC pump
-- element + external driver, all US-sourceable.
-- ============================================================

-- The existing "Progressive Cavity Pump" part stays as-is with
-- MAI/StoneFlower/Community Interest options (turnkey solutions).
-- These new parts are the individual components for a DIY build.

-- ── NEMA23 Geared Stepper Motor (Pump Drive) ──────────────
-- StoneFlower uses NEMA23 3A with planetary gearbox.
-- 10:1 ratio gives ~6Nm output at low RPM — perfect for
-- driving a PC pump rotor at 50-300 RPM.
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'NEMA23 Planetary Geared Stepper (10:1) — Pump Drive',
        'Drives the PC pump rotor. 10:1 planetary gearbox provides ~6Nm output torque at low RPM (50-300 RPM pump speed). Must be high-torque variant (76mm+ body, 2.8A+). This replaces the "NEMA23 Motor for Extruder" for the stepper-driven pump approach. Controlled via Kraken extruder stepper output for precise volumetric extrusion.',
        1, 'motor + gearbox assembly', 'buy', 15);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'StepperOnline US',
   'https://www.omc-stepperonline.com/nema-23-stepper-motor-l-76mm-gear-ratio-10-1-high-precision-planetary-gearbox-23hs30-2804s-hg10',
   '23HS30-2804S-HG10 — 76mm body, 2.8A, 10:1 HG series planetary. 6Nm max permissible output torque. High precision (15 arc-min backlash).',
   true),
  (currval('parts_id_seq'), 'StepperOnline US',
   'https://www.omc-stepperonline.com/nema-23-stepper-motor-l-76mm-gear-ratio-10-1-mg-series-planetary-gearbox-23hs30-2904s-mg10',
   '23HS30-2904S-MG10 — MG series, 2.9A, 10:1 planetary. Budget option with 30 arc-min backlash. Adequate for pump drive.',
   true),
  (currval('parts_id_seq'), 'Amazon',
   'https://amazon.com',
   'STEPPERONLINE NEMA23 10:1 planetary gearbox stepper — also available via Amazon US Prime.',
   true);

-- ── External High-Current Stepper Driver (TMC5160) ────────
-- The Kraken has onboard TMC5160 drivers but they max out at
-- ~3A. For the pump motor under load, an external driver gives
-- headroom and can run at higher voltage (48V) for more torque
-- at speed. SPI interface lets Klipper control it identically
-- to onboard drivers (StallGuard, StealthChop, SpreadCycle).
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'External Stepper Driver — TMC5160 (48V High Current)',
        'Drives the geared pump motor via Kraken STEP/DIR/EN signals. External driver recommended for pump load: higher current capacity (up to 6A) and 48V support for more torque headroom. SPI interface enables StallGuard for stall detection (material blockage alarm). If using Kraken onboard driver at 3A, this part is optional but recommended.',
        1, 'driver board', 'buy', 16);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'West3D (US)',
   'https://west3d.com/products/tmc5160-pro-48v-stepper-motor-driver-drivers-btt',
   'BTT TMC5160 Pro V1.2 — 48V, external MOSFETs, SPI interface. Purpose-built for high-power steppers.',
   true),
  (currval('parts_id_seq'), 'Amazon',
   'https://amazon.com',
   'BIGTREETECH TMC5160T Pro V1.0 — 48V high-voltage stepper driver, SPI/UART.',
   true),
  (currval('parts_id_seq'), 'Digi-Key',
   'https://digikey.com',
   'Analog Devices TMC5160-BOB evaluation board — reference design for custom integration.',
   true);

-- ── Progressive Cavity Pump Element (Rotor + Stator) ──────
-- This is the core pumping element. The rotor orbits inside
-- the stator, creating progressing cavities that push material.
-- For concrete/mortar with aggregates up to 6mm, need a pump
-- element with sufficient cavity size.
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'Progressive Cavity Pump Element (Rotor + Stator)',
        'Core pumping element — chrome-plated stainless steel rotor orbiting inside an elastomer stator. For mortar/concrete with aggregates up to 2-6mm. Stator material: Buna Nitrile (NBR) for morite/concrete, EPDM for alkaline mixes. Expect stator replacement every 200-500 hours depending on aggregate abrasiveness. This is the hardest component to source small-quantity in the US — see community interest option.',
        1, 'rotor + stator set', 'buy', 17);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Continental Ultra Pumps (Missouri)',
   'https://www.continentalultrapumps.com/store/CP22-progressing-cavity-pump.html',
   'CP22 pump — 0.4-4.9 GPM, 100 PSI, 3/4" NPT, chrome SS rotor, Buna stator. Light-duty but smallest US-made PC pump. Rebuild kits available with replacement rotor+stator. Call 636-456-6006 for component pricing.',
   true),
  (currval('parts_id_seq'), 'Progressive Cavity Parts (US)',
   'https://www.progressivecavityparts.com/',
   'Aftermarket replacement rotors and stators for Moyno, Seepex, Netzsch, Continental. Domestically-sourced steel. Can match rotor/stator to your pump housing geometry.',
   true),
  (currval('parts_id_seq'), 'Seepex (via US distributors)',
   'https://www.seepex.com/en-nam/products/pumps/standard-progressive-cavity-pumps/bn-pump-with-block-design/',
   'BN series — smallest industrial PC pump, 30 L/hr to 500 m³/hr, up to 96 bar. US distributors: Tencarva, Edelmann, Cummins-Wagner. Overkill but bulletproof.',
   true),
  (currval('parts_id_seq'), 'Community Interest: Custom Batch',
   '',
   'INTEREST CHECK — small-batch custom rotor+stator set sized for this printer. CNC-machined SS rotor + cast NBR stator. Need 10 commitments. Submit a supplier suggestion to register interest.',
   true);

-- ── Pump Universal Joint / Flex Coupling ──────────────────
-- PC pump rotors orbit (not just rotate) — the connecting rod
-- between motor shaft and rotor needs a universal joint or
-- flexible coupling to accommodate the eccentric motion.
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'Pump Drive Coupling — Universal Joint + Connecting Rod',
        'Converts motor rotation to rotor orbital motion. PC pump rotors orbit eccentrically inside the stator — a rigid shaft connection will break. Use a gear-type universal joint (best for high thrust loads) or double-cardan joint. The connecting rod length must match your rotor pitch. For DIY: a flexible jaw coupling (L-type) at the motor end + a pin-type universal joint at the rotor end works.',
        1, 'coupling assembly', 'buy', 18);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'McMaster-Carr',
   'https://mcmaster.com',
   'Miniature universal joints + flex couplings. Search "miniature universal joint" and "jaw coupling". Match bore sizes to motor output shaft and rotor drive shaft.',
   true),
  (currval('parts_id_seq'), 'Amazon',
   'https://amazon.com',
   'Stainless steel universal joint couplers (various bore sizes 8-14mm) + L-shaped jaw couplings.',
   true),
  (currval('parts_id_seq'), 'Self-Manufacture',
   '',
   'CNC or 3D print (metal SLS) a custom connecting rod matched to your specific rotor geometry. STL files available in the repo /cad/pump/ directory.',
   true);

-- ── Pump Housing / Bearing Block ──────────────────────────
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        'Pump Housing & Bearing Assembly',
        'Encloses the rotor/stator and provides bearing support for the drive shaft. Must handle axial thrust from the pumping action. If using a Continental CP22, the housing is included. For DIY: CNC aluminum housing with sealed bearings, or adapt a pipe fitting as the stator housing with flanged bearing blocks.',
        1, 'assembly', 'cnc', 19);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Continental Ultra Pumps',
   'https://www.continentalultrapumps.com/',
   'CP22 housing included with pump purchase — cast iron or stainless steel.',
   true),
  (currval('parts_id_seq'), 'McMaster-Carr',
   'https://mcmaster.com',
   'DIY: Flanged ball bearings (sealed, stainless) + Schedule 40 SS pipe as stator housing + NPT fittings for inlet/outlet.',
   true),
  (currval('parts_id_seq'), 'SendCutSend',
   'https://sendcutsend.com',
   'CNC-machined aluminum end plates and motor mount. Upload DXF/STEP from repo /cad/pump/ directory.',
   true),
  (currval('parts_id_seq'), 'Self-Manufacture',
   '',
   '3D printed PETG prototype housing for testing. Not suitable for production use — concrete slurry is abrasive.',
   true);

-- ── 48V Power Supply (for external pump driver) ───────────
-- Only needed if using the external TMC5160 driver at 48V.
-- The main 24V PSU stays for the Kraken and everything else.
INSERT INTO parts (category, name, description, qty, unit, mfg_type, sort_order)
VALUES ('Concrete Extrusion System',
        '48V Power Supply for Pump Driver (Optional)',
        'Only needed if running the external TMC5160 pump driver at 48V for maximum torque. Provides dedicated power for the geared pump stepper. 48V at 150-200W is sufficient for a single NEMA23. If running the pump motor from the Kraken onboard driver at 24V, this is not needed.',
        1, 'PSU', 'buy', 21);
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  (currval('parts_id_seq'), 'Mouser Electronics',
   'https://mouser.com',
   'Mean Well LRS-200-48 — 48V 200W enclosed PSU. Reliable, widely used in CNC.',
   true),
  (currval('parts_id_seq'), 'Digi-Key',
   'https://digikey.com',
   'Mean Well UHP-200-48 — 48V 200W slim profile.',
   true),
  (currval('parts_id_seq'), 'Amazon',
   'https://amazon.com',
   'Mean Well 48V PSU — also available via Amazon Prime.',
   true);

-- ── Update the original "NEMA23 Motor for Extruder" ───────
-- Clarify that this is the non-geared option for simpler setups
UPDATE parts
SET description = 'Direct-drive option (no gearbox) for simpler pump setups or peristaltic pump. If building the stepper-driven progressive cavity pump, use the "NEMA23 Planetary Geared Stepper (10:1)" instead — the gearbox is essential for the torque required to drive a PC pump rotor through concrete.'
WHERE name = 'NEMA23 Motor for Extruder'
  AND category = 'Concrete Extrusion System';
