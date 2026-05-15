"""Tax calculator for Moroccan tax system (IR, IS, TVA)."""
import json, os
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tax")

class TaxCalculator:
    def __init__(self):
        self.ir = self._load("ir_brackets.json")
        self.is_rates = self._load("is_rates.json")
        self.tva = self._load("tva_rates.json")

    def _load(self, fname):
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def calculate_ir(self, annual_revenue: float, expenses: float = 0,
                      nb_children: int = 0, regime: str = "reel") -> dict:
        """Calculate Impôt sur le Revenu (IR)."""
        net_imposable = max(0, annual_revenue - expenses)

        if regime == "forfaitaire":
            abattement = min(net_imposable * 0.35, 30000)
            net_imposable = max(0, net_imposable - abattement)

        # Apply IR brackets
        tax = 0
        for bracket in self.ir.get("ir_brackets", []):
            if bracket["max"] is None:
                if net_imposable > bracket["min"]:
                    tax += (net_imposable - bracket["min"]) * bracket["rate"]
            elif bracket["min"] <= net_imposable <= bracket["max"]:
                tax += (net_imposable - bracket["min"]) * bracket["rate"]
                break
            elif net_imposable > bracket["max"]:
                tax += (bracket["max"] - bracket["min"] + 1) * bracket["rate"]

        # Family deduction
        deduction = nb_children * self.ir.get("family_deduction_per_child", 360)
        tax = max(0, tax - deduction)

        cnss = net_imposable * self.ir.get("social_security_rate", 0.0424)
        net_apres_impot = net_imposable - tax - cnss

        mensual = {
            "brut": round(annual_revenue / 12, 2),
            "net": round(net_apres_impot / 12, 2),
            "ir": round(tax / 12, 2),
            "cnss": round(cnss / 12, 2),
        }

        return {
            "regime": regime,
            "revenu_brut_annuel": round(annual_revenue, 2),
            "frais": round(expenses, 2),
            "net_imposable": round(net_imposable, 2),
            "ir_annuel": round(tax, 2),
            "ir_taux_effectif": round(tax / max(net_imposable, 1) * 100, 2),
            "cnss_annuelle": round(cnss, 2),
            "net_apres_impot": round(net_apres_impot, 2),
            "mensuel": mensual,
            "nb_enfants": nb_children,
        }

    def calculate_is(self, net_profit: float, sector: str = "standard") -> dict:
        """Calculate Impôt sur les Sociétés (IS)."""
        base_rate = self.is_rates.get("is_base_rate", 0.20)
        high_rate = self.is_rates.get("is_high_rate", 0.31)
        threshold = self.is_rates.get("is_threshold_base", 100000000)

        # Check special sector rates
        sector_rate = None
        if sector in self.is_rates.get("sectors", {}):
            sector_rate = self.is_rates["sectors"][sector]["rate"]

        if sector_rate:
            rate = sector_rate
        elif net_profit > threshold:
            rate = high_rate
        else:
            rate = base_rate

        tax = net_profit * rate
        cotisation_minimale = max(net_profit * 0.005, 3000)

        return {
            "benefice_net": round(net_profit, 2),
            "taux_is": rate * 100,
            "is_a_payer": round(tax, 2),
            "cotisation_minimale": round(cotisation_minimale, 2),
            "secteur": sector,
            "is_effectif": round(tax / max(net_profit, 1) * 100, 2),
        }

    def calculate_tva(self, ht_amount: float, tva_rate: float = 0.20) -> dict:
        """Calculate TVA (Taxe sur la Valeur Ajoutée)."""
        tva = ht_amount * tva_rate
        ttc = ht_amount + tva
        return {
            "ht": round(ht_amount, 2),
            "tva_rate": tva_rate * 100,
            "tva": round(tva, 2),
            "ttc": round(ttc, 2),
        }

    def calculate_cnss(self, monthly_salary: float) -> dict:
        """Calculate CNSS contributions."""
        plafond = 6000
        base = min(monthly_salary, plafond)
        employee_part = base * self.ir.get("cnss_employee_rate", 0.0424)
        employer_part = base * self.ir.get("cnss_employer_rate", 0.1285)
        return {
            "salaire_brut_mensuel": round(monthly_salary, 2),
            "base_cotisation": round(base, 2),
            "part_salariale": round(employee_part, 2),
            "part_patronale": round(employer_part, 2),
            "total": round(employee_part + employer_part, 2),
        }

    def simulate_charges(self, monthly_revenue: float, monthly_expenses: float = 0,
                         regime: str = "auto_entrepreneur") -> dict:
        """Complete charge simulation for auto-entrepreneur or small business."""
        annual_revenue = monthly_revenue * 12
        annual_expenses = monthly_expenses * 12

        if regime == "auto_entrepreneur":
            taux_global = 0.01 if annual_revenue <= 50000 else (
                0.02 if annual_revenue <= 200000 else 0.05
            )
            charges_annuelles = annual_revenue * taux_global
            return {
                "regime": regime,
                "chiffre_affaires_mensuel": round(monthly_revenue, 2),
                "chiffre_affaires_annuel": round(annual_revenue, 2),
                "taux_global": taux_global * 100,
                "charges_annuelles": round(charges_annuelles, 2),
                "charges_mensuelles": round(charges_annuelles / 12, 2),
                "revenu_net_annuel": round(annual_revenue - charges_annuelles, 2),
                "revenu_net_mensuel": round((annual_revenue - charges_annuelles) / 12, 2),
            }

        ir_result = self.calculate_ir(annual_revenue, annual_expenses)
        return {
            "regime": regime,
            "mensuel": {
                "ca": round(monthly_revenue, 2),
                "frais": round(monthly_expenses, 2),
                "marge": round(monthly_revenue - monthly_expenses, 2),
            },
            "annuel": {
                "ca": round(annual_revenue, 2),
                "frais": round(annual_expenses, 2),
                "resultat": round(annual_revenue - annual_expenses, 2),
            },
            "ir": ir_result,
        }

tax_calculator = TaxCalculator()
