import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.patches import FancyArrowPatch, Arc, Circle
import matplotlib.animation as animation

# Physical Constants
G = 9.81
RHO_WATER = 1025.0     # kg/m^3 (Sea water)
RHO_BONITO = 1050.0    # kg/m^3 (Bonito fish density)
DRUM_RADIUS = 0.25     # m
VM = 4.0               # Mechanical advantage (polipasto 4x)
EFFICIENCY = 0.85      # Winch transmission efficiency
H_BOOM = 3.4           # m (Altura vertical de la punta de la pluma sobre el CG del buque)

# Motor Specs (Name, Power in Watts)
MOTORS = {
    "Yanmar 3TNV88": 18000.0,
    "Caterpillar C1.5": 15000.0,
    "Chongqing Mini": 12000.0
}

# Initial State
mass = 500.0           # kg
v_winch_set = 0.5      # m/s
v_current_set = 1.5    # m/s (transverse current speed)
k_cable = 5000.0       # N/m (Cable stiffness)
c_cable = 300.0        # N*s/m (Cable damping)
selected_motor = "Yanmar 3TNV88"

# Simulation Time & Solver State
dt = 0.005             # Physics timestep (s)
time = 0.0
L_nominal = 15.0       # Nominal cable length (m)
y_net = -10.0          # Net position (m)
v_net = 0.0            # Net velocity (m/s)

# History for Plotting
time_hist = []
tension_hist = []
power_hist = []
drag_hist = []
buoyancy_hist = []

import matplotlib.gridspec as gridspec

# Matplotlib Figure Setup
plt.rcParams['font.family'] = 'sans-serif'
fig = plt.figure(figsize=(15, 10.5), facecolor='#FFFFFF')
fig.canvas.manager.set_window_title('Simulador de Dinámica del Winche Pesquero (Bonito)')

# Grid Layout
gs = gridspec.GridSpec(2, 3, figure=fig)
ax_sim = fig.add_subplot(gs[:, :-1], facecolor='#FFFFFF')
ax_plots = fig.add_subplot(gs[0, -1], facecolor='#FFFFFF')
ax_power = fig.add_subplot(gs[1, -1], facecolor='#FFFFFF')

# Adjust layout to fit widgets at bottom
plt.subplots_adjust(bottom=0.25, left=0.05, right=0.97, top=0.94, wspace=0.3, hspace=0.35)

# Initialize lines/plots
ax_sim.set_xlim(-12, 12)
ax_sim.set_ylim(-13.5, 6.0)
ax_sim.set_title("Diagrama de Cuerpo Libre (DCL) Dinámico", color='#0B2545', fontsize=11, fontweight='bold')
ax_sim.set_aspect('equal')
ax_sim.xaxis.set_visible(False)
ax_sim.yaxis.set_visible(False)
for spine in ax_sim.spines.values():
    spine.set_visible(False)

# ──────────────────────────────────────────────────────────
#  STATIC DCL ELEMENTS (created once, updated in animate)
# ──────────────────────────────────────────────────────────

# 1. Water fill (cyan background below water line y=0)
water_fill = ax_sim.fill_between(
    np.linspace(-12, 12, 100), -20, 0,
    color='#E0F2FE', alpha=0.5, zorder=0
)

# 2. Water surface wave line
wave_line, = ax_sim.plot([], [], color='#0284C7', linewidth=2.5, zorder=2)

# 3. "Nivel del mar" label
ax_sim.text(4.8, 0.4, "Nivel del mar", color='#0369A1', fontsize=7,
            fontweight='bold', fontstyle='italic', zorder=10)

# 4. Boat hull polygon
# 9. Boat elements
import matplotlib.patches as patches
boat_patch = plt.Polygon(np.zeros((4, 2)), color='#64748B', zorder=5)
cabin_patch = plt.Polygon(np.zeros((4, 2)), color='#94A3B8', zorder=5)
ax_sim.add_patch(boat_patch)
ax_sim.add_patch(cabin_patch)

# Cabin Windows
window1 = patches.Rectangle((0,0), 1, 1, facecolor='#E0F2FE', edgecolor='#475569', lw=1, zorder=6)
window2 = patches.Rectangle((0,0), 1, 1, facecolor='#E0F2FE', edgecolor='#475569', lw=1, zorder=6)
ax_sim.add_patch(window1)
ax_sim.add_patch(window2)

# 6. Boom (pluma de carga)
boom_line, = ax_sim.plot([], [], color='#334155', linewidth=5, solid_capstyle='round', zorder=4)
boom_dot_base = plt.Circle((0, 0), 0.12, color='#475569', zorder=5)
ax_sim.add_patch(boom_dot_base)
boom_dot_tip = plt.Circle((0, 0), 0.10, color='#475569', zorder=5)
ax_sim.add_patch(boom_dot_tip)

# 7. Winch cable from boom tip to drum
winch_cable_line, = ax_sim.plot([], [], color='#94A3B8', linewidth=1.2, zorder=3)
# Winch drum circle
drum_circle = plt.Circle((-2.0, 1.35), 0.15, color='#475569', zorder=5)
ax_sim.add_patch(drum_circle)

# 8. Cable line (from boom tip to net)
cable_line, = ax_sim.plot([], [], color='#1E293B', linewidth=1.8, zorder=3)

# 9. Net circle (orange with light fill)
net_circle = plt.Circle((0, -5), 0.7, facecolor='#FFF7ED', edgecolor='#EA580C',
                         linewidth=2.0, zorder=6)
ax_sim.add_patch(net_circle)

# 10. Net grid lines (cross-hatch pattern inside the circle) - 4 horizontal + 4 vertical
net_grid_lines = []
for i in range(7):
    lh, = ax_sim.plot([], [], color='#FB923C', linewidth=0.6, zorder=7)
    lv, = ax_sim.plot([], [], color='#FB923C', linewidth=0.6, zorder=7)
    net_grid_lines.append((lh, lv))

# 11. CM dot on net center
cm_dot = plt.Circle((0, -5), 0.06, color='#0F172A', zorder=8)
ax_sim.add_patch(cm_dot)

