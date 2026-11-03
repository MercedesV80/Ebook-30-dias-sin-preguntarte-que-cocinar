#!/usr/bin/env python3
"""Genera el Visor Editorial A4 interactivo del ebook completo.

Permite recorrer hoja por hoja el ebook en el navegador tal como saldrá
en el PDF impreso, con navegación por teclado, selector de secciones,
modo página individual / doble página / scroll continuo y estado real
de ilustraciones.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import motor

DATOS = RAIZ / "datos"
DISENO = RAIZ / "diseno"
SALIDA = RAIZ / "salida"

def generar_visor():
    config, recetas, cal = motor.cargar()
    
    editorial_path = DATOS / "contenido_editorial.json"
    ed = json.loads(editorial_path.read_text(encoding="utf-8")) if editorial_path.exists() else {}

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

    paginas = []
    indice = []

    # ==========================================
    # PÁGINA 1: PORTADA
    # ==========================================
    p1 = f"""
    <div class="sheet-a4 portada-sheet" data-page="1" data-title="Portada">
      <div class="portada-content">
        <div>
          <span class="portada-badge">Edición 2026 · Guía Maestra</span>
          <h1 class="portada-title">{config.get("titulo")}</h1>
          <p class="portada-subtitle">{config.get("subtitulo")}</p>
        </div>

        <div class="portada-img-wrap">
          <img src="../diseno/ilustraciones/portada.png" alt="Portada {config.get('titulo')}">
        </div>

        <div class="portada-footer">
          <p><strong>{config.get("marca")}</strong> · {config.get("edicion")}</p>
          <p>{config.get("copyright")}</p>
          <p style="margin-top: 1.5mm; font-size: 6.5pt; max-width: 550px; margin-left: auto; margin-right: auto; color: #777;">
            {config.get("aviso_profesional")}
          </p>
        </div>
      </div>
    </div>
    """
    paginas.append(p1)
    indice.append({"num": 1, "titulo": "Portada", "seccion": "Portada"})

    # ==========================================
    # PÁGINA 2: ANTES DE EMPEZAR & FILOSOFÍA
    # ==========================================
    p2 = f"""
    <div class="sheet-a4" data-page="2" data-title="Antes de empezar">
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
        <ul style="padding-left: 4mm; font-size: 8.5pt; color: #444; margin-top: 2mm;">
          {"".join(f"<li style='margin-bottom:1mm;'>{t}</li>" for t in ed.get("introduccion", {}).get("circulo_improvisacion", {}).get("trampas", []))}
        </ul>
      </div>

      <div class="sheet-page-footer">
        <span>{config.get("titulo")}</span>
        <span>Página 2</span>
      </div>
    </div>
    """
    paginas.append(p2)
    indice.append({"num": 2, "titulo": "Antes de empezar", "seccion": "Introducción"})

    # ==========================================
    # PÁGINA 3: EL MÉTODO DE LOS 15 MINUTOS
    # ==========================================
    p3 = f"""
    <div class="sheet-a4" data-page="3" data-title="El Método de los 15 Minutos">
      <h2 class="section-title">El Método de los 15 Minutos</h2>
      <p class="section-desc">Planificación semanal ágil: 6 pasos para organizar la cocina familiar</p>

      <div class="grid-2col">
        {"".join(f'''
        <div class="mini-card" style="padding: 2.5mm 3.5mm;">
          <h4>Paso {p["paso"]} · {p["titulo"]}</h4>
          <p style="font-size: 8pt; color: #555;">{p["detalle"]}</p>
        </div>
        ''' for p in ed.get("metodo", {}).get("los_15_minutos", {}).get("pasos", []))}
      </div>

      <div class="editorial-box" style="margin-top: 4mm;">
        <h3>La fórmula de un plato práctico y balanceado</h3>
        <p>{ed.get("metodo", {}).get("formula_plato", {}).get("bajada", "")}</p>
        <div class="grid-3col">
          {"".join(f'''
          <div class="mini-card" style="text-align: center;">
            <h4 style="color: var(--accent-sage);">{c["nombre"]}</h4>
            <p style="font-size: 7.5pt;">{c["rol"]}</p>
          </div>
          ''' for c in ed.get("metodo", {}).get("formula_plato", {}).get("componentes", []))}
        </div>
      </div>

      <div class="editorial-box">
        <h3>Criterios inteligentes antes de ir al súper</h3>
        <ul style="padding-left: 4mm; font-size: 8.5pt;">
          {"".join(f"<li style='margin-bottom:1.5mm;'>{c}</li>" for c in ed.get("metodo", {}).get("compras_estrategicas", {}).get("consejos", []))}
        </ul>
      </div>

      <div class="sheet-page-footer">
        <span>{config.get("titulo")}</span>
        <span>Página 3</span>
      </div>
    </div>
    """
    paginas.append(p3)
    indice.append({"num": 3, "titulo": "El Método de 15 Minutos", "seccion": "Método"})

    # ==========================================
    # PÁGINA 4: CONSERVACIÓN Y EMERGENCIAS
    # ==========================================
    p4 = f"""
    <div class="sheet-a4" data-page="4" data-title="Conservación Segura & Emergencias">
      <h2 class="section-title">Conservación Segura & Comidas de Emergencia</h2>
      <p class="section-desc">Pautas bromatológicas para cocinar de más con total tranquilidad</p>

      <div class="editorial-box">
        <h3>Pautas generales de seguridad alimentaria</h3>
        <div class="grid-2col">
          {"".join(f'''
          <div class="mini-card" style="background:#fcfcfc;">
            <h4 style="font-size: 8.5pt; color: var(--accent-sage);">🛡️ {pt["titulo"]}</h4>
            <p style="font-size: 7.5pt; color: #333;">{pt["texto"]}</p>
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
            <p style="font-size: 7.5pt;">{p["detalle"]}</p>
          </div>
          ''' for p in ed.get("estrategias", {}).get("comidas_emergencia", {}).get("planes", []))}
        </div>
      </div>

      <div class="editorial-box">
        <h3>Una base, tres comidas diferentes</h3>
        <ul style="padding-left: 4mm; font-size: 8pt;">
          {"".join(f"<li style='margin-bottom:1mm;'>{p}</li>" for p in ed.get("estrategias", {}).get("aprovechamiento", {}).get("pautas", []))}
        </ul>
      </div>

      <div class="sheet-page-footer">
        <span>{config.get("titulo")}</span>
        <span>Página 4</span>
      </div>
    </div>
    """
    paginas.append(p4)
    indice.append({"num": 4, "titulo": "Conservación & Emergencias", "seccion": "Seguridad"})

    # ==========================================
    # PÁGINA 5: CALENDARIO (DÍAS 1 A 15)
    # ==========================================
    rows_cal_1 = ""
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

        rows_cal_1 += f"""
        <tr>
          <td><span class="cal-day-num">Día {dia_num}</span><br><small>{nombre_d}</small></td>
          <td>{alm_txt} {alm_tag}</td>
          <td>{cena_txt} {cena_tag} {postre_txt}</td>
        </tr>
        """

    p5 = f"""
    <div class="sheet-a4" data-page="5" data-title="Calendario Días 1 a 15">
      <h2 class="section-title">Calendario Mensual · Días 1 a 15</h2>
      <p class="section-desc">Planificación de almuerzo y cena con rotación equilibrada de proteínas</p>

      <table class="cal-table">
        <thead>
          <tr>
            <th style="width: 14%;">Día</th>
            <th style="width: 43%;">Almuerzo</th>
            <th style="width: 43%;">Cena & Postre</th>
          </tr>
        </thead>
        <tbody>
          {rows_cal_1}
        </tbody>
      </table>

      <div class="sheet-page-footer">
        <span>{config.get("titulo")}</span>
        <span>Página 5</span>
      </div>
    </div>
    """
    paginas.append(p5)
    indice.append({"num": 5, "titulo": "Calendario Mensual (Días 1 a 15)", "seccion": "Calendario"})

    # ==========================================
    # PÁGINA 6: CALENDARIO (DÍAS 16 A 30)
    # ==========================================
    rows_cal_2 = ""
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

        rows_cal_2 += f"""
        <tr>
          <td><span class="cal-day-num">Día {dia_num}</span><br><small>{nombre_d}</small></td>
          <td>{alm_txt} {alm_tag}</td>
          <td>{cena_txt} {cena_tag} {postre_txt}</td>
        </tr>
        """

    p6 = f"""
    <div class="sheet-a4" data-page="6" data-title="Calendario Días 16 a 30">
      <h2 class="section-title">Calendario Mensual · Días 16 a 30</h2>
      <p class="section-desc">Planificación de almuerzo y cena con rotación equilibrada de proteínas</p>

      <table class="cal-table">
        <thead>
          <tr>
            <th style="width: 14%;">Día</th>
            <th style="width: 43%;">Almuerzo</th>
            <th style="width: 43%;">Cena & Postre</th>
          </tr>
        </thead>
        <tbody>
          {rows_cal_2}
        </tbody>
      </table>

      <div class="sheet-page-footer">
        <span>{config.get("titulo")}</span>
        <span>Página 6</span>
      </div>
    </div>
    """
    paginas.append(p6)
    indice.append({"num": 6, "titulo": "Calendario Mensual (Días 16 a 30)", "seccion": "Calendario"})

    # ==========================================
    # PÁGINAS 7 EN ADELANTE: RECETARIO (1 PÁGINA A4 POR RECETA)
    # ==========================================
    page_num = 7
    ilustradas_count = 0
    pendientes_count = 0

    for r in recetas.values():
        img_file = DISENO / "ilustraciones" / f"{r['id']}.png"
        
        if img_file.exists():
            ilustradas_count += 1
            img_markup = f'''
            <div class="recipe-img-box">
              <img src="../diseno/ilustraciones/{r["id"]}.png" alt="{r["nombre"]}">
            </div>'''
            badge_art = "🎨 Ilustrada"
        else:
            pendientes_count += 1
            img_markup = f'''
            <div class="recipe-img-box pending-art">
              <span class="pending-icon">🖌️</span>
              <div class="pending-title">Ilustración en proceso</div>
              <div class="pending-sub">Acuarela gastronómica con trazo de tinta (próxima cuota)</div>
            </div>'''
            badge_art = "⏳ Arte en proceso"

        ing_items = "".join(f"<li><span>{i['item']}</span> <strong>{i['cantidad']} {i['unidad']}</strong></li>" for i in r["ingredientes"])
        pasos_items = "".join(f"<li>{p}</li>" for p in r["pasos"])

        senales = f'<div class="cue-pdf"><strong>👀 Señal de cocción:</strong> {r["senales_coccion"]}</div>' if r.get("senales_coccion") else ""
        acomp_verde = f'<div class="cue-pdf" style="background:#f0fdf4; border-left:3px solid #22c55e; color:#166534; margin-top:2mm;">{r["acompanamiento_verde"]}</div>' if r.get("acompanamiento_verde") else ""
        chicos = f'<div class="var-pdf-box"><strong>👶 Versión chicos</strong>{r["version_chicos"]}</div>' if r.get("version_chicos") else ""
        adultos = f'<div class="var-pdf-box"><strong>🌶️ Variante adultos</strong>{r["variante_adultos"]}</div>' if r.get("variante_adultos") else ""
        variants_html = f'<div class="variants-pdf-grid">{chicos}{adultos}</div>' if (chicos or adultos) else ""
        sobra = f'<div class="sobra-pdf">🧊 <strong>Conservación:</strong> {r["si_te_sobra"]}</div>' if r.get("si_te_sobra") else ""
        calorias = f'<span class="pill-pdf cal">~{r["nutricion"]["kcal"]} kcal (estimación por porción de adulto)</span>' if r.get("nutricion") else ""

        p_receta = f"""
        <div class="sheet-a4 recipe-sheet" data-page="{page_num}" data-title="{r['nombre']}" data-tipo="{r['tipo']}">
          <div class="recipe-header-pdf">
            <div>
              <h3 class="recipe-title-pdf">{r['nombre']}</h3>
              <small style="color: #666;">Proteína: {r['proteina']} · Dificultad: {r['dificultad']}</small>
            </div>
            <div class="recipe-pills">
              <span class="pill-pdf time">⏱️ {r['tiempo_total']} min (activo: {r['tiempo_activo']}m)</span>
              {calorias}
            </div>
          </div>

          {img_markup}

          <div class="recipe-layout-grid">
            <div>
              <div class="col-title">Ingredientes (4 porciones)</div>
              <ul class="ing-pdf-list">
                {ing_items}
              </ul>
              {sobra}
            </div>

            <div>
              <div class="col-title">Preparación</div>
              <ol class="steps-pdf-list">
                {pasos_items}
              </ol>
              {senales}
              {variants_html}
            </div>
          </div>

          <div class="sheet-page-footer">
            <span>{config.get("titulo")} · Recetario</span>
            <span>Página {page_num}</span>
          </div>
        </div>
        """
        paginas.append(p_receta)
        indice.append({
            "num": page_num,
            "titulo": r["nombre"],
            "seccion": "Recetario",
            "tipo": r["tipo"],
            "tiene_arte": img_file.exists()
        })
        page_num += 1

    # ==========================================
    # LISTAS DE COMPRAS SEMANALES (1 PÁGINA A4 POR SEMANA)
    # ==========================================
    for s_idx, s in enumerate(semanas_info, 1):
        sectores_cols = ""
        for sector, items in s["sectores"]:
            items_markup = ""
            for it in items:
                det = f" <small style='color:#777;'>({it['detalle']})</small>" if it["detalle"] else ""
                items_markup += f"""
                <div class="shop-item-pdf">
                  <span class="check-box-pdf"></span>
                  <span><strong>{it['item']}</strong>: {it['texto']}{det}</span>
                </div>
                """
            sectores_cols += f"""
            <div class="shop-sec-col">
              <h4>{sector}</h4>
              {items_markup}
            </div>
            """

        alacena_markup = ""
        if s["alacena"]:
            alacena_str = ", ".join(s["alacena"])
            alacena_markup = f"""
            <div class="alacena-pdf">
              <strong>🧂 Revisá en tu alacena antes de salir:</strong> {alacena_str}
            </div>
            """

        p_shop = f"""
        <div class="sheet-a4" data-page="{page_num}" data-title="Lista de Compras Semana {s_idx}">
          <h2 class="section-title">Lista de Compras · Días {s['desde']} a {s['hasta']}</h2>
          <p class="section-desc">Cantidades exactas consolidadas según el calendario, organizadas por sector de góndola</p>

          <div class="shop-sectors-pdf">
            {sectores_cols}
          </div>
          {alacena_markup}

          <div class="sheet-page-footer">
            <span>{config.get("titulo")} · Compras</span>
            <span>Página {page_num}</span>
          </div>
        </div>
        """
        paginas.append(p_shop)
        indice.append({
            "num": page_num,
            "titulo": f"Lista de Compras (Semana {s_idx} · Días {s['desde']} a {s['hasta']})",
            "seccion": "Compras"
        })
        page_num += 1

    # ==========================================
    # PÁGINA FINAL: COMPROMISO Y CIERRE
    # ==========================================
    p_final = f"""
    <div class="sheet-a4" data-page="{page_num}" data-title="Compromiso Familiar y Cierre" style="display:flex; flex-direction:column; justify-content:space-between;">
      <div>
        <h2 class="section-title">Tu compromiso familiar de 30 días</h2>
        <p class="section-desc">Menos decisiones diarias, más tranquilidad en el hogar</p>

        <div class="editorial-box" style="padding: 6mm 8mm; margin-top: 6mm; border-left: 4px solid var(--accent-sage); background: #fdfbf7;">
          <p style="font-size: 11pt; line-height: 1.7; color: var(--text-dark);">
            {ed.get("estrategias", {}).get("compromiso", {}).get("texto", "")}
          </p>
        </div>

        <div class="editorial-box" style="margin-top: 8mm;">
          <h3>Fuentes oficiales y pautas de salud</h3>
          <p style="font-size: 8.5pt; color: #555; line-height: 1.55;">
            Esta guía ofrece ideas generales de organización y cocina doméstica; no reemplaza el asesoramiento nutricional o médico particular.
            Referencias para ampliar: Guías Alimentarias para la Población Argentina (Ministerio de Salud); Organización Mundial de la Salud (Healthy diet); ANMAT (Manipulación de alimentos y recomendaciones de conservación en el hogar).
          </p>
        </div>
      </div>

      <div style="text-align: center; color: #888; font-size: 8pt; border-top: 1px solid var(--border-soft); padding-top: 6mm; margin-bottom: 4mm;">
        <p style="font-size: 9.5pt; color: var(--text-dark); margin-bottom: 1.5mm;"><strong>{config.get("marca")}</strong> · {config.get("edicion")}</p>
        <p>{config.get("copyright")}</p>
      </div>

      <div class="sheet-page-footer">
        <span>{config.get("titulo")} · Cierre</span>
        <span>Página {page_num}</span>
      </div>
    </div>
    """
    paginas.append(p_final)
    indice.append({
        "num": page_num,
        "titulo": "Compromiso Familiar y Fuentes",
        "seccion": "Cierre"
    })

    total_paginas = len(paginas)

    # Serializar índice para JS
    indice_json = json.dumps(indice, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{config.get("titulo")} · Visor Editorial A4 Completo</title>
  <style>
    @font-face {{
      font-family: 'Fraunces';
      src: url('../diseno/fuentes/Fraunces.ttf') format('truetype');
      font-weight: 400 700;
      font-style: normal;
    }}
    @font-face {{
      font-family: 'Fraunces';
      src: url('../diseno/fuentes/Fraunces-Italic.ttf') format('truetype');
      font-weight: 400 700;
      font-style: italic;
    }}
    @font-face {{
      font-family: 'Nunito Sans';
      src: url('../diseno/fuentes/NunitoSans.ttf') format('truetype');
      font-weight: 300 800;
      font-style: normal;
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
    }}

    body {{
      font-family: 'Nunito Sans', sans-serif;
      color: var(--text-dark);
      background: #2a2d30;
      line-height: 1.5;
      font-size: 9.5pt;
      overflow-x: hidden;
      min-height: 100vh;
    }}

    /* BARRA SUPERIOR DE HERRAMIENTAS Y NAVEGACIÓN */
    .viewer-toolbar {{
      position: sticky;
      top: 0;
      z-index: 1000;
      background: rgba(30, 32, 34, 0.96);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid #44494e;
      color: #e5e7eb;
      padding: 0.6rem 1.2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }}

    .toolbar-left {{
      display: flex;
      align-items: center;
      gap: 1rem;
    }}

    .book-tag {{
      font-family: 'Fraunces', serif;
      font-size: 1.05rem;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .book-tag span {{
      color: var(--accent-terracotta);
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-family: 'Nunito Sans', sans-serif;
      font-weight: 800;
      background: rgba(200, 90, 50, 0.18);
      padding: 2px 8px;
      border-radius: 4px;
      border: 1px solid rgba(200, 90, 50, 0.35);
    }}

    .toolbar-center {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
      background: #181a1b;
      padding: 0.3rem 0.6rem;
      border-radius: 8px;
      border: 1px solid #3d4247;
    }}

    .btn-nav {{
      background: #2f343a;
      border: 1px solid #484f57;
      color: #ffffff;
      padding: 0.35rem 0.8rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.88rem;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      transition: all 0.15s ease;
    }}
    .btn-nav:hover {{
      background: var(--accent-terracotta);
      border-color: var(--accent-terracotta);
    }}
    .btn-nav:disabled {{
      opacity: 0.35;
      cursor: not-allowed;
      background: #24272a;
      border-color: #383c40;
    }}

    .page-input-wrap {{
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.88rem;
      color: #b3bac2;
      font-weight: 600;
    }}
    .page-input {{
      width: 52px;
      padding: 0.25rem 0.4rem;
      text-align: center;
      font-weight: 700;
      background: #2a2d31;
      border: 1px solid #4a5159;
      color: #ffffff;
      border-radius: 5px;
      font-size: 0.9rem;
    }}

    .toolbar-right {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}

    .view-select, .section-select {{
      background: #2a2d31;
      border: 1px solid #484f57;
      color: #ffffff;
      padding: 0.35rem 0.65rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      max-width: 260px;
    }}
    .view-select:focus, .section-select:focus {{
      outline: 2px solid var(--accent-terracotta);
    }}

    /* CONTENEDOR PRINCIPAL DEL VISOR */
    .viewer-stage {{
      padding: 2rem 1rem 4rem;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      min-height: calc(100vh - 65px);
    }}

    /* HOJAS A4 REALES (EDITORIALES) */
    .sheet-a4 {{
      width: 210mm;
      min-height: 297mm;
      max-height: 297mm;
      padding: 14mm 16mm 14mm 16mm;
      background: #ffffff;
      box-shadow: 0 14px 40px rgba(0,0,0,0.35), 0 2px 6px rgba(0,0,0,0.18);
      border-radius: 3px;
      position: relative;
      overflow: hidden;
      display: none;
      flex-direction: column;
      justify-content: space-between;
      color: var(--text-dark);
      background-clip: padding-box;
    }}

    .sheet-a4.active {{
      display: flex !important;
      animation: fadeIn 0.15s ease-out;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0.7; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* MODO SCROLL CONTINUO */
    body.mode-scroll .viewer-stage {{
      flex-direction: column;
      align-items: center;
      gap: 2rem;
    }}
    body.mode-scroll .sheet-a4 {{
      display: flex !important;
    }}

    /* MODO DOBLE PÁGINA (SPREAD) */
    body.mode-spread .viewer-stage {{
      flex-direction: row;
      justify-content: center;
      gap: 1.5mm;
    }}
    body.mode-spread .sheet-a4 {{
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }}

    /* PIE DE PÁGINA DE LA HOJA A4 */
    .sheet-page-footer {{
      margin-top: auto;
      padding-top: 3mm;
      border-top: 1px solid var(--border-soft);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 7.5pt;
      color: #888;
      font-family: 'Nunito Sans', sans-serif;
    }}

    /* PORTADA */
    .portada-sheet {{
      background: var(--bg-cream);
      padding: 0;
    }}
    .portada-content {{
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 20mm 20mm;
      text-align: center;
    }}
    .portada-badge {{
      display: inline-block;
      font-size: 8.5pt;
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
      margin-bottom: 3.5mm;
    }}
    .portada-subtitle {{
      font-size: 12.5pt;
      color: var(--text-muted);
      max-width: 500px;
      margin: 0 auto 6mm;
      line-height: 1.4;
    }}
    .portada-img-wrap {{
      max-width: 360px;
      margin: 0 auto;
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 8px 24px rgba(0,0,0,0.08);
      border: 1px solid var(--border-soft);
    }}
    .portada-img-wrap img {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .portada-footer {{
      margin-top: 6mm;
      font-size: 8pt;
      color: #777;
      border-top: 1px solid var(--border-soft);
      padding-top: 3.5mm;
    }}

    /* SECCIONES EDITORIALES */
    .section-title {{
      font-family: 'Fraunces', serif;
      font-size: 19pt;
      color: var(--accent-terracotta);
      border-bottom: 2px solid var(--accent-terracotta-light);
      padding-bottom: 2mm;
      margin-bottom: 3.5mm;
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
      font-size: 8.8pt;
      line-height: 1.45;
    }}
    .editorial-box p:last-child {{ margin-bottom: 0; }}

    .highlight-card {{
      background: #ffffff;
      border-left: 3px solid var(--accent-terracotta);
      padding: 2.5mm 3.5mm;
      border-radius: 0 6px 6px 0;
      margin: 2.5mm 0;
      font-size: 8.5pt;
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
      padding: 2.5mm 3mm;
      font-size: 8pt;
    }}
    .mini-card h4 {{
      font-family: 'Fraunces', serif;
      font-size: 9pt;
      color: var(--accent-terracotta);
      margin-bottom: 1mm;
    }}

    /* CALENDARIO */
    .cal-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 2.5mm;
      font-size: 8pt;
    }}
    .cal-table th {{
      background: var(--accent-sage);
      color: #ffffff;
      padding: 2mm 2.5mm;
      font-weight: 700;
      text-align: left;
      font-size: 8pt;
    }}
    .cal-table td {{
      border: 1px solid var(--border-soft);
      padding: 1.8mm 2.2mm;
      vertical-align: top;
    }}
    .cal-table tr:nth-child(even) {{
      background: #faf8f5;
    }}
    .cal-day-num {{
      font-weight: 800;
      color: var(--accent-terracotta);
    }}
    .cal-tag {{
      display: inline-block;
      font-size: 6.5pt;
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 3px;
      margin-left: 2px;
    }}
    .tag-sobra {{ background: #fef3c7; color: #92400e; }}
    .tag-freezer {{ background: #e0f2fe; color: #075985; }}
    .tag-doble {{ background: #dcfce7; color: #166534; }}

    /* PÁGINA DE RECETA */
    .recipe-header-pdf {{
      border-bottom: 2px solid var(--border-soft);
      padding-bottom: 2mm;
      margin-bottom: 2.5mm;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .recipe-title-pdf {{
      font-family: 'Fraunces', serif;
      font-size: 14.5pt;
      color: var(--text-dark);
      line-height: 1.15;
    }}
    .recipe-pills {{
      display: flex;
      gap: 2mm;
    }}
    .pill-pdf {{
      font-size: 7.5pt;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 50px;
      background: var(--bg-cream);
      border: 1px solid var(--border-soft);
    }}
    .pill-pdf.time {{ background: var(--accent-sage-light); color: var(--accent-sage); }}
    .pill-pdf.cal {{ background: var(--accent-terracotta-light); color: var(--accent-terracotta); }}

    .recipe-img-box {{
      width: 175px;
      height: 175px;
      margin: 0 auto 2.5mm;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border-soft);
      background: var(--bg-cream);
      display: flex;
      justify-content: center;
      align-items: center;
      flex-shrink: 0;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .recipe-img-box img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }}

    /* PLACEHOLDER TRANSPARENTE CUANDO FALTA IMAGEN (ESTADO REAL) */
    .recipe-img-box.pending-art {{
      flex-direction: column;
      border: 1.5px dashed #d5cbbf;
      background: #fbf8f3;
      padding: 1rem;
      text-align: center;
    }}
    .pending-icon {{
      font-size: 1.6rem;
      margin-bottom: 0.3rem;
    }}
    .pending-title {{
      font-family: 'Fraunces', serif;
      font-size: 8.5pt;
      font-weight: 700;
      color: var(--accent-sage);
      margin-bottom: 0.2rem;
    }}
    .pending-sub {{
      font-size: 6.8pt;
      color: #8c857b;
      line-height: 1.25;
    }}

    .recipe-layout-grid {{
      display: grid;
      grid-template-columns: 1fr 1.4fr;
      gap: 4.5mm;
      flex-grow: 1;
    }}
    .col-title {{
      font-size: 8pt;
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.08em;
      color: var(--accent-sage);
      margin-bottom: 1.2mm;
      border-bottom: 1px solid var(--border-soft);
      padding-bottom: 0.8mm;
    }}
    .ing-pdf-list {{
      list-style: none;
      font-size: 8.2pt;
    }}
    .ing-pdf-list li {{
      padding: 0.8mm 0;
      border-bottom: 1px dotted var(--border-soft);
      display: flex;
      justify-content: space-between;
    }}
    .steps-pdf-list {{
      padding-left: 3.5mm;
      font-size: 8.2pt;
    }}
    .steps-pdf-list li {{
      margin-bottom: 1.2mm;
      line-height: 1.32;
    }}

    .cue-pdf {{
      background: var(--accent-sage-light);
      border-left: 3px solid var(--accent-sage);
      padding: 1.8mm 2.5mm;
      border-radius: 0 4px 4px 0;
      font-size: 7.8pt;
      margin-top: 2mm;
      color: #1a3325;
    }}
    .variants-pdf-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2.2mm;
      margin-top: 2mm;
    }}
    .var-pdf-box {{
      background: #fcfbf9;
      border: 1px solid var(--border-soft);
      border-radius: 4px;
      padding: 1.8mm;
      font-size: 7.3pt;
      line-height: 1.22;
    }}
    .var-pdf-box strong {{
      display: block;
      color: var(--accent-terracotta);
      font-size: 6.8pt;
      text-transform: uppercase;
      margin-bottom: 0.4mm;
    }}
    .sobra-pdf {{
      font-size: 7.3pt;
      color: #666;
      margin-top: 1.8mm;
      border-top: 1px dashed var(--border-soft);
      padding-top: 1.2mm;
    }}

    /* LISTAS DE COMPRAS */
    .shop-sectors-pdf {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3.5mm;
      margin-top: 2.5mm;
    }}
    .shop-sec-col h4 {{
      font-size: 7.8pt;
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.06em;
      color: var(--accent-sage);
      border-bottom: 1px solid var(--border-soft);
      padding-bottom: 0.8mm;
      margin-bottom: 1.2mm;
    }}
    .shop-item-pdf {{
      font-size: 7.8pt;
      padding: 0.7mm 0;
      display: flex;
      gap: 1.8mm;
    }}
    .check-box-pdf {{
      display: inline-block;
      width: 9px;
      height: 9px;
      border: 1px solid #888;
      border-radius: 2px;
      margin-top: 2px;
      flex-shrink: 0;
    }}
    .alacena-pdf {{
      background: #fdfaf5;
      border: 1px solid #eedec8;
      border-left: 3px solid var(--accent-mustard);
      border-radius: 4px;
      padding: 2.2mm 3.2mm;
      margin-top: 3.5mm;
      font-size: 7.8pt;
    }}

    /* ATAJOS Y ESTADO FLOTANTE */
    .status-toast {{
      position: fixed;
      bottom: 1rem;
      right: 1rem;
      background: rgba(20, 22, 24, 0.92);
      backdrop-filter: blur(8px);
      color: #e2e8f0;
      padding: 0.5rem 0.9rem;
      border-radius: 8px;
      font-size: 0.78rem;
      border: 1px solid #3c4147;
      display: flex;
      align-items: center;
      gap: 0.8rem;
      z-index: 1000;
    }}
    .status-badge {{
      background: #2b3931;
      color: #72d59b;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 0.72rem;
    }}

    @media print {{
      .viewer-toolbar, .status-toast {{ display: none !important; }}
      body {{ background: #ffffff !important; }}
      .viewer-stage {{ padding: 0 !important; }}
      .sheet-a4 {{
        box-shadow: none !important;
        margin: 0 !important;
        page-break-after: always !important;
        break-after: page !important;
        display: flex !important;
      }}
    }}
  </style>
</head>
<body>

  <!-- BARRA DE HERRAMIENTAS INTERACTIVA -->
  <header class="viewer-toolbar">
    <div class="toolbar-left">
      <div class="book-tag">
        📖 {config.get("titulo")}
        <span>A4 Editorial</span>
      </div>
    </div>

    <div class="toolbar-center">
      <button class="btn-nav" id="btn-first" title="Primera página (Home)">⏮</button>
      <button class="btn-nav" id="btn-prev" title="Página anterior (←)">◀ Anterior</button>
      <div class="page-input-wrap">
        <span>Pág</span>
        <input type="number" id="page-num-input" class="page-input" min="1" max="{total_paginas}" value="1">
        <span>/ {total_paginas}</span>
      </div>
      <button class="btn-nav" id="btn-next" title="Página siguiente (→)">Siguiente ▶</button>
      <button class="btn-nav" id="btn-last" title="Última página (End)">⏭</button>
    </div>

    <div class="toolbar-right">
      <select id="section-jump" class="section-select" title="Saltar a sección">
        <option value="" disabled selected>📑 Índice del Ebook...</option>
      </select>

      <select id="view-mode" class="view-select">
        <option value="single">📄 Página Individual</option>
        <option value="spread">📖 Doble Página</option>
        <option value="scroll">📜 Tira Continua</option>
      </select>

      <a href="index.html" class="btn-nav" style="text-decoration:none; background:#24362b; border-color:#385845;" title="Cambiar a vista web interactiva">
        🌐 Vista Web
      </a>
    </div>
  </header>

  <!-- ESCENARIO DEL VISOR -->
  <main class="viewer-stage" id="stage">
    {"".join(paginas)}
  </main>

  <!-- ESTADO DEL PROYECTO FLOTANTE -->
  <div class="status-toast">
    <span>Ilustraciones: <strong style="color:#72d59b;">{ilustradas_count} listas</strong> ({ilustradas_count}/{len(recetas)})</span>
    <span>Pendientes por cuota: <strong style="color:#f6ad55;">{pendientes_count}</strong></span>
    <span class="status-badge">Total {total_paginas} págs</span>
  </div>

  <script>
    const totalPages = {total_paginas};
    const indice = {indice_json};
    let currentPage = 1;
    let viewMode = 'single';

    const sheets = Array.from(document.querySelectorAll('.sheet-a4'));
    const pageInput = document.getElementById('page-num-input');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const btnFirst = document.getElementById('btn-first');
    const btnLast = document.getElementById('btn-last');
    const sectionSelect = document.getElementById('section-jump');
    const viewSelect = document.getElementById('view-mode');

    // Poblar dropdown de secciones
    let currentSec = "";
    indice.forEach(item => {{
      if (item.seccion !== currentSec) {{
        currentSec = item.seccion;
        const optgroup = document.createElement('optgroup');
        optgroup.label = currentSec.toUpperCase();
        sectionSelect.appendChild(optgroup);
      }}
      const opt = document.createElement('option');
      opt.value = item.num;
      const tag = item.tiene_arte === false ? " ⏳" : (item.tiene_arte === true ? " ✓" : "");
      opt.textContent = `Pág ${{item.num}}: ${{item.titulo}}${{tag}}`;
      sectionSelect.lastElementChild.appendChild(opt);
    }});

    function updateView() {{
      document.body.classList.remove('mode-single', 'mode-spread', 'mode-scroll');
      document.body.classList.add('mode-' + viewMode);

      sheets.forEach(s => s.classList.remove('active'));

      if (viewMode === 'single') {{
        const sheet = sheets[currentPage - 1];
        if (sheet) sheet.classList.add('active');
        window.scrollTo({{ top: 0, behavior: 'instant' }});
      }} else if (viewMode === 'spread') {{
        // Si es portada (pág 1), se muestra sola; luego pares e impares juntos
        if (currentPage === 1) {{
          sheets[0].classList.add('active');
        }} else {{
          const p1 = (currentPage % 2 === 0) ? currentPage : currentPage - 1;
          const p2 = p1 + 1;
          if (sheets[p1 - 1]) sheets[p1 - 1].classList.add('active');
          if (sheets[p2 - 1]) sheets[p2 - 1].classList.add('active');
        }}
        window.scrollTo({{ top: 0, behavior: 'instant' }});
      }} else if (viewMode === 'scroll') {{
        const target = sheets[currentPage - 1];
        if (target) {{
          target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
      }}

      pageInput.value = currentPage;
      btnPrev.disabled = (currentPage <= 1);
      btnFirst.disabled = (currentPage <= 1);
      btnNext.disabled = (currentPage >= totalPages);
      btnLast.disabled = (currentPage >= totalPages);

      // Sincronizar dropdown
      sectionSelect.value = currentPage;
    }}

    function goToPage(n) {{
      n = Math.max(1, Math.min(totalPages, parseInt(n) || 1));
      currentPage = n;
      updateView();
    }}

    btnPrev.addEventListener('click', () => goToPage(viewMode === 'spread' && currentPage > 2 ? currentPage - 2 : currentPage - 1));
    btnNext.addEventListener('click', () => goToPage(viewMode === 'spread' && currentPage > 1 ? currentPage + 2 : currentPage + 1));
    btnFirst.addEventListener('click', () => goToPage(1));
    btnLast.addEventListener('click', () => goToPage(totalPages));

    pageInput.addEventListener('change', (e) => goToPage(e.target.value));

    sectionSelect.addEventListener('change', (e) => {{
      if (e.target.value) {{
        goToPage(e.target.value);
      }}
    }});

    viewSelect.addEventListener('change', (e) => {{
      viewMode = e.target.value;
      updateView();
    }});

    // Atajos de teclado: Flechas, PageUp, PageDown, Home, End
    window.addEventListener('keydown', (e) => {{
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {{
        e.preventDefault();
        btnNext.click();
      }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
        e.preventDefault();
        btnPrev.click();
      }} else if (e.key === 'Home') {{
        e.preventDefault();
        goToPage(1);
      }} else if (e.key === 'End') {{
        e.preventDefault();
        goToPage(totalPages);
      }}
    }});

    // Iniciar en página 1
    updateView();
  </script>
</body>
</html>
"""
    SALIDA.mkdir(exist_ok=True)
    visor_out = SALIDA / "visor.html"
    visor_out.write_text(html, encoding="utf-8")
    print("✅ Visor Editorial A4 generado exitosamente en:", visor_out)
    return visor_out

if __name__ == "__main__":
    generar_visor()

