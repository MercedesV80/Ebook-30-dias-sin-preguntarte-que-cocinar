#!/usr/bin/env python3
"""Compila el ebook completo en PDF editorial de alta fidelidad (formato A4 para venta).
Soporta edición completa comercial (A4 con imágenes optimizadas) y edición liviana para celular.
"""
import json
import math
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import motor

DATOS = RAIZ / "datos"
DISENO = RAIZ / "diseno"
SALIDA = RAIZ / "salida"

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def generar_html_pdf(edicion="completa"):
    config, recetas, cal = motor.cargar()
    
    editorial_path = DATOS / "contenido_editorial.json"
    ed = json.loads(editorial_path.read_text(encoding="utf-8")) if editorial_path.exists() else {}

    # Selección de directorio de imágenes según la edición
    if edicion == "celular":
        img_dir = DISENO / "ilustraciones_mobile"
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

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>{config.get("titulo", "30 días sin preguntarte qué cocinar")} · Edición Impresa</title>
  <style>
    @font-face {{
      font-family: 'Fraunces';
      src: url('{DISENO / "fuentes/Fraunces.ttf"}') format('truetype');
      font-weight: 400 700;
      font-style: normal;
    }}
    @font-face {{
      font-family: 'Fraunces';
      src: url('{DISENO / "fuentes/Fraunces-Italic.ttf"}') format('truetype');
      font-weight: 400 700;
      font-style: italic;
    }}
    @font-face {{
      font-family: 'Nunito Sans';
      src: url('{DISENO / "fuentes/NunitoSans.ttf"}') format('truetype');
      font-weight: 300 800;
      font-style: normal;
    }}

    @page {{
      size: A4 portrait;
      margin: 10mm 12mm 10mm 12mm;
      @bottom-right {{
        content: counter(page);
        font-family: 'Nunito Sans', sans-serif;
        font-size: 7.5pt;
        color: #888;
      }}
    }}

    @page:first {{
      margin: 0;
      @bottom-right {{ content: ""; }}
    }}

    :root {{
      --bg-cream: #faf7f2;
      --bg-card: #ffffff;
      --text-dark: #242726;
      --text-muted: #525755;
      --accent-terracotta: #c85a32;
      --accent-terracotta-light: #fbeee8;
      --accent-sage: #386149;
      --accent-sage-light: #edf4ef;
      --accent-mustard: #c9881e;
      --border-soft: #e2dad0;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}

    body {{
      font-family: 'Nunito Sans', sans-serif;
      color: var(--text-dark);
      background: #ffffff;
      line-height: 1.45;
      font-size: 9pt;
    }}

    .page-break {{
      page-break-after: always;
      break-after: page;
    }}

    .no-break {{
      page-break-inside: avoid;
      break-inside: avoid;
    }}

    /* --- PORTADA --- */
    .portada-page {{
      height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 20mm 18mm;
      background: var(--bg-cream);
      text-align: center;
      box-sizing: border-box;
    }}
    .portada-badge {{
      display: inline-block;
      font-size: 8pt;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      padding: 4px 12px;
      border-radius: 50px;
      background: var(--accent-terracotta-light);
      color: var(--accent-terracotta);
      margin-bottom: 6mm;
    }}
    .portada-title {{
      font-family: 'Fraunces', serif;
      font-size: 30pt;
      font-weight: 700;
      color: var(--text-dark);
      line-height: 1.15;
      margin-bottom: 3mm;
    }}
    .portada-subtitle {{
      font-size: 12pt;
      color: var(--text-muted);
      max-width: 500px;
      margin: 0 auto 6mm;
      line-height: 1.35;
    }}
    .portada-img-wrap {{
      max-width: 360px;
      margin: 0 auto;
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 6px 20px rgba(0,0,0,0.07);
      border: 1px solid var(--border-soft);
    }}
    .portada-img-wrap img {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .portada-footer {{
      margin-top: 6mm;
      font-size: 7.5pt;
      color: #777;
      border-top: 1px solid var(--border-soft);
      padding-top: 3mm;
    }}

    /* --- PÁGINAS EDITORIALES / INTRODUCCIÓN --- */
    .section-title {{
      font-family: 'Fraunces', serif;
      font-size: 18pt;
      color: var(--accent-terracotta);
      border-bottom: 2px solid var(--accent-terracotta-light);
      padding-bottom: 1.5mm;
      margin-bottom: 3mm;
    }}
    .section-desc {{
      font-size: 9.5pt;
      color: var(--text-muted);
      margin-bottom: 4mm;
      font-style: italic;
    }}

    .editorial-box {{
      background: var(--bg-cream);
      border-radius: 8px;
      border: 1px solid var(--border-soft);
      padding: 3.5mm 4.5mm;
      margin-bottom: 3.5mm;
    }}
    .editorial-box h3 {{
      font-family: 'Fraunces', serif;
      font-size: 11pt;
      color: var(--accent-sage);
      margin-bottom: 1.5mm;
    }}
    .editorial-box p {{
      margin-bottom: 1.5mm;
      font-size: 8.5pt;
      line-height: 1.4;
    }}
    .editorial-box p:last-child {{ margin-bottom: 0; }}

    .highlight-card {{
      background: #ffffff;
      border-left: 3px solid var(--accent-terracotta);
      padding: 2.5mm 3.5mm;
      border-radius: 0 6px 6px 0;
      margin: 2.5mm 0;
      font-size: 8pt;
    }}
    .highlight-card ul {{ padding-left: 4mm; }}
    .highlight-card li {{ margin-bottom: 1mm; }}

    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3.5mm;
      margin: 2.5mm 0;
    }}
    .grid-3col {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 2.5mm;
      margin: 2.5mm 0;
    }}

    .mini-card {{
      background: #ffffff;
      border: 1px solid var(--border-soft);
      border-radius: 6px;
      padding: 2.5mm;
      font-size: 8pt;
    }}
    .mini-card h4 {{
      font-family: 'Fraunces', serif;
      font-size: 9pt;
      color: var(--accent-terracotta);
      margin-bottom: 1mm;
    }}

    /* --- CALENDARIO MENSUAL --- */
    .cal-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 2.5mm;
      font-size: 7.5pt;
    }}
    .cal-table th {{
      background: var(--accent-sage);
      color: #ffffff;
      padding: 2mm;
      font-weight: 700;
      text-align: left;
      font-size: 7.5pt;
    }}
    .cal-table td {{
      border: 1px solid var(--border-soft);
      padding: 1.8mm 2.2mm;
      vertical-align: top;
    }}
    .cal-table tr:nth-child(even) {{
      background: #faf9f6;
    }}
    .cal-day-num {{
      font-weight: 800;
      color: var(--accent-terracotta);
    }}
    .cal-tag {{
      display: inline-block;
      font-size: 6.2pt;
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 3px;
      margin-left: 2px;
    }}
    .tag-sobra {{ background: #fef3c7; color: #92400e; }}
    .tag-freezer {{ background: #e0f2fe; color: #075985; }}
    .tag-doble {{ background: #dcfce7; color: #166534; }}
    .tag-batch {{ background: #fef08a; color: #854d0e; }}

    /* --- RECETAS A 2 POR PÁGINA (OPCIÓN A) --- */
    .recipe-double-page {{
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-sizing: border-box;
    }}
    .recipe-card-half {{
      height: 48.8%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      border: 1px solid var(--border-soft);
      border-radius: 7px;
      padding: 2.8mm 3.5mm;
      background: #ffffff;
      box-sizing: border-box;
    }}
    .recipe-card-half.single {{
      height: auto;
      max-height: 85%;
    }}
    .recipe-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 1.5px solid var(--border-soft);
      padding-bottom: 1.2mm;
      margin-bottom: 1.8mm;
    }}
    .recipe-title-pdf {{
      font-family: 'Fraunces', serif;
      font-size: 11pt;
      font-weight: 700;
      color: var(--text-dark);
      line-height: 1.15;
    }}
    .recipe-meta-sub {{
      font-size: 6.8pt;
      color: #666;
      margin-top: 0.5mm;
    }}
    .recipe-pills {{
      display: flex;
      gap: 1.5mm;
      flex-shrink: 0;
      white-space: nowrap;
    }}
    .pill-pdf {{
      font-size: 6.5pt;
      font-weight: 700;
      padding: 1.5px 6px;
      border-radius: 50px;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
    }}
    .pill-pdf.time {{ background: var(--accent-sage-light); color: var(--accent-sage); }}
    .pill-pdf.cal {{ background: var(--accent-terracotta-light); color: var(--accent-terracotta); }}

    .recipe-card-body {{
      display: grid;
      grid-template-columns: 36% 64%;
      gap: 3mm;
      flex-grow: 1;
    }}
    .recipe-left-col {{
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .recipe-thumb-wrap {{
      display: flex;
      align-items: center;
      gap: 2mm;
      margin-bottom: 1mm;
    }}
    .recipe-thumb-img {{
      width: 44px;
      height: 44px;
      border-radius: 5px;
      object-fit: cover;
      border: 1px solid var(--border-soft);
      flex-shrink: 0;
    }}
    .col-title {{
      font-size: 7pt;
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.06em;
      color: var(--accent-sage);
      margin-bottom: 1mm;
      border-bottom: 1px solid var(--border-soft);
      padding-bottom: 0.5mm;
    }}
    .ing-pdf-list {{
      list-style: none;
      font-size: 6.8pt;
      line-height: 1.25;
    }}
    .ing-pdf-list li {{
      padding: 0.5mm 0;
      border-bottom: 1px dotted var(--border-soft);
      display: flex;
      justify-content: space-between;
    }}
    .steps-pdf-list {{
      padding-left: 3.2mm;
      font-size: 6.8pt;
      line-height: 1.28;
      margin-bottom: 1mm;
    }}
    .steps-pdf-list li {{
      margin-bottom: 0.8mm;
    }}
    .cue-pdf {{
      background: var(--accent-sage-light);
      border-left: 2.5px solid var(--accent-sage);
      padding: 1mm 2mm;
      border-radius: 0 3px 3px 0;
      font-size: 6.5pt;
      margin-top: 1mm;
      color: #1a3325;
      line-height: 1.2;
    }}
    .variants-pdf-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.8mm;
      margin-top: 1mm;
    }}
    .var-pdf-box {{
      background: #fcfbf9;
      border: 1px solid var(--border-soft);
      border-radius: 3px;
      padding: 1mm 1.5mm;
      font-size: 6.4pt;
      line-height: 1.18;
    }}
    .var-pdf-box strong {{
      display: block;
      color: var(--accent-terracotta);
      font-size: 6.2pt;
      text-transform: uppercase;
      margin-bottom: 0.2mm;
    }}
    .sobra-pdf {{
      font-size: 6.4pt;
      color: #666;
      margin-top: 1mm;
      border-top: 1px dashed var(--border-soft);
      padding-top: 0.8mm;
      line-height: 1.18;
    }}

    /* --- LISTAS DE COMPRAS (1 PÁGINA POR SEMANA, 3 COLUMNAS SIN DESBORDE) --- */
    .shop-sectors-pdf {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 2.8mm;
      margin-top: 2mm;
    }}
    .shop-sec-col {{
      break-inside: avoid;
    }}
    .shop-sec-col h4 {{
      font-size: 7.2pt;
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: var(--accent-sage);
      border-bottom: 1px solid var(--border-soft);
      padding-bottom: 0.8mm;
      margin-bottom: 1mm;
    }}
    .shop-item-pdf {{
      font-size: 6.8pt;
      padding: 0.4mm 0;
      display: flex;
      gap: 1.5mm;
      line-height: 1.2;
    }}
    .check-box-pdf {{
      display: inline-block;
      width: 7.5px;
      height: 7.5px;
      border: 1px solid #777;
      border-radius: 2px;
      margin-top: 1px;
      flex-shrink: 0;
    }}
    .alacena-pdf {{
      background: #fdfaf5;
      border: 1px solid #eedec8;
      border-left: 3px solid var(--accent-mustard);
      border-radius: 4px;
      padding: 1.8mm 2.8mm;
      margin-top: 2.5mm;
      font-size: 7.2pt;
      line-height: 1.3;
    }}
  </style>
</head>
<body>

  <!-- 1. PORTADA -->
  <section class="portada-page page-break">
    <div>
      <span class="portada-badge">{config.get("edicion", "Edición 2026")} · Sistema Familiar</span>
      <h1 class="portada-title">{config.get("titulo", "30 días sin preguntarte qué cocinar")}</h1>
      <p class="portada-subtitle">{config.get("subtitulo", "El sistema práctico de comidas planificadas para familias ocupadas")}</p>
      
      <div class="portada-img-wrap">
        <img src="{portada_img}" alt="Portada {config.get('titulo')}">
      </div>
    </div>
    <div class="portada-footer">
      <p><strong>{config.get("marca")}</strong> · Guía culinaria argentina cotidiana</p>
      <p style="margin-top: 1mm; font-size: 7pt; color: #999;">
        32 platos principales · 13 opciones de desayunos, colaciones, viandas y postres · Calendario coordinado · Listas de compras exactas
      </p>
    </div>
  </section>

  <!-- 2. ÍNDICE Y FILOSOFÍA -->
  <section class="page-break">
    <h2 class="section-title">Antes de empezar</h2>
    <p class="section-desc">Un sistema simple para recuperar tranquilidad en la cocina doméstica</p>

    <div class="editorial-box" style="background:#fffcf8; border-left: 3px solid var(--accent-terracotta); padding: 3mm 4mm; margin-bottom: 3mm;">
      <h4 style="font-family: 'Fraunces', serif; color: var(--accent-terracotta); margin: 0 0 1mm 0; font-size: 9.5pt;">Quién hizo esta guía</h4>
      <p style="font-size: 8pt; color: #444; line-height: 1.45; margin: 0;">{ed.get("quien_hizo_esta_guia", {}).get("texto", "")}</p>
    </div>

    <div class="editorial-box">
      {"".join(f"<p>{p}</p>" for p in ed.get("introduccion", {}).get("antes_de_empezar", {}).get("parrafos", []))}
      <div class="highlight-card">
        <strong>Tres principios para no abandonar:</strong>
        <ul>
          {"".join(f"<li>{c}</li>" for c in ed.get("introduccion", {}).get("antes_de_empezar", {}).get("claves", []))}
        </ul>
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

    <div class="editorial-box">
      <h3>El círculo de la improvisación</h3>
      <p>{ed.get("introduccion", {}).get("circulo_improvisacion", {}).get("bajada", "")}</p>
      <ul style="padding-left: 4mm; font-size: 8pt; color: #444; margin-top: 1.5mm;">
        {"".join(f"<li style='margin-bottom:0.8mm;'>{t}</li>" for t in ed.get("introduccion", {}).get("circulo_improvisacion", {}).get("trampas", []))}
      </ul>
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
    <p class="section-desc">Pautas bromatológicas para cocinar de más con total tranquilidad</p>

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

    <div class="editorial-box">
      <h3>Una base, tres comidas diferentes</h3>
      <ul style="padding-left: 4mm; font-size: 7.5pt;">
        {"".join(f"<li style='margin-bottom:0.8mm;'>{p}</li>" for p in ed.get("estrategias", {}).get("aprovechamiento", {}).get("pautas", []))}
      </ul>
    </div>

    <div class="editorial-box" style="border-left: 3px solid #eab308; background: #fefce8; padding: 2mm 3mm; margin-top: 2mm;">
      <h4 style="font-family: 'Fraunces', serif; color: #854d0e; font-size: 8.5pt; margin: 0 0 1mm 0;">🧂 {ed.get("pauta_sodio", {}).get("titulo", "Atención al sodio")}</h4>
      <p style="font-size: 7pt; color: #713f12; line-height: 1.3; margin: 0;">{ed.get("pauta_sodio", {}).get("texto", "")}</p>
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

    <div class="grid-2col" style="margin-top: 2.5mm;">
      <div class="editorial-box" style="margin-bottom: 0;">
        <h3 style="color: var(--accent-terracotta); font-size: 10pt;">Porciones de referencia para chicos</h3>
        {"".join(f"""
        <div class="mini-card" style="margin-bottom: 1.8mm;">
          <strong style="color: var(--accent-sage); font-size: 7.5pt;">👶 {r['rango']}</strong>
          <p style="font-size: 7pt; color: #444; margin-top: 0.5mm;">{r['porcion']}</p>
        </div>
        """ for r in ed.get("porciones", {}).get("referencia_edades", []))}
      </div>

      <div class="editorial-box" style="margin-bottom: 0;">
        <h3 style="font-size: 10pt;">Pautas clave al cambiar cantidades</h3>
        {"".join(f"""
        <div style="margin-bottom: 2mm;">
          <strong style="font-size: 7.5pt; color: var(--accent-terracotta);">• {p['titulo']}:</strong>
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
        <h3 style="color: #dc2626; font-size: 10pt;">🛡️ Prevención de atragantamiento</h3>
        {"".join(f"""
        <div class="mini-card" style="margin-bottom: 1.8mm;">
          <strong style="color: #991b1b; font-size: 7.5pt;">{al['alimento']}</strong>
          <p style="font-size: 7pt; color: #444; margin-top: 0.5mm;">{al['adaptacion']}</p>
        </div>
        """ for al in ed.get("seguridad_infantil", {}).get("alimentos_riesgo", []))}

        <div style="background: #fef2f2; border-left: 3px solid #ef4444; padding: 1.8mm 2.5mm; border-radius: 4px; margin-top: 2mm;">
          <strong style="font-size: 7.5pt; color: #991b1b;">🍯 {ed.get("seguridad_infantil", {}).get("regla_miel", {}).get("titulo", "")}</strong>
          <p style="font-size: 6.8pt; color: #7f1d1d; margin: 0.5mm 0 0 0;">{ed.get("seguridad_infantil", {}).get("regla_miel", {}).get("texto", "")}</p>
        </div>
      </div>

      <div class="editorial-box">
        <h3 style="color: var(--accent-sage); font-size: 10pt;">🌱 Consejos para chicos selectivos</h3>
        {"".join(f"""
        <div style="margin-bottom: 1.8mm; padding-bottom: 1.2mm; border-bottom: 1px dashed #e2e8f0;">
          <strong style="font-size: 7.5pt; color: var(--accent-terracotta);">{c['numero']}. {c['titulo']}:</strong>
          <span style="font-size: 7pt; color: #444;"> {c['texto']}</span>
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
    <p class="section-desc">Rotación de desayunos, meriendas y viandas + tus plantillas descargables</p>

    <div class="editorial-box" style="margin-top: 2mm;">
      <h3 style="margin-bottom: 1.2mm;">Esquema semanal rotativo (Desayunos, Colaciones y Viandas)</h3>
      <table class="cal-table" style="font-size: 7pt;">
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

    <div class="editorial-box" style="margin-top: 2.5mm;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin-bottom: 1.2mm; color: var(--accent-terracotta);">📥 Cómo usar tu Pack de Imprimibles A4</h3>
        <span style="background: #fdf2f8; color: #9d174d; font-size: 6.5pt; font-weight: bold; padding: 1px 5px; border-radius: 3px; border: 1px solid #fbcfe8;">PDF Independiente Incluido</span>
      </div>
      <p style="font-size: 7.5pt; color: #555; margin-bottom: 1.5mm;">{ed.get("como_usar_imprimibles", {}).get("bajada", "")}</p>
      
      <div class="grid-2col">
        {"".join(f"""
        <div class="mini-card" style="padding: 1.8mm 2.5mm;">
          <strong style="font-size: 7.2pt; color: var(--accent-sage);">{h['nombre']}</strong>
          <p style="font-size: 6.8pt; color: #444; margin: 0.5mm 0 0 0;">{h['uso']}</p>
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
          <th style="width: 15%;">Día</th>
          <th style="width: 42.5%;">Almuerzo</th>
          <th style="width: 42.5%;">Cena & Postre</th>
        </tr>
      </thead>
      <tbody>
"""

    for d in cal["dias"][:15]:
        dia_num = d["dia"]
        nombre_d = motor.nombre_dia(dia_num).capitalize()
        alm = d["almuerzo"]
        if "receta" in alm:
            alm_txt = recetas[alm["receta"]]["nombre"]
            alm_tag = f'<span class="cal-tag tag-doble">x{alm.get("porciones", 4)}</span>' if alm.get("porciones", 4) > 4 else ""
        elif "sobra_de" in alm:
            alm_txt = recetas[alm["sobra_de"]]["nombre"]
            alm_tag = '<span class="cal-tag tag-sobra">Sobra</span>'
        else:
            alm_txt = recetas[alm["del_freezer"]]["nombre"]
            alm_tag = '<span class="cal-tag tag-freezer">Freezer</span>'

        cena = d["cena"]
        if "receta" in cena:
            cena_txt = recetas[cena["receta"]]["nombre"]
            cena_tag = f'<span class="cal-tag tag-doble">x{cena.get("porciones", 4)}</span>' if cena.get("porciones", 4) > 4 else ""
        elif "sobra_de" in cena:
            cena_txt = recetas[cena["sobra_de"]]["nombre"]
            cena_tag = '<span class="cal-tag tag-sobra">Sobra</span>'
        else:
            cena_txt = recetas[cena["del_freezer"]]["nombre"]
            cena_tag = '<span class="cal-tag tag-freezer">Freezer</span>'

        postre = d.get("postre_cena")
        postre_txt = f'<br><small style="color:#777;">🍰 {recetas[postre]["nombre"]}</small>' if postre else ""
        batch_txt = f'<br><span class="cal-tag tag-batch">{d["nota_batch"]}</span>' if d.get("nota_batch") else ""

        html += f"""
        <tr>
          <td><span class="cal-day-num">Día {dia_num}</span><br><small>{nombre_d}</small>{batch_txt}</td>
          <td>{alm_txt} {alm_tag}</td>
          <td>{cena_txt} {cena_tag} {postre_txt}</td>
        </tr>
        """

    html += """
      </tbody>
    </table>
  </section>

  <!-- 6. CALENDARIO MENSUAL (DÍAS 16 A 30) -->
  <section class="page-break">
    <h2 class="section-title">Calendario Mensual · Días 16 a 30</h2>
    <p class="section-desc">Planificación de almuerzo y cena con rotación equilibrada de proteínas. 💡 Para desayunos y viandas consultá la <strong>Semana Tipo de Extras</strong>.</p>

    <table class="cal-table">
      <thead>
        <tr>
          <th style="width: 15%;">Día</th>
          <th style="width: 42.5%;">Almuerzo</th>
          <th style="width: 42.5%;">Cena & Postre</th>
        </tr>
      </thead>
      <tbody>
"""

    for d in cal["dias"][15:]:
        dia_num = d["dia"]
        nombre_d = motor.nombre_dia(dia_num).capitalize()
        alm = d["almuerzo"]
        if "receta" in alm:
            alm_txt = recetas[alm["receta"]]["nombre"]
            alm_tag = f'<span class="cal-tag tag-doble">x{alm.get("porciones", 4)}</span>' if alm.get("porciones", 4) > 4 else ""
        elif "sobra_de" in alm:
            alm_txt = recetas[alm["sobra_de"]]["nombre"]
            alm_tag = '<span class="cal-tag tag-sobra">Sobra</span>'
        else:
            alm_txt = recetas[alm["del_freezer"]]["nombre"]
            alm_tag = '<span class="cal-tag tag-freezer">Freezer</span>'

        cena = d["cena"]
        if "receta" in cena:
            cena_txt = recetas[cena["receta"]]["nombre"]
            cena_tag = f'<span class="cal-tag tag-doble">x{cena.get("porciones", 4)}</span>' if cena.get("porciones", 4) > 4 else ""
        elif "sobra_de" in cena:
            cena_txt = recetas[cena["sobra_de"]]["nombre"]
            cena_tag = '<span class="cal-tag tag-sobra">Sobra</span>'
        else:
            cena_txt = recetas[cena["del_freezer"]]["nombre"]
            cena_tag = '<span class="cal-tag tag-freezer">Freezer</span>'

        postre = d.get("postre_cena")
        postre_txt = f'<br><small style="color:#777;">🍰 {recetas[postre]["nombre"]}</small>' if postre else ""
        batch_txt = f'<br><span class="cal-tag tag-batch">{d["nota_batch"]}</span>' if d.get("nota_batch") else ""

        html += f"""
        <tr>
          <td><span class="cal-day-num">Día {dia_num}</span><br><small>{nombre_d}</small>{batch_txt}</td>
          <td>{alm_txt} {alm_tag}</td>
          <td>{cena_txt} {cena_tag} {postre_txt}</td>
        </tr>
        """

    html += """
      </tbody>
    </table>
  </section>

  <!-- 7. SECCIÓN RECETARIO (2 RECETAS POR PÁGINA · OPCIÓN A) -->
"""

    def render_recipe_card(r, is_single=False):
        img_file = img_dir / f"{r['id']}.png"
        if not img_file.exists():
            img_file = DISENO / "ilustraciones" / f"{r['id']}.png"

        img_html = f'<img class="recipe-thumb-img" src="{img_file}" alt="{r["nombre"]}">' if img_file.exists() else ''

        # 3.3 Unidades legibles
        ing_items = "".join(f"<li><span>{i['item']}</span> <strong>{motor.cantidad_legible(i['cantidad'], i['unidad'])}</strong></li>" for i in r["ingredientes"])
        pasos_items = "".join(f"<li>{p}</li>" for p in r["pasos"])

        senales = f'<div class="cue-pdf"><strong>👀 Señal:</strong> {r["senales_coccion"]}</div>' if r.get("senales_coccion") else ""
        acomp_verde = f'<div class="cue-pdf" style="background:#f0fdf4; border-left:2.5px solid #22c55e; color:#166534;">{r["acompanamiento_verde"]}</div>' if r.get("acompanamiento_verde") else ""
        nota_seg = f'<div class="cue-pdf" style="background:#fff7ed; border-left:2.5px solid #f97316; color:#9a3412;">🐟 <strong>Nota:</strong> {r["nota_seguridad"]}</div>' if r.get("nota_seguridad") else ""
        chicos = f'<div class="var-pdf-box"><strong>👶 Versión chicos</strong>{r["version_chicos"]}</div>' if r.get("version_chicos") else ""
        adultos = f'<div class="var-pdf-box"><strong>🌶️ Variante adultos</strong>{r["variante_adultos"]}</div>' if r.get("variante_adultos") else ""
        variants_html = f'<div class="variants-pdf-grid">{chicos}{adultos}</div>' if (chicos or adultos) else ""
        sobra = f'<div class="sobra-pdf">🧊 <strong>Conservación:</strong> {r["si_te_sobra"]}</div>' if r.get("si_te_sobra") else ""
        
        # 3.2 Íconos de tiempo y kcal compactos sin partirse
        calorias = f'<span class="pill-pdf cal">~{r["nutricion"]["kcal"]} kcal (adulto)</span>' if r.get("nutricion") else ""
        tiempo_pill = f'<span class="pill-pdf time">⏱️ {r["tiempo_total"]}m · {r["tiempo_activo"]}m act</span>'

        card_class = "recipe-card-half single" if is_single else "recipe-card-half"

        return f"""
        <div class="{card_class}">
          <div>
            <div class="recipe-card-header">
              <div>
                <h3 class="recipe-title-pdf">{r['nombre']}</h3>
                <div class="recipe-meta-sub">Proteína: {r['proteina']} · Dificultad: {r['dificultad']}</div>
              </div>
              <div class="recipe-pills">
                {tiempo_pill}
                {calorias}
              </div>
            </div>

            <div class="recipe-card-body">
              <div class="recipe-left-col">
                <div>
                  <div class="recipe-thumb-wrap">
                    {img_html}
                    <div class="col-title" style="flex:1;">Ingredientes (4 porc.)</div>
                  </div>
                  <ul class="ing-pdf-list">
                    {ing_items}
                  </ul>
                </div>
                {sobra}
              </div>

              <div>
                <div class="col-title">Preparación</div>
                <ol class="steps-pdf-list">
                  {pasos_items}
                </ol>
                {senales}
                {variants_html}
                {nota_seg}
                {acomp_verde}
              </div>
            </div>
          </div>
        </div>
        """

    recetas_lista = list(recetas.values())
    for i in range(0, len(recetas_lista), 2):
        r1 = recetas_lista[i]
        r2 = recetas_lista[i + 1] if i + 1 < len(recetas_lista) else None

        if r2:
            html += f"""
            <section class="recipe-double-page page-break">
              {render_recipe_card(r1)}
              {render_recipe_card(r2)}
            </section>
            """
        else:
            html += f"""
            <section class="recipe-double-page page-break">
              {render_recipe_card(r1, is_single=True)}
            </section>
            """

    # 8. LISTAS DE COMPRAS SEMANALES (1 PÁGINA POR SEMANA, 3 COLUMNAS SIN DESBORDE)
    for s in semanas_info:
        html += f"""
        <section class="page-break">
          <h2 class="section-title">Lista de Compras · Días {s['desde']} a {s['hasta']}</h2>
          <p class="section-desc">Cantidades calculadas exactamente según el menú, organizadas por sector de góndola</p>

          <div class="shop-sectors-pdf">
        """
        for sector, items in s["sectores"]:
            html += f"""
            <div class="shop-sec-col">
              <h4>{sector}</h4>
            """
            for it in items:
                det = f" <small style='color:#777;'>({it['detalle']})</small>" if it["detalle"] else ""
                html += f"""
                <div class="shop-item-pdf">
                  <span class="check-box-pdf"></span>
                  <span><strong>{it['item']}</strong>: {it['texto']}{det}</span>
                </div>
                """
            html += "</div>"

        html += "</div>"
        if s["alacena"]:
            alacena_str = ", ".join(s["alacena"])
            html += f"""
            <div class="alacena-pdf">
              <strong>🧂 Revisá en tu alacena:</strong> {alacena_str}
            </div>
            """
        html += "</section>"

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

    html += f"""
    <section class="page-break">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <h2 class="section-title">Lista de Compras · Extras</h2>
          <p class="section-desc">Ingredientes para resolver la Semana Tipo de Desayunos, Colaciones y Viandas</p>
        </div>
        <span style="background: #eef6ee; color: #166534; font-size: 7.2pt; font-weight: bold; padding: 2px 7px; border-radius: 4px; border: 1px solid #bbf7d0;">Bloque Separado</span>
      </div>

      <div class="shop-sectors-pdf">
    """
    for sector, items in extras_sectores:
        html += f"""
        <div class="shop-sec-col">
          <h4>{sector}</h4>
        """
        for it in items:
            html += f"""
            <div class="shop-item-pdf">
              <span class="check-box-pdf"></span>
              <span><strong>{it['item']}</strong>: {it['texto']}</span>
            </div>
            """
        html += "</div>"
    html += "</div></section>"

    # 9. PÁGINA FINAL / COMPROMISO Y FUENTES
    html += f"""
    <section class="page-break" style="padding-top: 8mm;">
      <h2 class="section-title">Tu compromiso familiar de 30 días</h2>
      <p class="section-desc">Menos decisiones diarias, más tranquilidad en el hogar</p>

      <div class="editorial-box" style="padding: 5mm 7mm; margin-top: 4mm; border-left: 4px solid var(--accent-sage);">
        <p style="font-size: 10pt; line-height: 1.6; color: var(--text-dark);">
          {ed.get("estrategias", {}).get("compromiso", {}).get("texto", "")}
        </p>
      </div>

      <div class="editorial-box" style="margin-top: 6mm;">
        <h3>Fuentes oficiales y pautas de salud</h3>
        <p style="font-size: 7.8pt; color: #555; line-height: 1.45;">
          Esta guía ofrece ideas generales de organización y cocina doméstica; no reemplaza el asesoramiento nutricional o médico particular.
          Referencias para ampliar: Guías Alimentarias para la Población Argentina (Ministerio de Salud); Organización Mundial de la Salud (Healthy diet); Manuales bromatológicos de manipulación y conservación de alimentos.
        </p>
      </div>

      <div style="text-align: center; margin-top: 15mm; color: #888; font-size: 7.5pt;">
        <p><strong>{config.get("marca")}</strong> · {config.get("edicion")}</p>
        <p>{config.get("copyright")}</p>
      </div>
    </section>

</body>
</html>
"""
    SALIDA.mkdir(exist_ok=True)
    html_out = SALIDA / f"ebook_para_pdf_{edicion}.html" if edicion != "completa" else SALIDA / "ebook_para_pdf.html"
    html_out.write_text(html, encoding="utf-8")
    return html_out

def compilar_pdf(edicion="completa"):
    html_file = generar_html_pdf(edicion=edicion)
    if edicion == "celular":
        pdf_out = SALIDA / "30_dias_sin_preguntarte_que_cocinar_celular.pdf"
    else:
        pdf_out = SALIDA / "30_dias_sin_preguntarte_que_cocinar.pdf"
    
    cmd = [
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        f"--print-to-pdf={pdf_out}",
        "--no-pdf-header-footer",
        str(html_file)
    ]
    
    print(f"⏳ Compilando PDF ({edicion}) con motor de impresión A4...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("❌ Error al generar el PDF:", res.stderr)
        sys.exit(res.returncode)
    
    size_mb = pdf_out.stat().st_size / (1024 * 1024)
    print(f"🎉 PDF editorial ({edicion}) generado con éxito en: {pdf_out} ({size_mb:.2f} MB)")
    return pdf_out

if __name__ == "__main__":
    compilar_pdf("completa")
    compilar_pdf("celular")
