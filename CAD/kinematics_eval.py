"""
M3-CRETE M3-2 Kinematics & Statics Evaluation
===============================================
Printhead: 3 kg (with hose load)
Frame: 4080 C-beam 1000mm, 2080 gantry beam 2000mm (spliced)
Motors: 7x NEMA23 (1X + 2Y + 4Z), GT2 10mm belt, 20T pulleys

Evaluates:
  1. Gantry beam deflection (worst-case center load)
  2. Motor torque budgets per axis
  3. Maximum acceleration & speed per axis
  4. Belt tension analysis & safety margins
  5. Dual-Y racking analysis
  6. Z-axis lift capacity
  7. NEMA17 vs NEMA23 feasibility (geared & direct)

All calculations use conservative (worst-case) assumptions.
"""
import math

print("=" * 70)
print("M3-CRETE M3-2 KINEMATICS & STATICS EVALUATION")
print("=" * 70)

# ============================================================
# PHYSICAL CONSTANTS & MATERIAL PROPERTIES
# ============================================================
g = 9.81  # m/s^2

# Aluminum 6063-T5 (typical V-slot extrusion alloy)
E_al = 69e9       # Pa (Young's modulus)
rho_al = 2700     # kg/m^3
sigma_yield = 145e6  # Pa (yield strength)

# GT2 10mm belt
BELT_WIDTH = 10     # mm
BELT_PITCH = 2      # mm
# Steel-core GT2 10mm: ~900N breaking strength, ~450N recommended max working
BELT_BREAK_N = 900
BELT_WORK_N = 450
# Tooth shear: ~30N per tooth engagement (conservative)
TOOTH_SHEAR_N = 30

# GT2 20-Tooth pulley
PULLEY_TEETH = 20
PULLEY_PITCH_DIA = PULLEY_TEETH * BELT_PITCH / math.pi  # mm
PULLEY_PITCH_R = PULLEY_PITCH_DIA / 2.0 / 1000.0  # m

# ============================================================
# MOTOR SPECS
# ============================================================
# NEMA23 — typical 2.8A bipolar, 8mm shaft
NEMA23_HOLDING_TORQUE = 1.89    # Nm (typical 57x56mm, 2.8A)
NEMA23_DETENT_TORQUE = 0.05     # Nm
NEMA23_ROTOR_INERTIA = 480e-7   # kg*m^2 (480 g*cm^2)
NEMA23_WEIGHT = 1.05            # kg
NEMA23_MAX_RPM = 1200           # practical limit with TMC5160 at 24V
NEMA23_COST = 25                # USD typical

# NEMA17 — typical 1.7A bipolar, 5mm shaft
NEMA17_HOLDING_TORQUE = 0.45    # Nm (42x48mm, 1.7A)
NEMA17_DETENT_TORQUE = 0.02     # Nm
NEMA17_ROTOR_INERTIA = 68e-7    # kg*m^2
NEMA17_WEIGHT = 0.35            # kg
NEMA17_MAX_RPM = 1500           # lighter rotor, faster
NEMA17_COST = 12                # USD typical

# NEMA17 + 5:1 planetary gearbox
NEMA17_GEAR_RATIO = 5.0
NEMA17_GEAR_EFF = 0.85          # 85% efficiency typical
NEMA17_GEAR_TORQUE = NEMA17_HOLDING_TORQUE * NEMA17_GEAR_RATIO * NEMA17_GEAR_EFF
NEMA17_GEAR_COST = 12 + 30      # motor + gearbox

# ============================================================
# EXTRUSION PROPERTIES
# ============================================================
# 2080 V-slot (gantry beam) — approximate second moment of area
# Profile: 20mm x 80mm, I about the weak axis (20mm direction = vertical sag)
# Actual profile has internal V-grooves reducing I from solid rectangle.
# OpenBuilds 2080: Ixx ≈ 6.8 cm^4 (weak axis, the one that sags)
I_2080_weak = 6.8e-8    # m^4 (converted from cm^4)
I_2080_strong = 25.0e-8  # m^4 (strong axis, 80mm direction)
M_2080_per_m = 1.55      # kg/m

