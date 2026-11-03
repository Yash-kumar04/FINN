import fitz
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

doc = fitz.open("pipeline/downloads/DIXON_Outcome30102026.pdf")

print("=== PAGE 1 ===")
print(doc[0].get_text())

print("\n=== PAGE 3 ===")
print(doc[2].get_text())

print("\n=== PAGE 11 ===")
print(doc[10].get_text())
