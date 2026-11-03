#!/usr/bin/env python3
"""Compilador de producción · Edición 2026 para el Ebook "30 días sin preguntarte qué cocinar"
Genera:
1. salida/30-dias-sin-preguntarte-que-cocinar_completo.pdf (Edición completa A4 para impresión: 2 recetas por página, tipografía ≥ 9pt)
2. salida/30-dias-sin-preguntarte-que-cocinar_celular.pdf (Edición liviana para celular: 1 receta por página aprovechando el espacio vertical, < 10 MB)
"""
import json
import math
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
import pypdf

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import motor

DATOS = RAIZ / "datos"
DISENO = RAIZ / "diseno"
SALIDA = RAIZ / "salida"

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Mapeo exacto de sobras y del freezer para que NUNCA aparezca "None"
SOBRAS_TEXTOS = {
    (5, "almuerzo"): "Sobras del chili (cocinado el día 4)",
    (11, "almuerzo"): "Sobras del cerdo agridulce (cocinado el día 10)",
    (12, "cena"): "Albóndigas del freezer (cocinadas el día 7)",
    (15, "almuerzo"): "Sobras de las milanesas (cocinadas el día 14)",
    (15, "cena"): "Sobras del guiso de lentejas (cocinado el día 14)",
    (26, "almuerzo"): "Sobras del chili (cocinado el día 25)",
}