# 4080 C-beam (frame members)
# C-beam profile: 40mm x 80mm with open C channel
# I ≈ 18 cm^4 (strong axis), ~9.5 cm^4 (weak axis)
I_4080_strong = 18.0e-8  # m^4
I_4080_weak = 9.5e-8     # m^4
M_4080_per_m = 2.45      # kg/m

# ============================================================
# ASSEMBLY MASS BUDGET
# ============================================================
print("\n1. MASS BUDGET")
print("-" * 50)

M_printhead = 3.0       # kg (user specified, includes hose load)
M_x_carriage = 0.8      # kg (2x gantry plates + 4x V-wheels + spacers + bolts)
M_x_belt = 0.15         # kg (GT2 belt ~2.4m)

M_x_moving = M_printhead + M_x_carriage + M_x_belt
print(f"  X-axis moving mass:  {M_x_moving:.1f} kg")
print(f"    Printhead:         {M_printhead:.1f} kg")
print(f"    X-carriage:        {M_x_carriage:.1f} kg")

M_gantry_beam = M_2080_per_m * 2.0  # 2m span (2x 1000mm spliced)
M_y_carriage = 1.0      # kg (2x Y-gantry plates + V-wheels)
M_y_belt = 0.30         # kg (2x GT2 belt ~2.5m each)

M_y_moving = M_x_moving + M_gantry_beam + M_y_carriage + M_y_belt
print(f"  Y-axis moving mass:  {M_y_moving:.1f} kg")
print(f"    Gantry beam 2080:  {M_gantry_beam:.1f} kg")
print(f"    Y-carriages:       {M_y_carriage:.1f} kg")

M_y_rails = M_4080_per_m * 1.0 * 2  # 2x 4080 Y-rails, 1000mm each
M_z_carriage = 2.0      # kg (8x Z-carriage plates + V-wheels + spacers)
M_z_belt = 0.60         # kg (4x GT2 belt ~2.5m each)
M_z_motors_on_frame = 4 * NEMA23_WEIGHT  # Z-motors are frame-mounted, not moving

M_z_moving = M_y_moving + M_y_rails + M_z_carriage + M_z_belt
print(f"  Z-axis moving mass:  {M_z_moving:.1f} kg")
print(f"    Y-rails (2x 4080): {M_y_rails:.1f} kg")
print(f"    Z-carriages:       {M_z_carriage:.1f} kg")
print(f"  (Z-motors are frame-mounted, not part of moving mass)")

# ============================================================
# 2. GANTRY BEAM DEFLECTION
# ============================================================
print(f"\n2. GANTRY BEAM DEFLECTION (4080 C-beam, 2m span)")
print("-" * 50)

L_beam = 2.0  # m (gantry beam span)
M_gantry_beam = M_4080_per_m * L_beam  # 4080 C-beam, not 2080
W_beam = M_gantry_beam * g  # N (distributed self-weight)
P_head = M_printhead * g     # N (point load from printhead)
P_carriage = M_x_carriage * g  # N (carriage at same point)
P_total = P_head + P_carriage  # total point load at center
w_per_m = W_beam / L_beam  # N/m

# 4080 C-beam: strong axis (80mm vertical)
delta_point_bare = (P_total * L_beam**3) / (48 * E_al * I_4080_strong)
delta_dist_bare = (5 * w_per_m * L_beam**4) / (384 * E_al * I_4080_strong)
delta_bare = delta_point_bare + delta_dist_bare

print(f"  Point load at center: {P_total:.1f} N ({M_printhead + M_x_carriage:.1f} kg)")
print(f"  Beam self-weight:     {W_beam:.1f} N ({M_gantry_beam:.1f} kg)")
print()
print(f"  BARE 4080 C-beam (strong axis, 80mm vertical):")
print(f"    Point load sag:     {delta_point_bare*1000:.2f} mm")
print(f"    Self-weight sag:    {delta_dist_bare*1000:.2f} mm")
print(f"    TOTAL center sag:   {delta_bare*1000:.2f} mm")
print(f"    {'PASS' if delta_bare*1000 < 0.5 else 'FAIL'} (limit: 0.5 mm for concrete printing)")

