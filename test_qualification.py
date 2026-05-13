"""Quick test for legal qualification engine."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.agent.legal_reasoning import qualifier

tests = [
    'شنو هي شروط الزواج فالمغرب؟',
    'كيفاش نأسس شركة SARL؟',
    'شنو هي عقوبة السرقة؟',
    'بغيت نرفع قضية ضد مشغلي',
    'واش يمكن ليا نخرج المكري من المحل التجاري',
    'واش الضريبة على القيمة المضافة عندنا فالمغرب؟',
    'بغيت نعرف الحقوق العينية',
]

for t in tests:
    q = qualifier.qualify(t)
    print(f"Q: {t[:40]:40s} -> Domaine: {q['primary_domain']:12s} | Niveau: {q['norm_label']}")

print("\n--- Abrogation tests ---")
print(f"قانون 06.07: {qualifier.check_abrogation('قانون 06.07')}")
print(f"commercial: {qualifier.check_abrogation('commercial')}")
