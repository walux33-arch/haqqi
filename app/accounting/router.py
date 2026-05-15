"""Accounting API: tax calculator, invoice generator, reports."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
from app.accounting.tax_calculator import tax_calculator
from app.accounting.invoice_generator import invoice_generator

router = APIRouter(prefix="/api/comptabilite", tags=["Comptabilité"])

# ─── Request Models ───

class IRRequest(BaseModel):
    revenu_annuel: float = Field(..., ge=0)
    frais: float = 0
    nb_enfants: int = 0
    regime: str = "reel"

class ISRequest(BaseModel):
    benefice_net: float = Field(..., ge=0)
    secteur: str = "standard"

class TVARequest(BaseModel):
    montant_ht: float = Field(..., ge=0)
    taux_tva: float = 0.20

class CNSSRequest(BaseModel):
    salaire_mensuel: float = Field(..., ge=0)

class SimulationRequest(BaseModel):
    ca_mensuel: float = Field(..., ge=0)
    frais_mensuels: float = 0
    regime: str = "auto_entrepreneur"

class InvoiceItem(BaseModel):
    description: str
    quantity: float = 1
    unit: str = "unité"
    unit_price: float = Field(..., ge=0)
    tva_rate: float = 0.20

class InvoiceRequest(BaseModel):
    seller_name: str
    seller_ice: str = ""
    seller_rc: str = ""
    seller_cnss: str = ""
    seller_address: str = ""
    seller_city: str = ""
    seller_phone: str = ""
    seller_email: str = ""
    seller_if: str = ""
    buyer_name: str
    buyer_ice: str = ""
    buyer_address: str = ""
    buyer_city: str = ""
    items: list[InvoiceItem]
    payment_method: str = "virement"
    bank_name: str = ""
    bank_rib: str = ""
    bank_swift: str = ""
    notes: str = ""
    due_date: str = ""

# ─── Endpoints ───

@router.post("/ir")
def calculate_ir(req: IRRequest):
    return tax_calculator.calculate_ir(req.revenu_annuel, req.frais, req.nb_enfants, req.regime)

@router.post("/is")
def calculate_is(req: ISRequest):
    return tax_calculator.calculate_is(req.benefice_net, req.secteur)

@router.post("/tva")
def calculate_tva(req: TVARequest):
    return tax_calculator.calculate_tva(req.montant_ht, req.taux_tva)

@router.post("/cnss")
def calculate_cnss(req: CNSSRequest):
    return tax_calculator.calculate_cnss(req.salaire_mensuel)

@router.post("/simulation")
def simulate(req: SimulationRequest):
    return tax_calculator.simulate_charges(req.ca_mensuel, req.frais_mensuels, req.regime)

@router.post("/facture")
def generate_invoice(req: InvoiceRequest):
    data = req.model_dump()
    data["items"] = [i.model_dump() for i in req.items]
    invoice = invoice_generator.generate(data)
    path = invoice_generator.save(invoice, "json")
    return {"invoice": invoice, "saved_to": path}

@router.post("/facture/html", response_class=HTMLResponse)
def generate_invoice_html(req: InvoiceRequest):
    data = req.model_dump()
    data["items"] = [i.model_dump() for i in req.items]
    invoice = invoice_generator.generate(data)
    html = invoice_generator.to_html(invoice)
    invoice_generator.save(invoice, "html")
    return html

@router.get("/taux")
def get_tax_rates():
    """Get current tax rates (IR brackets, IS rates, TVA rates)."""
    return {
        "ir": tax_calculator.ir,
        "is": tax_calculator.is_rates,
        "tva": tax_calculator.tva,
    }