# 12. "CM" and "Bonito" labels
cm_label = ax_sim.text(0, 0, "CM", color='#0F172A', fontsize=7, fontweight='bold',
                       ha='right', va='bottom', zorder=9,
                       bbox=dict(facecolor='#FFF7ED', edgecolor='none', pad=0.8, alpha=0.9))
bonito_label = ax_sim.text(0, 0, "Bonito", color='#0F172A', fontsize=7, fontweight='bold',
                           ha='left', va='bottom', zorder=9, fontstyle='italic',
                           bbox=dict(facecolor='#FFF7ED', edgecolor='none', pad=0.8, alpha=0.9))

# 13. "Polipasto" label near boom tip
polipasto_label = ax_sim.text(0, 0, "Polipasto", color='#475569', fontsize=6,
                               fontweight='bold', ha='center', va='bottom', zorder=10)

# ── DCL VECTOR ARROWS (main force vectors) ──
bbox_props = dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=0.3)

# Weight P (Red, down)
arrow_P = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                           arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=2.5,
                                          mutation_scale=14),
                           zorder=8, annotation_clip=True)
label_P = ax_sim.text(0, 0, "", color='#DC2626', fontsize=8, fontweight='bold',
                      ha='center', va='top', zorder=9, bbox=bbox_props, clip_on=True)

# Drag Fd (Orange, inclined down-left)
arrow_Fd = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                            arrowprops=dict(arrowstyle="-|>", color='#C2410C', lw=2.2,
                                           mutation_scale=13),
                            zorder=8, annotation_clip=True)
label_Fd = ax_sim.text(0, 0, "", color='#C2410C', fontsize=8, fontweight='bold',
                       ha='right', va='top', zorder=9, bbox=bbox_props, clip_on=True)

# Tension T (Blue, inclined up-right)
arrow_T = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                           arrowprops=dict(arrowstyle="-|>", color='#2563EB', lw=2.8,
                                          mutation_scale=15),
                           zorder=8, annotation_clip=True)
label_T = ax_sim.text(0, 0, "", color='#2563EB', fontsize=9, fontweight='bold',
                      ha='left', va='bottom', zorder=9, bbox=bbox_props, clip_on=True)

# ── DCL COMPONENT VECTORS (dashed) ──

# Tx component (Blue dashed, horizontal right from CM)
arrow_Tx = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                            arrowprops=dict(arrowstyle="-|>", color='#1E40AF', lw=1.3,
                                           linestyle='dashed', mutation_scale=10),
                            zorder=7, annotation_clip=True)
label_Tx = ax_sim.text(0, 0, "", color='#1E40AF', fontsize=6.5, fontweight='bold',
                       ha='center', va='center', zorder=9, bbox=bbox_props, clip_on=True)

# Ty component (Blue dashed, vertical up from Tx tip)
arrow_Ty = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                            arrowprops=dict(arrowstyle="-|>", color='#1E40AF', lw=1.3,
                                           linestyle='dashed', mutation_scale=10),
                            zorder=7, annotation_clip=True)
label_Ty = ax_sim.text(0, 0, "", color='#1E40AF', fontsize=6.5, fontweight='bold',
                       ha='center', va='center', zorder=9, bbox=bbox_props, clip_on=True)

# Fdx component (Orange dashed, horizontal left from CM)
arrow_Fdx = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                             arrowprops=dict(arrowstyle="-|>", color='#9A3412', lw=1.3,
                                            linestyle='dashed', mutation_scale=10),
                             zorder=7, annotation_clip=True)
label_Fdx = ax_sim.text(0, 0, "", color='#9A3412', fontsize=6.5, fontweight='bold',
                        ha='center', va='center', zorder=9, bbox=bbox_props, clip_on=True)

# Fdy component (Orange dashed, vertical down from Fdx tip)
arrow_Fdy = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                             arrowprops=dict(arrowstyle="-|>", color='#9A3412', lw=1.3,
                                            linestyle='dashed', mutation_scale=10),
                             zorder=7, annotation_clip=True)
label_Fdy = ax_sim.text(0, 0, "", color='#9A3412', fontsize=6.5, fontweight='bold',
                        ha='center', va='center', zorder=9, bbox=bbox_props, clip_on=True)

# ── DCL 2: BOAT VECTORS (Reaction & Equilibrium) ──
boat_cg_dot = plt.Circle((0, 0), 0.08, color='#0F172A', zorder=10)
ax_sim.add_patch(boat_cg_dot)
label_cg_boat = ax_sim.text(0, 0, "CG", color='#0F172A', fontsize=7, fontweight='bold',
                            ha='right', va='bottom', zorder=11,
                            bbox=dict(facecolor='#FFF7ED', edgecolor='none', pad=0.8, alpha=0.9), clip_on=True)

arrow_P_buque = ax_sim.annotate('', xy=(0,0), xytext=(0,0), arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=2.5, mutation_scale=14), zorder=8, annotation_clip=True)
label_P_buque = ax_sim.text(0, 0, "", color='#DC2626', fontsize=8, fontweight='bold', ha='center', va='top', zorder=9, bbox=bbox_props, clip_on=True)

arrow_N_casco = ax_sim.annotate('', xy=(0,0), xytext=(0,0), arrowprops=dict(arrowstyle="-|>", color='#16A34A', lw=2.5, mutation_scale=14), zorder=8, annotation_clip=True)
label_N_casco = ax_sim.text(0, 0, "", color='#16A34A', fontsize=8, fontweight='bold', ha='center', va='bottom', zorder=9, bbox=bbox_props, clip_on=True)

arrow_F_prop = ax_sim.annotate('', xy=(0,0), xytext=(0,0), arrowprops=dict(arrowstyle="-|>", color='#D97706', lw=2.5, mutation_scale=14), zorder=8, annotation_clip=True)
label_F_prop = ax_sim.text(0, 0, "", color='#D97706', fontsize=8, fontweight='bold', ha='left', va='center', zorder=9, bbox=bbox_props, clip_on=True)

