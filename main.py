from cardscan.validator import scan_text_advanced
from cardscan.masker import redact_text

sample_chat = (
    "Order serial is 9876543210123456 (fake). "
    "But user typed cardis4111111111111111now and amex 3782-822463-10005 together."
)

print("--- 🔍 DISCOVERY ---")
for cc in scan_text_advanced(sample_chat):
    print(f"Detected {cc['brand']} ({cc['style']})")

print("\n--- 🛡️ REDACTION OUTPUT ---")
print(redact_text(sample_chat))
