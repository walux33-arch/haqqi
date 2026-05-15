"""SaaS subscription plans and pricing."""
import os, json
from typing import Optional

PLANS = {
    "free": {
        "name": "Free",
        "name_ar": "مجاني",
        "price_mad": 0,
        "price_id": "",
        "features": {
            "chat_messages": 50,
            "invoices_month": 5,
            "tax_calculations": 10,
            "legal_articles": True,
            "admin_procedures": False,
            "support": "community",
        },
        "features_ar": [
            "50 رسالة قانونية شهرياً",
            "5 فواتير إلكترونية شهرياً",
            "10 عملية حساب ضريبي",
            "الوصول لـ 5,697 مادة قانونية",
        ],
    },
    "pro": {
        "name": "Pro",
        "name_ar": "احترافي",
        "price_mad": 299,
        "price_id": "price_pro_monthly",
        "features": {
            "chat_messages": 1000,
            "invoices_month": 100,
            "tax_calculations": -1,
            "legal_articles": True,
            "admin_procedures": True,
            "support": "priority",
            "pdf_export": True,
            "contracts": True,
        },
        "features_ar": [
            "1,000 رسالة قانونية شهرياً",
            "100 فاتورة إلكترونية شهرياً",
            "حسابات ضريبية غير محدودة",
            "الوصول لـ 5,697 مادة قانونية",
            "50+ مسطرة إدارية",
            "تصدير PDF",
            "توليد العقود",
            "دعم ذو أولوية",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "name_ar": "مؤسساتي",
        "price_mad": 999,
        "price_id": "price_enterprise_monthly",
        "features": {
            "chat_messages": -1,
            "invoices_month": -1,
            "tax_calculations": -1,
            "legal_articles": True,
            "admin_procedures": True,
            "pdf_export": True,
            "contracts": True,
            "api_access": True,
            "white_label": True,
            "dedicated_support": True,
            "custom_integration": True,
        },
        "features_ar": [
            "رسائل قانونية غير محدودة",
            "فواتير غير محدودة",
            "حسابات ضريبية غير محدودة",
            "الوصول الكامل للمواد القانونية",
            "جميع المساطر الإدارية",
            "API مخصص",
            "علامة بيضاء (White Label)",
            "دعم حصري",
            "دمج مخصص مع أنظمتكم",
        ],
    },
}

def get_plan(plan_id: str) -> Optional[dict]:
    return PLANS.get(plan_id)

def list_plans() -> dict:
    return PLANS

def get_feature(features: dict, key: str) -> str:
    val = features.get(key, 0)
    if val == -1:
        return "غير محدود"
    return str(val)