arrow_Tp = ax_sim.annotate('', xy=(0,0), xytext=(0,0), arrowprops=dict(arrowstyle="-|>", color='#1E40AF', lw=2.8, mutation_scale=15), zorder=8, annotation_clip=True)
label_Tp = ax_sim.text(0, 0, "", color='#1E40AF', fontsize=9, fontweight='bold', ha='right', va='top', zorder=9, bbox=bbox_props, clip_on=True)

arrow_Tpy = ax_sim.annotate('', xy=(0,0), xytext=(0,0), arrowprops=dict(arrowstyle="-|>", color='#3B82F6', lw=1.3, linestyle='dashed', mutation_scale=10), zorder=7, annotation_clip=True)
label_Tpy = ax_sim.text(0, 0, "", color='#3B82F6', fontsize=6.5, fontweight='bold', ha='left', va='center', zorder=9, bbox=bbox_props, clip_on=True)

arrow_Tpx = ax_sim.annotate('', xy=(0,0), xytext=(0,0), arrowprops=dict(arrowstyle="-|>", color='#3B82F6', lw=1.3, linestyle='dashed', mutation_scale=10), zorder=7, annotation_clip=True)
label_Tpx = ax_sim.text(0, 0, "", color='#3B82F6', fontsize=6.5, fontweight='bold', ha='center', va='top', zorder=9, bbox=bbox_props, clip_on=True)

# DCL 2: Height dimension line h (CG to boom tip)
h_dim_line, = ax_sim.plot([], [], color='#475569', linewidth=1.0, linestyle=':', zorder=6)
h_dim_arrow, = ax_sim.plot([], [], color='#475569', linewidth=1.2, zorder=6)
label_h = ax_sim.text(0, 0, "", color='#0F172A', fontsize=10, fontweight='bold',
                      ha='left', va='center', zorder=9, clip_on=True)

# DCL 2: Theta arc on boom tip
arc_theta2_line, = ax_sim.plot([], [], color='#0F172A', linewidth=1.2, zorder=8)
label_theta2 = ax_sim.text(0, 0, "", color='#0F172A', fontsize=8, fontweight='bold',
                           ha='center', va='center', zorder=9)

# ── DCL REFERENCE LINES ──

# Vertical reference dashed line through CM
ref_vertical_line, = ax_sim.plot([], [], color='#9CA3AF', linewidth=0.8,
                                  linestyle='--', zorder=6)

# Projection line from T tip to vertical axis (dotted)
proj_T_line, = ax_sim.plot([], [], color='#9CA3AF', linewidth=0.7,
                            linestyle=':', zorder=6)

# Projection line from Fd tip to vertical axis (dotted)
proj_Fd_line, = ax_sim.plot([], [], color='#9CA3AF', linewidth=0.7,
                             linestyle=':', zorder=6)

# ── ANGLE ARCS ──
arc_theta_line, = ax_sim.plot([], [], color='#0F172A', linewidth=1.2, zorder=8)
label_theta = ax_sim.text(0, 0, "", color='#0F172A', fontsize=8, fontweight='bold',
                          ha='center', va='center', zorder=9)

arc_phi_line, = ax_sim.plot([], [], color='#0F172A', linewidth=1.2, zorder=8)
label_phi = ax_sim.text(0, 0, "", color='#0F172A', fontsize=8, fontweight='bold',
                        ha='center', va='center', zorder=9)

# ── COORDINATE AXES (small reference frame in bottom-left) ──
ax_sim.annotate('', xy=(-4.8, -8.5), xytext=(-5.5, -8.5),
                arrowprops=dict(arrowstyle='->', color='#6B7280', lw=1.2), zorder=10)
ax_sim.text(-4.7, -8.5, 'x', color='#6B7280', fontsize=8, fontweight='bold',
            ha='left', va='center')
ax_sim.annotate('', xy=(-5.5, -7.8), xytext=(-5.5, -8.5),
                arrowprops=dict(arrowstyle='->', color='#6B7280', lw=1.2), zorder=10)
ax_sim.text(-5.5, -7.6, 'y', color='#6B7280', fontsize=8, fontweight='bold',
            ha='center', va='bottom')

# ── CURRENT ARROWS ──
arrow_curr1 = ax_sim.annotate('v_corr', xy=(0,0), xytext=(0,0),
                              arrowprops=dict(arrowstyle="->", color='#0096C7', lw=1.5, alpha=0.6),
                              color='#0096C7', fontsize=7, alpha=0.8, fontweight='bold')
arrow_curr2 = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                              arrowprops=dict(arrowstyle="->", color='#0096C7', lw=1.5, alpha=0.6))
arrow_curr3 = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                              arrowprops=dict(arrowstyle="->", color='#0096C7', lw=1.5, alpha=0.6))

# ── HIDDEN BUOYANCY ARROW (kept for compatibility) ──
arrow_E = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                           arrowprops=dict(arrowstyle="->", color='#16A34A', lw=0),
                           visible=False)

# ──────────────────────────────────────────────────────────
#  TELEMETRY & PLOTS
# ──────────────────────────────────────────────────────────

# Plot 1: Tension vs Time
ax_plots.set_title("Tensión Dinámica en la Red", color='#0B2545', fontsize=10, fontweight='bold')
ax_plots.set_xlabel("Tiempo (s)", color='#334155', fontsize=8)
ax_plots.set_ylabel("Tensión (N)", color='#334155', fontsize=8)
ax_plots.tick_params(colors='#334155', labelsize=8)
ax_plots.grid(True, color='#E2E8F0', linestyle='--')
tension_line, = ax_plots.plot([], [], color='#2563EB', linewidth=1.5)

