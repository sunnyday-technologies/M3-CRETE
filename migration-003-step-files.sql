-- ============================================================
-- Migration 003: Add STEP File URL Tracking
-- Cross-references supplier options with 3D CAD model
-- availability. Enables CAD Library view for building
-- the complete digital model of the printer.
-- ============================================================

-- 1. Add step_url column to supplier_options
ALTER TABLE supplier_options ADD COLUMN IF NOT EXISTS step_url TEXT;

-- 2. Add a comment for documentation
COMMENT ON COLUMN supplier_options.step_url IS
  'URL to download STEP/STP 3D model from this supplier. NULL if no CAD available.';

-- ============================================================
-- Populate known STEP file URLs
-- Matched on part name + supplier name for idempotent updates.
-- ============================================================

-- ── Frame & Structure — Aluminum Extrusions ──────────────────

-- 4080 V-Slot Extrusion → 8020 Inc
UPDATE supplier_options SET step_url = 'https://8020.net/shop/40-8016.html'
WHERE supplier_name = '8020 Inc (US Manufacturer)'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%4080%' AND category LIKE 'Frame%Extrusion%');

-- 4080 V-Slot → Misumi
UPDATE supplier_options SET step_url = 'https://us.misumi-ec.com/vona2/mech/M1500000000/M1501000000/M1501010000/'
WHERE supplier_name LIKE 'Misumi%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%4080%' AND category LIKE 'Frame%Extrusion%');

-- 2040 V-Slot Extrusion → 8020 Inc
UPDATE supplier_options SET step_url = 'https://8020.net/shop/20-2040.html'
WHERE supplier_name = '8020 Inc (US Manufacturer)'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%2040%' AND category LIKE 'Frame%Extrusion%');

-- 2040 V-Slot → Misumi
UPDATE supplier_options SET step_url = 'https://us.misumi-ec.com/vona2/mech/M1500000000/M1501000000/M1501010000/'
WHERE supplier_name LIKE 'Misumi%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%2040%' AND category LIKE 'Frame%Extrusion%');

-- 2020 Extrusion → 8020 Inc
UPDATE supplier_options SET step_url = 'https://8020.net/shop/20-2020.html'
WHERE supplier_name = '8020 Inc (US Manufacturer)'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%2020%' AND category LIKE 'Frame%Extrusion%');

-- ── Frame Hardware & Brackets ────────────────────────────────

-- Cast Corner Brackets → McMaster-Carr
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Corner Bracket%' AND category LIKE 'Frame Hardware%');

-- T-Nuts → McMaster-Carr
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%T-Nut%' AND category LIKE 'Frame Hardware%');

-- Gusset Plates → McMaster/SendCutSend
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Gusset%' AND category LIKE 'Frame Hardware%');

UPDATE supplier_options SET step_url = 'https://sendcutsend.com'
WHERE supplier_name LIKE 'SendCutSend%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Gusset%' AND category LIKE 'Frame Hardware%');

-- ── X-Axis Motion System ─────────────────────────────────────

-- MGN15 Linear Rail → Hiwin (official CAD downloads)
UPDATE supplier_options SET step_url = 'https://www.hiwin.com/linear-guideways/mgn/mgn15.html'
WHERE supplier_name LIKE 'Hiwin%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%MGN15%Linear Rail%');

-- MGN15H Carriage Blocks → Hiwin
UPDATE supplier_options SET step_url = 'https://www.hiwin.com/linear-guideways/mgn/mgn15.html'
WHERE supplier_name LIKE 'Hiwin%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%MGN15H%Carriage%');

-- NEMA23 Motor for X → StepperOnline (product page has STEP download)
UPDATE supplier_options SET step_url = 'https://www.omc-stepperonline.com/nema-23-bipolar-45mm-body-3a'
WHERE supplier_name LIKE 'StepperOnline%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%NEMA23%' AND name LIKE '%X-Axis%');

-- GT2 Timing Belt → Gates (official CAD library)
UPDATE supplier_options SET step_url = 'https://www.gates.com/us/en/resources/engineering-tools/design-flex-pro.html'
WHERE supplier_name LIKE 'Gates%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%GT2%Belt%');

-- GT2 Pulleys → McMaster-Carr / StepperOnline
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%GT2%Pulley%' OR name LIKE '%Idler%Pulley%');

UPDATE supplier_options SET step_url = 'https://www.omc-stepperonline.com/accessories/pulleys'
WHERE supplier_name LIKE 'StepperOnline%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%GT2%Pulley%');

-- ── Dual Y-Axis Motion System ────────────────────────────────

