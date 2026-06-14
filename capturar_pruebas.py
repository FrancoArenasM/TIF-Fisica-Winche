"""
Script de Captura Automática de Pruebas del Simulador de Winche Pesquero.
Ejecuta la simulación con distintas configuraciones, espera a que se estabilice,
y guarda capturas PNG de alta resolución para insertar en el informe LaTeX.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving images
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc, Circle
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec

# ── Import physics engine from simulation (inline copy for isolation) ──
G = 9.81
RHO_WATER = 1025.0
RHO_BONITO = 1050.0
DRUM_RADIUS = 0.25
VM = 4.0
EFFICIENCY = 0.85
H_BOOM = 3.4

MOTORS = {
    "Yanmar 3TNV88": 18000.0,
    "Caterpillar C1.5": 15000.0,
    "Chongqing Mini": 12000.0
}

def vectorScalePhys(force_val):
    val = abs(force_val)
    if val <= 0:
        return 0
    return max(0.5, min(4.0, 0.5 + (val / 2500.0)))


def run_simulation_and_capture(mass, v_winch, v_current, k_cable, motor_name, 
                                 is_submerged, filename, title_extra=""):
    """Run simulation for given parameters, let it stabilize, and save a screenshot."""
    
    c_cable = 300.0
    dt = 0.005
    L_nominal = 15.0
    y_net = -10.0
    v_net = 0.0
    time_val = 0.0
    
    # Run physics for 200 steps to let it stabilize
    n_steps = 400
    substeps = 10
    
    time_hist = []
    tension_hist = []
    power_hist = []
    
    for step in range(n_steps):
        weight = mass * G
        dt_sub = dt / substeps
        
        for _ in range(substeps):
            time_val += dt_sub
            y_tip = 5.0
            v_tip = 0.0
            L_nominal = max(2.0, L_nominal - v_winch * dt_sub)
            stretch = y_tip - y_net - L_nominal
            
            if stretch > 0:
                T_y = k_cable * stretch + c_cable * (v_tip - v_net + v_winch)
                if T_y < 0:
                    T_y = 0.0
            else:
                T_y = 0.0
            
            buoyancy = 0.0
            
            if is_submerged:
                v_rel_x = v_current
                v_rel_y = -v_net
                v_rel_mag = np.sqrt(v_rel_x**2 + v_rel_y**2)
                A_proj = 0.5 * (mass / 100.0)**(2/3)
                F_drag_mag = 0.5 * 1.2 * RHO_WATER * A_proj * v_rel_mag**2
                F_dx = F_drag_mag * (v_current / v_rel_mag) if v_rel_mag > 0 else 0.0
                F_dy = F_drag_mag * (v_net / v_rel_mag) if v_rel_mag > 0 else 0.0
            else:
                F_dx = 0.0
                F_dy = 0.0
            
            T_x = F_dx
            a_net = (T_y - weight - F_dy) / mass
            v_net += a_net * dt_sub
            y_net += v_net * dt_sub
            Tension = np.sqrt(T_x**2 + T_y**2)
        
        T_winch = Tension / VM
        torque_drum = T_winch * DRUM_RADIUS
        power_watts = (Tension * v_winch) / EFFICIENCY
        power_kw = power_watts / 1000.0
        
        time_hist.append(time_val)
        tension_hist.append(Tension)
        power_hist.append(power_kw)
    
    # ── Now create the figure for the final stabilized state ──
    theta = np.arctan2(T_x, T_y) if T_y > 0 else 0.0
    Fd_mag = np.sqrt(F_dx**2 + F_dy**2) if is_submerged else 0.0
    
    m_power = MOTORS[motor_name]
    power_hp = power_kw * 1.34102
    load_pct = (power_kw / (m_power / 1000.0)) * 100.0
    status_msg = "SOBRECARGA!" if load_pct > 100 else "ÓPTIMO" if load_pct >= 15 else "SUBUTILIZADO"
    M_escora = Tension * np.sin(theta) * H_BOOM
    
    # Create figure
    fig = plt.figure(figsize=(16, 10), facecolor='#FFFFFF', dpi=150)
    gs = gridspec.GridSpec(2, 3, figure=fig)
    ax_sim = fig.add_subplot(gs[:, :-1], facecolor='#FFFFFF')
    ax_plots = fig.add_subplot(gs[0, -1], facecolor='#FFFFFF')
    ax_power = fig.add_subplot(gs[1, -1], facecolor='#FFFFFF')
    plt.subplots_adjust(bottom=0.12, left=0.05, right=0.97, top=0.92, wspace=0.3, hspace=0.35)
    
    scenario = "Corriente Marina" if v_current > 0 else "Mar en Calma"
    fig.suptitle(f"Simulador Winche Pesquero — {scenario}{title_extra}", 
                 fontsize=13, fontweight='bold', color='#0B2545')
    
    # Simulation panel
    ax_sim.set_xlim(-12, 12)
    ax_sim.set_ylim(-13.5, 6.0)
    ax_sim.set_title("Diagrama de Cuerpo Libre (DCL) Dinámico", color='#0B2545', fontsize=11, fontweight='bold')
    ax_sim.set_aspect('equal')
    ax_sim.xaxis.set_visible(False)
    ax_sim.yaxis.set_visible(False)
    for spine in ax_sim.spines.values():
        spine.set_visible(False)
    
    # Water
    ax_sim.fill_between(np.linspace(-12, 12, 100), -20, 0, color='#E0F2FE', alpha=0.5, zorder=0)
    x_wave = np.linspace(-12, 12, 200)
    y_wave = 0.15 + 0.08 * np.sin(x_wave * 2.0 + 3.0 * time_val)
    ax_sim.plot(x_wave, y_wave, color='#0284C7', linewidth=2.5, zorder=2)
    ax_sim.text(4.8, 0.4, "Nivel del mar", color='#0369A1', fontsize=7, fontweight='bold', fontstyle='italic')
    
    # Boat (matching TikZ Figure 2)
    y_boat = 0.0
    y_tip_v = 5.0
    boat_x = [-3.5, 1.0, 1.8, -4.0]
    boat_y = [y_boat, y_boat, y_boat+1.2, y_boat+1.2]
    ax_sim.fill(boat_x, boat_y, color='#64748B', edgecolor='#1E293B', linewidth=1.5, zorder=3)
    
    cabin_x = [-2.5, -0.5, -0.5, -2.5]
    cabin_y = [y_boat+1.2, y_boat+1.2, y_boat+2.2, y_boat+2.2]
    ax_sim.fill(cabin_x, cabin_y, color='#94A3B8', edgecolor='#475569', linewidth=1, zorder=4)
    
    # Windows
    ax_sim.add_patch(patches.Rectangle((-2.2, y_boat+1.4), 0.5, 0.5, facecolor='#E0F2FE', edgecolor='#475569', lw=1, zorder=5))
    ax_sim.add_patch(patches.Rectangle((-1.3, y_boat+1.4), 0.5, 0.5, facecolor='#E0F2FE', edgecolor='#475569', lw=1, zorder=5))
    
    # Drum
    ax_sim.add_patch(plt.Circle((-3.0, y_boat+1.35), 0.15, color='#475569', zorder=5))
    
    # Boom
    boom_base_x, boom_base_y = 0.5, y_boat + 1.2
    boom_tip_x, boom_tip_y = 3.5, y_tip_v
    ax_sim.plot([boom_base_x, boom_tip_x], [boom_base_y, boom_tip_y], color='#334155', linewidth=5, solid_capstyle='round', zorder=4)
    ax_sim.add_patch(plt.Circle((boom_base_x, boom_base_y), 0.12, color='#475569', zorder=5))
    ax_sim.add_patch(plt.Circle((boom_tip_x, boom_tip_y), 0.10, color='#475569', zorder=5))
    ax_sim.text(boom_tip_x, boom_tip_y + 0.2, "Polipasto", color='#475569', fontsize=6, fontweight='bold', ha='center', va='bottom')
    
    # Winch cable
    ax_sim.plot([boom_tip_x, -3.0], [boom_tip_y, y_boat+1.35], color='#94A3B8', linewidth=1.2, zorder=3)
    
    # Cable to net
    x_tip = boom_tip_x
    x_net = x_tip - (y_tip_v - y_net) * np.tan(theta)
    x_net = max(-5.0, min(5.0, x_net))
    ax_sim.plot([x_tip, x_net], [y_tip_v, y_net], color='#1E293B', linewidth=1.8, zorder=3)
    
    # Net
    net_radius = 0.7
    ax_sim.add_patch(plt.Circle((x_net, y_net), net_radius, facecolor='#FFF7ED', edgecolor='#EA580C', linewidth=2.0, zorder=6))
    
    # Net grid
    r = net_radius * 0.75
    for i in range(7):
        spacing = 2 * r / 8
        offset = -r + spacing * (i + 1)
        if abs(offset) < r:
            hw = np.sqrt(r**2 - offset**2)
            ax_sim.plot([x_net-hw, x_net+hw], [y_net+offset, y_net+offset], color='#FB923C', linewidth=0.6, zorder=7)
            ax_sim.plot([x_net+offset, x_net+offset], [y_net-hw, y_net+hw], color='#FB923C', linewidth=0.6, zorder=7)
    
    # CM dot and labels
    ax_sim.add_patch(plt.Circle((x_net, y_net), 0.06, color='#0F172A', zorder=8))
    bbox_lbl = dict(facecolor='#FFF7ED', edgecolor='none', pad=0.8, alpha=0.9)
    ax_sim.text(x_net - 0.15, y_net + 0.15, "CM", color='#0F172A', fontsize=7, fontweight='bold', ha='right', va='bottom', bbox=bbox_lbl, zorder=9)
    ax_sim.text(x_net + 0.15, y_net + 0.15, "Bonito", color='#0F172A', fontsize=7, fontweight='bold', ha='left', va='bottom', fontstyle='italic', bbox=bbox_lbl, zorder=9)
    
    # ── DCL 1 Vectors ──
    bbox_props = dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=0.3)
    vs = 1.3
    
    def sv(val):
        return vectorScalePhys(val) * vs
    
    # Weight P
    P_scale = sv(weight) * 0.4
    ax_sim.annotate('', xy=(x_net, y_net - P_scale), xytext=(x_net, y_net),
                    arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=2.5, mutation_scale=14), zorder=8)
    ax_sim.text(x_net, y_net - P_scale - 0.4, f"$\\vec{{P}}$ = {int(weight)} N", color='#DC2626', fontsize=8,
               fontweight='bold', ha='center', va='top', bbox=bbox_props, zorder=9)
    
    # Vertical reference
    ax_sim.plot([x_net, x_net], [y_net - P_scale - 0.8, y_net + P_scale + 2.0], 
               color='#9CA3AF', linewidth=0.8, linestyle='--', zorder=6)
    
    # Drag Fd
    if is_submerged and Fd_mag > 0.5:
        Fd_scale = sv(Fd_mag)
        Fd_dir_x = -F_dx / Fd_mag
        Fd_dir_y = -abs(F_dy) / Fd_mag
        Fd_end_x = x_net + Fd_dir_x * Fd_scale
        Fd_end_y = y_net + Fd_dir_y * Fd_scale
        
        ax_sim.annotate('', xy=(Fd_end_x, Fd_end_y), xytext=(x_net, y_net),
                        arrowprops=dict(arrowstyle="-|>", color='#C2410C', lw=2.2, mutation_scale=13), zorder=8)
        ax_sim.text(Fd_end_x - 0.2, Fd_end_y - 0.2, f"$\\vec{{F}}_d$ = {int(Fd_mag)} N", color='#C2410C',
                   fontsize=8, fontweight='bold', ha='right', va='top', bbox=bbox_props, zorder=9)
        
        # Fdx, Fdy components
        Fdx_end_x = x_net + Fd_dir_x * Fd_scale * (F_dx / Fd_mag)
        ax_sim.annotate('', xy=(Fdx_end_x, y_net), xytext=(x_net, y_net),
                        arrowprops=dict(arrowstyle="-|>", color='#9A3412', lw=1.3, linestyle='dashed', mutation_scale=10), zorder=7)
        ax_sim.text(Fdx_end_x - 0.1, y_net + 0.35, f"$F_{{d,x}}$={int(F_dx)}N", color='#9A3412',
                   fontsize=6.5, fontweight='bold', ha='right', bbox=bbox_props, zorder=9)
        
        ax_sim.annotate('', xy=(Fdx_end_x, Fd_end_y), xytext=(Fdx_end_x, y_net),
                        arrowprops=dict(arrowstyle="-|>", color='#9A3412', lw=1.3, linestyle='dashed', mutation_scale=10), zorder=7)
        ax_sim.text(Fdx_end_x - 0.2, Fd_end_y - 0.1, f"$F_{{d,y}}$={int(abs(F_dy))}N", color='#9A3412',
                   fontsize=6.5, fontweight='bold', va='top', bbox=bbox_props, zorder=9)
        
        # Phi arc
        phi = np.arctan2(F_dx, abs(F_dy)) if abs(F_dy) > 0 else np.pi/2
        phi_deg = np.degrees(phi)
        ax_sim.text(x_net - 0.5, y_net - 1.0, f"φ={phi_deg:.0f}°", color='#0F172A', fontsize=8, fontweight='bold')
    
    # Tension T
    if Tension > 1:
        T_scale = sv(Tension)
        T_dir_x = T_x / Tension
        T_dir_y = T_y / Tension
        T_end_x = x_net + T_dir_x * T_scale
        T_end_y = y_net + T_dir_y * T_scale
        
        ax_sim.annotate('', xy=(T_end_x, T_end_y), xytext=(x_net, y_net),
                        arrowprops=dict(arrowstyle="-|>", color='#2563EB', lw=2.8, mutation_scale=15), zorder=8)
        ax_sim.text(T_end_x + 0.2, T_end_y + 0.2, f"$\\vec{{T}}$ = {int(Tension)} N", color='#2563EB',
                   fontsize=9, fontweight='bold', ha='left', va='bottom', bbox=bbox_props, zorder=9)
        
        # Tx, Ty
        Tx_end_x = x_net + T_dir_x * T_scale
        ax_sim.annotate('', xy=(Tx_end_x, y_net), xytext=(x_net, y_net),
                        arrowprops=dict(arrowstyle="-|>", color='#1E40AF', lw=1.3, linestyle='dashed', mutation_scale=10), zorder=7)
        ax_sim.text(Tx_end_x + 0.1, y_net - 0.45, f"$T_x$={int(T_x)}N", color='#1E40AF',
                   fontsize=6.5, fontweight='bold', ha='left', bbox=bbox_props, zorder=9)
        
        ax_sim.annotate('', xy=(Tx_end_x, T_end_y), xytext=(Tx_end_x, y_net),
                        arrowprops=dict(arrowstyle="-|>", color='#1E40AF', lw=1.3, linestyle='dashed', mutation_scale=10), zorder=7)
        ax_sim.text(Tx_end_x + 0.2, T_end_y + 0.1, f"$T_y$={int(T_y)}N", color='#1E40AF',
                   fontsize=6.5, fontweight='bold', va='bottom', bbox=bbox_props, zorder=9)
        
        # Theta label
        ax_sim.text(x_net + 0.5, y_net + 1.8, f"θ={np.degrees(theta):.1f}°", color='#0F172A', fontsize=8, fontweight='bold')
    
    # ── DCL 2: Boat Vectors ──
    x_cg = (-3.5 + 1.0 + 1.8 + -4.0) / 4.0
    y_cg = y_boat + 0.6
    ax_sim.add_patch(plt.Circle((x_cg, y_cg), 0.08, color='#0F172A', zorder=10))
    ax_sim.text(x_cg - 0.2, y_cg + 0.2, "CG", color='#0F172A', fontsize=7, fontweight='bold', ha='right', va='bottom',
               bbox=dict(facecolor='#FFF7ED', edgecolor='none', pad=0.8, alpha=0.9), zorder=11)
    
    # P_buque, N_casco, F_prop
    ax_sim.annotate('', xy=(x_cg, y_cg - 1.8), xytext=(x_cg, y_cg),
                    arrowprops=dict(arrowstyle="-|>", color='#DC2626', lw=2.5, mutation_scale=14), zorder=8)
    ax_sim.text(x_cg, y_cg - 2.1, r"$\vec{P}_{buque}$", color='#DC2626', fontsize=8, fontweight='bold', ha='center', va='top', bbox=bbox_props)
    
    N_scale_v = 1.8 + (T_y/Tension * sv(Tension) if Tension > 1 else 0)
    ax_sim.annotate('', xy=(x_cg, y_cg + N_scale_v), xytext=(x_cg, y_cg),
                    arrowprops=dict(arrowstyle="-|>", color='#16A34A', lw=2.5, mutation_scale=14), zorder=8)
    ax_sim.text(x_cg, y_cg + N_scale_v + 0.2, r"$\vec{N}_{casco}$", color='#16A34A', fontsize=8, fontweight='bold', ha='center', va='bottom', bbox=bbox_props)
    
    if Tension > 1 and T_x > 5:
        F_prop_s = (T_x/Tension)*sv(Tension)
        ax_sim.annotate('', xy=(x_cg + F_prop_s, y_cg), xytext=(x_cg, y_cg),
                        arrowprops=dict(arrowstyle="-|>", color='#D97706', lw=2.5, mutation_scale=14), zorder=8)
        ax_sim.text(x_cg + F_prop_s + 0.1, y_cg, r"$\vec{F}_{prop}$", color='#D97706', fontsize=8, fontweight='bold', ha='left', bbox=bbox_props)
    
    # T' reaction
    if Tension > 1:
        Tp_dir_x = -T_dir_x
        Tp_dir_y = -T_dir_y
        Tp_end_x = boom_tip_x + Tp_dir_x * T_scale
        Tp_end_y = boom_tip_y + Tp_dir_y * T_scale
        ax_sim.annotate('', xy=(Tp_end_x, Tp_end_y), xytext=(boom_tip_x, boom_tip_y),
                        arrowprops=dict(arrowstyle="-|>", color='#1E40AF', lw=2.8, mutation_scale=15), zorder=8)
        ax_sim.text(Tp_end_x - 0.2, Tp_end_y - 0.2, "$\\vec{T}'$", color='#1E40AF', fontsize=9, fontweight='bold', ha='right', va='top', bbox=bbox_props)
    
    # h dimension
    h_x = boom_tip_x + 1.5
    ax_sim.plot([h_x, h_x], [y_cg, boom_tip_y], color='#475569', linewidth=1.2, zorder=6)
    ax_sim.plot([x_cg, h_x+0.3], [y_cg, y_cg], color='#475569', linewidth=0.8, linestyle=':', zorder=6)
    ax_sim.plot([boom_tip_x, h_x+0.3], [boom_tip_y, boom_tip_y], color='#475569', linewidth=0.8, linestyle=':', zorder=6)
    ax_sim.text(h_x + 0.2, (y_cg + boom_tip_y)/2, f"$h$ = {H_BOOM:.1f} m", color='#0F172A', fontsize=10, fontweight='bold', ha='left', va='center')
    
    # Current arrows
    if v_current > 0.05:
        ax_sim.annotate(f'v_corr: {v_current:.1f} m/s', xy=(3.5 - v_current*1.2, -3.0), xytext=(3.5, -3.0),
                       arrowprops=dict(arrowstyle="->", color='#0096C7', lw=1.5, alpha=0.6),
                       color='#0096C7', fontsize=7, alpha=0.8, fontweight='bold')
    
    # Coordinate axes
    ax_sim.annotate('', xy=(-4.8, -8.5), xytext=(-5.5, -8.5), arrowprops=dict(arrowstyle='->', color='#6B7280', lw=1.2))
    ax_sim.text(-4.7, -8.5, 'x', color='#6B7280', fontsize=8, fontweight='bold', ha='left', va='center')
    ax_sim.annotate('', xy=(-5.5, -7.8), xytext=(-5.5, -8.5), arrowprops=dict(arrowstyle='->', color='#6B7280', lw=1.2))
    ax_sim.text(-5.5, -7.6, 'y', color='#6B7280', fontsize=8, fontweight='bold', ha='center', va='bottom')
    
    # Telemetry box
    telem = (
        f"t = {time_val:.2f} s  |  m = {int(mass)} kg\n"
        f"θ = {np.degrees(theta):.1f}°  |  T = {int(Tension)} N\n"
        f"T_winch = {int(T_winch)} N  |  τ = {torque_drum:.1f} N·m\n"
        f"P_req = {power_kw:.2f} kW ({power_hp:.1f} HP)\n"
        f"M_escora = {M_escora:.0f} N·m  (h={H_BOOM}m)\n"
        f"Motor: {motor_name} → {int(load_pct)}% ({status_msg})"
    )
    ax_sim.text(-11.5, 5.5, telem, color='#1E293B', fontfamily='monospace', fontsize=7.5,
               va='top', ha='left', zorder=15,
               bbox=dict(facecolor='#F1F5F9', alpha=0.95, edgecolor='#CBD5E1', boxstyle='round,pad=0.4'))
    
    # Parameters box (bottom of sim)
    params = (
        f"Masa: {int(mass)} kg  |  V. Izaje: {v_winch} m/s  |  "
        f"Corriente: {v_current} m/s  |  Rigidez Cable: {int(k_cable)} N/m  |  "
        f"Motor: {motor_name}"
    )
    ax_sim.text(0, -12.8, params, color='#334155', fontsize=7, ha='center', va='top',
               bbox=dict(facecolor='#F8FAFC', edgecolor='#CBD5E1', boxstyle='round,pad=0.5'))
    
    # ── Plots ──
    ax_plots.set_title("Tensión Dinámica en la Red", color='#0B2545', fontsize=10, fontweight='bold')
    ax_plots.set_xlabel("Tiempo (s)", color='#334155', fontsize=8)
    ax_plots.set_ylabel("Tensión (N)", color='#334155', fontsize=8)
    ax_plots.tick_params(colors='#334155', labelsize=8)
    ax_plots.grid(True, color='#E2E8F0', linestyle='--')
    ax_plots.plot(time_hist, tension_hist, color='#2563EB', linewidth=1.5)
    if tension_hist:
        ax_plots.set_ylim(0, max(1000, max(tension_hist)*1.1))
    
    ax_power.set_title("Potencia del Motor Requerida vs Límite", color='#0B2545', fontsize=10, fontweight='bold')
    ax_power.set_xlabel("Tiempo (s)", color='#334155', fontsize=8)
    ax_power.set_ylabel("Potencia (kW)", color='#334155', fontsize=8)
    ax_power.tick_params(colors='#334155', labelsize=8)
    ax_power.grid(True, color='#E2E8F0', linestyle='--')
    ax_power.plot(time_hist, power_hist, color='#16A34A', linewidth=1.5)
    ax_power.axhline(y=m_power/1000, color='#DC2626', linestyle=':', label=f'Límite {motor_name}')
    ax_power.legend(loc='upper right', fontsize=8)
    if power_hist:
        ax_power.set_ylim(0, max(5, max(max(power_hist), m_power/1000)*1.1))
    
    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='#FFFFFF')
    plt.close()
    print(f"[OK] Captura guardada: {filename}")
    
    return {
        'T': Tension, 'theta_deg': np.degrees(theta), 'T_winch': T_winch,
        'torque': torque_drum, 'power_kw': power_kw, 'power_hp': power_hp,
        'M_escora': M_escora, 'load_pct': load_pct, 'status': status_msg,
        'Fd_mag': Fd_mag
    }


# ═══════════════════════════════════════════
#  EJECUTAR PRUEBAS
# ═══════════════════════════════════════════
print("=" * 60)
print("  CAPTURA AUTOMÁTICA DE PRUEBAS DEL SIMULADOR")
print("=" * 60)

output_dir = "simulacion"

# Prueba 1: Escenario 1 — Mar en calma (v_corriente = 0)
r1 = run_simulation_and_capture(
    mass=500, v_winch=0.5, v_current=0.0, k_cable=5000, 
    motor_name="Yanmar 3TNV88", is_submerged=True,
    filename=f"{output_dir}/prueba1_mar_calma.png",
    title_extra=" — m=500kg, v=0.5m/s"
)

# Prueba 2: Escenario 2 — Corriente marina 1.5 m/s
r2 = run_simulation_and_capture(
    mass=500, v_winch=0.5, v_current=1.5, k_cable=5000,
    motor_name="Yanmar 3TNV88", is_submerged=True,
    filename=f"{output_dir}/prueba2_corriente_1_5.png",
    title_extra=" — m=500kg, v_corr=1.5m/s"
)

# Prueba 3: Carga máxima (1500 kg) con corriente
r3 = run_simulation_and_capture(
    mass=1500, v_winch=0.5, v_current=1.5, k_cable=5000,
    motor_name="Yanmar 3TNV88", is_submerged=True,
    filename=f"{output_dir}/prueba3_carga_maxima.png",
    title_extra=" — m=1500kg, v_corr=1.5m/s"
)

# Prueba 4: Alta velocidad de izaje (2.0 m/s)
r4 = run_simulation_and_capture(
    mass=500, v_winch=2.0, v_current=1.5, k_cable=5000,
    motor_name="Yanmar 3TNV88", is_submerged=True,
    filename=f"{output_dir}/prueba4_alta_velocidad.png",
    title_extra=" — m=500kg, v_izaje=2.0m/s"
)

# Prueba 5: Motor inadecuado (Chongqing Mini con carga alta)
r5 = run_simulation_and_capture(
    mass=1000, v_winch=1.0, v_current=2.0, k_cable=5000,
    motor_name="Chongqing Mini", is_submerged=True,
    filename=f"{output_dir}/prueba5_motor_sobrecarga.png",
    title_extra=" — m=1000kg, Motor Chongqing"
)

print("\n" + "=" * 60)
print("  RESUMEN DE RESULTADOS")
print("=" * 60)
for i, (label, r) in enumerate([
    ("Prueba 1: Mar en Calma (500kg)", r1),
    ("Prueba 2: Corriente 1.5m/s (500kg)", r2),
    ("Prueba 3: Carga Máxima (1500kg)", r3),
    ("Prueba 4: Alta Velocidad (2.0m/s)", r4),
    ("Prueba 5: Motor Sobrecarga", r5),
], 1):
    print(f"\n  {label}")
    print(f"    T={int(r['T'])}N  theta={r['theta_deg']:.1f} deg  P={r['power_kw']:.2f}kW  M_e={r['M_escora']:.0f} N*m  [{r['status']}]")

print("\n[OK] Todas las capturas generadas exitosamente.")