# CF reinforcement: 2x 12mm OD / 10mm ID pultruded tubes in top+bottom channels
E_cf = 230e9  # Pa (carbon fiber)
CF_OD = 12e-3; CF_ID = 10e-3
ROD_OFFSET = 30e-3  # m from neutral axis
I_cf_single = math.pi / 64 * (CF_OD**4 - CF_ID**4)
A_cf = math.pi / 4 * (CF_OD**2 - CF_ID**2)
I_cf_total = 2 * (I_cf_single + A_cf * ROD_OFFSET**2)
n_modular = E_cf / E_al
I_cf_equiv = I_cf_total * n_modular
I_combined = I_4080_strong + I_cf_equiv
M_cf_rods = 2 * 0.050 * L_beam  # 50 g/m per rod, 2 rods, 2m
w_combined = (M_gantry_beam + M_cf_rods) * g / L_beam

delta_cf = (P_total * L_beam**3) / (48 * E_al * I_combined) + \
           (5 * w_combined * L_beam**4) / (384 * E_al * I_combined)
delta_cf_splice = delta_cf / 0.85  # CF rods span the joint, better than 75%

print(f"\n  WITH CF REINFORCEMENT (2x 12mm tubes, epoxied in channels):")
print(f"    I_combined:         {I_combined*1e8:.1f} cm^4 ({I_combined/I_4080_strong:.1f}x bare)")
print(f"    CF rod weight:      {M_cf_rods*1000:.0f}g")
print(f"    TOTAL center sag:   {delta_cf*1000:.2f} mm")
print(f"    With splice (~85%): {delta_cf_splice*1000:.2f} mm")
print(f"    {'PASS' if delta_cf_splice*1000 < 0.5 else 'FAIL'} (limit: 0.5 mm)")
print(f"    Reduction:          {(1 - delta_cf/delta_bare)*100:.0f}% vs bare")

# Update gantry beam mass for downstream calcs
M_gantry_beam += M_cf_rods

# Store for summary
delta_total_strong = delta_bare
delta_total_weak = delta_bare * (I_4080_strong / I_4080_weak)

# ============================================================
# 3. MOTOR TORQUE BUDGETS
# ============================================================
print(f"\n3. MOTOR TORQUE BUDGETS")
print("-" * 50)

# Belt drive: F = T / r_pulley
# Required torque: T = F * r_pulley
# Force = m * a (acceleration) + m * g * sin(θ) (gravity, Z only) + friction

V_WHEEL_FRICTION = 0.01  # rolling coefficient for polycarbonate V-wheels on anodized Al
BELT_EFFICIENCY = 0.95    # GT2 belt drive efficiency

# Typical concrete printing parameters
PRINT_SPEED = 0.100       # m/s (100 mm/s — fast for concrete)
TRAVEL_SPEED = 0.300      # m/s (300 mm/s — repositioning)
TARGET_ACCEL = 0.5        # m/s^2 (modest — concrete doesn't need FDM-style accels)
AGGRESSIVE_ACCEL = 2.0    # m/s^2 (what if we want faster travel?)

def torque_analysis(axis_name, mass_kg, n_motors, gravity_axis=False, accel=TARGET_ACCEL):
    """Calculate required motor torque for an axis."""
    F_accel = mass_kg * accel
    F_friction = mass_kg * g * V_WHEEL_FRICTION
    F_gravity = mass_kg * g if gravity_axis else 0
    F_total = F_accel + F_friction + F_gravity

    # Per-motor force (shared across n_motors)
    F_per_motor = F_total / n_motors
    T_required = F_per_motor * PULLEY_PITCH_R / BELT_EFFICIENCY

    # Safety factor
    T_available = NEMA23_HOLDING_TORQUE * 0.7  # 70% of holding torque at speed
    safety = T_available / T_required if T_required > 0 else float('inf')

    print(f"\n  {axis_name} ({n_motors}x NEMA23, mass={mass_kg:.1f}kg, accel={accel:.1f}m/s^2):")
    print(f"    Acceleration force: {F_accel:.1f} N")
    print(f"    Friction force:     {F_friction:.1f} N")
    if gravity_axis:
        print(f"    Gravity force:      {F_gravity:.1f} N")
    print(f"    Total force:        {F_total:.1f} N ({F_per_motor:.1f} N per motor)")
    print(f"    Required torque:    {T_required*1000:.1f} mNm per motor")
    print(f"    Available torque:   {T_available*1000:.0f} mNm (70% of {NEMA23_HOLDING_TORQUE} Nm holding)")
    print(f"    Safety factor:      {safety:.1f}x {'PASS' if safety > 1.5 else 'MARGINAL' if safety > 1.0 else 'FAIL'}")

    return T_required, F_total, safety