# Plot 2: Power vs Time
ax_power.set_title("Potencia del Motor Requerida vs Límite", color='#0B2545', fontsize=10, fontweight='bold')
ax_power.set_xlabel("Tiempo (s)", color='#334155', fontsize=8)
ax_power.set_ylabel("Potencia (kW)", color='#334155', fontsize=8)
ax_power.tick_params(colors='#334155', labelsize=8)
ax_power.grid(True, color='#E2E8F0', linestyle='--')
power_line, = ax_power.plot([], [], color='#16A34A', linewidth=1.5)
motor_limit_line = ax_power.axhline(y=18.0, color='#DC2626', linestyle=':', label='Límite Motor')
ax_power.legend(loc='upper right', fontsize=8, labelcolor='#1E293B', facecolor='#FFFFFF', edgecolor='#CBD5E1')

# Text Telemetry Box
telemetry_text = ax_sim.text(-11.5, 5.5, "", color='#1E293B', fontfamily='monospace', fontsize=7.5,
                             va='top', ha='left', zorder=15,
                             bbox=dict(facecolor='#F1F5F9', alpha=0.95, edgecolor='#CBD5E1',
                                      boxstyle='round,pad=0.4'))

# ──────────────────────────────────────────────────────────
#  WIDGETS (Sliders, Radio Buttons, Buttons)
# ──────────────────────────────────────────────────────────

axcolor = '#F1F5F9'
slider_text_color = '#1E293B'

# Slide 1: Mass
ax_mass = plt.axes([0.1, 0.18, 0.3, 0.025], facecolor=axcolor)
s_mass = Slider(ax_mass, 'Masa (kg)', 100.0, 1500.0, valinit=500.0, valstep=50.0, color='#0284C7')
s_mass.label.set_color(slider_text_color)
s_mass.valtext.set_color(slider_text_color)

# Slide 2: Winch Speed
ax_speed = plt.axes([0.1, 0.13, 0.3, 0.025], facecolor=axcolor)
s_speed = Slider(ax_speed, 'V. Izaje (m/s)', 0.1, 2.0, valinit=0.5, valstep=0.1, color='#0284C7')
s_speed.label.set_color(slider_text_color)
s_speed.valtext.set_color(slider_text_color)

# Slide 3: Marine Current
ax_current = plt.axes([0.1, 0.08, 0.3, 0.025], facecolor=axcolor)
s_current = Slider(ax_current, 'Corriente (m/s)', 0.0, 2.5, valinit=1.5, valstep=0.1, color='#0284C7')
s_current.label.set_color(slider_text_color)
s_current.valtext.set_color(slider_text_color)

# Slide 4: Cable Stiffness
ax_stiff = plt.axes([0.55, 0.18, 0.3, 0.025], facecolor=axcolor)
s_stiff = Slider(ax_stiff, 'Rigidez Cable (N/m)', 1000.0, 10000.0, valinit=5000.0, valstep=500.0, color='#0284C7')
s_stiff.label.set_color(slider_text_color)
s_stiff.valtext.set_color(slider_text_color)

# Radio Buttons: Motor auxiliary select
ax_motor = plt.axes([0.88, 0.02, 0.1, 0.12], facecolor='#FFFFFF')
radio_motor = RadioButtons(ax_motor, ('Yanmar', 'Cat C1.5', 'Chongqing'), active=0, activecolor='#0284C7')
for label in radio_motor.labels:
    label.set_color('#1E293B')
    label.set_fontsize(8)

# Radio Buttons: Catch State (Submerged / Air)
ax_state = plt.axes([0.55, 0.08, 0.15, 0.04], facecolor='#FFFFFF')
radio_state = RadioButtons(ax_state, ('Sumergida', 'En Aire'), active=0, activecolor='#16A34A')
for label in radio_state.labels:
    label.set_color('#1E293B')
    label.set_fontsize(8)

# Radio Buttons: Scenario Select (Escenario 1 / Escenario 2)
ax_scenario = plt.axes([0.55, 0.13, 0.25, 0.04], facecolor='#FFFFFF')
radio_scenario = RadioButtons(ax_scenario, ('Esc. 1 (Mar en Calma)', 'Esc. 2 (Corriente Marina)'), active=1, activecolor='#0284C7')
for label in radio_scenario.labels:
    label.set_color('#1E293B')
    label.set_fontsize(8)

def change_scenario(label):
    if 'Esc. 1' in label:
        if s_current.val != 0.0:
            s_current.set_val(0.0)
    else:
        if s_current.val == 0.0:
            s_current.set_val(1.5)
radio_scenario.on_clicked(change_scenario)

def get_selected_motor_specs():
    m_name = radio_motor.value_selected
    if m_name == 'Yanmar':
        return "Yanmar 3TNV88", 18000.0
    elif m_name == 'Cat C1.5':
        return "Caterpillar C1.5", 15000.0
    else:
        return "Chongqing Mini", 12000.0

# Reset Button
ax_reset = plt.axes([0.72, 0.08, 0.1, 0.04], facecolor='#F1F5F9')
btn_reset = Button(ax_reset, 'Reiniciar', color='#0B2545', hovercolor='#134074')
btn_reset.label.set_color('#FFFFFF')
btn_reset.label.set_fontsize(9)

def reset_sim(event):
    global time, y_net, v_net, L_nominal, time_hist, tension_hist, power_hist
    time = 0.0
    y_net = -10.0
    v_net = 0.0
    L_nominal = 15.0
    time_hist.clear()
    tension_hist.clear()
    power_hist.clear()
btn_reset.on_clicked(reset_sim)


# ──────────────────────────────────────────────────────────
#  VECTOR SCALING UTILITY
# ──────────────────────────────────────────────────────────
def vectorScalePhys(force_val):
    """Logarithmic-linear visual scaling for vectors so they don't grow too huge or small."""
    val = abs(force_val)
    if val <= 0:
        return 0
    return max(0.5, min(4.0, 0.5 + (val / 2500.0)))


