import re
from pathlib import Path

v3_path = Path("scripts/compilar_v3.py")
v4_path = Path("scripts/compilar_v4.py")

v3_text = v3_path.read_text(encoding="utf-8")
v4_text = v4_path.read_text(encoding="utf-8")

# Extract section 3 and 4 from v3
start_v3 = v3_text.find("  <!-- 3. EL MÉTODO & LA FÓRMULA DEL PLATO -->")
end_v3 = v3_text.find("  <!-- 4B. CÓMO AJUSTAR LAS PORCIONES -->")
section_3_4_v3 = v3_text[start_v3:end_v3]

# In v4:
start_v4 = v4_text.find("  <!-- 3. EL MÉTODO & LA FÓRMULA DEL PLATO -->")
end_v4 = v4_text.find("  <!-- 4B. CÓMO AJUSTAR LAS PORCIONES -->")

v4_text = v4_text[:start_v4] + section_3_4_v3 + v4_text[end_v4:]
v4_path.write_text(v4_text, encoding="utf-8")
print("Successfully patched sections 3 and 4 into compilar_v4.py")