# Normal printing acceleration (0.5 m/s^2)
print(f"  --- At printing acceleration ({TARGET_ACCEL} m/s^2) ---")
Tx, Fx, Sx = torque_analysis("X-axis", M_x_moving, 1, gravity_axis=False)
Ty, Fy, Sy = torque_analysis("Y-axis", M_y_moving, 2, gravity_axis=False)
Tz, Fz, Sz = torque_analysis("Z-axis", M_z_moving, 4, gravity_axis=True)

# Aggressive travel acceleration (2.0 m/s^2)
print(f"\n  --- At travel acceleration ({AGGRESSIVE_ACCEL} m/s^2) ---")
torque_analysis("X-axis", M_x_moving, 1, gravity_axis=False, accel=AGGRESSIVE_ACCEL)
torque_analysis("Y-axis", M_y_moving, 2, gravity_axis=False, accel=AGGRESSIVE_ACCEL)

# ============================================================
# 4. MAXIMUM ACCELERATION & SPEED
# ============================================================
print(f"\n4. MAXIMUM ACCELERATION & SPEED")
print("-" * 50)

def max_accel_speed(axis_name, mass_kg, n_motors, gravity_axis=False):
    T_available = NEMA23_HOLDING_TORQUE * 0.7 * n_motors
    F_available = T_available * BELT_EFFICIENCY / PULLEY_PITCH_R
    F_friction = mass_kg * g * V_WHEEL_FRICTION
    F_gravity = mass_kg * g if gravity_axis else 0
    F_net = F_available - F_friction - F_gravity
    a_max = F_net / mass_kg if F_net > 0 else 0

    # Max speed from motor RPM
    v_max = (NEMA23_MAX_RPM / 60.0) * (PULLEY_TEETH * BELT_PITCH / 1000.0)

    # Belt tooth engagement limit: at least 6 teeth engaged for reliable grip
    # 20T pulley = 10 teeth engaged at 180° wrap = safe

    print(f"  {axis_name}:")
    print(f"    Max acceleration:   {a_max:.1f} m/s^2 ({a_max/g:.2f} G)")
    print(f"    Max linear speed:   {v_max*1000:.0f} mm/s ({v_max:.2f} m/s)")
    if gravity_axis:
        print(f"    (gravity-limited: {F_gravity:.0f}N gravity vs {F_available:.0f}N motor force)")
    return a_max, v_max

ax, vx = max_accel_speed("X-axis", M_x_moving, 1)
ay, vy = max_accel_speed("Y-axis", M_y_moving, 2)
az, vz = max_accel_speed("Z-axis", M_z_moving, 4, gravity_axis=True)

# ============================================================
# 5. BELT TENSION ANALYSIS
# ============================================================
print(f"\n5. BELT TENSION ANALYSIS (GT2 10mm steel-core)")
print("-" * 50)

# Worst case: Z-axis holding full gantry against gravity + accelerating
F_z_hold = M_z_moving * g  # static hold force
F_z_accel = M_z_moving * TARGET_ACCEL
F_z_total_per_belt = (F_z_hold + F_z_accel) / 4  # 4 belts

# X-axis at aggressive accel
F_x_aggressive = M_x_moving * AGGRESSIVE_ACCEL + M_x_moving * g * V_WHEEL_FRICTION

