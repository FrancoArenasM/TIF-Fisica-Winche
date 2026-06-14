import numpy as np

# Physical Constants (matching simulacion_winche.py and TIF_Fisica_Winche.tex)
G = 9.81
RHO_WATER = 1025.0
DRUM_RADIUS = 0.25
VM = 4.0
EFFICIENCY = 0.85

def run_telemetry_tests():
    print("=" * 70)
    print("PRUEBAS DE TELEMETRÍA - SISTEMA DE IZAJE DEL WINCHE PESQUERO")
    print("=" * 70)
    print(f"Parámetros Constantes:")
    print(f"  g = {G} m/s^2")
    print(f"  Densidad Agua (rho) = {RHO_WATER} kg/m^3")
    print(f"  Radio de Tambor = {DRUM_RADIUS} m")
    print(f"  Ventaja Mecánica (VM) = {VM} (polipasto 4x)")
    print(f"  Eficiencia de Transmisión = {EFFICIENCY}")
    print("-" * 70)

    # Test parameters
    m = 500.0  # kg
    weight = m * G
    A_proj = 0.5 * (m / 100.0)**(2/3)
    Cd = 1.2
    
    # Theoretical / LaTeX document values
    latex_vals = {
        "calma": {
            "Tension": 5130.0,
            "T_winch": 1282.5,
            "Torque": 320.6,
            "Power": 3.02,
            "Theta": 0.0,
            "Drag": 225.0
        },
        "corriente": {
            "Tension": 6005.0,
            "T_winch": 1501.0,
            "Torque": 375.0,
            "Power": 3.53,
            "Theta": 20.77,
            "Drag": 2245.0
        }
    }

    # --- ESCENARIO 1: MAR EN CALMA ---
    v_winch_1 = 0.5
    v_curr_1 = 0.0
    
    # Under steady-state Calm: net vertical velocity v_net = v_winch_1
    v_rel_1 = v_winch_1
    F_drag_1 = 0.5 * Cd * RHO_WATER * A_proj * v_rel_1**2
    T_x_1 = 0.0
    T_y_1 = weight + F_drag_1
    Tension_1 = np.sqrt(T_x_1**2 + T_y_1**2)
    T_winch_1 = Tension_1 / VM
    Torque_1 = T_winch_1 * DRUM_RADIUS
    Power_watts_1 = (Tension_1 * v_winch_1) / EFFICIENCY
    Power_kw_1 = Power_watts_1 / 1000.0
    Theta_deg_1 = np.degrees(np.arctan2(T_x_1, T_y_1))
    
    print("ESCENARIO 1: Buque Estacionario en Mar en Calma")
    print(f"  Velocidad Izaje: {v_winch_1} m/s | Velocidad Corriente: {v_curr_1} m/s")
    print(f"  Masa Red: {m} kg | Peso Calculado: {weight:.1f} N")
    print(f"  Área Proyectada de la Red: {A_proj:.4f} m^2")
    
    # Verify values against LaTeX
    print("\n  Comparativa de Telemetría:")
    print("  " + "-" * 64)
    print("  Variable             | Calc. Simulación | Valor LaTeX | Diferencia")
    print("  " + "-" * 64)
    print(f"  F. Arrastre (Fd)     | {F_drag_1:16.1f} N | {latex_vals['calma']['Drag']:10.1f} N | {abs(F_drag_1 - latex_vals['calma']['Drag']):10.2f} N")
    print(f"  Tensión Cable (T)    | {Tension_1:16.1f} N | {latex_vals['calma']['Tension']:10.1f} N | {abs(Tension_1 - latex_vals['calma']['Tension']):10.2f} N")
    print(f"  Tensión Winche (4x)  | {T_winch_1:16.1f} N | {latex_vals['calma']['T_winch']:10.1f} N | {abs(T_winch_1 - latex_vals['calma']['T_winch']):10.2f} N")
    print(f"  Torque de Tambor     | {Torque_1:16.2f} Nm| {latex_vals['calma']['Torque']:10.1f} Nm| {abs(Torque_1 - latex_vals['calma']['Torque']):10.2f} Nm")
    print(f"  Potencia Motor       | {Power_kw_1:16.3f} kW| {latex_vals['calma']['Power']:10.2f} kW| {abs(Power_kw_1 - latex_vals['calma']['Power']):10.3f} kW")
    print(f"  Ángulo Cable (theta) | {Theta_deg_1:16.2f}° | {latex_vals['calma']['Theta']:10.1f}° | {abs(Theta_deg_1 - latex_vals['calma']['Theta']):10.2f}°")
    print("  " + "-" * 64)
    
    # Asserts
    assert abs(F_drag_1 - latex_vals['calma']['Drag']) < 1.0, f"Error en Arrastre Calma: {F_drag_1} N"
    assert abs(Tension_1 - latex_vals['calma']['Tension']) < 1.0, f"Error en Tensión Calma: {Tension_1} N"
    assert abs(Torque_1 - latex_vals['calma']['Torque']) < 1.0, f"Error en Torque Calma: {Torque_1} Nm"
    assert abs(Power_kw_1 - latex_vals['calma']['Power']) < 0.05, f"Error en Potencia Calma: {Power_kw_1} kW"
    assert abs(Theta_deg_1 - latex_vals['calma']['Theta']) < 0.01, f"Error en Ángulo Calma: {Theta_deg_1}°"
    print("  [OK] Escenario 1 pasó todas las pruebas y es coherente con el informe LaTeX.")
    print("-" * 70)

    # --- ESCENARIO 2: CORRIENTE MARINA TRANSVERSAL ---
    v_winch_2 = 0.5
    v_curr_2 = 1.5
    
    # Under steady-state Current: net vertical velocity v_net = v_winch_2
    v_rel_mag_2 = np.sqrt(v_curr_2**2 + v_winch_2**2)
    phi_rad_2 = np.arctan2(v_curr_2, v_winch_2)
    phi_deg_2 = np.degrees(phi_rad_2)
    
    F_drag_2 = 0.5 * Cd * RHO_WATER * A_proj * v_rel_mag_2**2
    F_dx_2 = F_drag_2 * np.sin(phi_rad_2)
    F_dy_2 = F_drag_2 * np.cos(phi_rad_2)
    
    # Equilibrium
    T_x_2 = F_dx_2
    T_y_2 = weight + F_dy_2
    Tension_2 = np.sqrt(T_x_2**2 + T_y_2**2)
    T_winch_2 = Tension_2 / VM
    Torque_2 = T_winch_2 * DRUM_RADIUS
    Power_watts_2 = (Tension_2 * v_winch_2) / EFFICIENCY
    Power_kw_2 = Power_watts_2 / 1000.0
    Theta_deg_2 = np.degrees(np.arctan2(T_x_2, T_y_2))

    print("ESCENARIO 2: Izaje bajo Efecto de Corriente Marina Transversal")
    print(f"  Velocidad Izaje: {v_winch_2} m/s | Velocidad Corriente: {v_curr_2} m/s")
    print(f"  V. Relativa Resultante: {v_rel_mag_2:.4f} m/s | Ángulo Arrastre (phi): {phi_deg_2:.2f}°")
    print(f"  Componentes de Arrastre Calculados: Fd_x = {F_dx_2:.1f} N, Fd_y = {F_dy_2:.1f} N")
    
    # Verify values against LaTeX
    print("\n  Comparativa de Telemetría:")
    print("  " + "-" * 64)
    print("  Variable             | Calc. Simulación | Valor LaTeX | Diferencia")
    print("  " + "-" * 64)
    print(f"  F. Arrastre (Fd)     | {F_drag_2:16.1f} N | {latex_vals['corriente']['Drag']:10.1f} N | {abs(F_drag_2 - latex_vals['corriente']['Drag']):10.2f} N")
    print(f"  Tensión Cable (T)    | {Tension_2:16.1f} N | {latex_vals['corriente']['Tension']:10.1f} N | {abs(Tension_2 - latex_vals['corriente']['Tension']):10.2f} N")
    print(f"  Tensión Winche (4x)  | {T_winch_2:16.1f} N | {latex_vals['corriente']['T_winch']:10.1f} N | {abs(T_winch_2 - latex_vals['corriente']['T_winch']):10.2f} N")
    print(f"  Torque de Tambor     | {Torque_2:16.2f} Nm| {latex_vals['corriente']['Torque']:10.1f} Nm| {abs(Torque_2 - latex_vals['corriente']['Torque']):10.2f} Nm")
    print(f"  Potencia Motor       | {Power_kw_2:16.3f} kW| {latex_vals['corriente']['Power']:10.2f} kW| {abs(Power_kw_2 - latex_vals['corriente']['Power']):10.3f} kW")
    print(f"  Ángulo Cable (theta) | {Theta_deg_2:16.2f}° | {latex_vals['corriente']['Theta']:10.1f}° | {abs(Theta_deg_2 - latex_vals['corriente']['Theta']):10.2f}°")
    print("  " + "-" * 64)
    
    # Asserts
    assert abs(F_drag_2 - latex_vals['corriente']['Drag']) < 3.0, f"Error en Arrastre Corriente: {F_drag_2} N"
    assert abs(Tension_2 - latex_vals['corriente']['Tension']) < 3.0, f"Error en Tensión Corriente: {Tension_2} N"
    assert abs(Torque_2 - latex_vals['corriente']['Torque']) < 1.0, f"Error en Torque Corriente: {Torque_2} Nm"
    assert abs(Power_kw_2 - latex_vals['corriente']['Power']) < 0.05, f"Error en Potencia Corriente: {Power_kw_2} kW"
    assert abs(Theta_deg_2 - latex_vals['corriente']['Theta']) < 0.1, f"Error en Ángulo Corriente: {Theta_deg_2}°"
    print("  [OK] Escenario 2 pasó todas las pruebas y es coherente con el informe LaTeX.")
    print("=" * 70)
    print("TODAS LAS PRUEBAS FÍSICAS DE TELEMETRÍA SE COMPLETARON CON ÉXITO")
    print("El simulador Python cumple estrictamente con las ecuaciones del informe LaTeX.")
    print("=" * 70)

if __name__ == "__main__":
    run_telemetry_tests()
