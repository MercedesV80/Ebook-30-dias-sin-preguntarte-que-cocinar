"""Script de actualización para Fase B en generar_pdf.py, generar_preview.py y generar_visor.py
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

def patch_file(filepath):
    text = filepath.read_text(encoding="utf-8")
    
    # 1. Autoría en Sección 2
    target_s2 = '<p class="section-desc">Un sistema simple para recuperar tranquilidad en la cocina doméstica</p>'
    replace_s2 = target_s2 + '''

    <div class="editorial-box" style="background:#fffcf8; border-left: 3px solid var(--accent-terracotta); padding: 3mm 4mm; margin-bottom: 3mm;">
      <h4 style="font-family: 'Fraunces', serif; color: var(--accent-terracotta); margin: 0 0 1mm 0; font-size: 9.5pt;">Quién hizo esta guía</h4>
      <p style="font-size: 8pt; color: #444; line-height: 1.45; margin: 0;">{ed.get("quien_hizo_esta_guia", {}).get("texto", "")}</p>
    </div>'''
    if target_s2 in text and 'Quién hizo esta guía' not in text:
        text = text.replace(target_s2, replace_s2)

    # 2. Pauta de sodio en Sección 4
    pauta_sodio_html = '''    <div class="editorial-box" style="border-left: 3px solid #eab308; background: #fefce8; padding: 2.5mm 3.5mm; margin-top: 2.5mm;">
      <h4 style="font-family: 'Fraunces', serif; color: #854d0e; font-size: 9pt; margin: 0 0 1mm 0;">🧂 {ed.get("pauta_sodio", {}).get("titulo", "Atención al sodio")}</h4>
      <p style="font-size: 7.5pt; color: #713f12; line-height: 1.35; margin: 0;">{ed.get("pauta_sodio", {}).get("texto", "")}</p>
    </div>'''
    if 'Atención al sodio' not in text:
        target_s4_end = '<!-- 5. CALENDARIO MENSUAL (DÍAS 1 A 15) -->'
        # insert before calendar
        text = text.replace(target_s4_end, pauta_sodio_html + '\n  </section>\n\n  ' + target_s4_end)

    # 3. Páginas 4B, 4C, 4D
    new_pages = '''
  <!-- 4B. CÓMO AJUSTAR LAS PORCIONES -->
  <section class="page-break">
    <h2 class="section-title">{ed.get("porciones", {}).get("titulo", "Cómo ajustar las porciones")}</h2>
    <p class="section-desc">{ed.get("porciones", {}).get("bajada", "")}</p>

    <div class="editorial-box" style="margin-top: 3mm;">
      <h3 style="margin-bottom: 2mm;">Tabla de equivalencias según los integrantes</h3>
      <table class="cal-table" style="margin-top: 1mm;">
        <thead>
          <tr>
            <th style="width: 25%;">Personas</th>
            <th style="width: 25%;">Factor de ajuste</th>
            <th style="width: 25%;">Carnes / Pollo</th>
            <th style="width: 25%;">Arroz / Fideos secos</th>
          </tr>
        </thead>
        <tbody>
          {"".join(f"""
          <tr>
            <td><strong>{row['personas']}</strong></td>
            <td>{row['factor']}</td>
            <td>{row['ejemplo_carne']}</td>
            <td>{row['ejemplo_arroz_pasta']}</td>
          </tr>
          """ for row in ed.get("porciones", {}).get("tabla_factores", []))}
        </tbody>
      </table>
    </div>

    <div class="grid-2col" style="margin-top: 3mm;">
      <div class="editorial-box" style="margin-bottom: 0;">
        <h3 style="color: var(--accent-terracotta); font-size: 10.5pt;">Porciones de referencia para chicos</h3>
        {"".join(f"""
        <div class="mini-card" style="margin-bottom: 2mm;">
          <strong style="color: var(--accent-sage);">👶 {r['rango']}</strong>
          <p style="font-size: 7.5pt; color: #444; margin-top: 1mm;">{r['porcion']}</p>
        </div>
        """ for r in ed.get("porciones", {}).get("referencia_edades", []))}
      </div>

      <div class="editorial-box" style="margin-bottom: 0;">
        <h3 style="font-size: 10.5pt;">Pautas clave al cambiar cantidades</h3>
        {"".join(f"""
        <div style="margin-bottom: 2.5mm;">
          <strong style="font-size: 8pt; color: var(--accent-terracotta);">• {p['titulo']}:</strong>
          <span style="font-size: 7.5pt; color: #444;"> {p['texto']}</span>
        </div>
        """ for p in ed.get("porciones", {}).get("pautas_clave", []))}
      </div>
    </div>

    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 2.5mm 3.5mm; margin-top: 3mm; font-size: 7.5pt; color: #555;">
      ℹ️ <strong>Aclaración:</strong> {ed.get("porciones", {}).get("aclaracion", "")}
    </div>
  </section>

  <!-- 4C. SEGURIDAD CON CHICOS & COMER EN PAZ -->
  <section class="page-break">
    <h2 class="section-title">Seguridad con Chicos & Comer en Paz</h2>
    <p class="section-desc">Pautas de seguridad alimentaria infantil y estrategias cotidianas sin peleas</p>

    <div class="grid-2col" style="margin-top: 3mm;">
      <!-- Columna 1: Seguridad -->
      <div class="editorial-box">
        <h3 style="color: #dc2626; font-size: 10.5pt;">🛡️ Prevención de atragantamiento</h3>
        {"".join(f"""
        <div class="mini-card" style="margin-bottom: 2mm;">
          <strong style="color: #991b1b; font-size: 8pt;">{al['alimento']}</strong>
          <p style="font-size: 7.5pt; color: #444; margin-top: 0.5mm;">{al['adaptacion']}</p>
        </div>
        """ for al in ed.get("seguridad_infantil", {}).get("alimentos_riesgo", []))}

        <div style="background: #fef2f2; border-left: 3px solid #ef4444; padding: 2mm 3mm; border-radius: 4px; margin-top: 2mm;">
          <strong style="font-size: 8pt; color: #991b1b;">🍯 {ed.get("seguridad_infantil", {}).get("regla_miel", {}).get("titulo", "")}</strong>
          <p style="font-size: 7pt; color: #7f1d1d; margin: 0.5mm 0 0 0;">{ed.get("seguridad_infantil", {}).get("regla_miel", {}).get("texto", "")}</p>
        </div>
      </div>

      <!-- Columna 2: Comer en paz -->
      <div class="editorial-box">
        <h3 style="color: var(--accent-sage); font-size: 10.5pt;">🌱 Consejos para chicos selectivos</h3>
        {"".join(f"""
        <div style="margin-bottom: 2mm; padding-bottom: 1.5mm; border-bottom: 1px dashed #e2e8f0;">
          <strong style="font-size: 8pt; color: var(--accent-terracotta);">{c['numero']}. {c['titulo']}:</strong>
          <span style="font-size: 7.5pt; color: #444;"> {c['texto']}</span>
        </div>
        """ for c in ed.get("con_chicos_en_casa", {}).get("consejos", []))}
      </div>
    </div>

    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 2mm 3mm; margin-top: 1mm; font-size: 7pt; color: #666; text-align: center;">
      {ed.get("seguridad_infantil", {}).get("aclaracion", "")}
    </div>
  </section>

  <!-- 4D. SEMANA TIPO DE EXTRAS & PACK DE IMPRIMIBLES -->
  <section class="page-break">
    <h2 class="section-title">Semana Tipo de Extras & Pack de Imprimibles</h2>
    <p class="section-desc">Rotación de desayunos, meriendas y viandas + tus plantillas descargables</p>

    <div class="editorial-box" style="margin-top: 2mm;">
      <h3 style="margin-bottom: 1.5mm;">Esquema semanal rotativo (Desayunos, Colaciones y Viandas)</h3>
      <table class="cal-table" style="font-size: 7.5pt;">
        <thead>
          <tr>
            <th style="width: 14%;">Día</th>
            <th style="width: 30%;">Desayuno / Merienda</th>
            <th style="width: 26%;">Colación / Snack</th>
            <th style="width: 30%;">Vianda / Postre</th>
          </tr>
        </thead>
        <tbody>
          {"".join(f"""
          <tr>
            <td><strong>{d['dia']}</strong></td>
            <td>{d['desayuno']}</td>
            <td>{d['colacion']}</td>
            <td><small>🍱 {d['vianda']}</small><br><small style='color:#777;'>🍰 {d['postre']}</small></td>
          </tr>
          """ for d in ed.get("semana_extras", {}).get("dias", []))}
        </tbody>
      </table>
    </div>

    <div class="editorial-box" style="margin-top: 3mm;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin-bottom: 1.5mm; color: var(--accent-terracotta);">📥 Cómo usar tu Pack de Imprimibles A4</h3>
        <span style="background: #fdf2f8; color: #9d174d; font-size: 7pt; font-weight: bold; padding: 1px 6px; border-radius: 4px; border: 1px solid #fbcfe8;">PDF Independiente Incluido</span>
      </div>
      <p style="font-size: 8pt; color: #555; margin-bottom: 2mm;">{ed.get("como_usar_imprimibles", {}).get("bajada", "")}</p>
      
      <div class="grid-2col">
        {"".join(f"""
        <div class="mini-card" style="padding: 2mm 3mm;">
          <strong style="font-size: 8pt; color: var(--accent-sage);">{h['nombre']}</strong>
          <p style="font-size: 7pt; color: #444; margin: 1mm 0 0 0;">{h['uso']}</p>
        </div>
        """ for h in ed.get("como_usar_imprimibles", {}).get("herramientas", []))}
      </div>
    </div>
  </section>
'''
    if '<!-- 4B. CÓMO AJUSTAR LAS PORCIONES -->' not in text:
        text = text.replace('<!-- 5. CALENDARIO MENSUAL (DÍAS 1 A 15) -->', new_pages + '\n  <!-- 5. CALENDARIO MENSUAL (DÍAS 1 A 15) -->')

    # 4. Kcal y Acompañamiento verde en recetas
    old_cal = 'calorias = f\'<span class="pill-pdf cal">~{r["nutricion"]["kcal"]} kcal</span>\' if r.get("nutricion") else ""'
    new_cal = 'calorias = f\'<span class="pill-pdf cal">~{r["nutricion"]["kcal"]} kcal (estimación por porción de adulto)</span>\' if r.get("nutricion") else ""'
    text = text.replace(old_cal, new_cal)

    old_rec = 'senales = f\'<div class="cue-pdf"><strong>👀 Señal de cocción:</strong> {r["senales_coccion"]}</div>\' if r.get("senales_coccion") else ""'
    new_rec = old_rec + '\n        acomp_verde = f\'<div class="cue-pdf" style="background:#f0fdf4; border-left:3px solid #22c55e; color:#166534; margin-top:2mm;">{r["acompanamiento_verde"]}</div>\' if r.get("acompanamiento_verde") else ""'
    if 'acomp_verde =' not in text:
        text = text.replace(old_rec, new_rec)
        text = text.replace('{nota_seg}', '{nota_seg}\n                {acomp_verde}')

    # 5. Lista de compras Extras
    extras_code = """
    # 8B. LISTA DE COMPRAS EXTRAS (DESAYUNOS, COLACIONES Y VIANDAS)
    extras_recetas = [
        'tostadas-queso-tomate', 'palitos-verdura-hummus', 'vianda-sandwich-arabe', 'helado-banana',
        'avena-nocturna', 'bolitas-avena-banana', 'vianda-bowl-pollo-arroz', 'manzanas-asadas',
        'panqueques-banana', 'vianda-ensalada-lentejas', 'postre-chocolate-maicena',
        'licuado-banana', 'crumble-manzana'
    ]
    tot_extras = defaultdict(float)
    for rid in extras_recetas:
        r_ex = recetas.get(rid)
        if not r_ex: continue
        for ing in r_ex['ingredientes']:
            k_ex = (ing['sector'], ing['item'], ing['unidad'])
            tot_extras[k_ex] += ing['cantidad']

    sectores_orden = ['verduras y frutas', 'carnes y huevos', 'lácteos', 'almacén', 'panificados']
    extras_sectores = []
    for s_nom in sectores_orden:
        s_items = []
        for (sec, itm, uni), cant in sorted(tot_extras.items()):
            if sec == s_nom:
                s_items.append({'item': itm, 'texto': motor.cantidad_legible(cant, uni)})
        if s_items:
            extras_sectores.append((s_nom, s_items))

    html += f\"\"\"
    <section class="page-break">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <h2 class="section-title">Lista de Compras · Extras</h2>
          <p class="section-desc">Ingredientes para resolver la Semana Tipo de Desayunos, Colaciones y Viandas</p>
        </div>
        <span style="background: #eef6ee; color: #166534; font-size: 7.5pt; font-weight: bold; padding: 2px 8px; border-radius: 4px; border: 1px solid #bbf7d0;">Bloque Separado</span>
      </div>

      <div class="shop-sectors-pdf" style="margin-top: 3mm;">
    \"\"\"
    for sector, items in extras_sectores:
        html += f\"\"\"
        <div class="shop-sec-col">
          <h4>{sector}</h4>
        \"\"\"
        for it in items:
            html += f\"\"\"
            <div class="shop-item-pdf">
              <span class="check-box-pdf"></span>
              <span><strong>{it['item']}</strong>: {it['texto']}</span>
            </div>
            \"\"\"
        html += "</div>"
    html += "</div></section>"
"""
    if '# 8B. LISTA DE COMPRAS EXTRAS' not in text:
        target_final = '    # 9. PÁGINA FINAL / COMPROMISO Y FUENTES'
        text = text.replace(target_final, extras_code + '\n' + target_final)

    filepath.write_text(text, encoding="utf-8")
    print(f"✅ {filepath.name} parcheado con éxito")

if __name__ == "__main__":
    patch_file(RAIZ / "scripts" / "generar_pdf.py")