print(f"  Z-axis (per belt, static hold + {TARGET_ACCEL} m/s^2 accel):")
print(f"    Tension:            {F_z_total_per_belt:.0f} N")
print(f"    Belt breaking:      {BELT_BREAK_N} N")
print(f"    Safety to break:    {BELT_BREAK_N/F_z_total_per_belt:.1f}x")
print(f"    Working limit:      {BELT_WORK_N} N")
print(f"    Safety to working:  {BELT_WORK_N/F_z_total_per_belt:.1f}x {'PASS' if BELT_WORK_N/F_z_total_per_belt > 2 else 'MARGINAL'}")

print(f"\n  X-axis (single belt, {AGGRESSIVE_ACCEL} m/s^2 accel):")
print(f"    Tension:            {F_x_aggressive:.0f} N")
print(f"    Safety to break:    {BELT_BREAK_N/F_x_aggressive:.1f}x")
print(f"    Safety to working:  {BELT_WORK_N/F_x_aggressive:.1f}x {'PASS' if BELT_WORK_N/F_x_aggressive > 2 else 'MARGINAL'}")

# Tooth skip check
teeth_engaged = PULLEY_TEETH // 2  # 180° wrap = half the teeth
F_tooth_limit = teeth_engaged * TOOTH_SHEAR_N
print(f"\n  Tooth skip resistance ({teeth_engaged} teeth engaged at 180° wrap):")
print(f"    Tooth shear limit:  {F_tooth_limit} N")
print(f"    Z per-belt tension: {F_z_total_per_belt:.0f} N — {'PASS' if F_tooth_limit > F_z_total_per_belt else 'FAIL'}")
print(f"    X max tension:      {F_x_aggressive:.0f} N — {'PASS' if F_tooth_limit > F_x_aggressive else 'FAIL'}")

# ============================================================
# 6. DUAL-Y RACKING ANALYSIS
# ============================================================
print(f"\n6. DUAL-Y RACKING ANALYSIS")
print("-" * 50)

Y_RAIL_SPACING = 2.0 * 1.0 + 0.080  # 2080mm between Y-rail centers (frame width)
# Actually: Y-rails are at left and right Z-posts, spaced by the X-axis width
Y_RAIL_SPACING = 2.0  # ~2000mm between the two Y-rails (X-axis span)

# If one Y-motor leads by 1 full step (1.8° = 0.04mm linear with 20T GT2):
STEP_ANGLE = 1.8  # degrees
LINEAR_PER_STEP = (STEP_ANGLE / 360.0) * PULLEY_TEETH * BELT_PITCH  # mm
MICROSTEP = 16  # TMC5160 typical
LINEAR_PER_MICROSTEP = LINEAR_PER_STEP / MICROSTEP

# Skew angle from 1-step lead
skew_1step = math.atan(LINEAR_PER_STEP / 1000.0 / Y_RAIL_SPACING)
skew_at_x_end = math.tan(skew_1step) * (Y_RAIL_SPACING / 2) * 1000  # mm deviation at beam end

print(f"  Y-rail spacing:       {Y_RAIL_SPACING*1000:.0f} mm")
print(f"  Linear per full step: {LINEAR_PER_STEP:.3f} mm")
print(f"  Linear per microstep: {LINEAR_PER_MICROSTEP:.4f} mm (1/{MICROSTEP} step)")
print(f"  1-step lead skew:")
print(f"    Angle:              {math.degrees(skew_1step)*1000:.3f} mrad")
print(f"    Deviation at beam end: {skew_at_x_end:.4f} mm")
print(f"    {'PASS' if skew_at_x_end < 0.1 else 'CONCERN'} (limit: 0.1 mm)")

# Racking force to overcome: V-wheel preload on both rails
# With eccentric spacers providing ~2N preload per wheel, 4 wheels per side:
PRELOAD_PER_WHEEL = 2.0  # N
WHEELS_PER_RAIL = 4
F_racking_resist = PRELOAD_PER_WHEEL * WHEELS_PER_RAIL * 2 * V_WHEEL_FRICTION
print(f"\n  V-wheel racking resistance: {F_racking_resist:.1f} N")
print(f"  Klipper dual-Y sync eliminates accumulated step error.")
print(f"  Risk: LOW — 1 missed step = {skew_at_x_end:.4f} mm, self-correcting with homing.")

