# M3-CRETE Firmware

Klipper configuration for the M3-CRETE concrete 3D printer motion system.

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

- **Controller:** BTT Kraken v1.0 (STM32H723, 8× onboard TMC5160)
- **Host:** Raspberry Pi 5 8GB running Klipper + Moonraker + Mainsail
- **Motion steppers:** 7× NEMA23 3–4.5Nm, 8mm shaft (1×X + 2×Y + 4×Z)
- **Nozzle valve:** 1× small stepper (NEMA17/23) on Kraken DRIVER7
- **Feed pump:** 1× NEMA34 on external driver (owner-supplied)
- **Y/Z belts:** GT2 10mm + 20-tooth pulleys (looped)
- **X belt:** GT2 6mm + 20-tooth pulley (fixed strand, pinion drive)
- **V-wheels:** Polycarbonate, eccentric-spacer adjustable
- **Homing:** Sensorless StallGuard on all axes — no physical endstops

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

  ◆ = Z motor (NEMA23) on top brace, straddling each 4080 C-beam Z-post
      (4 motors total, each with its own StallGuard-based homing)
```

### Home positions (all sensorless — no physical endstops)

| Axis | Home direction | Home position | Stall target        |
|------|----------------|---------------|---------------------|
| X    | toward X−      | X = 0         | left frame post     |
| Y    | toward Y−      | Y = 0         | front Z-posts frame |
| Z    | toward Z+      | Z = 1000      | top brace (per post)|

**Homing sequence** (set in `homing.cfg`):

1. **Z first** — all 4 Z posts drive UP into the top brace in parallel. Each post's StallGuard fires independently on its own driver, giving per-corner coplanarity without a physical probe.
2. **X second** — gantry is now at safe height, X-carriage jogs left into the frame post until stall.
3. **Y last** — both Y motors drive the gantry forward into the front frame until the primary stalls (the secondary follows).

### Why Z first

If X or Y homed first with Z at an unknown position, the printhead could hit an obstacle mid-frame. Z homing up to a hard mechanical stop guarantees the gantry is at maximum height before any horizontal motion — if the printhead has to pass over a touch plate, finished print, or tool tray, it's clear above it.

### Motion limits (concrete-appropriate, conservative defaults)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `max_velocity` | 100 mm/s | Tune up after input shaping |
| `max_accel` | 1500 mm/s² | Concrete mass demands gentle accel |
| `max_z_velocity` | 25 mm/s | Z belts, not leadscrews |
| `max_z_accel` | 300 mm/s² | |
| `square_corner_velocity` | 5.0 mm/s | Low to prevent belt slip on corners |

## Build from source (Klipper firmware for the Kraken)

On the Raspberry Pi:

```bash
cd ~
git clone https://github.com/Klipper3d/klipper.git
cd klipper
make menuconfig
```

In `menuconfig`, set:

```
Micro-controller Architecture ........... STMicroelectronics STM32
Processor model ......................... STM32H723
Bootloader offset ....................... 128KiB bootloader
Clock Reference ......................... 25 MHz crystal
Communication interface ................. USB (on PA11/PA12)
```

Save and exit, then:

```bash
make
```

The compiled firmware lands at `~/klipper/out/klipper.bin`.

## Flashing the Kraken

1. Copy `klipper.bin` to a FAT32-formatted microSD card, renaming it to `firmware.bin`.
2. Power off the Kraken.
3. Insert the SD card.
4. Power on — the bootloader will flash automatically (~10 seconds).
5. On successful flash, `firmware.bin` will be renamed to `FIRMWARE.CUR` on the card.

## Installing this config

1. Copy this entire `firmware/` directory to `~/printer_data/config/` on the Pi.
2. Rename `printer.cfg` to the name Moonraker expects (default: `printer.cfg` in that directory — leave it as-is if you copied the folder contents directly).
3. Edit `mcu.cfg` — replace the `XXXXXXXXXXXXXXXX` placeholder with the real serial ID. Find it with:

   ```bash
   ls /dev/serial/by-id/
   ```

4. Restart Klipper via Mainsail (**Machine** → **Restart**) or:

   ```bash
   sudo systemctl restart klipper
   ```

## First-boot checklist

Do these in order, one at a time, before any actual printing.

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

The first `G28 Z` will drive all 4 Z posts UP into the top brace. Each post stalls independently when its corner meets the brace — you should hear 4 distinct "thunks" over about a second. If one corner doesn't stall, its `driver_SGT` is too high; lower it.

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

- **Feed pump** (`pump_feed`) — the big NEMA34 upstream of the hose. Has its own pressure advance (typical 0.5–1.5 seconds) to pressurize the hose ahead of valve commanded moves. Runs on an external driver via Kraken's MOTOR7 header.
- **Nozzle valve** (`extruder`) — a small, fast actuator at the printhead. Pressure advance = 0. Effectively a metering valve with ~1 % retraction capability for clean corners. Runs on Kraken's DRIVER7 onboard TMC5160.

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
- **Pin assignments for BTT Kraken are based on the upstream `example-kraken.cfg`** — verify against your board revision on first boot.
- **Extruder `rotation_distance` is a placeholder** — must be calibrated against your specific pump geometry.
- **Input shaping not yet tuned.** Add an ADXL345 to the toolhead mount and run `SHAPER_CALIBRATE` after mechanical commissioning.

## Contributing

This config is part of the M3-CRETE project: <https://github.com/sunnyday-technologies/M3-CRETE>

Licensed under CERN-OHL-W-2.0. Issues and PRs welcome at the repo above.
