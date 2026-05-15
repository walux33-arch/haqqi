"""Invoice generator compliant with Loi 16.23 (electronic invoice)."""
import json, os, uuid
from datetime import datetime
from typing import Optional

class InvoiceGenerator:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "invoices")
        os.makedirs(self.data_dir, exist_ok=True)

    def generate(self, invoice_data: dict) -> dict:
        """Generate invoice with Loi 16.23 mandatory fields."""
        now = datetime.now()
        invoice = {
            "invoice_number": invoice_data.get("invoice_number", f"FAC-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"),
            "date": invoice_data.get("date", now.strftime("%Y-%m-%d")),
            "due_date": invoice_data.get("due_date", ""),
            "seller": {
                "name": invoice_data.get("seller_name", ""),
                "ice": invoice_data.get("seller_ice", ""),
                "rc": invoice_data.get("seller_rc", ""),
                "cnss": invoice_data.get("seller_cnss", ""),
                "address": invoice_data.get("seller_address", ""),
                "city": invoice_data.get("seller_city", ""),
                "phone": invoice_data.get("seller_phone", ""),
                "email": invoice_data.get("seller_email", ""),
                "if": invoice_data.get("seller_if", ""),
            },
            "buyer": {
                "name": invoice_data.get("buyer_name", ""),
                "ice": invoice_data.get("buyer_ice", ""),
                "address": invoice_data.get("buyer_address", ""),
                "city": invoice_data.get("buyer_city", ""),
            },
            "items": [],
            "totals": {
                "ht": 0.0,
                "tva": 0.0,
                "ttc": 0.0,
            },
            "payment": {
                "method": invoice_data.get("payment_method", "virement"),
                "bank": invoice_data.get("bank_name", ""),
                "rib": invoice_data.get("bank_rib", ""),
                "swift": invoice_data.get("bank_swift", ""),
            },
            "notes": invoice_data.get("notes", ""),
            "is_electronic": True,
            "generated_at": now.isoformat(),
        }

        for item in invoice_data.get("items", []):
            qty = float(item.get("quantity", 1))
            pu = float(item.get("unit_price", 0))
            tva_rate = float(item.get("tva_rate", 0.20))
            ht = qty * pu
            tva = ht * tva_rate
            invoice["items"].append({
                "description": item.get("description", ""),
                "quantity": qty,
                "unit": item.get("unit", "unité"),
                "unit_price": pu,
                "ht": round(ht, 2),
                "tva_rate": tva_rate,
                "tva": round(tva, 2),
                "ttc": round(ht + tva, 2),
            })
            invoice["totals"]["ht"] += ht
            invoice["totals"]["tva"] += tva
            invoice["totals"]["ttc"] += ht + tva

        invoice["totals"]["ht"] = round(invoice["totals"]["ht"], 2)
        invoice["totals"]["tva"] = round(invoice["totals"]["tva"], 2)
        invoice["totals"]["ttc"] = round(invoice["totals"]["ttc"], 2)

        return invoice

    def to_html(self, invoice: dict) -> str:
        """Render invoice as HTML."""
        items_rows = ""
        for i, item in enumerate(invoice["items"], 1):
            items_rows += f"""
            <tr>
                <td style="padding:8px;border:1px solid #ddd;text-align:center">{i}</td>
                <td style="padding:8px;border:1px solid #ddd">{item['description']}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:center">{item['quantity']}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:right">{item['unit_price']:,.2f}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:right">{item['ht']:,.2f}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:center">{item['tva_rate']*100:.0f}%</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:right">{item['ttc']:,.2f}</td>
            </tr>"""

        s = invoice["seller"]
        b = invoice["buyer"]

        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8"><title>فاتورة - {invoice['invoice_number']}</title>
<style>
  body {{ font-family: 'DejaVu Sans', 'Tajawal', sans-serif; font-size: 12px; padding: 20px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #1a5632; color: white; padding: 10px; text-align: center; }}
  .header {{ background: #f0fdf4; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
  .total-row td {{ font-weight: bold; font-size: 14px; }}
</style></head>
<body>
<div class="header">
  <table style="border:none"><tr>
    <td style="border:none;width:50%">
      <h1 style="margin:0;color:#1a5632">فاتورة</h1>
      <p style="margin:4px 0"><strong>رقم:</strong> {invoice['invoice_number']}</p>
      <p style="margin:4px 0"><strong>التاريخ:</strong> {invoice['date']}</p>
      <p style="margin:4px 0"><strong>تاريخ الاستحقاق:</strong> {invoice['due_date']}</p>
    </td>
    <td style="border:none;width:50%;text-align:left">
      <p style="margin:4px 0"><strong>المورد:</strong> {s['name']}</p>
      <p style="margin:4px 0">ICE: {s['ice']} | RC: {s['rc']}</p>
      <p style="margin:4px 0">IF: {s['if']} | CNSS: {s['cnss']}</p>
      <p style="margin:4px 0">{s['address']}, {s['city']}</p>
    </td>
  </tr></table>
</div>

<table style="margin-bottom:15px;border:none">
  <tr><td style="border:none"><strong>الزبون:</strong> {b['name']}</td></tr>
  <tr><td style="border:none">ICE: {b['ice']} | {b['address']}, {b['city']}</td></tr>
</table>

<table>
  <thead><tr>
    <th>#</th><th>البيان</th><th>الكمية</th><th>ثمن الوحدة</th><th>HT</th><th>TVA</th><th>TTC</th>
  </tr></thead>
  <tbody>{items_rows}</tbody>
  <tfoot>
    <tr class="total-row"><td colspan="4" style="text-align:left;padding:8px;border:1px solid #ddd">المجموع</td>
      <td style="padding:8px;border:1px solid #ddd;text-align:right">{invoice['totals']['ht']:,.2f}</td>
      <td style="padding:8px;border:1px solid #ddd;text-align:right">{invoice['totals']['tva']:,.2f}</td>
      <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#1a5632">{invoice['totals']['ttc']:,.2f}</td>
    </tr>
  </tfoot>
</table>

<div style="margin-top:20px;padding:10px;background:#f9f9f9;border-radius:5px">
  <p><strong>طريقة الأداء:</strong> {invoice['payment']['method']}</p>
  {f'<p><strong>RIB:</strong> {invoice["payment"]["rib"]}</p>' if invoice['payment']['rib'] else ''}
  {f'<p style="font-size:11px;color:#666">{invoice["notes"]}</p>' if invoice['notes'] else ''}
</div>

<p style="margin-top:30px;font-size:10px;color:#999;text-align:center">
  فاتورة إلكترونية - conforme à la Loi 16.23 | Générée le {invoice['generated_at'][:10]}
</p>
</body></html>"""

    def save(self, invoice: dict, fmt: str = "json") -> str:
        """Save invoice to file."""
        fname = f"{invoice['invoice_number'].replace('/', '_')}.{fmt}"
        path = os.path.join(self.data_dir, fname)
        if fmt == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(invoice, f, ensure_ascii=False, indent=2)
        elif fmt == "html":
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.to_html(invoice))
        return path

invoice_generator = InvoiceGenerator()