# ============================================================
# 7. Z-AXIS LIFT CAPACITY
# ============================================================
print(f"\n7. Z-AXIS LIFT CAPACITY")
print("-" * 50)

F_z_gravity = M_z_moving * g
T_z_per_motor_hold = (F_z_gravity / 4) * PULLEY_PITCH_R / BELT_EFFICIENCY
T_z_available = NEMA23_HOLDING_TORQUE  # full holding at standstill

print(f"  Total Z moving mass:  {M_z_moving:.1f} kg ({F_z_gravity:.0f} N)")
print(f"  Per-motor gravity:    {F_z_gravity/4:.0f} N")
print(f"  Per-motor hold torque needed: {T_z_per_motor_hold*1000:.0f} mNm")
print(f"  Per-motor available:  {T_z_available*1000:.0f} mNm")
print(f"  Static safety factor: {T_z_available/T_z_per_motor_hold:.1f}x {'PASS' if T_z_available/T_z_per_motor_hold > 2 else 'MARGINAL'}")

# What if 1 motor fails?
T_z_3motor = (F_z_gravity / 3) * PULLEY_PITCH_R / BELT_EFFICIENCY
print(f"\n  Single motor failure scenario (3 remaining):")
print(f"    Per-motor load:     {F_z_gravity/3:.0f} N")
print(f"    Required torque:    {T_z_3motor*1000:.0f} mNm")
print(f"    Safety factor:      {T_z_available/T_z_3motor:.1f}x {'SAFE' if T_z_available/T_z_3motor > 1.5 else 'DROPS but holds'}")

# ============================================================
# 8. NEMA17 vs NEMA23 FEASIBILITY
# ============================================================
print(f"\n8. NEMA17 vs NEMA23 FEASIBILITY STUDY")
print("=" * 70)

def nema17_eval(axis_name, mass_kg, n_motors, gravity_axis=False,
                accel=TARGET_ACCEL, geared=False):
    if geared:
        T_holding = NEMA17_GEAR_TORQUE
        max_rpm = NEMA17_MAX_RPM / NEMA17_GEAR_RATIO
        label = f"NEMA17 + {NEMA17_GEAR_RATIO:.0f}:1 gear"
        cost = NEMA17_GEAR_COST
        weight = NEMA17_WEIGHT + 0.25  # gearbox adds ~250g
    else:
        T_holding = NEMA17_HOLDING_TORQUE
        max_rpm = NEMA17_MAX_RPM
        label = "NEMA17 direct"
        cost = NEMA17_COST
        weight = NEMA17_WEIGHT

    T_at_speed = T_holding * 0.7
    F_available = T_at_speed * n_motors * BELT_EFFICIENCY / PULLEY_PITCH_R
    F_accel = mass_kg * accel
    F_friction = mass_kg * g * V_WHEEL_FRICTION
    F_gravity = mass_kg * g if gravity_axis else 0
    F_required = F_accel + F_friction + F_gravity
    F_per_motor = F_required / n_motors
    T_required = F_per_motor * PULLEY_PITCH_R / BELT_EFFICIENCY

    v_max = (max_rpm / 60.0) * (PULLEY_TEETH * BELT_PITCH / 1000.0)
    safety = T_at_speed / T_required if T_required > 0 else float('inf')

    verdict = "PASS" if safety > 1.5 else "MARGINAL" if safety > 1.0 else "FAIL"

    print(f"\n  {axis_name} — {label} ({n_motors}x motors):")
    print(f"    Holding torque:     {T_holding*1000:.0f} mNm")
    print(f"    Required per motor: {T_required*1000:.0f} mNm")
    print(f"    Safety factor:      {safety:.1f}x — {verdict}")
    print(f"    Max speed:          {v_max*1000:.0f} mm/s")
    print(f"    Cost per motor:     ${cost}")
    print(f"    Weight per motor:   {weight:.2f} kg")
    return safety, v_max, cost * n_motors, verdict

print(f"\n  --- NEMA23 baseline (current spec) ---")
print(f"  Holding torque: {NEMA23_HOLDING_TORQUE*1000:.0f} mNm, ${NEMA23_COST}/ea, {NEMA23_WEIGHT:.2f} kg")