def generar_html_pdf(edicion="completa"):
    config, recetas, cal = motor.cargar()
    
    editorial_path = DATOS / "contenido_editorial.json"
    ed = json.loads(editorial_path.read_text(encoding="utf-8")) if editorial_path.exists() else {}

    # Directorio de imágenes según la edición
    if edicion == "celular":
        img_dir = DISENO / "ilustraciones_mobile" if (DISENO / "ilustraciones_mobile").exists() else DISENO / "ilustraciones"
    else:
        img_dir = DISENO / "ilustraciones_opt" if (DISENO / "ilustraciones_opt").exists() else DISENO / "ilustraciones"

    portada_img = img_dir / "portada.png"
    if not portada_img.exists():
        portada_img = DISENO / "ilustraciones/portada.png"

    semanas_info = []
    for a, b in motor.semanas():
        tot, detalle = motor.lista_compras(config, recetas, cal, a, b)
        sectores, alacena = motor.lista_para_imprimir(config, tot)
        semanas_info.append({
            "desde": a,
            "hasta": b,
            "sectores": sectores,
            "alacena": alacena
        })

    # Punto 3: Base de pollo cocido se mueve al COMIENZO del recetario como "Receta base"
    receta_base_pollo = [r for r in recetas.values() if r.get("id") == "base-pollo-cocido"]
    recetas_principales = [r for r in recetas.values() if r.get("tipo") == "principal"]
    recetas_extras = [r for r in recetas.values() if r.get("tipo") in ["desayuno", "colacion", "vianda", "postre"]]
    
    # Lista ordenada: Base de pollo primero, luego 32 principales, luego 13 extras (total 46)
    recetas_a_incluir = receta_base_pollo + recetas_principales + recetas_extras

    # Cálculo exacto de página de la Base de Pollo Cocido:
    # 1 portada + 6 páginas editoriales (Antes de empezar, Método, Seguridad, Porciones, Chicos, Extras) + 2 páginas calendario (1-15, 16-30) = 9 páginas previas.
    # El recetario comienza exactamente en la página 10 en AMBAS ediciones.
    base_pollo_pag = 10

    # Tipografía de recetas según edición
    if edicion == "completa":
        font_recipe_body = "9.2pt"
        line_height_body = "1.34"
        font_recipe_title = "11.5pt"
        font_recipe_sub = "7.8pt"
        font_col_title = "8.5pt"
        font_cue = "7.8pt"
        img_height = "35mm"
        card_half_padding = "3.2mm 4.2mm"
    else:
        font_recipe_body = "9.6pt"
        line_height_body = "1.38"
        font_recipe_title = "14pt"
        font_recipe_sub = "8.2pt"
        font_col_title = "9.2pt"
        font_cue = "8.3pt"
        img_height = "64mm"
        card_half_padding = "3.5mm 4.5mm"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>{config.get("titulo", "30 días sin preguntarte qué cocinar")} · Edición 2026</title>
  <style>
    @font-face {{
      font-family: 'Fraunces';
      src: url('{DISENO / "fuentes/Fraunces.ttf"}') format('truetype');
      font-weight: 400 700;
    }}
    @font-face {{
      font-family: 'Nunito Sans';
      src: url('{DISENO / "fuentes/NunitoSans.ttf"}') format('truetype');
      font-weight: 400 600 700 800;
    }}

    :root {{
      --bg-cream: #FAF7F2;
      --bg-card: #FFFFFF;
      --text-dark: #2B2A27;
      --text-muted: #5C5852;
      --accent-terracotta: #D96B43;
      --accent-terracotta-light: #F7EBE4;
      --accent-sage: #5B8266;
      --accent-sage-light: #EBF2EC;
      --accent-mustard: #E3A857;
      --border-soft: #EBDCCC;
    }}

    @page {{
      size: A4 portrait;
      margin: 10mm 12mm 12mm 12mm;
      @bottom-center {{
        content: counter(page);
        font-family: 'Fraunces', serif;
        font-size: 8pt;
        color: #888;
      }}
    }}

    *, *:before, *:after {{ box-sizing: border-box; }}

    body {{
      font-family: 'Nunito Sans', sans-serif;
      color: var(--text-dark);
      background: var(--bg-cream);
      margin: 0;
      padding: 0;
      font-size: 8pt;
      line-height: 1.35;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    .page-break {{
      page-break-after: always;
      break-after: page;
      height: 100%;
      min-height: 275mm;
      box-sizing: border-box;
      position: relative;
    }}
    .page-break:last-child {{
      page-break-after: avoid;
      break-after: avoid;
    }}

    h1, h2, h3, h4 {{
      font-family: 'Fraunces', serif;
      color: var(--text-dark);
      margin: 0 0 1.5mm 0;
      line-height: 1.15;
    }}
    p {{ margin: 0 0 2mm 0; }}

    .section-title {{
      font-size: 15pt;
      color: var(--accent-terracotta);
      border-bottom: 2px solid var(--border-soft);
      padding-bottom: 1.5mm;
      margin-bottom: 1mm;
    }}
    .section-desc {{
      font-size: 8pt;
      color: var(--text-muted);
      margin-bottom: 3.5mm;
      font-style: italic;
    }}

    .editorial-box {{
      background: #FFFFFF;
      border: 1px solid var(--border-soft);
      border-radius: 6px;
      padding: 3mm 4mm;
      margin-bottom: 3mm;
    }}
    .editorial-box h3 {{
      font-size: 10.5pt;
      color: var(--accent-terracotta);
      margin-bottom: 1.5mm;
    }}

    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3.5mm;
    }}
    .grid-3col {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 3mm;
    }}

    .mini-card {{
      background: #FFFFFF;
      border: 1px solid var(--border-soft);
      border-radius: 5px;
      padding: 2.2mm 3mm;
    }}
    .mini-card h4 {{
      font-size: 8pt;
      color: var(--accent-sage);
      margin-bottom: 1mm;
    }}
    .mini-card p {{
      font-size: 7.2pt;
      color: var(--text-muted);
      margin: 0;
      line-height: 1.25;
    }}

    .highlight-card {{
      background: var(--accent-terracotta-light);
      border-left: 3.5px solid var(--accent-terracotta);
      border-radius: 4px;
      padding: 2.5mm 3.5mm;
      margin: 2mm 0;
      font-size: 7.5pt;
    }}
    .highlight-card ul {{
      margin: 1mm 0 0 0;
      padding-left: 4mm;
    }}
    .highlight-card li {{
      margin-bottom: 1mm;
    }}

    /* TABLAS EDITORIALES */
    .cal-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 7.5pt;
      background: #fff;
      border-radius: 5px;
      overflow: hidden;
      border: 1px solid var(--border-soft);
    }}
    .cal-table th {{
      background: var(--accent-sage);
      color: #fff;
      font-weight: 700;
      padding: 2mm 2.5mm;
      text-align: left;
      font-size: 7.8pt;
    }}
    .cal-table td {{
      padding: 2mm 2.5mm;
      border-bottom: 1px solid #f0e6da;
      vertical-align: middle;
    }}
    .cal-table tr:nth-child(even) {{
      background: #faf8f5;
    }}
    .cal-day-num {{
      font-weight: 800;
      color: var(--accent-terracotta);
    }}
    .badge-batch {{
      display: inline-block;
      background: #fffbeb;
      color: #92400e;
      border: 1px solid #fde68a;
      border-radius: 3px;
      padding: 1.5px 5px;
      font-size: 6.5pt;
      font-weight: bold;
      margin-top: 1.5px;
    }}

    /* ==============================================================
       ESTILOS DE RECETAS: EDICIÓN COMPLETA (2 POR PÁGINA)
       ============================================================== */
    .recipe-double-page {{
      page-break-after: always;
      break-after: page;
      height: 100%;
      min-height: 275mm;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-sizing: border-box;
    }}
    .recipe-card-half {{
      border: 1px solid var(--border-soft);
      border-radius: 7px;
      padding: {card_half_padding};
      background: #ffffff;
      height: 48.6%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-sizing: border-box;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .card-half-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 1.5px solid var(--border-soft);
      padding-bottom: 1.2mm;
      margin-bottom: 1.5mm;
    }}
    .card-half-title {{
      font-family: 'Fraunces', serif;
      font-size: {font_recipe_title};
      color: var(--text-dark);
      margin: 0;
      line-height: 1.15;
    }}
    .card-half-sub {{
      font-size: {font_recipe_sub};
      color: var(--text-muted);
      margin-top: 0.5mm;
    }}
    .card-half-pills {{
      display: flex;
      gap: 1.5mm;
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .pill-pdf {{
      font-size: 7.2pt;
      font-weight: 700;
      padding: 1.8px 6.5px;
      border-radius: 50px;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
    }}
    .pill-pdf.time {{ background: var(--accent-sage-light); color: var(--accent-sage); }}
    .pill-pdf.cal {{ background: var(--accent-terracotta-light); color: var(--accent-terracotta); }}

    .card-half-grid {{
      display: grid;
      grid-template-columns: 0.76fr 1.24fr;
      gap: 3.8mm;
      flex-grow: 1;
    }}
    .card-half-left {{
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
    }}
    .card-half-img {{
      width: 100%;
      height: {img_height};
      object-fit: cover;
      border-radius: 4px;
      border: 1px solid var(--border-soft);
      margin-bottom: 1.5mm;
    }}
    .card-half-col-title {{
      font-size: {font_col_title};
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--accent-sage);
      margin-bottom: 1.2mm;
      border-bottom: 1px solid #f0e6da;
      padding-bottom: 0.5mm;
    }}
    .card-half-ings {{
      list-style: none;
      padding: 0;
      margin: 0;
      font-size: {font_recipe_body};
      line-height: {line_height_body};
    }}
    .card-half-ings li {{
      padding: 0.5mm 0;
      border-bottom: 1px dotted #f5ede4;
      display: flex;
      justify-content: space-between;
    }}
    .card-half-ings strong {{
      color: var(--accent-terracotta);
    }}
    .card-half-steps {{
      padding-left: 4.2mm;
      margin: 0 0 1.5mm 0;
      font-size: {font_recipe_body};
      line-height: {line_height_body};
    }}
    .card-half-steps li {{
      margin-bottom: 1.2mm;
    }}
    .cue-compact {{
      font-size: {font_cue};
      line-height: 1.25;
      padding: 1.2mm 2.2mm;
      border-radius: 3px;
      margin-top: 1.2mm;
      border-left: 2.5px solid #ccc;
    }}
    .cue-compact.cue-brown {{ background: #faf4ed; border-color: #d97706; color: #78350f; }}
    .cue-compact.cue-green {{ background: #f0fdf4; border-color: #22c55e; color: #166534; }}
    .cue-compact.cue-orange {{ background: #fff7ed; border-color: #f97316; color: #9a3412; }}
    .variants-compact {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2.5mm;
      margin-top: 1.2mm;
      font-size: {font_cue};
      line-height: 1.25;
      background: #faf8f5;
      padding: 1.5mm 2.2mm;
      border-radius: 4px;
      border: 1px solid #f0e6da;
    }}
    .variants-compact strong {{
      display: block;
      color: var(--accent-terracotta);
      font-size: {font_cue};
      margin-bottom: 0.5mm;
    }}
    .sobra-compact {{
      font-size: {font_cue};
      color: #666;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 3px;
      padding: 1.2mm 2.2mm;
      margin-top: 1.2mm;
      line-height: 1.25;
    }}

    /* ==============================================================
       ESTILOS DE RECETAS: EDICIÓN CELULAR (1 POR PÁGINA EXPANDIDA)
       ============================================================== */
    .recipe-page-mobile {{
      page-break-after: always;
      break-after: page;
      height: 100%;
      min-height: 275mm;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      box-sizing: border-box;
    }}
    .mobile-header {{
      border-bottom: 2px solid var(--border-soft);
      padding-bottom: 1.5mm;
      margin-bottom: 2mm;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .mobile-title {{
      font-family: 'Fraunces', serif;
      font-size: {font_recipe_title};
      color: var(--text-dark);
      margin: 0;
      line-height: 1.15;
    }}
    .mobile-sub {{
      font-size: {font_recipe_sub};
      color: var(--text-muted);
      margin-top: 0.5mm;
    }}
    .mobile-img-box {{
      width: 100%;
      height: {img_height};
      margin: 0 auto 2.5mm;
      border-radius: 6px;
      overflow: hidden;
      border: 1px solid var(--border-soft);
      background: #faf8f5;
      display: flex;
      justify-content: center;
      align-items: center;
    }}
    .mobile-img-box img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }}
    .mobile-grid {{
      display: grid;
      grid-template-columns: 0.85fr 1.15fr;
      gap: 4mm;
      flex-grow: 1;
    }}
    .mobile-col-title {{
      font-size: {font_col_title};
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--accent-sage);
      margin-bottom: 1.2mm;
      border-bottom: 1.5px solid #f0e6da;
      padding-bottom: 0.6mm;
    }}
    .mobile-ings {{
      list-style: none;
      padding: 0;
      margin: 0;
      font-size: {font_recipe_body};
      line-height: {line_height_body};
    }}
    .mobile-ings li {{
      padding: 0.55mm 0;
      border-bottom: 1px dotted #f0e6da;
      display: flex;
      justify-content: space-between;
    }}
    .mobile-ings strong {{
      color: var(--accent-terracotta);
    }}
    .mobile-steps {{
      padding-left: 4.5mm;
      margin: 0 0 1.5mm 0;
      font-size: {font_recipe_body};
      line-height: {line_height_body};
    }}
    .mobile-steps li {{
      margin-bottom: 1.2mm;
    }}
    .cue-mobile {{
      font-size: {font_cue};
      line-height: 1.28;
      padding: 1.2mm 2.2mm;
      border-radius: 4px;
      margin-top: 1.2mm;
      border-left: 3px solid #ccc;
    }}
    .variants-mobile {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2mm;
      margin-top: 1.4mm;
      font-size: {font_cue};
      line-height: 1.25;
      background: #faf8f5;
      padding: 1.5mm 2.2mm;
      border-radius: 4px;
      border: 1px solid #f0e6da;
    }}
    .variants-mobile strong {{
      display: block;
      color: var(--accent-terracotta);
      font-size: {font_cue};
      margin-bottom: 0.4mm;
    }}

    /* ==============================================================
       LISTAS DE COMPRAS: 3 COLUMNAS SIN DESBORDE NI TÍTULOS HUÉRFANOS
       ============================================================== */
    .shop-3cols {{
      display: grid;
      grid-template-columns: 1.15fr 0.95fr 0.9fr;
      gap: 4.5mm;
      margin-top: 3mm;
      align-items: start;
    }}
    .shop-sec-card {{
      background: #ffffff;
      border: 1px solid var(--border-soft);
      border-radius: 5px;
      padding: 2mm 2.8mm;
      margin-bottom: 2.8mm;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .shop-sec-card h4 {{
      font-size: 7.5pt;
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: var(--accent-sage);
      border-bottom: 1.5px solid var(--border-soft);
      padding-bottom: 0.8mm;
      margin: 0 0 1.2mm 0;
    }}
    .shop-item-row {{
      font-size: 7pt;
      padding: 0.4mm 0;
      display: flex;
      gap: 1.5mm;
      line-height: 1.25;
      align-items: flex-start;
    }}
    .check-box-pdf {{
      display: inline-block;
      width: 8px;
      height: 8px;
      border: 1px solid #777;
      border-radius: 2px;
      margin-top: 1.5px;
      flex-shrink: 0;
    }}
    .alacena-pdf {{
      background: #fdfaf5;
      border: 1px solid #eedec8;
      border-left: 3px solid var(--accent-mustard);
      border-radius: 4px;
      padding: 2mm 3mm;
      margin-top: 2.5mm;
      font-size: 7.2pt;
      color: #6b4e23;
    }}
  </style>
</head>
<body>

  <!-- 1. PORTADA -->
  <section class="page-break" style="display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center; background: #FFFBF7;">
    <div style="margin-top: 10mm;">
      <span style="font-size: 8.5pt; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase; color: var(--accent-terracotta);">Método de Cocina Cotidiana</span>
      <h1 style="font-size: 26pt; margin: 3mm 0 2mm; color: var(--text-dark); line-height: 1.1;">30 días sin preguntarte<br>qué cocinar</h1>
      <p style="font-size: 11pt; color: var(--text-muted); font-style: italic; max-width: 140mm; margin: 0 auto;">Un sistema real, flexible y sin culpa para resolver la comida familiar de todos los días</p>
    </div>

    <div style="width: 210px; height: 210px; margin: 8mm auto; border-radius: 50%; overflow: hidden; border: 4px solid #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.06); background: #FAF7F2; display: flex; align-items: center; justify-content: center;">
      <img src="{portada_img}" style="width: 100%; height: 100%; object-fit: cover;" alt="Portada">
    </div>

    <div style="margin-bottom: 8mm;">
      <p style="font-size: 9pt; font-weight: 700; color: var(--accent-sage); margin-bottom: 1mm;">32 Platos Principales · 13 Opciones de Extras · 6 Plantillas Imprimibles</p>
      <p style="font-size: 7.5pt; color: #888;">Edición 2026 · Saso Digital · Argentina</p>
    </div>
  </section>

  <!-- 2. ÍNDICE Y FILOSOFÍA -->
  <section class="page-break">
    <h2 class="section-title">Antes de empezar</h2>
    <p class="section-desc">Un sistema simple para recuperar tranquilidad en la cocina doméstica</p>

    <!-- Punto 9: Sección Quién hizo esta guía sin repetición simple... simples -->
    <div class="editorial-box" style="background:#fffcf8; border-left: 3px solid var(--accent-terracotta); padding: 3mm 4mm; margin-bottom: 3mm;">
      <h4 style="font-family: 'Fraunces', serif; color: var(--accent-terracotta); margin: 0 0 1mm 0; font-size: 9.5pt;">Quién hizo esta guía</h4>
      <p style="font-size: 8pt; color: #444; line-height: 1.45; margin: 0;">{ed.get("quien_hizo_esta_guia", {}).get("texto", "")}</p>
    </div>

    <div class="editorial-box">
      {"".join(f"<p>{p}</p>" for p in ed.get("introduccion", {}).get("antes_de_empezar", {}).get("parrafos", []))}
      
      <!-- Principios limpios sin fruta de estación -->
      <div class="highlight-card">
        <strong>Principios para no abandonar:</strong>
        <ul>
          {"".join(f"<li>{c}</li>" for c in ed.get("introduccion", {}).get("antes_de_empezar", {}).get("claves", []))}
        </ul>
      </div>

      <!-- Punto 8: Fruta de estación como nota destacada aparte debajo -->
      <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-left:3.5px solid #22c55e; border-radius:4px; padding:2mm 3.5mm; margin-top:2.5mm; font-size:7.5pt; color:#166534;">
        🍎 <strong>Fruta de estación:</strong> 1 por persona por día, como postre o colación fresca.
      </div>
    </div>

    <div class="editorial-box">
      <h3>Cómo usar esta guía según tu tiempo</h3>
      <p>{ed.get("introduccion", {}).get("como_usar_guia", {}).get("descripcion", "")}</p>
      <div class="grid-3col">
        {"".join(f'''
        <div class="mini-card">
          <h4>⏱️ {n["tiempo"]}</h4>
          <p>{n["accion"]}</p>
        </div>
        ''' for n in ed.get("introduccion", {}).get("como_usar_guia", {}).get("niveles", []))}
      </div>
    </div>
  </section>

  <!-- 3. EL MÉTODO & LA FÓRMULA DEL PLATO -->
  <section class="page-break">
    <h2 class="section-title">El Método de los 15 Minutos</h2>
    <p class="section-desc">Planificación semanal ágil: 6 pasos para organizar la cocina familiar</p>

    <div class="grid-2col">
      {"".join(f'''
      <div class="mini-card" style="padding: 2mm 3mm;">
        <h4>Paso {p["paso"]} · {p["titulo"]}</h4>
        <p style="font-size: 7.5pt; color: #555;">{p["detalle"]}</p>
      </div>
      ''' for p in ed.get("metodo", {}).get("los_15_minutos", {}).get("pasos", []))}
    </div>

    <div class="editorial-box" style="margin-top: 3mm;">
      <h3>La fórmula de un plato práctico y balanceado</h3>
      <p>{ed.get("metodo", {}).get("formula_plato", {}).get("bajada", "")}</p>
      <div class="grid-3col">
        {"".join(f'''
        <div class="mini-card" style="text-align: center;">
          <h4 style="color: var(--accent-sage);">{c["nombre"]}</h4>
          <p style="font-size: 7.2pt;">{c["rol"]}</p>
        </div>
        ''' for c in ed.get("metodo", {}).get("formula_plato", {}).get("componentes", []))}
      </div>
    </div>

    <div class="editorial-box">
      <h3>Criterios inteligentes antes de ir al súper</h3>
      <ul style="padding-left: 4mm; font-size: 8pt;">
        {"".join(f"<li style='margin-bottom:1mm;'>{c}</li>" for c in ed.get("metodo", {}).get("compras_estrategicas", {}).get("consejos", []))}
      </ul>
    </div>
  </section>

  <!-- 4. SEGURIDAD BROMATOLÓGICA Y EMERGENCIAS -->
  <section class="page-break">
    <h2 class="section-title">Conservación Segura & Comidas de Emergencia</h2>
    <p class="section-desc">Pautas sanitarias para cocinar de más con total tranquilidad</p>

    <div class="editorial-box">
      <h3>Pautas generales de seguridad alimentaria</h3>
      <div class="grid-2col">
        {"".join(f'''
        <div class="mini-card" style="background:#fcfcfc;">
          <h4 style="font-size: 8pt; color: var(--accent-sage);">🛡️ {pt["titulo"]}</h4>
          <p style="font-size: 7.2pt; color: #333;">{pt["texto"]}</p>
        </div>
        ''' for pt in ed.get("metodo", {}).get("conservacion_segura", {}).get("puntos", []))}
      </div>
    </div>

    <div class="editorial-box">
      <h3>Comidas de emergencia: Planes A, B y C</h3>
      <div class="grid-3col">
        {"".join(f'''
        <div class="mini-card">
          <h4>{p["plan"]}</h4>
          <p style="font-size: 7.2pt;">{p["detalle"]}</p>
        </div>
        ''' for p in ed.get("estrategias", {}).get("comidas_emergencia", {}).get("planes", []))}
      </div>
    </div>

    <!-- Punto 4: Una base, tres comidas diferentes (lunes, martes y miércoles) -->
    <div class="editorial-box">
      <h3>Una base, tres comidas diferentes</h3>
      <ul style="padding-left: 4mm; font-size: 7.5pt;">
        {"".join(f"<li style='margin-bottom:0.8mm;'>{p}</li>" for p in ed.get("estrategias", {}).get("aprovechamiento", {}).get("pautas", []))}
      </ul>
    </div>

    <div class="editorial-box" style="border-left: 3px solid #eab308; background: #fefce8; padding: 2mm 3mm; margin-top: 2mm;">
      <h4 style="font-family: 'Fraunces', serif; color: #854d0e; font-size: 8.5pt; margin: 0 0 1mm 0;">🧂 {ed.get("pauta_sodio", {}).get("titulo", "Atención al sodio")}</h4>
      <p style="font-size: 7.2pt; color: #713f12; line-height: 1.35; margin: 0;">{ed.get("pauta_sodio", {}).get("texto", "")}</p>
    </div>
  </section>

  <!-- 4B. CÓMO AJUSTAR LAS PORCIONES -->
  <section class="page-break">
    <h2 class="section-title">{ed.get("porciones", {}).get("titulo", "Cómo ajustar las porciones")}</h2>
    <p class="section-desc">{ed.get("porciones", {}).get("bajada", "")}</p>

    <div class="editorial-box" style="margin-top: 2.5mm;">
      <h3 style="margin-bottom: 1.5mm;">Tabla de equivalencias según los integrantes</h3>
      <table class="cal-table" style="margin-top: 1mm;">
        <thead>
          <tr>
            <th style="width: 22%;">Personas</th>
            <th style="width: 20%;">Factor</th>
            <th style="width: 22%;">Carne / Pollo</th>
            <th style="width: 18%;">Arroz seco</th>
            <th style="width: 18%;">Pasta seca</th>
          </tr>
        </thead>
        <tbody>
          {"".join(f"""
          <tr>
            <td><strong>{row['personas']}</strong></td>
            <td>{row['factor']}</td>
            <td>{row['ejemplo_carne']}</td>
            <td>{row.get('arroz_seco', '-')}</td>
            <td>{row.get('pasta_seca', '-')}</td>
          </tr>
          """ for row in ed.get("porciones", {}).get("tabla_factores", []))}
        </tbody>
      </table>
    </div>

    <div class="grid-2col" style="margin-top: 2.5mm;">
      <div class="editorial-box" style="margin-bottom: 0;">
        <h3 style="color: var(--accent-terracotta); font-size: 9.5pt;">Porciones de referencia para chicos</h3>
        {"".join(f"""
        <div class="mini-card" style="margin-bottom: 1.8mm;">
          <strong style="color: var(--accent-sage); font-size: 7.5pt;">👶 {r['rango']}</strong>
          <p style="font-size: 7pt; color: #444; margin-top: 0.5mm;">{r['porcion']}</p>
        </div>
        """ for r in ed.get("porciones", {}).get("referencia_edades", []))}
      </div>

      <div class="editorial-box" style="margin-bottom: 0;">
        <h3 style="font-size: 9.5pt;">Pautas clave al cambiar cantidades</h3>
        {"".join(f"""
        <div style="margin-bottom: 1.8mm;">
          <strong style="font-size: 7.2pt; color: var(--accent-terracotta);">• {p['titulo']}:</strong>
          <span style="font-size: 7pt; color: #444;"> {p['texto']}</span>
        </div>
        """ for p in ed.get("porciones", {}).get("pautas_clave", []))}
      </div>
    </div>

    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 2mm 3mm; margin-top: 2.5mm; font-size: 7pt; color: #555;">
      ℹ️ <strong>Aclaración:</strong> {ed.get("porciones", {}).get("aclaracion", "")}
    </div>
  </section>

  <!-- 4C. SEGURIDAD CON CHICOS & COMER EN PAZ -->
  <section class="page-break">
    <h2 class="section-title">Seguridad con Chicos & Comer en Paz</h2>
    <p class="section-desc">Pautas de seguridad alimentaria infantil y estrategias cotidianas sin peleas</p>

    <div class="grid-2col" style="margin-top: 2.5mm;">
      <div class="editorial-box">
        <h3 style="color: #dc2626; font-size: 9.5pt;">🛡️ Prevención de atragantamiento</h3>
        {"".join(f"""
        <div class="mini-card" style="margin-bottom: 1.6mm;">
          <strong style="color: #991b1b; font-size: 7.2pt;">{al['alimento']}</strong>
          <p style="font-size: 6.8pt; color: #444; margin-top: 0.5mm;">{al['adaptacion']}</p>
        </div>
        """ for al in ed.get("seguridad_infantil", {}).get("alimentos_riesgo", []))}

        <div style="background: #fef2f2; border-left: 3px solid #ef4444; padding: 1.5mm 2.2mm; border-radius: 4px; margin-top: 2mm;">
          <strong style="font-size: 7.2pt; color: #991b1b;">🍯 {ed.get("seguridad_infantil", {}).get("regla_miel", {}).get("titulo", "")}</strong>
          <p style="font-size: 6.8pt; color: #7f1d1d; margin: 0.5mm 0 0 0;">{ed.get("seguridad_infantil", {}).get("regla_miel", {}).get("texto", "")}</p>
        </div>
      </div>

      <div class="editorial-box">
        <h3 style="color: var(--accent-sage); font-size: 9.5pt;">🌱 Consejos para chicos selectivos</h3>
        {"".join(f"""
        <div style="margin-bottom: 1.6mm; padding-bottom: 1mm; border-bottom: 1px dashed #e2e8f0;">
          <strong style="font-size: 7.2pt; color: var(--accent-terracotta);">{c['numero']}. {c['titulo']}:</strong>
          <span style="font-size: 6.8pt; color: #444;"> {c['texto']}</span>
        </div>
        """ for c in ed.get("con_chicos_en_casa", {}).get("consejos", []))}
      </div>
    </div>

    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 1.8mm 2.5mm; margin-top: 1mm; font-size: 6.8pt; color: #666; text-align: center;">
      {ed.get("seguridad_infantil", {}).get("aclaracion", "")}
    </div>
  </section>

  <!-- 4D. SEMANA TIPO DE EXTRAS & PACK DE IMPRIMIBLES -->
  <section class="page-break">
    <h2 class="section-title">Semana Tipo de Extras & Pack de Imprimibles</h2>
    <p class="section-desc">Rotación de desayunos, meriendas y viandas + tus seis plantillas descargables</p>

    <div class="editorial-box" style="margin-top: 2mm;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5mm;">
        <h3 style="margin:0; color:var(--accent-terracotta); font-size:10pt;">Ciclo de 3 Días (A, B, C) · Desayunos, Colaciones y Viandas</h3>
        <span style="background:#eef6ee; color:#166534; font-size:6.8pt; font-weight:bold; padding:1.5px 6px; border-radius:4px; border:1px solid #bbf7d0;">Esquema Flexible</span>
      </div>
      <p style="font-size:7.2pt; color:#555; margin-bottom:2mm;">Un sistema simple de rotación para resolver desayunos, colaciones escolares y viandas sin aburrirse ni improvisar.</p>

      <table class="cal-table" style="font-size:7.2pt;">
        <thead>
          <tr>
            <th style="width: 14%;">Ciclo</th>
            <th style="width: 28%;">☀️ Desayuno / Merienda</th>
            <th style="width: 26%;">🍎 Colación escolar</th>
            <th style="width: 32%;">💼 Vianda para llevar</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong style="color:var(--accent-terracotta); font-size:8pt;">Día A</strong></td>
            <td>Tostadas con queso untable, tomate y orégano</td>
            <td>Palitos de verdura con hummus o queso untable</td>
            <td>Vianda: pan árabe relleno de queso, hojas verdes y zanahoria</td>
          </tr>
          <tr>
            <td><strong style="color:var(--accent-terracotta); font-size:8pt;">Día B</strong></td>
            <td>Avena de la noche con yogur y fruta</td>
            <td>Bolitas de avena, banana y cacao</td>
            <td>Vianda: bowl de pollo, arroz y choclo <small style="display:block; color:#92400e;">(usá la base cocida de los días marcados, p. {base_pollo_pag}; si no tenés, reemplazá por la vianda de lentejas)</small></td>
          </tr>
          <tr>
            <td><strong style="color:var(--accent-terracotta); font-size:8pt;">Día C</strong></td>
            <td>Panqueques de banana y avena</td>
            <td>Licuado de banana, leche y avena</td>
            <td>Vianda: ensalada de lentejas, zanahoria, queso y tomate</td>
          </tr>
          <tr style="background:#fdfaf6; border-top:1.5px solid var(--border-soft);">
            <td><strong style="color:var(--accent-sage); font-size:7.8pt;">🍨 Postres</strong></td>
            <td colspan="3">
              <strong>Regla semanal:</strong> Fruta fresca de estación 4 o 5 días por semana. Postre dulce casero 2 o 3 veces por semana (helado de banana en 5 min, manzanas asadas con canela, postre de chocolate sin huevo o crumble de manzana y avena).
            </td>
          </tr>
        </tbody>
      </table>

      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:3px solid var(--accent-sage); border-radius:4px; padding:1.8mm 3mm; margin-top:2mm; font-size:7pt; color:#475569;">
        💡 <strong>Cómo implementarlo:</strong> Repetí el ciclo durante la semana o mezclá libremente cualquier opción de cada columna.
      </div>
    </div>

    <div class="editorial-box" style="margin-top: 2.5mm;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin-bottom: 1.2mm; color: var(--accent-terracotta);">📥 Cómo usar tu Pack de 6 Imprimibles A4</h3>
        <span style="background: #fdf2f8; color: #9d174d; font-size: 6.5pt; font-weight: bold; padding: 1px 5px; border-radius: 3px; border: 1px solid #fbcfe8;">PDF Independiente Incluido</span>
      </div>
      <p style="font-size: 7.2pt; color: #555; margin-bottom: 1.5mm;">{ed.get("como_usar_imprimibles", {}).get("bajada", "")}</p>
      
      <div class="grid-3col">
        {"".join(f"""
        <div class="mini-card" style="padding: 1.6mm 2.2mm;">
          <strong style="font-size: 7pt; color: var(--accent-sage);">{h['nombre']}</strong>
          <p style="font-size: 6.5pt; color: #444; margin: 0.5mm 0 0 0;">{h['uso']}</p>
        </div>
        """ for h in ed.get("como_usar_imprimibles", {}).get("herramientas", []))}
      </div>
    </div>
  </section>

  <!-- 5. CALENDARIO MENSUAL (DÍAS 1 A 15) -->
  <section class="page-break">
    <h2 class="section-title">Calendario Mensual · Días 1 a 15</h2>
    <p class="section-desc">Planificación de almuerzo y cena con rotación equilibrada de proteínas. 💡 Para desayunos y viandas consultá la <strong>Semana Tipo de Extras</strong>.</p>

    <table class="cal-table">
      <thead>
        <tr>
          <th style="width: 14%;">Día</th>
          <th style="width: 43%;">☀️ Almuerzo</th>
          <th style="width: 43%;">🌙 Cena</th>
        </tr>
      </thead>
      <tbody>
  """

    for dia_idx in range(1, 16):
        d_info = cal["dias"][dia_idx - 1]
        dia_num = d_info["dia"]
        nombre_d = motor.nombre_dia(dia_num).capitalize()
        
        # Punto 1: Reemplazo exacto de sobras sin dejar jamás "None"
        if (dia_num, "almuerzo") in SOBRAS_TEXTOS:
            alm_txt = SOBRAS_TEXTOS[(dia_num, "almuerzo")]
        elif d_info["almuerzo"].get("receta"):
            alm_r = recetas.get(d_info["almuerzo"]["receta"])
            alm_txt = alm_r["nombre"] if alm_r else d_info["almuerzo"]["receta"]
        else:
            alm_txt = "Comida familiar planificada"

        if (dia_num, "cena") in SOBRAS_TEXTOS:
            cena_txt = SOBRAS_TEXTOS[(dia_num, "cena")]
        elif d_info["cena"].get("receta"):
            cena_r = recetas.get(d_info["cena"]["receta"])
            cena_txt = cena_r["nombre"] if cena_r else d_info["cena"]["receta"]
        else:
            cena_txt = "Cena familiar planificada"

        # Punto 1: Etiqueta ampliada x8 porciones (cocinar doble)
        alm_tag = f'<span class="badge-batch">x8 porciones (cocinar doble)</span>' if d_info["almuerzo"].get("porciones", 4) > 4 else ""
        cena_tag = f'<span class="badge-batch">x8 porciones (cocinar doble)</span>' if d_info["cena"].get("porciones", 4) > 4 else ""

        batch_txt = f'<br><span class="badge-batch">{d_info["nota_batch"]}</span>' if d_info.get("nota_batch") else ""

        html += f"""
        <tr>
          <td><span class="cal-day-num">Día {dia_num}</span><br><small>{nombre_d}</small>{batch_txt}</td>
          <td>{alm_txt} {alm_tag}</td>
          <td>{cena_txt} {cena_tag}</td>
        </tr>
        """

    html += """
      </tbody>
    </table>
  </section>

  <!-- 6. CALENDARIO MENSUAL (DÍAS 16 A 30) -->
  <section class="page-break">
    <h2 class="section-title">Calendario Mensual · Días 16 a 30</h2>
    <p class="section-desc">Continuación del menú mensual. Recordá que podés intercambiar días enteros o platos según tus horarios.</p>

    <table class="cal-table">
      <thead>
        <tr>
          <th style="width: 14%;">Día</th>
          <th style="width: 43%;">☀️ Almuerzo</th>
          <th style="width: 43%;">🌙 Cena</th>
        </tr>
      </thead>
      <tbody>
  """

    for dia_idx in range(16, 31):
        d_info = cal["dias"][dia_idx - 1]
        dia_num = d_info["dia"]
        nombre_d = motor.nombre_dia(dia_num).capitalize()
        
        # Punto 1: Reemplazo exacto de sobras sin dejar jamás "None"
        if (dia_num, "almuerzo") in SOBRAS_TEXTOS:
            alm_txt = SOBRAS_TEXTOS[(dia_num, "almuerzo")]
        elif d_info["almuerzo"].get("receta"):
            alm_r = recetas.get(d_info["almuerzo"]["receta"])
            alm_txt = alm_r["nombre"] if alm_r else d_info["almuerzo"]["receta"]
        else:
            alm_txt = "Comida familiar planificada"

        if (dia_num, "cena") in SOBRAS_TEXTOS:
            cena_txt = SOBRAS_TEXTOS[(dia_num, "cena")]
        elif d_info["cena"].get("receta"):
            cena_r = recetas.get(d_info["cena"]["receta"])
            cena_txt = cena_r["nombre"] if cena_r else d_info["cena"]["receta"]
        else:
            cena_txt = "Cena familiar planificada"

        # Punto 1: Etiqueta ampliada x8 porciones (cocinar doble)
        alm_tag = f'<span class="badge-batch">x8 porciones (cocinar doble)</span>' if d_info["almuerzo"].get("porciones", 4) > 4 else ""
        cena_tag = f'<span class="badge-batch">x8 porciones (cocinar doble)</span>' if d_info["cena"].get("porciones", 4) > 4 else ""

        batch_txt = f'<br><span class="badge-batch">{d_info["nota_batch"]}</span>' if d_info.get("nota_batch") else ""

        html += f"""
        <tr>
          <td><span class="cal-day-num">Día {dia_num}</span><br><small>{nombre_d}</small>{batch_txt}</td>
          <td>{alm_txt} {alm_tag}</td>
          <td>{cena_txt} {cena_tag}</td>
        </tr>
        """

    html += """
      </tbody>
    </table>
  </section>

  <!-- 7. SECCIÓN RECETARIO -->
"""

    if edicion == "completa":
        # EDICIÓN COMPLETA: 2 RECETAS POR PÁGINA (A4 IMPRESIÓN CON TIPOGRAFÍA ≥ 9pt)
        for idx in range(0, len(recetas_a_incluir), 2):
            par = recetas_a_incluir[idx:idx+2]
            html += f"""
            <section class="recipe-double-page page-break">
            """
            for r in par:
                img_file = img_dir / f"{r['id']}.png"
                img_tag = f'<img src="{img_file}" class="card-half-img" alt="{r["nombre"]}">' if img_file.exists() else ""
                
                # Referencia automática a la página real de la Base de Pollo Cocido
                ing_items = "".join(f"<li><span>{i['item'].replace('(usá la Base de pollo cocido, p. 57)', f'(Base pollo p. {base_pollo_pag})').replace('(Base pollo p. 55)', f'(Base pollo p. {base_pollo_pag})')}</span> <strong>{motor.cantidad_legible(i['cantidad'], i['unidad'])}</strong></li>" for i in r["ingredientes"])
                pasos_items = "".join(f"<li>{p.replace('p. 57', f'p. {base_pollo_pag}').replace('p. 55', f'p. {base_pollo_pag}')}</li>" for p in r["pasos"])

                # Badge especial si es la Receta Base
                badge_base = '<span class="badge-batch" style="background:#eef6ee; color:#166534; border-color:#bbf7d0; font-size:6.8pt; margin-left:2mm;">RECETA BASE · BATCH COOKING</span>' if r.get("id") == "base-pollo-cocido" else ""
                
                # Rendimiento especial para la base de pollo (Punto 5)
                rinde_box = f'<div class="cue-compact cue-brown" style="margin-top:1.2mm; font-weight:600;">⚖️ <strong>Rendimiento:</strong> {r["rinde"]}</div>' if r.get("rinde") else ""

                senales = f'<div class="cue-compact cue-brown"><strong>👀 Señal:</strong> {r["senales_coccion"]}</div>' if r.get("senales_coccion") else ""
                acomp_verde = f'<div class="cue-compact cue-green">🥗 {r["acompanamiento_verde"]}</div>' if r.get("acompanamiento_verde") else ""
                nota_seg = f'<div class="cue-compact cue-orange">🐟 <strong>Nota:</strong> {r["nota_seguridad"]}</div>' if r.get("nota_seguridad") else ""
                
                chicos = f'<div><strong>👶 Chicos:</strong> {r["version_chicos"]}</div>' if r.get("version_chicos") else ""
                adultos = f'<div><strong>🌶️ Adultos:</strong> {r["variante_adultos"]}</div>' if r.get("variante_adultos") else ""
                variants_html = f'<div class="variants-compact">{chicos}{adultos}</div>' if (chicos or adultos) else ""
                
                sobra = f'<div class="sobra-compact">🧊 <strong>Conservación:</strong> {r["si_te_sobra"]}</div>' if r.get("si_te_sobra") else ""
                calorias = f'<span class="pill-pdf cal">~{r["nutricion"]["kcal"]} kcal (adulto)</span>' if r.get("nutricion") else ""
                tiempo_pill = f'<span class="pill-pdf time">⏱️ {r["tiempo_total"]}m ({r["tiempo_activo"]}m act.)</span>'

                html += f"""
                <div class="recipe-card-half">
                  <div>
                    <div class="card-half-header">
                      <div>
                        <h3 class="card-half-title">{r['nombre']}{badge_base}</h3>
                        <div class="card-half-sub">Proteína: {r['proteina']} · Dificultad: {r['dificultad']}</div>
                      </div>
                      <div class="card-half-pills">
                        {tiempo_pill}
                        {calorias}
                      </div>
                    </div>

                    <div class="card-half-grid">
                      <div class="card-half-left">
                        {img_tag}
                        <div>
                          <div class="card-half-col-title">Ingredientes (4 porciones)</div>
                          <ul class="card-half-ings">
                            {ing_items}
                          </ul>
                        </div>
                      </div>

                      <div>
                        <div class="card-half-col-title">Preparación</div>
                        <ol class="card-half-steps">
                          {pasos_items}
                        </ol>
                        {rinde_box}
                        {senales}
                        {variants_html}
                        {nota_seg}
                        {acomp_verde}
                      </div>
                    </div>
                  </div>
                  {sobra}
                </div>
                """
            html += "</section>"

    else:
        # EDICIÓN CELULAR: 1 RECETA POR PÁGINA (EXPANDIDA, LETRA GRANDE E ILUSTRACIONES DE 60MM)
        for r in recetas_a_incluir:
            img_file = img_dir / f"{r['id']}.png"
            img_box = ""
            if img_file.exists():
                img_box = f'''
                <div class="mobile-img-box">
                  <img src="{img_file}" alt="{r["nombre"]}">
                </div>'''

            ing_items = "".join(f"<li><span>{i['item'].replace('(usá la Base de pollo cocido, p. 57)', f'(Base pollo p. {base_pollo_pag})').replace('(Base pollo p. 55)', f'(Base pollo p. {base_pollo_pag})')}</span> <strong>{motor.cantidad_legible(i['cantidad'], i['unidad'])}</strong></li>" for i in r["ingredientes"])
            pasos_items = "".join(f"<li>{p.replace('p. 57', f'p. {base_pollo_pag}').replace('p. 55', f'p. {base_pollo_pag}')}</li>" for p in r["pasos"])

            badge_base = '<span class="badge-batch" style="background:#eef6ee; color:#166534; border-color:#bbf7d0; font-size:7.5pt; margin-left:2mm;">RECETA BASE · BATCH COOKING</span>' if r.get("id") == "base-pollo-cocido" else ""
            rinde_box = f'<div class="cue-mobile" style="background:#faf4ed; border-color:#d97706; color:#78350f; font-weight:600;">⚖️ <strong>Rendimiento:</strong> {r["rinde"]}</div>' if r.get("rinde") else ""

            senales = f'<div class="cue-mobile" style="background:#faf4ed; border-color:#d97706; color:#78350f;"><strong>👀 Señal de cocción:</strong> {r["senales_coccion"]}</div>' if r.get("senales_coccion") else ""
            acomp_verde = f'<div class="cue-mobile" style="background:#f0fdf4; border-color:#22c55e; color:#166534;">🥗 {r["acompanamiento_verde"]}</div>' if r.get("acompanamiento_verde") else ""
            nota_seg = f'<div class="cue-mobile" style="background:#fff7ed; border-color:#f97316; color:#9a3412;">🐟 <strong>Nota:</strong> {r["nota_seguridad"]}</div>' if r.get("nota_seguridad") else ""
            
            chicos = f'<div><strong>👶 Versión chicos:</strong> {r["version_chicos"]}</div>' if r.get("version_chicos") else ""
            adultos = f'<div><strong>🌶️ Variante adultos:</strong> {r["variante_adultos"]}</div>' if r.get("variante_adultos") else ""
            variants_html = f'<div class="variants-mobile">{chicos}{adultos}</div>' if (chicos or adultos) else ""
            
            sobra = f'<div class="cue-mobile" style="background:#f8fafc; border-color:#cbd5e1; color:#475569; margin-top:2mm;">🧊 <strong>Conservación:</strong> {r["si_te_sobra"]}</div>' if r.get("si_te_sobra") else ""
            
            calorias = f'<span class="pill-pdf cal">~{r["nutricion"]["kcal"]} kcal (porción adulto)</span>' if r.get("nutricion") else ""
            tiempo_pill = f'<span class="pill-pdf time">⏱️ {r["tiempo_total"]} min ({r["tiempo_activo"]} activos)</span>'

            html += f"""
            <section class="recipe-page-mobile page-break">
              <div>
                <div class="mobile-header">
                  <div>
                    <h3 class="mobile-title">{r['nombre']}{badge_base}</h3>
                    <div class="mobile-sub">Proteína: {r['proteina']} · Dificultad: {r['dificultad']}</div>
                  </div>
                  <div class="card-half-pills">
                    {tiempo_pill}
                    {calorias}
                  </div>
                </div>

                {img_box}

                <div class="mobile-grid">
                  <div>
                    <div class="mobile-col-title">Ingredientes (4 porciones)</div>
                    <ul class="mobile-ings">
                      {ing_items}
                    </ul>
                    {sobra}
                  </div>

                  <div>
                    <div class="mobile-col-title">Preparación</div>
                    <ol class="mobile-steps">
                      {pasos_items}
                    </ol>
                    {rinde_box}
                    {senales}
                    {variants_html}
                    {acomp_verde}
                    {nota_seg}
                  </div>
                </div>
              </div>
            </section>
            """

    # 8. LISTAS DE COMPRAS SEMANALES (1 PÁGINA POR SEMANA, 3 COLUMNAS SIN DESBORDE)
    for s in semanas_info:
        col1_sectores = []
        col2_sectores = []
        col3_sectores = []

        for sec_nom, items in s["sectores"]:
            if sec_nom == "verduras y frutas":
                col1_sectores.append((sec_nom, items))
            elif sec_nom in ["carnes y huevos", "lácteos", "panificados"]:
                col2_sectores.append((sec_nom, items))
            else: # almacén, freezer, otros
                col3_sectores.append((sec_nom, items))

        def render_col(sectores_list):
            out = ""
            for sector, items in sectores_list:
                out += f"""
                <div class="shop-sec-card">
                  <h4>{sector}</h4>
                """
                for it in items:
                    det = f" <small style='color:#777;'>({it['detalle']})</small>" if it.get("detalle") else ""
                    out += f"""
                    <div class="shop-item-row">
                      <span class="check-box-pdf"></span>
                      <span><strong>{it['item']}</strong>: {it['texto']}{det}</span>
                    </div>
                    """
                out += "</div>"
            return out

        alacena_str = ", ".join(s["alacena"]) if s["alacena"] else ""
        alacena_box = f'<div class="alacena-pdf"><strong>🧂 Revisá en tu alacena:</strong> {alacena_str}</div>' if alacena_str else ""

        html += f"""
        <section class="page-break">
          <h2 class="section-title">Lista de Compras · Días {s['desde']} a {s['hasta']}</h2>
          <p class="section-desc">Cantidades calculadas exactamente según el menú, organizadas por sector de góndola</p>

          <div class="shop-3cols">
            <div>{render_col(col1_sectores)}</div>
            <div>{render_col(col2_sectores)}</div>
            <div>{render_col(col3_sectores)}</div>
          </div>
          {alacena_box}
        </section>
        """

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
            # Limpiar nombre del ingrediente para que en la lista no aparezca (p. 57)
            item_clean = ing['item'].replace('(usá la Base de pollo cocido, p. 57)', f'(Base de pollo cocido, p. {base_pollo_pag})')
            k_ex = (ing['sector'], item_clean, ing['unidad'])
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

    # Distribuir extras en 3 columnas
    ex_col1 = [s for s in extras_sectores if s[0] == "verduras y frutas"]
    ex_col2 = [s for s in extras_sectores if s[0] in ["carnes y huevos", "lácteos"]]
    ex_col3 = [s for s in extras_sectores if s[0] in ["almacén", "panificados"]]

    html += f"""
    <section class="page-break">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <h2 class="section-title">Lista de Compras · Extras</h2>
          <p class="section-desc">Ingredientes para resolver la Semana Tipo de Desayunos, Colaciones y Viandas</p>
        </div>
        <span style="background: #eef6ee; color: #166534; font-size: 7.2pt; font-weight: bold; padding: 2px 7px; border-radius: 4px; border: 1px solid #bbf7d0;">Bloque Separado</span>
      </div>

      <div class="shop-3cols">
        <div>{render_col(ex_col1)}</div>
        <div>{render_col(ex_col2)}</div>
        <div>{render_col(ex_col3)}</div>
      </div>
      <div class="alacena-pdf">
        <strong>💡 Consejo de compra:</strong> Estos ingredientes corresponden al esquema rotativo semanal de extras. Sumalos a tu compra semanal solo en los días que decidas preparar colaciones o viandas caseras.
      </div>
    </section>
    """

    # 9. CONTRAPORTADA
    html += f"""
  <section class="page-break" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background: #FFFBF7;">
    <div style="max-width: 130mm;">
      <h2 style="font-size: 22pt; color: var(--accent-terracotta); margin-bottom: 3mm;">Comer rico todos los días no debería ser un examen</h2>
      <p style="font-size: 9.5pt; color: var(--text-muted); line-height: 1.5; margin-bottom: 6mm;">
        Este libro fue pensado para devolverte tiempo y sacarte de la cabeza la pregunta que desgasta a miles de familias todas las noches.
      </p>
      <div style="width: 40mm; height: 1.5px; background: var(--accent-mustard); margin: 0 auto 6mm;"></div>
      <p style="font-size: 8pt; color: #888;">
        Diseñado con amor y practicidad cotidiana en Argentina.<br>
        <strong>Saso Digital · Edición 2026</strong>
      </p>
    </div>
  </section>

</body>
</html>
"""
    return html

def compilar(edicion="completa"):
    html_content = generar_html_pdf(edicion)
    
    if edicion == "celular":
        html_file = SALIDA / "ebook_para_pdf_celular.html"
        pdf_file = SALIDA / "30-dias-sin-preguntarte-que-cocinar_celular.pdf"
        log_file = SALIDA / "chrome_celular.log"
    else:
        html_file = SALIDA / "ebook_para_pdf.html"
        pdf_file = SALIDA / "30-dias-sin-preguntarte-que-cocinar_completo.pdf"
        log_file = SALIDA / "chrome_completa.log"

    html_file.write_text(html_content, encoding="utf-8")
    print(f"HTML [{edicion}] generado en: {html_file}")

    cmd = [
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        f"--print-to-pdf={pdf_file}",
        "--no-pdf-header-footer",
        str(html_file)
    ]

    with open(log_file, "w") as lf:
        subprocess.run(cmd, stdout=lf, stderr=lf, check=True)

    # Actualizar metadatos del PDF
    reader = pypdf.PdfReader(str(pdf_file))
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    metadata = {
        "/Title": "30 días sin preguntarte qué cocinar · Edición 2026",
        "/Author": "Saso Digital",
        "/Subject": "Guía de cocina cotidiana argentina y planificación familiar",
        "/Creator": "Saso Digital",
        "/Producer": "Saso Digital",
    }
    writer.add_metadata(metadata)
    with open(pdf_file, "wb") as f_out:
        writer.write(f_out)

    size_mb = pdf_file.stat().st_size / (1024 * 1024)
    print(f"PDF [{edicion}] generado y metadatos actualizados: {pdf_file} ({size_mb:.2f} MB)")
    return pdf_file

if __name__ == "__main__":
    ed = sys.argv[1] if len(sys.argv) > 1 else "ambas"
    if ed in ("completa", "ambas"):
        compilar("completa")
    if ed in ("celular", "ambas"):
        compilar("celular")
