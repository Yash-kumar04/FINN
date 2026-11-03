import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import fitz

def inspect_bank(name, filename):
    print("=" * 80)
    print(f"BANK: {name} ({filename})")
    print("=" * 80)
    doc = fitz.open(f"pipeline/downloads/{filename}")
    print(f"Total pages: {len(doc)}")
    
    for p_idx in range(len(doc)):
        txt = doc[p_idx].get_text()
        t_low = txt.lower()
        if "interest earned" in t_low or "total income" in t_low:
            if "profit before tax" in t_low or "profit after tax" in t_low or "net profit" in t_low:
                scope = "Consolidated" if "consolidated" in t_low else "Standalone"
                print(f"\n--- Page {p_idx+1} ({scope}) ---")
                for line in txt.split("\n"):
                    l_low = line.lower()
                    if any(k in l_low for k in ["interest earned", "total income", "revenue", "profit before", "profit after", "net profit", "operating profit"]):
                        print(f"   {line.strip()}")

inspect_bank("HDFC BANK", "HDFCBANK_17102026135520_OutcomeofBMResults_17oct2026.pdf")
inspect_bank("ICICI BANK", "ICICI2022_17102026152608_NSEBSE17102026.pdf")
inspect_bank("KOTAK MAHINDRA BANK", "KMBLTAB_24102026131109_OutcomeofBMOct242026SIGNED.pdf")

