"""
ACES-500 Cost Engine
Menerjemahkan BOQ menjadi RAB lengkap dengan traceability.
"""
from typing import Optional, Dict, Any, List
import json
from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.compiler.trace import TraceLog

class CostEngine:
    def __init__(self, kg: KnowledgeGraph, config: Optional[Dict[str, Any]] = None):
        self.kg = kg
        self._wi_by_code: Dict[str, Any] = {wi.code: wi for wi in self.kg.work_items.values()}

        default_config: Dict[str, Any] = {
            "overhead_pct": 10.0,
            "profit_pct": 10.0,
            "ppn_pct": 11.0,
            "pph_pct": 3.0,
            "contingency_pct": 5.0,
            "inflation_pct": 3.5,
            "duration_months": 12,
            "location_factor": 1.0,
            "building_area": None,
            "template": "SWASTA_DETAIL",
            "price_date": None,
            "include_value_engineering": False,
            "segment": None,
            "labor_productivity": "NORMAL",
            "risk_level": None,
            "include_smkk": False,
            "contract_value": None,
        }
        user_config = config or {}
        if config:
            merged = default_config.copy()
            merged.update(config)
            self.config: Dict[str, Any] = merged
        else:
            self.config = default_config

        # Override dari knowledge graph jika user tidak mensuplai
        if "ppn_pct" not in user_config and hasattr(self.kg, "ppn_rate"):
            self.config["ppn_pct"] = float(self.kg.ppn_rate) * 100
        if "pph_pct" not in user_config and hasattr(self.kg, "pph_rate"):
            self.config["pph_pct"] = float(self.kg.pph_rate) * 100
        if "risk_register" not in user_config and hasattr(self.kg, "risk_register"):
            self.config["risk_register"] = self.kg.risk_register
        if "schedule_weights" not in user_config and hasattr(self.kg, "schedule_weights"):
            self.config["schedule_weights"] = self.kg.schedule_weights

        self._validate_config()

    def _validate_config(self) -> None:
        overhead_pct = float(self.config["overhead_pct"])
        profit_pct = float(self.config["profit_pct"])
        contingency_pct = float(self.config["contingency_pct"])
        if not (2.0 <= overhead_pct <= 25.0):
            raise ValueError("overhead_pct harus antara 2% dan 25%")
        if not (5.0 <= profit_pct <= 25.0):
            raise ValueError("profit_pct harus antara 5% dan 25%")
        if not (1.0 <= contingency_pct <= 15.0):
            raise ValueError("contingency_pct harus antara 1% dan 15%")
        ppn_pct = float(self.config["ppn_pct"])
        pph_pct = float(self.config["pph_pct"])
        if not (0.0 <= ppn_pct <= 20.0):
            raise ValueError("ppn_pct harus antara 0% dan 20%")
        if not (0.0 <= pph_pct <= 10.0):
            raise ValueError("pph_pct harus antara 0% dan 10%")

    def _generate_cashflow(self, base_amount: float, weights: List[float]) -> Dict[str, Any]:
        total_weight = sum(weights)
        if total_weight <= 0:
            return {"error": "total bobot 0"}
        monthly = [round(base_amount * w, 2) for w in weights]
        cumulative = []
        running = 0.0
        for m in monthly:
            running += m
            cumulative.append(round(running, 2))

        # Default termin schedule: uang muka 20%, 3 termin @ 25%, retensi 5% (dibayar akhir)
        down_payment = round(base_amount * 0.20, 2)
        progress_terms = [
            {"term": "Termin 1", "trigger_progress": 0.25, "amount": round(base_amount * 0.25, 2)},
            {"term": "Termin 2", "trigger_progress": 0.50, "amount": round(base_amount * 0.25, 2)},
            {"term": "Termin 3", "trigger_progress": 0.75, "amount": round(base_amount * 0.25, 2)},
        ]
        retention = round(base_amount * 0.05, 2)

        return {
            "base_amount": round(base_amount, 2),
            "total_weight": round(total_weight, 4),
            "monthly_outflow": monthly,
            "cumulative_outflow": cumulative,
            "termin_schedule": {
                "down_payment": down_payment,
                "progress_terms": progress_terms,
                "retention": retention,
            },
        }

    def _productivity_factor(self, level: str) -> float:
        """Faktor produktivitas tenaga kerja. Koefisien = koefisien / faktor."""
        factors = {
            "NORMAL": 1.00,
            "LAHAN_SEMPIT": 0.85,
            "CUACA_BURUK": 0.75,
            "LEMBUR": 0.90,
            "MALAM": 0.80,
            "KETINGGIAN": 0.85,
        }
        return factors.get(str(level).upper(), 1.0)

    def _get_unit_price_for_item(self, wi_id: str, code: str, region: str, price_date: Optional[str] = None) -> Dict[str, Any]:
        """Pilih sumber harga: segment override jika tersedia, selain itu KG biasa."""
        segment = self.config.get("segment")
        if segment and hasattr(self.kg, "segment_overrides"):
            over = self.kg.segment_overrides.get(segment, {}).get(code)
            if over:
                from fastra_core.knowledge.segment_calibration import calculate_unit_price_from_override
                up = calculate_unit_price_from_override(over)
                up["segment_calibrated"] = True
                return up

        # Mapping sementara internal BOQ -> WorkItem_Code kalibrasi per segmen
        segment_map = {
            "Rumah Sederhana": {
                "STR.029": "WI-STR-BETON-K175",
                "STR.015": "WI-STR-BETON-K175",
                "STR.009": "WI-STR-PEMBESIAN-10KG",
                "STR.023": "WI-STR-PEMBESIAN-10KG",
                "STR.024": "WI-STR-PEMBESIAN-10KG",
                "DIN.005": "WI-ARS-PASANGAN-BATA-RINGAN-75MM",
            },
            "Rumah Menengah": {
                "STR.029": "WI-STR-BETON-K225",
                "STR.015": "WI-STR-BETON-K225",
                "STR.012": "WI-STR-BEKISTING-KOLOM",
                "STR.009": "WI-STR-PEMBESIAN-10KG",
                "STR.023": "WI-STR-PEMBESIAN-10KG",
                "STR.024": "WI-STR-PEMBESIAN-10KG",
            },
            "Rumah Mewah": {
                "STR.029": "WI-STR-BETON-K250",
                "STR.015": "WI-STR-BETON-K250",
                "STR.022": "WI-STR-BEKISTING-BALOK",
                "STR.021": "WI-STR-BEKISTING-PLAT",
            },
            "Ruko/Rukan": {
                "STR.029": "WI-STR-BETON-K250",
                "STR.015": "WI-STR-BETON-K250",
            },
            "Gedung": {
                "STR.029": "WI-STR-BETON-K300",
                "STR.015": "WI-STR-BETON-K300",
            },
            "Jalan/Jembatan": {
                "STR.029": "WI-INF-BETON-RIGID-PAVEMENT",
            },
        }
        if segment and code in segment_map.get(segment, {}):
            calibrated_code = segment_map[segment][code]
            over = self.kg.segment_overrides.get(segment, {}).get(calibrated_code)
            if over:
                from fastra_core.knowledge.segment_calibration import calculate_unit_price_from_override
                up = calculate_unit_price_from_override(over)
                up["segment_calibrated"] = True
                up["calibrated_from"] = calibrated_code
                return up

        return self.kg.get_unit_price(wi_id, region, price_date)

    def _build_vs_buy_analysis(self) -> Optional[Dict[str, Any]]:
        """Analisis Build vs Buy sederhana dari config build_vs_buy."""
        cfg = self.config.get("build_vs_buy")
        if not cfg:
            return None
        ready_mix = float(cfg.get("ready_mix_price", 0))
        site_mix = float(cfg.get("site_mix_price", 0))
        if ready_mix <= 0 or site_mix <= 0:
            return {
                "status": "NEEDS_DATA",
                "message": "Harga Ready Mix dan Site Mix belum diisi."
            }
        cheaper = "Ready Mix" if ready_mix <= site_mix else "Site Mix"
        saving = round(abs(ready_mix - site_mix), 2)
        return {
            "status": "COMPLETED",
            "ready_mix_price": ready_mix,
            "site_mix_price": site_mix,
            "cheaper_option": cheaper,
            "saving_per_unit": saving,
            "note": "Analisis berdasarkan harga per unit yang diberikan config build_vs_buy.",
        }

    def _format_template(self, template_name: str, rab: Dict[str, Any]) -> Dict[str, Any]:
        """Menghasilkan format output berbeda sesuai template."""
        if template_name == "PUPR Standard (AHSP)":
            return {
                "format": "PUPR_AHSP",
                "project": rab.get("project_uuid"),
                "direct_cost": rab.get("direct_cost"),
                "overhead": rab.get("overhead"),
                "profit": rab.get("profit"),
                "ppn": rab.get("ppn"),
                "pph_final": rab.get("pph_final"),
                "grand_total": rab.get("grand_total"),
                "items": [
                    {
                        "item_code": item.get("item_code"),
                        "description": item.get("description"),
                        "unit_price": item.get("unit_price"),
                        "quantity": item.get("quantity"),
                    } for item in rab.get("item_breakdown", [])
                ],
                "ahs_reference": [
                    item.get("ahs_reference") for item in rab.get("item_breakdown", []) if item.get("ahs_reference")
                ],
            }
        elif template_name == "BUMN Standard":
            return {
                "format": "BUMN_BOQ",
                "project": rab.get("project_uuid"),
                "items": [
                    {
                        "Item": item.get("item_code"),
                        "Description": item.get("description"),
                        "Unit": item.get("unit"),
                        "Quantity": item.get("quantity"),
                        "Rate": item.get("unit_price"),
                        "Total": item.get("total_price"),
                    } for item in rab.get("item_breakdown", [])
                ],
                "grand_total": rab.get("grand_total"),
            }
        elif template_name == "Bank Format (Kredit)":
            return {
                "format": "BANK_KREDIT",
                "project": rab.get("project_uuid"),
                "komponen_biaya": rab.get("division_summary"),
                "total_biaya": rab.get("grand_total"),
                "bobot": None,
            }
        elif template_name == "Simple Format (Kontraktor)":
            return {
                "format": "SIMPLE",
                "project": rab.get("project_uuid"),
                "pekerjaan": [
                    {
                        "uraian": item.get("description"),
                        "vol": item.get("quantity"),
                        "sat": item.get("unit"),
                        "harga_satuan": item.get("unit_price"),
                        "total": item.get("total_price"),
                    } for item in rab.get("item_breakdown", [])
                ],
                "grand_total": rab.get("grand_total"),
            }
        else:
            return {"format": "SWASTA_DETAIL", **rab}

    def generate_rab(self, boq: Dict[str, Any], region: str, price_date: Optional[str] = None) -> Dict[str, Any]:
        effective_price_date: Optional[str] = price_date
        if effective_price_date is None:
            pd = self.config.get("price_date")
            effective_price_date = pd if isinstance(pd, str) else None

        overhead_pct: float = float(self.config["overhead_pct"])
        profit_pct: float = float(self.config["profit_pct"])
        ppn_pct: float = float(self.config["ppn_pct"])
        pph_pct: float = float(self.config["pph_pct"])
        contingency_pct: float = float(self.config["contingency_pct"])
        inflation_pct: float = float(self.config["inflation_pct"])
        duration_months: int = int(self.config["duration_months"])
        building_area_value = self.config.get("building_area")
        building_area: Optional[float] = float(building_area_value) if building_area_value else None

        design_contingency_pct = float(self.config.get("design_contingency_pct", 0.0))
        construction_contingency_pct = float(self.config.get("construction_contingency_pct", 0.0))
        price_contingency_pct = float(self.config.get("price_contingency_pct", 0.0))
        risk_register = self.config.get("risk_register", [])

        item_breakdown: List[Dict[str, Any]] = []
        traceability: List[Dict[str, Any]] = []
        division_subtotals: Dict[str, Dict[str, Any]] = {}
        direct_cost = 0.0

        for div in boq.get("divisions", []):
            div_code = div.get("division_code", "DIV-00")
            div_subtotal = 0.0
            for item in div.get("items", []):
                code = item.get("item_code")
                qty = float(item.get("quantity", 0))
                unit = item.get("unit", "")
                description = item.get("description", "")
                boq_item_uuid = item.get("boq_item_uuid", "")

                wi = self._wi_by_code.get(code)
                wi_id = wi.id if wi else code
                up = self._get_unit_price_for_item(wi_id, code, region, effective_price_date)
                segment_calibrated = up.get("segment_calibrated", False)
                calibrated_from = up.get("calibrated_from")

                if segment_calibrated:
                    unit_price = up.get("unit_price", 0)
                    total_price = round(qty * unit_price, 2)
                else:
                    boq_unit_price = float(item.get("unit_price", 0))
                    boq_total_price = float(item.get("total_price", 0))
                    if boq_total_price > 0:
                        unit_price = boq_unit_price
                        total_price = boq_total_price
                    else:
                        unit_price = up.get("unit_price", 0)
                        total_price = round(qty * unit_price, 2)
                direct_cost += total_price
                div_subtotal += total_price

                if up.get("errors") and not segment_calibrated:
                    traceability.append({
                        "boq_source": boq_item_uuid,
                        "item_code": code,
                        "errors": up["errors"],
                    })
                    continue

                ahs_ref = wi.sni_ref if wi else ""
                trace = TraceLog(generated_at=boq.get("generated_at"))
                trace.add_step(
                    stage="COST_ENGINE",
                    operation="Calculate Unit Price",
                    input_entity=boq_item_uuid,
                    operation_detail=f"{description} @ {region}",
                    output_value=f"{unit_price} / {unit}",
                )
                trace.add_step(
                    stage="COST_ENGINE",
                    operation="Calculate Total Price",
                    operation_detail=f"{qty} {unit} x {unit_price}",
                    output_value=str(total_price),
                )
                audit_hash = trace.finalize()

                item_data = {
                    "boq_item_uuid": boq_item_uuid,
                    "item_code": code,
                    "description": description,
                    "quantity": qty,
                    "unit": unit,
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "material_breakdown": up.get("material_breakdown", []),
                    "labor_breakdown": up.get("labor_breakdown", []),
                    "equipment_breakdown": up.get("equipment_breakdown", []),
                    "ahs_reference": ahs_ref,
                    "audit_hash": audit_hash,
                    "segment_calibrated": segment_calibrated,
                    "calibrated_from": calibrated_from,
                }
                item_breakdown.append(item_data)
                traceability.append({
                    "boq_source": boq_item_uuid,
                    "item_code": code,
                    "quantity": qty,
                    "unit": unit,
                    "material_breakdown": up.get("material_breakdown", []),
                    "labor_breakdown": up.get("labor_breakdown", []),
                    "equipment_breakdown": up.get("equipment_breakdown", []),
                    "ahs_reference": ahs_ref,
                    "audit_hash": audit_hash,
                    "computed_at": boq.get("generated_at"),
                    "segment_calibrated": segment_calibrated,
                    "calibrated_from": calibrated_from,
                })

            division_subtotals[div_code] = {
                "division_code": div_code,
                "division_name": div.get("division_name", div_code),
                "subtotal": round(div_subtotal, 2),
            }

        direct_cost = round(direct_cost, 2)

        overhead = round(direct_cost * overhead_pct / 100, 2)
        profit = round((direct_cost + overhead) * profit_pct / 100, 2)
        dpp = round(direct_cost + overhead + profit, 2)
        ppn = round(dpp * ppn_pct / 100, 2)
        pph = round(dpp * pph_pct / 100, 2)
        # Contingency terpisah
        has_separate_contingency = (
            design_contingency_pct > 0 or
            construction_contingency_pct > 0 or
            price_contingency_pct > 0
        )
        if has_separate_contingency:
            design_contingency = round(direct_cost * design_contingency_pct / 100, 2)
            construction_contingency = round(direct_cost * construction_contingency_pct / 100, 2)
            price_contingency = round(direct_cost * price_contingency_pct / 100, 2)
            contingency = round(design_contingency + construction_contingency + price_contingency, 2)
        else:
            design_contingency = 0.0
            construction_contingency = 0.0
            price_contingency = 0.0
            contingency = round(direct_cost * contingency_pct / 100, 2)

        # Risk-based contingency (jika disediakan)
        risk_contingency = 0.0
        if risk_register:
            for risk in risk_register:
                probability = float(risk.get("probability", 0.0))
                impact = float(risk.get("impact", 0.0))
                risk_contingency += probability * impact
        risk_contingency = round(risk_contingency, 2)
        contingency = round(contingency + risk_contingency, 2)

        annual_inflation = inflation_pct / 100
        months = duration_months
        escalation_factor = (1 + annual_inflation) ** (months / 12) - 1
        escalation = round(dpp * escalation_factor, 2)

        # Material-specific escalation (linier sederhana)
        material_escalation = 0.0
        for item in item_breakdown:
            for mat in item.get("material_breakdown", []):
                cost = float(mat.get("cost", 0.0))
                vol = float(mat.get("volatility_factor", 0.0))
                material_escalation += cost * vol * (months / 12)
        material_escalation = round(material_escalation, 2)
        escalation = round(escalation + material_escalation, 2)

        grand_total = round(dpp + ppn + pph + contingency + escalation, 2)
        smkk_cost = None
        smkk_breakdown = None
        if self.config.get("include_smkk"):
            risk_level = self.config.get("risk_level") or "KECIL"
            from fastra_core.compiler.smkk_engine import calculate_smkk
            worker_count = int(self.config.get("worker_count", 25))
            contract_value = self.config.get("contract_value")
            smkk_result = calculate_smkk(
                risk_level,
                contract_value=contract_value,
                worker_count=worker_count,
                duration_months=duration_months,
            )
            smkk_cost = smkk_result["total_smkk"]
            smkk_breakdown = smkk_result["components"]
            grand_total = round(grand_total + smkk_cost, 2)

        # Multi-template
        template_name = self.config.get("template", "SWASTA_DETAIL")
        template_columns = []
        if hasattr(self.kg, "template_definitions"):
            template_columns = self.kg.template_definitions.get(template_name, [])

        # PPh Final berdasarkan kualifikasi
        pph_pct = float(self.config.get("pph_pct", 0))
        qualification = self.config.get("contractor_qualification")
        if qualification and hasattr(self.kg, "tax_rates"):
            # Coba cari tarif di kg.tax_rates
            for kategori, mapping in self.kg.tax_rates.items():
                for label, rate in mapping.items():
                    if qualification.upper() in label.upper():
                        pph_pct = float(rate) * 100  # rate dalam desimal
                        break
                else:
                    continue
                break
            self.config["pph_pct"] = pph_pct
            pph = round(dpp * pph_pct / 100, 2)

        # Pajak daerah / retribusi
        local_tax = float(self.config.get("local_tax", 0.0))
        grand_total = round(grand_total + local_tax, 2)

        build_vs_buy = self._build_vs_buy_analysis()
        # Template formatting
        template_output = self._format_template(template_name, {
            "project_uuid": boq.get("project_uuid"),
            "direct_cost": direct_cost,
            "overhead": overhead,
            "profit": profit,
            "ppn": ppn,
            "pph_final": pph,
            "grand_total": grand_total,
            "item_breakdown": item_breakdown,
            "division_summary": list(division_subtotals.values()),
        })

        cost_per_m2 = round(grand_total / building_area, 2) if building_area else None

        value_engineering: List[Dict[str, Any]] = []
        if self.config.get("include_value_engineering"):
            alternatives = getattr(self.kg, "alternative_materials", [])
            for item in item_breakdown:
                qty = float(item.get("quantity", 1))
                for mat in item.get("material_breakdown", []):
                    mat_id = mat.get("material_id")
                    for alt in alternatives:
                        if alt.get("original_id") != mat_id:
                            continue
                        if alt.get("status") not in ("Lebih Hemat", "Sebanding"):
                            continue
                        original_unit_price = float(mat.get("unit_price", 0))
                        alternative_unit_price = float(alt.get("alternative_price", 0))
                        coeff = float(mat.get("coefficient", 1))
                        waste = float(mat.get("waste_factor", 1.0))
                        saving_per_unit_work = (original_unit_price - alternative_unit_price) * coeff * waste
                        total_saving = saving_per_unit_work * qty
                        if total_saving > 0:
                            value_engineering.append({
                                "item_code": item.get("item_code"),
                                "material_id": mat_id,
                                "alternative_id": alt.get("alternative_id"),
                                "status": alt.get("status"),
                                "potential_saving": round(total_saving, 2),
                            })

        schedule_weights = self.config.get("schedule_weights")
        cashflow = None
        if schedule_weights:
            cashflow = self._generate_cashflow(grand_total, schedule_weights)

        template_name = self.config.get("template", "SWASTA_DETAIL")
        template_columns = getattr(self.kg, "template_definitions", {}).get(template_name, [])

        return {
            "project_uuid": boq.get("project_uuid"),
            "generated_at": boq.get("generated_at"),
            "template": self.config.get("template", "SWASTA_DETAIL"),
            "template_columns": template_columns,
            "cashflow": cashflow,
            "smkk_cost": smkk_cost,
            "smkk_breakdown": smkk_breakdown,
            "direct_cost": direct_cost,
            "overhead": overhead,
            "profit": profit,
            "dpp": dpp,
            "ppn": ppn,
            "pph_final": pph,
            "contingency": contingency,
            "contingency_breakdown": {
                "design": design_contingency,
                "construction": construction_contingency,
                "price": price_contingency,
                "risk": risk_contingency,
            },
            "escalation": escalation,
            "grand_total": grand_total,
            "cost_per_m2": cost_per_m2,
            "division_summary": list(division_subtotals.values()),
            "item_breakdown": item_breakdown,
            "traceability": traceability,
            "value_engineering": value_engineering,
            "build_vs_buy": build_vs_buy,
            "generated_by": "FASTRA Cost Engine v5.0 (ACES-500)",
        }
