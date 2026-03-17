-- Migration 004: Add M-Tec P20 3DCP as progressive cavity pump option
-- The m-tec connect P20 3DCP is one of the two most widely used pumps
-- in concrete 3D printing worldwide (alongside the MAI PICTOR-3D).
-- Standalone pump-only unit (no mixer) — you supply pre-mixed material.
-- Modbus-RTU control interface for integration with motion systems.
-- Note: 400V/50Hz European power — requires VFD or transformer for US 480V/60Hz.

-- Add M-Tec P20 3DCP supplier option
INSERT INTO supplier_options (part_id, supplier_name, product_url, notes, approved)
VALUES
  ((SELECT id FROM parts WHERE name = 'Progressive Cavity Pump' AND category = 'Concrete Extrusion System'),
   'M-Tec (Germany)',
   'https://www.m-tec.com/en/baustellentechnik/maschinen/3dcp/translate-to-english-m-tec-connect-p20-3dcp',
   'm-tec connect P20 3DCP — 3-24 L/min continuously adjustable, up to 4mm grain size, 30 bar, 95 kg. Modbus-RTU control via RS485/USB for direct integration with printer motion system. Standalone pump (no mixer) — pair with separate mixer or pre-mix. Note: 400V/50Hz European power, needs VFD or step-up transformer for US 480V/60Hz. No established US distributor — contact M-Tec directly or via DirectIndustry.',
   true);

-- Update the part description to reference M-Tec alongside MAI
UPDATE parts
SET description = 'Core extrusion component. The MAI PICTOR-3D (0.7-15.5 L/min, 2mm grain, analog 0-10V control) and m-tec P20 3DCP (3-24 L/min, 4mm grain, Modbus-RTU control) are the two most widely used pumps in concrete 3D printing worldwide. StoneFlower offers a third option with up to 6mm aggregate support. All are European-made — no established US distributors. If you want a US-sourced stepper-driven pump solution, leave a comment — at 10 commitments we will produce a small batch using NEMA23 + external driver controlled by the Kraken stepper signal for precise volumetric control.'
WHERE name = 'Progressive Cavity Pump'
  AND category = 'Concrete Extrusion System';