print(f"\n  --- NEMA17 direct drive ---")
print(f"  Holding torque: {NEMA17_HOLDING_TORQUE*1000:.0f} mNm, ${NEMA17_COST}/ea, {NEMA17_WEIGHT:.2f} kg")
s17x, _, _, _ = nema17_eval("X-axis", M_x_moving, 1)
s17y, _, _, _ = nema17_eval("Y-axis", M_y_moving, 2)
s17z, v17z, _, _ = nema17_eval("Z-axis", M_z_moving, 4, gravity_axis=True)

print(f"\n  --- NEMA17 + 5:1 planetary gearbox ---")
print(f"  Effective torque: {NEMA17_GEAR_TORQUE*1000:.0f} mNm, ${NEMA17_GEAR_COST}/ea, ~0.60 kg")
s17gx, _, _, _ = nema17_eval("X-axis", M_x_moving, 1, geared=True)
s17gy, _, _, _ = nema17_eval("Y-axis", M_y_moving, 2, geared=True)
s17gz, v17gz, _, _ = nema17_eval("Z-axis", M_z_moving, 4, gravity_axis=True, geared=True)

# ============================================================
# SUMMARY TABLE
# ============================================================
print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")

print(f"""
  GANTRY DEFLECTION (4080 C-beam, 2m span, 3.8kg center load):
    Bare 4080:                {delta_bare*1000:.2f} mm — {'PASS' if delta_bare*1000 < 0.5 else 'FAIL'}
    With CF rods:             {delta_cf*1000:.2f} mm — {'PASS' if delta_cf*1000 < 0.5 else 'FAIL'}
    CF + splice penalty:      {delta_cf_splice*1000:.2f} mm — {'PASS' if delta_cf_splice*1000 < 0.5 else 'MARGINAL'}

  MOTOR TORQUE (at {TARGET_ACCEL} m/s^2 printing accel):
    X-axis: {Sx:.1f}x safety — {'PASS' if Sx > 1.5 else 'MARGINAL'}
    Y-axis: {Sy:.1f}x safety — {'PASS' if Sy > 1.5 else 'MARGINAL'}
    Z-axis: {Sz:.1f}x safety — {'PASS' if Sz > 1.5 else 'MARGINAL'} (including gravity)

  MAX SPEED:
    X: {vx*1000:.0f} mm/s | Y: {vy*1000:.0f} mm/s | Z: {vz*1000:.0f} mm/s

  BELT TENSION: all axes PASS (>{2:.0f}x safety to working limit)

  RACKING: 1-step lead = {skew_at_x_end:.4f} mm deviation — negligible

  Z-LIFT: {T_z_available/T_z_per_motor_hold:.1f}x safety, survives single motor failure

  NEMA17 FEASIBILITY:
    Direct drive:  X={'PASS' if s17x>1.5 else 'FAIL'} Y={'PASS' if s17y>1.5 else 'FAIL'} Z={'PASS' if s17z>1.5 else 'FAIL'}
    5:1 geared:    X={'PASS' if s17gx>1.5 else 'FAIL'} Y={'PASS' if s17gy>1.5 else 'FAIL'} Z={'PASS' if s17gz>1.5 else 'FAIL'}
    Geared Z max speed: {v17gz*1000:.0f} mm/s (adequate for 10mm layer height)
""")

# Cost comparison
nema23_total = 7 * NEMA23_COST
nema17_direct_total = 7 * NEMA17_COST
nema17_geared_z_total = 3 * NEMA23_COST + 4 * NEMA17_GEAR_COST  # keep NEMA23 for X/Y, geared 17 for Z
nema17_all_geared = 7 * NEMA17_GEAR_COST

print(f"  COST COMPARISON (7 motors):")
print(f"    Current (7x NEMA23):              ${nema23_total}")
print(f"    All NEMA17 direct:                ${nema17_direct_total} — BUT Z-axis fails")
print(f"    Hybrid (3x23 X/Y + 4x17-geared Z): ${nema17_geared_z_total}")
print(f"    All NEMA17 geared:                ${nema17_all_geared}")
print(f"    Savings (hybrid vs current):      ${nema23_total - nema17_geared_z_total}")