# ──────────────────────────────────────────────────────────
#  NET GRID HELPER
# ──────────────────────────────────────────────────────────
def update_net_grid(cx, cy, radius):
    """Update cross-hatch grid lines clipped inside the net circle."""
    r = radius * 0.75  # inner grid region
    n = len(net_grid_lines)
    spacing = 2 * r / (n + 1)
    for i, (lh, lv) in enumerate(net_grid_lines):
        offset = -r + spacing * (i + 1)
        # horizontal line at y = cy + offset, clipped by circle
        if abs(offset) < r:
            half_w = np.sqrt(r**2 - offset**2)
            lh.set_data([cx - half_w, cx + half_w], [cy + offset, cy + offset])
            lv.set_data([cx + offset, cx + offset], [cy - half_w, cy + half_w])
        else:
            lh.set_data([], [])
            lv.set_data([], [])


# ──────────────────────────────────────────────────────────
#  ANIMATION LOOP (Physics + Rendering)
# ──────────────────────────────────────────────────────────
def animate(frame):
    global time, y_net, v_net, L_nominal, time_hist, tension_hist, power_hist

    # 1. Read current slider values
    m = s_mass.val
    v_winch = s_speed.val
    v_curr = s_current.val
    k = s_stiff.val
    is_submerged = (radio_state.value_selected == 'Sumergida')

    # Sync radio button if slider was moved manually
    if v_curr == 0.0 and radio_scenario.value_selected != 'Esc. 1 (Mar en Calma)':
        radio_scenario.eventson = False
        radio_scenario.set_active(0)
        radio_scenario.eventson = True
    elif v_curr > 0.0 and radio_scenario.value_selected != 'Esc. 2 (Corriente Marina)':
        radio_scenario.eventson = False
        radio_scenario.set_active(1)
        radio_scenario.eventson = True

    m_name, m_power = get_selected_motor_specs()
    motor_limit_line.set_ydata([m_power / 1000.0, m_power / 1000.0])
    motor_limit_line.set_label(f'Límite {m_name}')
    ax_power.legend(loc='upper right', fontsize=8, labelcolor='#1E293B', facecolor='#FFFFFF', edgecolor='#CBD5E1')

    # Running sub-steps for solver stability (Euler-Cromer)
    substeps = 10
    dt_sub = dt / substeps

    # Define weight outside loop
    weight = m * G

    for _ in range(substeps):
        time += dt_sub

        # Boom tip position (crane end) is stationary (no waves)
        y_tip = 5.0
        v_tip = 0.0

        # Winch winds the nominal cable length
        L_nominal = max(2.0, L_nominal - v_winch * dt_sub)

        # Cable elasticity model: vertical stretch
        stretch = y_tip - y_net - L_nominal

        # Hooke's Law + viscous damping (active only under extension)
        if stretch > 0:
            T_y = k * stretch + c_cable * (v_tip - v_net + v_winch)
            if T_y < 0:
                T_y = 0.0
        else:
            T_y = 0.0

        # Archimedes Buoyancy is removed (set to 0.0)
        buoyancy = 0.0

        # Hydrodynamic Drag in 2D
        if is_submerged:
            v_rel_x = v_curr
            v_rel_y = -v_net
            v_rel_mag = np.sqrt(v_rel_x**2 + v_rel_y**2)
            A_proj = 0.5 * (m / 100.0)**(2/3)
            # Drag force magnitude:
            F_drag_mag = 0.5 * 1.2 * RHO_WATER * A_proj * v_rel_mag**2
            # Components:
            F_dx = F_drag_mag * (v_curr / v_rel_mag) if v_rel_mag > 0 else 0.0
            F_dy = F_drag_mag * (v_net / v_rel_mag) if v_rel_mag > 0 else 0.0
        else:
            F_dx = 0.0
            F_dy = 0.0

        # Horizontal equilibrium: T_x = F_dx
        T_x = F_dx

        # Newton's Second Law for vertical motion: m * a_y = T_y - weight - F_dy
        a_net = (T_y - weight - F_dy) / m

        # Integrate vertical motion
        v_net += a_net * dt_sub
        y_net += v_net * dt_sub

        # Calculate Tension magnitude for current step
        Tension = np.sqrt(T_x**2 + T_y**2)

    # Calculations for Winch side (consider mechanical advantage VM = 4)
    T_winch = Tension / VM
    torque_drum = T_winch * DRUM_RADIUS
    power_watts = (Tension * v_winch) / EFFICIENCY
    power_kw = power_watts / 1000.0
    power_hp = power_kw * 1.34102

    # Append to History
    time_hist.append(time)
    tension_hist.append(Tension)
    power_hist.append(power_kw)

    # Cap history length to keep plot fast
    max_history = 300
    if len(time_hist) > max_history:
        time_hist.pop(0)
        tension_hist.pop(0)
        power_hist.pop(0)

    # 2. Update Plots
    tension_line.set_data(time_hist, tension_hist)
    power_line.set_data(time_hist, power_hist)

    if len(time_hist) > 1:
        ax_plots.set_xlim(time_hist[0], time_hist[-1])
        ax_plots.set_ylim(0, max(1000.0, max(tension_hist) * 1.1))

        ax_power.set_xlim(time_hist[0], time_hist[-1])
        ax_power.set_ylim(0, max(5.0, max(max(power_hist), m_power / 1000.0) * 1.1))

    # ══════════════════════════════════════════════
    # 3. UPDATE ANIMATION / DCL ELEMENTS
    # ══════════════════════════════════════════════
    y_boat = 0.0
    y_tip = 5.0

    # Wave line (flat in calm water, with minor decorative ripples)
    x_vals = np.linspace(-12, 12, 200)
    y_wave = 0.15 + 0.08 * np.sin(x_vals * 2.0 + 3.0 * time)
    wave_line.set_data(x_vals, y_wave)

    # Boat Hull Polygon (Facing Right — bow at +x, stern at -x)
    # Matches TikZ Figure 2: (-3.0,0)--(1.0,0)--(1.8,1.2)--(-3.5,1.2)
    boat_x = [-3.5, 1.0, 1.8, -4.0]
    boat_y = [y_boat, y_boat, y_boat + 1.2, y_boat + 1.2]
    boat_patch.set_xy(np.column_stack((boat_x, boat_y)))

    # Cabin (at stern, left side — matches TikZ: (-2.2,1.2) to (-0.5,2.2))
    cabin_x = [-2.5, -0.5, -0.5, -2.5]
    cabin_y = [y_boat + 1.2, y_boat + 1.2, y_boat + 2.2, y_boat + 2.2]
    cabin_patch.set_xy(np.column_stack((cabin_x, cabin_y)))

    # Update Windows (inside cabin)
    window1.set_bounds(-2.2, y_boat + 1.4, 0.5, 0.5)
    window2.set_bounds(-1.3, y_boat + 1.4, 0.5, 0.5)

    # Boom (extends to the RIGHT beyond the bow — matches TikZ: (0.6,1.2)--(3.5,4.0))
    boom_base_x, boom_base_y = 0.5, y_boat + 1.2
    boom_tip_x, boom_tip_y = 3.5, y_tip
    boom_line.set_data([boom_base_x, boom_tip_x], [boom_base_y, boom_tip_y])
    boom_dot_base.center = (boom_base_x, boom_base_y)
    boom_dot_tip.center = (boom_tip_x, boom_tip_y)
    polipasto_label.set_position((boom_tip_x, boom_tip_y + 0.2))

    # Winch cable and drum (at stern — matches TikZ: drum at (-2.8, 1.35))
    drum_circle.center = (-3.0, y_boat + 1.35)
    winch_cable_line.set_data([boom_tip_x, -3.0], [boom_tip_y, y_boat + 1.35])

    # Compute cable inclination angle theta
    theta = np.arctan2(T_x, T_y) if T_y > 0 else 0.0
    x_tip = boom_tip_x
    x_net = x_tip - (y_tip - y_net) * np.tan(theta)
    x_net = max(-5.0, min(5.0, x_net))

    # Cable line
    cable_line.set_data([x_tip, x_net], [y_tip, y_net])

    # Net
    net_radius = 0.7
    net_circle.center = (x_net, y_net)

    # Update net grid
    update_net_grid(x_net, y_net, net_radius)

    # CM dot and labels
    cm_dot.center = (x_net, y_net)
    cm_label.set_position((x_net - 0.15, y_net + 0.15))
    bonito_label.set_position((x_net + 0.15, y_net + 0.15))

    # ══════════════════════════════════════════════
    # 4. DCL FORCE VECTORS & COMPONENTS
    # ══════════════════════════════════════════════
    vs = 1.3  # Increase base visual scale multiplier to spread vectors
    
    def scale_vec(val):
        return vectorScalePhys(val) * vs

    # ── WEIGHT P (Red, straight down) ──
    P_scale = scale_vec(weight) * 0.4  # Restrict P scale
    P_end_x = x_net
    P_end_y = y_net - P_scale
    arrow_P.set_position((x_net, y_net))
    arrow_P.xy = (P_end_x, P_end_y)
    label_P.set_position((P_end_x, P_end_y - 0.4))
    label_P.set_text(f"$\\vec{{P}}$ = {int(weight)} N")

    # ── VERTICAL REFERENCE LINE through CM ──
    ref_vertical_line.set_data([x_net, x_net], [P_end_y - 0.8, y_net + P_scale + 2.0])

    # ── DRAG Fd (Orange, diagonal down-left) ──
    Fd_mag = np.sqrt(F_dx**2 + F_dy**2) if is_submerged else 0.0
    if is_submerged and Fd_mag > 0.5:
        Fd_scale = scale_vec(Fd_mag)
        # Direction: Fd points in -x (opposing current) and -y (opposing upward motion)
        Fd_dir_x = -F_dx / Fd_mag
        Fd_dir_y = -abs(F_dy) / Fd_mag
        Fd_end_x = x_net + Fd_dir_x * Fd_scale
        Fd_end_y = y_net + Fd_dir_y * Fd_scale

        arrow_Fd.set_position((x_net, y_net))
        arrow_Fd.xy = (Fd_end_x, Fd_end_y)
        label_Fd.set_position((Fd_end_x - 0.2, Fd_end_y - 0.2))
        label_Fd.set_ha('right')
        label_Fd.set_va('top')
        label_Fd.set_text(f"$\\vec{{F}}_d$ = {int(Fd_mag)} N")

        # Component Fdx (horizontal, left)
        Fdx_end_x = x_net + Fd_dir_x * Fd_scale * (F_dx / Fd_mag)
        arrow_Fdx.set_position((x_net, y_net))
        arrow_Fdx.xy = (Fdx_end_x, y_net)
        label_Fdx.set_position((Fdx_end_x - 0.1, y_net + 0.35))
        label_Fdx.set_ha('right')
        label_Fdx.set_text(f"$F_{{d,x}}$={int(F_dx)}N")

        # Component Fdy (vertical, down from Fdx tip)
        arrow_Fdy.set_position((Fdx_end_x, y_net))
        arrow_Fdy.xy = (Fdx_end_x, Fd_end_y)
        label_Fdy.set_position((Fdx_end_x - 0.2, Fd_end_y - 0.1))
        label_Fdy.set_va('top')
        label_Fdy.set_text(f"$F_{{d,y}}$={int(abs(F_dy))}N")

        # Projection line from Fd tip to vertical axis
        proj_Fd_line.set_data([Fd_end_x, x_net], [Fd_end_y, Fd_end_y])

        # ── ANGLE ARC φ (from negative y-axis to Fd vector) ──
        phi_deg = np.degrees(np.arctan2(F_dx, abs(F_dy))) if abs(F_dy) > 0.01 else 90.0
        if phi_deg > 2.0:
            arc_r = 1.2
            phi_angles = np.linspace(270, 270 - phi_deg, 20) * np.pi / 180.0
            arc_phi_x = x_net + arc_r * np.cos(phi_angles)
            arc_phi_y = y_net + arc_r * np.sin(phi_angles)
            arc_phi_line.set_data(arc_phi_x, arc_phi_y)
            label_phi.set_position((x_net - 0.4, y_net - arc_r - 0.25))
            label_phi.set_text(f"φ={phi_deg:.0f}°")
        else:
            arc_phi_line.set_data([], [])
            label_phi.set_text("")
    else:
        # No drag - hide components
        arrow_Fd.set_position((x_net, y_net))
        arrow_Fd.xy = (x_net, y_net)
        label_Fd.set_text("")
        arrow_Fdx.set_position((0, 0)); arrow_Fdx.xy = (0, 0); label_Fdx.set_text("")
        arrow_Fdy.set_position((0, 0)); arrow_Fdy.xy = (0, 0); label_Fdy.set_text("")
        proj_Fd_line.set_data([], [])
        arc_phi_line.set_data([], [])
        label_phi.set_text("")

    # ── TENSION T (Blue, diagonal up-right along cable) ──
    if Tension > 1:
        T_scale = scale_vec(Tension)
        T_dir_x = T_x / Tension
        T_dir_y = T_y / Tension
        T_end_x = x_net + T_dir_x * T_scale
        T_end_y = y_net + T_dir_y * T_scale

        arrow_T.set_position((x_net, y_net))
        arrow_T.xy = (T_end_x, T_end_y)
        label_T.set_position((T_end_x + 0.2, T_end_y + 0.2))
        label_T.set_ha('left')
        label_T.set_va('bottom')
        label_T.set_text(f"$\\vec{{T}}$ = {int(Tension)} N")

        # Component Tx (horizontal, right)
        Tx_end_x = x_net + T_dir_x * T_scale
        arrow_Tx.set_position((x_net, y_net))
        arrow_Tx.xy = (Tx_end_x, y_net)
        if T_x > 5:
            label_Tx.set_position((Tx_end_x + 0.1, y_net - 0.45))
            label_Tx.set_ha('left')
            label_Tx.set_text(f"$T_x$={int(T_x)}N")
        else:
            label_Tx.set_text("")

        # Component Ty (vertical, up from Tx tip)
        arrow_Ty.set_position((Tx_end_x, y_net))
        arrow_Ty.xy = (Tx_end_x, T_end_y)
        if T_y > 5:
            label_Ty.set_position((Tx_end_x + 0.2, T_end_y + 0.1))
            label_Ty.set_va('bottom')
            label_Ty.set_text(f"$T_y$={int(T_y)}N")
        else:
            label_Ty.set_text("")

        # Projection line from T tip to vertical axis
        proj_T_line.set_data([T_end_x, x_net], [T_end_y, T_end_y])

        # ── ANGLE ARC θ (from positive y-axis to T vector) ──
        theta_deg = np.degrees(theta)
        if theta_deg > 1.0:
            arc_r = 1.5
            theta_angles = np.linspace(90, 90 - theta_deg, 20) * np.pi / 180.0
            arc_theta_x = x_net + arc_r * np.cos(theta_angles)
            arc_theta_y = y_net + arc_r * np.sin(theta_angles)
            arc_theta_line.set_data(arc_theta_x, arc_theta_y)
            label_theta.set_position((x_net + 0.5, y_net + arc_r + 0.2))
            label_theta.set_text(f"θ={theta_deg:.1f}°")
        else:
            arc_theta_line.set_data([], [])
            label_theta.set_text("")
    else:
        arrow_T.set_position((x_net, y_net))
        arrow_T.xy = (x_net, y_net)
        label_T.set_text("")
        arrow_Tx.set_position((0, 0)); arrow_Tx.xy = (0, 0); label_Tx.set_text("")
        arrow_Ty.set_position((0, 0)); arrow_Ty.xy = (0, 0); label_Ty.set_text("")
        proj_T_line.set_data([], [])
        arc_theta_line.set_data([], [])
        label_theta.set_text("")

    # ══════════════════════════════════════════════
    # 5. DCL 2: BOAT EQUILIBRIUM VECTORS
    # ══════════════════════════════════════════════
    # CG at geometric centroid of hull polygon
    x_cg = (-3.5 + 1.0 + 1.8 + -4.0) / 4.0  # ≈ -1.175
    y_cg = y_boat + 0.6
    boat_cg_dot.center = (x_cg, y_cg)
    label_cg_boat.set_position((x_cg - 0.2, y_cg + 0.2))

    # Constant scale for boat weight (visual only)
    P_buque_scale = 1.8
    arrow_P_buque.set_position((x_cg, y_cg))
    arrow_P_buque.xy = (x_cg, y_cg - P_buque_scale)
    label_P_buque.set_position((x_cg, y_cg - P_buque_scale - 0.3))
    label_P_buque.set_text(r"$\vec{P}_{buque}$")

    # N_casco balances P_buque + Ty (roughly)
    N_scale = P_buque_scale + (T_y/Tension)*T_scale if Tension > 1 else P_buque_scale
    arrow_N_casco.set_position((x_cg, y_cg))
    arrow_N_casco.xy = (x_cg, y_cg + N_scale)
    label_N_casco.set_position((x_cg, y_cg + N_scale + 0.2))
    label_N_casco.set_text(r"$\vec{N}_{casco}$")

    # F_prop balances Tx (points to the RIGHT, toward the net)
    F_prop_scale = (T_x/Tension)*T_scale if Tension > 1 else 0.0
    if F_prop_scale > 0.1:
        arrow_F_prop.set_position((x_cg, y_cg))
        arrow_F_prop.xy = (x_cg + F_prop_scale, y_cg)
        label_F_prop.set_position((x_cg + F_prop_scale + 0.1, y_cg))
        label_F_prop.set_text(r"$\vec{F}_{prop}$")
    else:
        arrow_F_prop.set_position((x_cg, y_cg))
        arrow_F_prop.xy = (x_cg, y_cg)
        label_F_prop.set_text("")

    # Reaction T' on the boom tip (opposite direction to T)
    if Tension > 1:
        Tp_dir_x = -T_dir_x  # points LEFT (toward net)
        Tp_dir_y = -T_dir_y  # points DOWN
        Tp_end_x = boom_tip_x + Tp_dir_x * T_scale
        Tp_end_y = boom_tip_y + Tp_dir_y * T_scale

        arrow_Tp.set_position((boom_tip_x, boom_tip_y))
        arrow_Tp.xy = (Tp_end_x, Tp_end_y)
        label_Tp.set_position((Tp_end_x - 0.2, Tp_end_y - 0.2))
        label_Tp.set_text(f"$\\vec{{T}}'$")

        # T'y (vertical down from boom tip)
        Tpy_end_y = boom_tip_y + Tp_dir_y * T_scale
        arrow_Tpy.set_position((boom_tip_x, boom_tip_y))
        arrow_Tpy.xy = (boom_tip_x, Tpy_end_y)
        if T_y > 5:
            label_Tpy.set_position((boom_tip_x + 0.3, boom_tip_y + 0.5 * Tp_dir_y * T_scale))
            label_Tpy.set_ha('left')
            label_Tpy.set_text(r"$T'_y = T\cos\theta$")
        else:
            label_Tpy.set_text("")

        # T'x (horizontal left from T'y end, closing triangle)
        arrow_Tpx.set_position((boom_tip_x, Tpy_end_y))
        arrow_Tpx.xy = (Tp_end_x, Tpy_end_y)
        if T_x > 5:
            label_Tpx.set_position((boom_tip_x + 0.5 * Tp_dir_x * T_scale, Tpy_end_y - 0.3))
            label_Tpx.set_va('top')
            label_Tpx.set_text(r"$T'_x = T\sin\theta$")
        else:
            label_Tpx.set_text("")

        # Theta arc on boom tip (from vertical down to T' vector)
        theta_deg_val = np.degrees(theta)
        if theta_deg_val > 1.0:
            arc_r2 = 1.2
            arc_angles2 = np.linspace(270, 270 - theta_deg_val, 20) * np.pi / 180.0
            arc_x2 = boom_tip_x + arc_r2 * np.cos(arc_angles2)
            arc_y2 = boom_tip_y + arc_r2 * np.sin(arc_angles2)
            arc_theta2_line.set_data(arc_x2, arc_y2)
            label_theta2.set_position((boom_tip_x - 0.3, boom_tip_y - arc_r2 - 0.3))
            label_theta2.set_text(r"$\theta$")
        else:
            arc_theta2_line.set_data([], [])
            label_theta2.set_text("")

        # Height dimension line h (from CG to boom tip)
        h_x = boom_tip_x + 1.5
        h_dim_line.set_data([h_x, h_x], [y_cg, boom_tip_y])
        # Dotted extension lines from CG and boom tip
        h_dim_arrow.set_data(
            [x_cg, h_x + 0.3, boom_tip_x, h_x + 0.3],
            [y_cg, y_cg, boom_tip_y, boom_tip_y]
        )
        label_h.set_position((h_x + 0.2, (y_cg + boom_tip_y) / 2.0))
        label_h.set_text(f"$h$ = {H_BOOM:.1f} m")
    else:
        arrow_Tp.set_position((boom_tip_x, boom_tip_y))
        arrow_Tp.xy = (boom_tip_x, boom_tip_y)
        arrow_Tpx.set_position((boom_tip_x, boom_tip_y))
        arrow_Tpx.xy = (boom_tip_x, boom_tip_y)
        arrow_Tpy.set_position((boom_tip_x, boom_tip_y))
        arrow_Tpy.xy = (boom_tip_x, boom_tip_y)
        label_Tp.set_text("")
        label_Tpx.set_text("")
        label_Tpy.set_text("")
        arc_theta2_line.set_data([], [])
        label_theta2.set_text("")
        h_dim_line.set_data([], [])
        h_dim_arrow.set_data([], [])
        label_h.set_text("")

    # ── CURRENT ARROWS (underwater) ──
    if v_curr > 0.05:
        arrow_curr1.set_position((3.5, -3.0))
        arrow_curr1.xy = (3.5 - v_curr * 1.2, -3.0)
        arrow_curr1.set_text(f"v_corr: {v_curr:.1f} m/s")

        arrow_curr2.set_position((-1.0, -6.0))
        arrow_curr2.xy = (-1.0 - v_curr * 1.2, -6.0)
        arrow_curr2.set_text("")

        arrow_curr3.set_position((4.0, -7.5))
        arrow_curr3.xy = (4.0 - v_curr * 1.2, -7.5)
        arrow_curr3.set_text("")
    else:
        arrow_curr1.xy = (0, 0); arrow_curr1.set_position((0, 0)); arrow_curr1.set_text("")
        arrow_curr2.xy = (0, 0); arrow_curr2.set_position((0, 0)); arrow_curr2.set_text("")
        arrow_curr3.xy = (0, 0); arrow_curr3.set_position((0, 0)); arrow_curr3.set_text("")

    # ══════════════════════════════════════════════
    # 5. TELEMETRY TEXT BOX
    # ══════════════════════════════════════════════
    load_pct = (power_kw / (m_power / 1000.0)) * 100.0
    status_msg = "SOBRECARGA!" if load_pct > 100 else "ÓPTIMO" if load_pct >= 15 else "SUBUTILIZADO"
    M_escora = Tension * np.sin(theta) * H_BOOM  # Momento de escora (N·m)

    telemetry_text.set_text(
        f"t = {time:.2f} s  |  m = {int(m)} kg\n"
        f"θ = {np.degrees(theta):.1f}°  |  T = {int(Tension)} N\n"
        f"T_winch = {int(T_winch)} N  |  τ = {torque_drum:.1f} N·m\n"
        f"P_req = {power_kw:.2f} kW ({power_hp:.1f} HP)\n"
        f"M_escora = {M_escora:.0f} N·m  (h={H_BOOM}m)\n"
        f"Motor: {m_name} → {int(load_pct)}% ({status_msg})"
    )

    return (wave_line, boat_patch, boom_line, cable_line, net_circle, tension_line, power_line)


# Run Matplotlib animation (60fps interval -> ~16ms)
ani = animation.FuncAnimation(fig, animate, interval=16, blit=False, cache_frame_data=False)
plt.show()