-- V-Groove Wheels → OpenBuilds / McMaster
UPDATE supplier_options SET step_url = 'https://openbuildspartstore.com/v-slot-mini-v-wheel-kit/'
WHERE supplier_name LIKE 'OpenBuilds%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%V-Groove%Wheel%');

UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%V-Groove%Wheel%');

-- Eccentric Spacers → OpenBuilds
UPDATE supplier_options SET step_url = 'https://openbuildspartstore.com/eccentric-spacer/'
WHERE supplier_name LIKE 'OpenBuilds%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Eccentric%Spacer%');

-- NEMA23 Motors for Y → StepperOnline
UPDATE supplier_options SET step_url = 'https://www.omc-stepperonline.com/nema-23-bipolar-45mm-body-3a'
WHERE supplier_name LIKE 'StepperOnline%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%NEMA23%' AND (name LIKE '%Y-Axis%' OR name LIKE '%Y %'));

-- ── Quad Z-Axis System ───────────────────────────────────────

-- Lead Screws / Ball Screws → McMaster-Carr
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Lead Screw%' OR name LIKE '%Ball Screw%');

-- Lead Screw Nut Blocks → McMaster-Carr
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Lead Screw Nut%' OR name LIKE '%Anti-Backlash Nut%');

-- NEMA23 Motors for Z → StepperOnline
UPDATE supplier_options SET step_url = 'https://www.omc-stepperonline.com/nema-23-bipolar-45mm-body-3a'
WHERE supplier_name LIKE 'StepperOnline%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%NEMA23%' AND name LIKE '%Z%');

-- Flexible Couplings → McMaster / StepperOnline
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Flexible Coupling%' OR name LIKE '%Shaft Coupling%');

UPDATE supplier_options SET step_url = 'https://www.omc-stepperonline.com/accessories/flexible-coupling'
WHERE supplier_name LIKE 'StepperOnline%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Flexible Coupling%' OR name LIKE '%Shaft Coupling%');

-- Flanged Bearings → McMaster-Carr
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Flanged Bearing%' OR name LIKE '%Pillow Block%');

-- ── Electronics & Control System ─────────────────────────────

-- BTT Kraken → BigTreeTech GitHub (official STEP files)
UPDATE supplier_options SET step_url = 'https://github.com/bigtreetech/Kraken/tree/master/Hardware'
WHERE supplier_name LIKE '%BigTreeTech%' OR supplier_name LIKE '%BTT%' OR supplier_name LIKE '%West3D%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Kraken%');

-- Raspberry Pi 5 → RPi Foundation (official mechanical drawings)
UPDATE supplier_options SET step_url = 'https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf'
WHERE (supplier_name LIKE '%CanaKit%' OR supplier_name LIKE '%Vilros%' OR supplier_name LIKE '%PiShop%')
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Raspberry Pi 5%');

-- 7-inch Touchscreen → RPi Foundation
UPDATE supplier_options SET step_url = 'https://datasheets.raspberrypi.com/display/7-inch-display-mechanical-drawing.pdf'
WHERE part_id IN (SELECT id FROM parts WHERE name LIKE '%7%Touchscreen%' OR name LIKE '%7%Display%');

-- Mean Well PSU (24V) → Mean Well (official 3D models)
UPDATE supplier_options SET step_url = 'https://www.meanwell.com/webapp/product/search.aspx?prod=LRS-350'
WHERE supplier_name LIKE '%Mouser%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Power Supply%' AND name LIKE '%24V%');

UPDATE supplier_options SET step_url = 'https://www.meanwell.com/webapp/product/search.aspx?prod=LRS-350'
WHERE supplier_name LIKE '%Digi-Key%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Power Supply%' AND name LIKE '%24V%');

-- E-Stop Mushroom Button → McMaster-Carr / AutomationDirect
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%E-Stop%' OR name LIKE '%Emergency%Stop%');

UPDATE supplier_options SET step_url = 'https://www.automationdirect.com/cad-drawings'
WHERE supplier_name LIKE 'AutomationDirect%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%E-Stop%' OR name LIKE '%Emergency%Stop%');

-- Cable Drag Chain → igus (official CAD configurator)
UPDATE supplier_options SET step_url = 'https://www.igus.com/info/e-chains-3d-cad-configurator'
WHERE supplier_name LIKE 'igus%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Drag Chain%');

-- GX16-4 Connectors → McMaster alternatives have CAD
UPDATE supplier_options SET step_url = 'https://www.digikey.com/en/models'
WHERE supplier_name LIKE 'Digi-Key%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%GX16%');

-- IEC C14 Inlet → Digi-Key / Mouser (have 3D model downloads)
UPDATE supplier_options SET step_url = 'https://www.digikey.com/en/models'
WHERE supplier_name LIKE 'Digi-Key%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%IEC C14%');

