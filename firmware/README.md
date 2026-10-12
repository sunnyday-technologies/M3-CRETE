# M3-CRETE Firmware — development reference

**This directory is a reference, not an install target.** The Klipper config
the machine runs lives in [M3-CRETE-FIRMWARE](https://github.com/sunnyday-technologies/M3-CRETE-FIRMWARE): `klipper/printer.cfg`,
installed with that repo's `install.sh`. Install from there. Do not copy this
directory onto the Pi.

This directory sketches the full-machine Klipper config (all axes, the nozzle
valve, the feed pump and the macros) ahead of the staged bring-up in
M3-CRETE-FIRMWARE. It does not load as-is: the feed-pump signal pins are
unassigned (see [Driver slots](#driver-slots-btt-kraken-v10)).

## What's in this directory

| File | Purpose |
|------|---------|
| `printer.cfg` | Top-level entry point — includes every other file |
| `mcu.cfg` | BTT Kraken MCU connection (serial path) |
| `kinematics.cfg` | Cartesian kinematics, build volume, motion limits |
| `steppers.cfg` | 7 motion steppers (X, 2×Y, 4×Z) + extruder/pump |
| `tmc.cfg` | TMC5160 driver settings — currents, StallGuard thresholds |
| `homing.cfg` | Sensorless homing sequence (no physical endstops) |
| `z_tilt.cfg` | Quad Z self-tramming |
| `macros.cfg` | START_PRINT, END_PRINT, pump priming, pump flush, pressure advance |
| `input_shaper.cfg` | ADXL345 + resonance tester + input shaper (optional include) |

## Hardware assumed

- **Controller:** BTT Kraken V1.0 (STM32H723, 8 onboard drivers, slots S1–S8; BTT lists them as TMC2160)
- **Host:** Raspberry Pi 5 8GB running Klipper + Moonraker + Mainsail
- **Motion steppers:** 7× NEMA23 3–4.5Nm, 8mm shaft (1×X + 2×Y + 4×Z)
- **Nozzle valve:** 1× small stepper (NEMA17/23) on Kraken slot S8
- **Feed pump:** 1× NEMA34 on external driver (owner-supplied); signal pins not assigned yet
- **Y belts:** GT2 10mm + 20-tooth pulleys (looped)
- **Z drive:** Tr8x2 lead screws (8 mm, 2 mm lead, single start), motors on top of each post, 8 mm couplers
- **X belt:** GT2 6mm + 20-tooth pulley (fixed strand, pinion drive)
- **V-wheels:** Polycarbonate, eccentric-spacer adjustable
- **Homing:** Sensorless StallGuard on all axes — no physical endstops

## Driver slots (BTT Kraken V1.0)

| Slot | Klipper section | step | dir | enable | cs | DIAG | sense_resistor |
|------|-----------------|------|-----|--------|----|------|----------------|
| S1 | `stepper_z` (Z0, front-left) | PC14 | PC13 | !PE6 | PD6 | PC15 | 0.022 |
| S2 | `stepper_z1` (Z1, front-right) | PE5 | PE4 | !PE3 | PD5 | PF0 | 0.022 |
| S3 | `stepper_z2` (Z2, rear-left) | PE2 | PE1 | !PE0 | PD4 | PF1 | 0.022 |
| S4 | `stepper_z3` (Z3, rear-right) | PB9 | PB8 | !PB7 | PD3 | PF2 | 0.022 |
| S5 | `stepper_x` | PG9 | PG10 | !PG13 | PD2 | PF3 | 0.075 |
| S6 | `stepper_y` (left, primary) | PG11 | PD7 | !PG12 | PA15 | PF4 | 0.075 |
| S7 | `stepper_y1` (right) | PB4 | PB3 | !PB5 | PA9 | — | 0.075 |
| S8 | `extruder` (nozzle valve) | PG15 | PB6 | !PG14 | PA10 | — | 0.075 |

- All eight drivers share a **software SPI** bus: SCK PC6, MOSI PC8, MISO PC7.
- Sensorless homing needs the slot's DIAG jumper fitted.
- `sense_resistor` depends on the slot **and the board revision**. On a Kraken
  V1.0, S1–S4 are 0.022 and S5–S8 are 0.075. On a V1.1, S1–S4 are 0.050.
  Klipper computes motor current from this value, so a wrong one silently
  scales the real current. For example, 0.075 configured on a 0.022 slot gives
  about 3.4× the configured `run_current`. Check the board revision before
  using these values.
- Z on S1–S4 is the slot allocation of the hardware-verified Stage-1 config in
  M3-CRETE-FIRMWARE, and those four rows match it. S5–S8 have not been run on
  the machine.
- The feed pump's external driver needs three spare GPIO for step, dir and
  enable, because all eight slots are in use. They are left unassigned here.
  M3-CRETE-FIRMWARE will assign the spare-header pins in its planned Stage 3
  config.

Pin sources: BTT's official
[`generic-bigtreetech-kraken.cfg`](https://github.com/bigtreetech/BIGTREETECH-Kraken/blob/master/Firmware/generic-bigtreetech-kraken.cfg)
(commit `4a3303f`), cross-checked against BTT's
[Kraken wiki](https://global.bttwiki.com/Kraken.html) (pin diagram and
specification table) and Marlin's `pins_BTT_KRAKEN_V1_0.h`.

## Axis conventions & motor layout

Frame origin `(0, 0, 0)` is at the **front-left corner of the build surface**. Looking down from above:

```
              X=0                                      X=2000
             ┌──────────────────────────────────────────┐    Y=1000
             │ Z2◆                                 Z3◆ │    (REAR)
             │                                          │
             │                                          │  ← Y motors
             │                                          │    (2× at rear,
             │                                          │     inboard of
             │           BUILD VOLUME                   │     rear Z-posts)
             │         2000 × 1000 × 1000 mm             │
             │                                          │
             │                                          │  ← X motor
             │                                          │    on X-carriage
             │                                          │    (pinion drive,
             │                                          │     travels with
             │ Z0◆                                 Z1◆ │     the printhead)
             └──────────────────────────────────────────┘    Y=0
                                                             (FRONT, HOME)

             ← X−                                     X+ →
                HOME

  ◆ = Z motor (NEMA23) on top of each 4080 C-beam Z-post, turning a
      Tr8x2 lead screw (4 motors total, each with its own StallGuard homing)
```

### Home positions (all sensorless — no physical endstops)

| Axis | Home direction | Home position | Stall target        |
|------|----------------|---------------|---------------------|
| X    | toward X−      | X = 0         | left frame post     |
| Y    | toward Y−      | Y = 0         | front Z-posts frame |
| Z    | toward Z−      | Z = position_endstop (measured) | bottom hard-stop block (per post) |

**Homing sequence** (set in `homing.cfg`):

1. **Z first** — all 4 Z posts drive DOWN onto their bottom hard-stop blocks in parallel, at a reduced homing current. Each post's StallGuard fires independently on its own driver (each Z stepper has its own virtual endstop), giving per-corner coplanarity without a physical probe. The gantry then lifts 10 mm.
2. **X second** — the development sequence assumes Z reached its configured reference position before an X-axis stall-detection move; this is not a verified safe-height guarantee.
3. **Y last** — both Y motors drive the gantry forward into the front frame until the primary stalls (the secondary follows).

### Why Z first

If X or Y moves with Z at an unknown position, the printhead can contact an obstacle. The current development sequence establishes a Z reference first by homing down toward the build surface, so the build area must be clear before `G28`. Stall sensing and a hard stop do not guarantee clearance, repeatability, safe force, or a clear path. A qualified commissioning plan must verify the actual envelope, obstructions, speeds, currents, stopping behavior, guarding, and recovery before any automated homing sequence is enabled.

### Development motion references (not validated safe limits)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `max_velocity` | 100 mm/s | Tune up after input shaping |
| `max_accel` | 1500 mm/s² | Concrete mass demands gentle accel |
| `max_z_velocity` | 10 mm/s | Tr8x2 lead screws: 300 rpm |
| `max_z_accel` | 100 mm/s² | |
| `square_corner_velocity` | 5.0 mm/s | Low to prevent belt slip on corners |

## Building, flashing and installing

Use M3-CRETE-FIRMWARE for all three. Its
[`klipper/README.md`](https://github.com/sunnyday-technologies/M3-CRETE-FIRMWARE/blob/main/klipper/README.md) has the tested
`menuconfig` settings (including the "Enable extra low-level configuration
options" checkbox), the microSD and USB DFU flashing procedures, and the
staged commissioning notes. Its `install.sh` installs the machine config.

Do not copy this directory to `~/printer_data/config/`.

## Commissioning reference

On the machine, follow the stage notes in M3-CRETE-FIRMWARE. The steps below
describe how this full reference config is meant to be tuned once every axis
is wired. Do them in order, one at a time, before any actual printing.

### 1. Verify MCU connection

```
RESTART
FIRMWARE_RESTART
```

Klipper should report "Ready" in Mainsail. If it errors, check the serial path in `mcu.cfg`.

### 2. Power on one stepper at a time, verify motion direction

Using the Mainsail jog buttons, move each axis 10mm in its positive direction. Confirm:

- **X+** moves the gantry toward the **right** (looking at the front of the machine)
- **Y+** moves the gantry toward the **rear**
- **Z+** moves the gantry **up**

If any axis moves the wrong way, flip the `dir_pin` polarity in `steppers.cfg` by adding or removing the `!` prefix.

### 3. Verify Y dual-drive synchronization

Jog Y by 100mm. The left and right Y rails must move together — if one lags, they're not synced. Check that `stepper_y1` has the same `rotation_distance` and `microsteps` as `stepper_y`.

### 4. Calibrate rotation_distance per axis

Mark a starting point with tape. Jog the axis exactly 100mm via Mainsail. Measure with a tape measure. If the actual distance is off, adjust `rotation_distance` proportionally:

```
new_rotation_distance = old_rotation_distance × (actual / requested)
```

### 5. Tune StallGuard thresholds (sensorless homing)

This is the trickiest part. For each axis, iterate:

1. Issue `G28 X` (or Y or Z).
2. Watch the motion:
   - **Stalls before reaching the frame** → `driver_SGT` is too sensitive → **increase** by 1 in `tmc.cfg`
   - **Crashes into the frame without stalling** → `driver_SGT` is not sensitive enough → **decrease** by 1
3. Restart Klipper (`FIRMWARE_RESTART`) after each change.
4. Repeat until homing stops reliably at the frame.

Use the `SHOW_SG` macro to see live StallGuard values while the printer is idle.

### 6. Test quad Z homing

Clear the build area first: Z homes down. The first `G28 Z` drives all 4 Z posts DOWN onto their hard-stop blocks at the reduced homing current (`Z_HOME_CURRENT` in `homing.cfg`). Each post stalls independently when its carriage meets its block, so you should hear 4 distinct stops. If one corner doesn't stall, its `driver_SGT` is too high; lower it.

Then measure the nozzle height above the build surface with the carriages on the blocks and set `position_endstop` and `position_min` in `steppers.cfg` to it. Measure the carriage travel and set `position_max` below it: a lead screw does not slip if driven into the top mount.

### 7. Calibrate the nozzle valve and feed pump independently

Because the two steppers are synced, you have to calibrate them one at a time.

**Step 7a — Feed pump (`pump_feed`):**

1. `PUMP_UNSYNC` (disconnect the pump from the valve)
2. Disconnect the hose from the nozzle and route it into a measuring cup
3. `G1 E100 F60` (runs only the pump, valve stays closed)
4. Measure the output volume
5. Scale: `new_rotation_distance = old × (commanded / actual)`
6. Edit `steppers.cfg` → `[extruder_stepper pump_feed]` → `rotation_distance`
7. `FIRMWARE_RESTART`
8. `PUMP_RESYNC`

**Step 7b — Nozzle valve (`extruder`):**

1. With hose reconnected and pump running synced, command `G1 E100 F60`
2. Measure what comes out the nozzle
3. If pump output is already calibrated and valve output is off, scale the valve's `rotation_distance` (in `[extruder]`) using the same formula
4. `FIRMWARE_RESTART`

In practice the valve rarely needs precise calibration — it's a metering gate, not a volumetric pump — but doing both ensures the two are in agreement.

### 8. Test a small print

Use a 10cm × 10cm single-wall square at a slow speed (30 mm/s) for the first print. Check:

- First-layer adhesion and squish
- Belt tension (no slapping or visible stretch under accel)
- Pump flow consistency

## Pump architecture — feed pump + nozzle valve

M3-CRETE uses a two-stage fluid-handling system:

- **Feed pump** (`pump_feed`) — the big NEMA34 upstream of the hose. Has its own pressure advance (typical 0.5–1.5 seconds) to pressurize the hose ahead of valve commanded moves. Runs on an external driver; its signal pins are not assigned yet (all eight onboard slots are in use).
- **Nozzle valve** (`extruder`) — a small, fast actuator at the printhead. Pressure advance = 0. Effectively a metering valve with ~1 % retraction capability for clean corners. Runs on Kraken slot S8.

Both steppers are synchronized: every `G1 E...` move drives both at once. The feed pump runs *ahead* of the valve in time (by the amount of its pressure advance) so material arrives at the valve exactly when it opens.

### Why independent pressure advance matters

Concrete hoses are compressible and viscous — unlike a rigid FDM filament path, the pressure in the hose lags the pump by hundreds of milliseconds. If you drove the pump and valve with the same PA, the valve would either dribble (if PA is low) or over-pressurize at corners (if PA is high). Splitting them means:

- **Valve PA = 0** → opens and closes on time, clean corners
- **Pump PA = 0.8** → hose is already pressurized when the valve opens

### Tuning

Use the `SET_PUMP_PA` macro during a test print:

```
SET_PUMP_PA ADVANCE=0.5    ; start here
; print a corner-test pattern, observe
SET_PUMP_PA ADVANCE=0.8    ; increase if corners dribble after direction change
SET_PUMP_PA ADVANCE=0.3    ; decrease if corners bulge before direction change
```

The default in `START_PRINT` is `ADVANCE=0.8`. Edit `macros.cfg` once you've found your hose's sweet spot.

### Independent pump control

To run the feed pump solo (e.g. manually fill the hopper without opening the valve):

```
PUMP_UNSYNC           ; feed pump disconnects from valve
; jog pump manually via G1 E... — only pump moves
PUMP_RESYNC           ; feed pump reconnects for normal printing
```

## Safety notes

- **Flush the pump line within 5 minutes of print completion.** Concrete cures inside the line and will lock the pump solid.
- **StallGuard homing is not foolproof.** If you're standing inside the machine's envelope, always power off the motors first.
- **Test all motion at low current first** (`run_current: 1.2` in `tmc.cfg`) and raise in 0.2A increments after verifying thermal behavior.
- **The X axis is 2m long and heavy.** Homing speeds above 30 mm/s will cause belt slip before the frame is reached.

## Input shaping (ADXL345)

A 2m concrete printer has long belt spans that resonate at low frequencies — without input shaping, corner moves leave visible ringing for several cm. The `input_shaper.cfg` file is a drop-in module that enables Klipper's resonance measurement + compensation workflow using an ADXL345 accelerometer wired to the Raspberry Pi's GPIO SPI bus.

**Setup is a three-step thing:**

1. **Buy the part** — it's BOM item 71 (ADXL345, ~$10 from BTT/Adafruit/Amazon). Mount it rigidly to the printhead or X-carriage using M3 screws. Zip ties will give you garbage data.

2. **Wire it** — 6 wires from the breakout to the Pi's 40-pin header. The full pinout is in `input_shaper.cfg` at the top of the file. TL;DR: power + SPI on Pi pins 1, 9, 19, 21, 22, 23.

3. **Enable the include** — uncomment the `[include input_shaper.cfg]` line in `printer.cfg`, then follow the setup procedure inside `input_shaper.cfg` (enable SPI on the Pi, install the host MCU, run `SHAPER_CALIBRATE`).

Klipper's `SHAPER_CALIBRATE` will sweep the printer and print recommended `shaper_freq_x` / `shaper_freq_y` values. Paste those into the `[input_shaper]` section at the bottom of `input_shaper.cfg` and `FIRMWARE_RESTART`.

After tuning, you can leave the ADXL345 installed or remove it — the input shaper values stay in the config either way.

## Known limitations (v0.1)

- **No physical probe** — Z_TILT_ADJUST is stubbed out until a probe is wired in. First-layer calibration is currently manual.
- **Driver pins and sense resistors are written for a Kraken V1.0** (see [Driver slots](#driver-slots-btt-kraken-v10)). S1–S4 (Z) match the hardware-verified Stage-1 config. S5–S8 (X, Y, Y1, valve) have not run on the machine.
- **The config does not load as-is.** The feed-pump signal pins are unassigned, so Klipper stops with a missing `step_pin` error for `pump_feed`.
- **The extruder's placeholder thermistor input (T0) has nothing connected.** An open thermistor input reads out of range and Klipper shuts down, so this needs a decision before the config can run.
- **Extruder `rotation_distance` is a placeholder** — must be calibrated against your specific pump geometry.
- **Input shaping not yet tuned.** Add an ADXL345 to the toolhead mount and run `SHAPER_CALIBRATE` after mechanical commissioning.

## Contributing

This config is part of the M3-CRETE project: <https://github.com/sunnyday-technologies/M3-CRETE>

Licensed under CERN-OHL-W-2.0. Issues and PRs welcome at the repo above.
