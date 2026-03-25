import math

# ────────────────────────────────────────────────────────────────────────────────
# ECP 203-2018 & ACI 318-19 core calculations
# ────────────────────────────────────────────────────────────────────────────────

class StructuralService:
    @staticmethod
    def calc_column(b_mm: float, t_mm: float, height_m: float, fcu_mpa: float, fy_mpa: float, load_kn: float, rho_pct: float):
        """Short column design check — ECP 203."""
        b = b_mm / 1000; d = t_mm / 1000; h = height_m
        Ag = b * d  # m²
        rho = rho_pct / 100
        As = rho * Ag  # m²
        Pu_kn = 0.35 * fcu_mpa * 1000 * (Ag - As) + 0.67 * fy_mpa * 1000 * As
        status = "✅ آمن" if Pu_kn >= load_kn else "❌ يحتاج مراجعة"
        concrete_vol = Ag * h  # m³
        steel_kg = As * h * 7850  # density 7850 kg/m³
        return {
            "Ag_m2": round(Ag, 4),
            "As_m2": round(As, 6),
            "Pu_kn": round(Pu_kn, 1),
            "Pd_kn": load_kn,
            "status": status,
            "concrete_m3": round(concrete_vol, 3),
            "steel_kg": round(steel_kg, 1),
        }

    @staticmethod
    def calc_beam(b_mm: float, h_mm: float, span_m: float, fcu_mpa: float, fy_mpa: float, moment_knm: float):
        """Rectangular beam design — ECP 203 / ACI 318."""
        b = b_mm / 1000; h = h_mm / 1000
        d = h - 0.05  # effective depth (50 mm cover)
        phi_b = 0.9
        Rn = moment_knm * 1000 / (phi_b * b * d**2)
        m = fy_mpa / (0.85 * fcu_mpa)
        rho_req = (1/m) * (1 - math.sqrt(max(0, 1 - 2*m*Rn/(fy_mpa*1000))))
        rho_min = max(1.4/fy_mpa, 0.25 * math.sqrt(fcu_mpa)/fy_mpa)
        rho_max = 0.75 * 0.85 * 0.85 * fcu_mpa/fy_mpa * (600/(600+fy_mpa))
        rho_use = max(rho_req, rho_min)
        status = "✅ آمن" if rho_use <= rho_max else "⚠️ رفع القطاع"
        As_cm2 = rho_use * b * d * 10000
        concrete_vol = b * h * span_m
        steel_wt = rho_use * (b * d) * span_m * 7850
        return {
            "d_m": round(d, 3),
            "rho": rho_use,
            "As_cm2": round(As_cm2, 2),
            "rho_max": round(rho_max, 4),
            "status": status,
            "concrete_m3": round(concrete_vol, 3),
            "steel_kg": round(steel_wt, 1),
        }

    @staticmethod
    def calc_slab(span_m: float, thickness_mm: float, fcu_mpa: float, fy_mpa: float, load_kpa: float, slab_type="one-way"):
        """One-way or two-way slab check."""
        t_s = thickness_mm / 1000
        t_min = span_m / (28 if slab_type == "one-way" else 40)
        status_thick = "✅" if t_s >= t_min else f"⚠️ سماكة أدنى: {t_min*1000:.0f} mm"
        wu = 1.4 * t_s * 25 + 1.6 * load_kpa
        Mu = wu * span_m**2 / 8
        d = t_s - 0.025
        Rn = Mu * 1000 / (0.9 * 1.0 * d**2)
        m = fy_mpa / (0.85 * fcu_mpa)
        rho = (1/m) * (1 - math.sqrt(max(0, 1 - 2*m*Rn/(fy_mpa*1000))))
        rho = max(rho, 0.002)
        As = rho * 1.0 * d * 10000
        return {
            "thickness_mm": thickness_mm,
            "t_min_mm": round(t_min * 1000, 0),
            "status_thick": status_thick,
            "wu_kpa": round(wu, 2),
            "Mu_knm": round(Mu, 2),
            "As_cm2": round(As, 2),
            "concrete_m3_per_m2": t_s,
        }

    @staticmethod
    def calc_footing(load_kn: float, qa_kpa: float, fcu_mpa: float, fy_mpa: float, col_b_mm: float, col_d_mm: float):
        """Square isolated footing sizing."""
        A_req = (load_kn * 1.1) / qa_kpa
        L = math.ceil(math.sqrt(A_req) * 10) / 10
        t = max(0.3, (L - col_b_mm/1000) / 4)
        t = math.ceil(t * 10) / 10
        c_b = col_b_mm / 1000
        M = (load_kn * 1.4) / (L) * ((L - c_b) / 2)**2 / 2
        d = t - 0.075
        Rn = M * 1000 / (0.9 * L * d**2)
        m_r = fy_mpa / (0.85 * fcu_mpa)
        rho = (1 / m_r) * (1 - math.sqrt(max(0, 1 - 2*m_r*Rn/(fy_mpa*1000))))
        As = max(rho, 0.002) * L * d * 10000
        conc_vol = L * L * t
        steel_kg = max(rho, 0.002) * (L * d) * L * 7850
        return {
            "A_req_m2": round(A_req, 2),
            "L_m": L,
            "t_m": t,
            "As_cm2": round(As, 2),
            "concrete_m3": round(conc_vol, 3),
            "steel_kg": round(steel_kg, 1),
        }