UPDATE supplier_options SET step_url = 'https://www.mouser.com/Connectors/_/N-5g3v?P=1z0z7pt'
WHERE supplier_name LIKE 'Mouser%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%IEC C14%');

-- 24V Safety Contactor → Digi-Key / AutomationDirect
UPDATE supplier_options SET step_url = 'https://www.digikey.com/en/models'
WHERE supplier_name LIKE 'Digi-Key%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Safety Contactor%' OR name LIKE '%24V%Relay%');

UPDATE supplier_options SET step_url = 'https://www.automationdirect.com/cad-drawings'
WHERE supplier_name LIKE 'AutomationDirect%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Safety Contactor%' OR name LIKE '%24V%Relay%');

-- DIN-Rail Terminal Blocks → Digi-Key / AutomationDirect
UPDATE supplier_options SET step_url = 'https://www.phoenixcontact.com/en-us/products'
WHERE supplier_name LIKE 'Digi-Key%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%DIN-Rail Terminal%');

UPDATE supplier_options SET step_url = 'https://www.automationdirect.com/cad-drawings'
WHERE supplier_name LIKE 'AutomationDirect%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%DIN-Rail Terminal%');

-- Snap-On Ferrite Cores → Digi-Key (Fair-Rite has CAD)
UPDATE supplier_options SET step_url = 'https://www.digikey.com/en/models'
WHERE supplier_name LIKE 'Digi-Key%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Ferrite%');

-- ── Concrete Extrusion System ────────────────────────────────

-- NEMA23 Planetary Geared Stepper → StepperOnline (product pages have STEP)
UPDATE supplier_options SET step_url = 'https://www.omc-stepperonline.com/nema-23-stepper-motor-l-76mm-gear-ratio-10-1-high-precision-planetary-gearbox-23hs30-2804s-hg10'
WHERE supplier_name LIKE 'StepperOnline%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%NEMA23 Planetary Geared%');

-- External TMC5160 Driver → West3D / BTT GitHub
UPDATE supplier_options SET step_url = 'https://github.com/bigtreetech/TMC5160T-Pro/tree/master/Hardware'
WHERE supplier_name LIKE 'West3D%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%External Stepper Driver%TMC5160%');

-- Progressive Cavity Pump Element → Continental
UPDATE supplier_options SET step_url = 'https://www.continentalultrapumps.com/store/CP22-progressing-cavity-pump.html'
WHERE supplier_name LIKE 'Continental%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Progressive Cavity Pump Element%');

-- Pump Drive Coupling → McMaster-Carr
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Pump Drive Coupling%' OR name LIKE '%Universal Joint%');

-- Pump Housing → McMaster / SendCutSend
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Pump Housing%' OR name LIKE '%Bearing Assembly%');

UPDATE supplier_options SET step_url = 'https://sendcutsend.com'
WHERE supplier_name LIKE 'SendCutSend%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Pump Housing%' OR name LIKE '%Bearing Assembly%');

-- Self-Manufacture parts → repo CAD directory
UPDATE supplier_options SET step_url = '/cad/pump/'
WHERE supplier_name LIKE 'Self-Manufacture%'
  AND part_id IN (SELECT id FROM parts WHERE category = 'Concrete Extrusion System');

-- 48V PSU → Mean Well (official 3D models)
UPDATE supplier_options SET step_url = 'https://www.meanwell.com/webapp/product/search.aspx?prod=LRS-200-48'
WHERE supplier_name LIKE 'Mouser%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%48V Power Supply%');

UPDATE supplier_options SET step_url = 'https://www.meanwell.com/webapp/product/search.aspx?prod=UHP-200-48'
WHERE supplier_name LIKE 'Digi-Key%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%48V Power Supply%');

-- ── Nozzle / Print Head ──────────────────────────────────────

-- Print head components → McMaster
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE name LIKE '%Nozzle%' OR name LIKE '%Print Head%');

-- ── Fasteners & Hardware (McMaster for all) ──────────────────
UPDATE supplier_options SET step_url = 'https://mcmaster.com'
WHERE supplier_name LIKE 'McMaster%'
  AND part_id IN (SELECT id FROM parts WHERE category = 'Fasteners & Hardware');

-- ============================================================
-- Summary: After running this migration, query to verify:
-- SELECT p.name, so.supplier_name, so.step_url
-- FROM supplier_options so
-- JOIN parts p ON p.id = so.part_id
-- WHERE so.step_url IS NOT NULL
-- ORDER BY p.category, p.sort_order;
-- ============================================================
