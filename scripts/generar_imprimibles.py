"""Generador del Pack de Imprimibles A4 (PDF independiente)
Contiene 6 herramientas prácticas de alta calidad listas para imprimir y usar en el hogar:
1. Planificador Semanal de Comidas (con columna de Extras y alerta 'Cocinar de más hoy')
2. Inventario Inteligente (con recuadro 'Usar primero esta semana / Vence pronto')
3. Mis 5 Comidas de Emergencia (con amplio espacio para ingredientes comodín)
4. Lista de Compras en Blanco por Sector (16-18 renglones con casilleros 'Ya lo tengo' y 'Comprar')
5. Nuestro Compromiso Familiar de 30 Días (con fecha libre para cualquier año)
6. Calendario de 30 Días para la Heladera (vista mensual con almuerzo, cena y batch cooking)
"""

import subprocess
import sys
from pathlib import Path
import json
import pypdf

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "salida"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

sys.path.insert(0, str(RAIZ / "scripts"))
import motor

def generar_html():
    config, recetas, cal = motor.cargar()
    
    # Preparamos los datos del calendario para la plantilla 6
    sobras_map = {
        (5, "almuerzo"): "Sobras del chili (cocinado el día 4)",
        (11, "almuerzo"): "Sobras del cerdo agridulce (cocinado el día 10)",
        (12, "cena"): "Albóndigas del freezer (cocinadas el día 7)",
        (15, "almuerzo"): "Sobras de las milanesas (cocinadas el día 14)",
        (15, "cena"): "Sobras del guiso de lentejas (cocinado el día 14)",
        (26, "almuerzo"): "Sobras del chili (cocinado el día 25)",
    }
    dias_cal = []
    for d in cal["dias"]:
        alm = sobras_map.get((d["dia"], "almuerzo")) or recetas.get(d["almuerzo"].get("receta", ""), {}).get("nombre", "")
        cen = sobras_map.get((d["dia"], "cena")) or recetas.get(d["cena"].get("receta", ""), {}).get("nombre", "")
        # Simplificamos nombres para que entren perfecto en la casilla
        alm_short = alm.replace(" con ensalada de tomate", "").replace(", zanahoria y zapallito", "")
        cen_short = cen.replace(" con ensalada de tomate", "").replace(", zanahoria y zapallito", "")
        nb = d.get("nota_batch", "")
        batch_badge = ""
        if "pollo" in nb.lower():
            if d["dia"] == 6:
                batch_badge = "🍗 Base pollo (900g)"
            elif d["dia"] == 21:
                batch_badge = "🍗 Base pollo (1,3kg)"
            else:
                batch_badge = "🍗 Base pollo"
        elif "arroz" in nb.lower():
            batch_badge = "🍚 Arroz extra (450g)"
        dias_cal.append({
            "dia": d["dia"],
            "alm": alm_short,
            "cen": cen_short,
            "badge": batch_badge
        })

    # Renglones vacíos para listas e inventario
    def make_rows_checkbox(count, rubro_name=""):
        rows = ""
        for _ in range(count):
            rows += f"""
            <div class="row-checkbox">
              <span class="box-tengo" title="Ya lo tengo"></span>
              <span class="box-comprar" title="Comprar"></span>
              <span class="line-text"></span>
            </div>
            """
        return rows

    def make_rows_inventory(count):
        rows = ""
        for _ in range(count):
            rows += """
            <div class="row-inventory">
              <span class="inv-check"></span>
              <span class="inv-item"></span>
              <span class="inv-qty"></span>
              <span class="inv-date"></span>
            </div>
            """
        return rows

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Pack de imprimibles · 30 días sin preguntarte qué cocinar</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 10mm 12mm 12mm 12mm;
      @bottom-center {{
        content: "30 días sin preguntarte qué cocinar · Saso Digital · Pack de imprimibles";
        font-size: 7.5pt;
        color: #888;
      }}
    }}
    *, *:before, *:after {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Nunito Sans", sans-serif;
      color: #2b2b2b;
      margin: 0;
      padding: 0;
      background: #fff;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    .sheet {{
      page-break-after: always;
      height: 100%;
      min-height: 275mm;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-sizing: border-box;
    }}
    .sheet:last-child {{
      page-break-after: avoid;
    }}
    .header {{
      border-bottom: 2px solid #E07A5F;
      padding-bottom: 2.5mm;
      margin-bottom: 3.5mm;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .header-left .tag {{
      font-size: 7.5pt;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #E07A5F;
      margin-bottom: 1mm;
      display: block;
    }}
    .header-left .title {{
      font-size: 15pt;
      font-weight: 800;
      color: #3D405B;
      margin: 0;
      line-height: 1.1;
    }}
    .header-right {{
      text-align: right;
      font-size: 8.5pt;
      color: #666;
    }}
    .header-right strong {{
      color: #333;
    }}
    .instructions {{
      font-size: 8pt;
      color: #555;
      background: #fdfaf6;
      border: 1px solid #f0e6da;
      border-left: 3.5px solid #E07A5F;
      border-radius: 4px;
      padding: 2mm 3mm;
      margin-bottom: 3.5mm;
      line-height: 1.35;
    }}

    /* PLANTILLA 1: PLANIFICADOR SEMANAL */
    .planner-table {{
      width: 100%;
      border-collapse: collapse;
      flex-grow: 1;
      margin-bottom: 3mm;
    }}
    .planner-table th {{
      background: #3D405B;
      color: #fff;
      font-size: 8pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 2.2mm 2mm;
      border: 1px solid #2b2d42;
      text-align: left;
    }}
    .planner-table td {{
      border: 1px solid #cbd5e1;
      padding: 2.5mm 3mm;
      vertical-align: top;
      font-size: 8pt;
      height: 25.5mm;
    }}
    .planner-day {{
      font-weight: 800;
      color: #E07A5F;
      font-size: 9.5pt;
      margin-bottom: 1.5mm;
      display: flex;
      justify-content: space-between;
    }}
    .planner-line {{
      border-bottom: 1px dashed #e2e8f0;
      height: 7.5mm;
      margin-bottom: 1.5mm;
    }}
    .planner-batch-box {{
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-radius: 4px;
      padding: 1.5mm 2mm;
      font-size: 7.5pt;
      color: #92400e;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .planner-batch-box strong {{
      display: block;
      color: #b45309;
      font-size: 7.5pt;
      margin-bottom: 1mm;
    }}
    .planner-batch-extra-line {{
      border-bottom: 1px dashed #fcd34d;
      height: 5.5mm;
      margin-top: 1mm;
    }}
    .planner-notes {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 5px;
      padding: 2.5mm 3.5mm;
      font-size: 8pt;
    }}
    .planner-notes-lines {{
      display: flex;
      gap: 4mm;
      margin-top: 1.5mm;
    }}
    .planner-notes-line {{
      flex: 1;
      border-bottom: 1px solid #cbd5e1;
      height: 5.5mm;
    }}

    /* PLANTILLA 2: INVENTARIO INTELIGENTE */
    .urgent-box {{
      background: #fff5f5;
      border: 2px solid #feb2b2;
      border-radius: 6px;
      padding: 3mm 4mm;
      margin-bottom: 4mm;
    }}
    .urgent-box h3 {{
      margin: 0 0 2mm 0;
      color: #c53030;
      font-size: 9.5pt;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      display: flex;
      justify-content: space-between;
    }}
    .urgent-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2.5mm 6mm;
    }}
    .urgent-row {{
      display: flex;
      align-items: center;
      gap: 2mm;
      border-bottom: 1px dashed #feb2b2;
      padding-bottom: 1mm;
      height: 6mm;
    }}
    .urgent-box-sq {{
      width: 11px;
      height: 11px;
      border: 1.5px solid #e53e3e;
      border-radius: 2px;
      display: inline-block;
      flex-shrink: 0;
    }}
    .inventory-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 3.5mm;
      flex-grow: 1;
    }}
    .inv-col {{
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      background: #ffffff;
      overflow: hidden;
    }}
    .inv-col-header {{
      background: #edf2f7;
      border-bottom: 2px solid #cbd5e1;
      padding: 2.2mm 2.5mm;
      font-size: 8.5pt;
      font-weight: 800;
      color: #2d3748;
      display: flex;
      justify-content: space-between;
    }}
    .inv-col-titles {{
      display: flex;
      font-size: 6.8pt;
      font-weight: 700;
      color: #718096;
      padding: 1mm 2mm;
      border-bottom: 1px solid #e2e8f0;
      background: #f8fafc;
    }}
    .inv-col-titles span:nth-child(1) {{ width: 14px; }}
    .inv-col-titles span:nth-child(2) {{ flex: 1; }}
    .inv-col-titles span:nth-child(3) {{ width: 28px; text-align: center; }}
    .inv-col-titles span:nth-child(4) {{ width: 26px; text-align: right; }}
    .row-inventory {{
      display: flex;
      align-items: center;
      border-bottom: 1px solid #f1f5f9;
      height: 10.5mm;
      padding: 0 2mm;
      gap: 1.5mm;
    }}
    .inv-check {{
      width: 10px;
      height: 10px;
      border: 1px solid #a0aec0;
      border-radius: 2px;
      display: inline-block;
      flex-shrink: 0;
    }}
    .inv-item {{
      flex: 1;
      border-bottom: 1px dotted #e2e8f0;
      height: 5mm;
    }}
    .inv-qty {{
      width: 26px;
      border-bottom: 1px dotted #e2e8f0;
      height: 5mm;
    }}
    .inv-date {{
      width: 24px;
      border-bottom: 1px dotted #e2e8f0;
      height: 5mm;
    }}

    /* PLANTILLA 3: MIS 5 COMIDAS DE EMERGENCIA */
    .emergency-cards {{
      display: flex;
      flex-direction: column;
      gap: 3.5mm;
      flex-grow: 1;
    }}
    .emer-card {{
      border: 1.5px solid #cbd5e1;
      border-left: 5px solid #E07A5F;
      border-radius: 6px;
      padding: 2.8mm 4mm;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 44mm;
    }}
    .emer-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 1.5mm;
      margin-bottom: 1.5mm;
    }}
    .emer-num {{
      font-size: 9pt;
      font-weight: 800;
      color: #E07A5F;
    }}
    .emer-name-line {{
      flex: 1;
      margin: 0 4mm;
      border-bottom: 1px solid #94a3b8;
      height: 5mm;
    }}
    .emer-time {{
      font-size: 7.5pt;
      color: #64748b;
      font-weight: 600;
    }}
    .emer-body {{
      display: grid;
      grid-template-columns: 1.1fr 1fr;
      gap: 4mm;
    }}
    .emer-col-title {{
      font-size: 7.2pt;
      font-weight: 700;
      text-transform: uppercase;
      color: #475569;
      margin-bottom: 1mm;
    }}
    .emer-lines {{
      display: flex;
      flex-direction: column;
      gap: 2mm;
    }}
    .emer-line {{
      border-bottom: 1px dashed #cbd5e1;
      height: 5mm;
    }}

    /* PLANTILLA 4: LISTA DE COMPRAS POR SECTOR (TODOS LOS RUBROS CON 17 RENGLONES) */
    .shop-grid-3col {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 3.5mm;
      flex-grow: 1;
    }}
    .shop-grid-4col {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr 1fr;
      gap: 3mm;
      flex-grow: 1;
    }}
    .shop-box {{
      border: 1px solid #cbd5e1;
      border-radius: 5px;
      padding: 2mm 2.5mm;
      display: flex;
      flex-direction: column;
      background: #ffffff;
    }}
    .shop-box-title {{
      font-size: 8pt;
      font-weight: 800;
      color: #1e293b;
      border-bottom: 2px solid #E07A5F;
      padding-bottom: 1mm;
      margin-bottom: 1.2mm;
      display: flex;
      justify-content: space-between;
      align-items: center;
      white-space: nowrap;
    }}
    .shop-box-legend {{
      font-size: 6.2pt;
      color: #64748b;
      font-weight: 600;
    }}
    .row-checkbox {{
      display: flex;
      align-items: center;
      gap: 1.8mm;
      height: 8.2mm;
      border-bottom: 1px solid #f1f5f9;
    }}
    .box-tengo {{
      width: 9px;
      height: 9px;
      border: 1.5px solid #94a3b8;
      border-radius: 2px;
      display: inline-block;
      flex-shrink: 0;
    }}
    .box-comprar {{
      width: 9px;
      height: 9px;
      border: 1.5px solid #E07A5F;
      border-radius: 2px;
      display: inline-block;
      flex-shrink: 0;
    }}
    .line-text {{
      flex: 1;
      border-bottom: 1px dotted #cbd5e1;
      height: 4mm;
    }}
    .shop-tip-box {{
      background: #fdfaf6;
      border: 1px solid #e2e8f0;
      border-radius: 4px;
      padding: 1.8mm 3mm;
      font-size: 7.2pt;
      color: #555;
      margin-top: 2.5mm;
    }}

    /* PLANTILLA 5: COMPROMISO FAMILIAR */
    .pledge-card {{
      border: 2px solid #E07A5F;
      border-radius: 8px;
      padding: 5mm 7mm;
      background: #fdfaf6;
      flex-grow: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .pledge-title {{
      text-align: center;
      font-size: 16pt;
      font-weight: 800;
      color: #3D405B;
      margin: 0 0 2mm 0;
    }}
    .pledge-sub {{
      text-align: center;
      font-size: 9pt;
      color: #666;
      margin-bottom: 4mm;
    }}
    .pledge-date-row {{
      display: flex;
      justify-content: center;
      gap: 3mm;
      align-items: center;
      font-size: 9pt;
      font-weight: 700;
      margin-bottom: 4mm;
      color: #333;
    }}
    .pledge-date-line {{
      border-bottom: 1.5px solid #333;
      width: 60mm;
      height: 5mm;
      text-align: center;
      letter-spacing: 0.1em;
    }}
    .pledge-rules {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 4mm 5mm;
      margin-bottom: 4mm;
    }}
    .pledge-rule-item {{
      font-size: 8.8pt;
      color: #333;
      margin-bottom: 2.5mm;
      display: flex;
      gap: 2.5mm;
      line-height: 1.35;
    }}
    .pledge-signatures {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6mm 10mm;
      margin-top: 3mm;
    }}
    .pledge-sig-box {{
      border-bottom: 1.5px solid #94a3b8;
      height: 12mm;
      display: flex;
      align-items: flex-end;
      padding-bottom: 1mm;
      font-size: 7.5pt;
      color: #64748b;
    }}
    .pledge-reward {{
      background: #f0fdf4;
      border: 1.5px dashed #86efac;
      border-radius: 6px;
      padding: 3mm 4mm;
      margin-top: 3mm;
      font-size: 8.5pt;
      color: #166534;
    }}
    .pledge-reward-line {{
      border-bottom: 1px dashed #22c55e;
      height: 5.5mm;
      margin-top: 1mm;
    }}

    /* PLANTILLA 6: CALENDARIO DE 30 DÍAS PARA LA HELADERA */
    .cal-grid-month {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 2mm;
      flex-grow: 1;
      margin-bottom: 2mm;
    }}
    .cal-day-card {{
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      padding: 1.8mm 2mm;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 38mm;
      box-sizing: border-box;
    }}
    .cal-day-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 1mm;
      margin-bottom: 1mm;
    }}
    .cal-day-num-badge {{
      font-weight: 800;
      font-size: 7.5pt;
      color: #ffffff;
      background: #3D405B;
      border-radius: 3px;
      padding: 1px 4px;
    }}
    .cal-meal-slot {{
      font-size: 6.8pt;
      line-height: 1.15;
      color: #333;
      margin-bottom: 1mm;
    }}
    .cal-meal-slot strong {{
      color: #E07A5F;
      font-size: 6.5pt;
      text-transform: uppercase;
      display: block;
    }}
    .cal-batch-badge {{
      background: #fef3c7;
      color: #92400e;
      border: 1px solid #fde68a;
      border-radius: 2px;
      font-size: 6pt;
      font-weight: 800;
      padding: 1px 3px;
      text-align: center;
      margin-top: 1mm;
    }}
  </style>
</head>
<body>

  <!-- ==================== PLANTILLA 1 ==================== -->
  <section class="sheet">
    <div>
      <div class="header">
        <div class="header-left">
          <span class="tag">Plantilla 1 · Planificación Semanal</span>
          <h1 class="title">Planificador Semanal de Comidas</h1>
        </div>
        <div class="header-right">
          Semana del: _____ / _____<br>
          <strong>Saso Digital · Edición 2026</strong>
        </div>
      </div>
      <div class="instructions">
        <strong>💡 Cómo usarlo:</strong> Pegalo en la puerta de la heladera. Completá el almuerzo, cena y extras de cada día. Usá la columna <strong>Cocinar de más hoy</strong> para anticipar el pollo cocido o arroz extra sin improvisar.
      </div>
    </div>

    <table class="planner-table">
      <thead>
        <tr>
          <th style="width: 13%;">Día</th>
          <th style="width: 25%;">☀️ Almuerzo</th>
          <th style="width: 25%;">🌙 Cena</th>
          <th style="width: 22%;">🍎 Extras (Desayuno / Vianda)</th>
          <th style="width: 15%;">💡 Cocinar de más hoy</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><div class="planner-day">LUNES</div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-batch-box"><strong>Base extra:</strong><span>[ ] Pollo / [ ] Arroz</span><div class="planner-batch-extra-line"></div></div></td>
        </tr>
        <tr>
          <td><div class="planner-day">MARTES</div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-batch-box"><strong>Base extra:</strong><span>[ ] Pollo / [ ] Arroz</span><div class="planner-batch-extra-line"></div></div></td>
        </tr>
        <tr>
          <td><div class="planner-day">MIÉRCOLES</div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-batch-box"><strong>Base extra:</strong><span>[ ] Pollo / [ ] Arroz</span><div class="planner-batch-extra-line"></div></div></td>
        </tr>
        <tr>
          <td><div class="planner-day">JUEVES</div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-batch-box"><strong>Base extra:</strong><span>[ ] Pollo / [ ] Arroz</span><div class="planner-batch-extra-line"></div></div></td>
        </tr>
        <tr>
          <td><div class="planner-day">VIERNES</div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-batch-box"><strong>Base extra:</strong><span>[ ] Pollo / [ ] Arroz</span><div class="planner-batch-extra-line"></div></div></td>
        </tr>
        <tr>
          <td><div class="planner-day">SÁBADO</div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-batch-box"><strong>Base extra:</strong><span>[ ] Pollo / [ ] Arroz</span><div class="planner-batch-extra-line"></div></div></td>
        </tr>
        <tr>
          <td><div class="planner-day">DOMINGO</div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-line"></div><div class="planner-line"></div></td>
          <td><div class="planner-batch-box"><strong>Base extra:</strong><span>[ ] Pollo / [ ] Arroz</span><div class="planner-batch-extra-line"></div></div></td>
        </tr>
      </tbody>
    </table>

    <div class="planner-notes">
      <strong>📝 Notas de la semana / compras imprevistas:</strong>
      <div class="planner-notes-lines">
        <div class="planner-notes-line"></div>
        <div class="planner-notes-line"></div>
      </div>
    </div>
  </section>

  <!-- ==================== PLANTILLA 2 ==================== -->
  <section class="sheet">
    <div>
      <div class="header">
        <div class="header-left">
          <span class="tag">Plantilla 2 · Paso 2 del Método</span>
          <h1 class="title">Inventario Inteligente del Hogar</h1>
        </div>
        <div class="header-right">
          Fecha de revisión: _____ / _____<br>
          <strong>Saso Digital · Edición 2026</strong>
        </div>
      </div>
      <div class="instructions">
        <strong>💡 Cómo usarlo:</strong> Dedicá 10 minutos antes de comprar. Anotá primero lo que <strong>vence pronto o debe usarse esta semana</strong>. Luego chequeá tus reservas de freezer, heladera y alacena para no comprar repetido.
      </div>
    </div>

    <!-- RECUADRO CENTRAL OBLIGATORIO: USAR PRIMERO ESTA SEMANA -->
    <div class="urgent-box">
      <h3>
        <span>🚨 Usar primero esta semana / Vence pronto</span>
        <span style="font-size: 7.5pt; text-transform:none; font-weight: normal; color:#742a2a;">Priorizá estos ingredientes en tu menú</span>
      </h3>
      <div class="urgent-grid">
        <div class="urgent-row"><span class="urgent-box-sq"></span><span style="flex:1;"></span><span style="font-size:7pt; color:#a0aec0;">Vence: ___/___</span></div>
        <div class="urgent-row"><span class="urgent-box-sq"></span><span style="flex:1;"></span><span style="font-size:7pt; color:#a0aec0;">Vence: ___/___</span></div>
        <div class="urgent-row"><span class="urgent-box-sq"></span><span style="flex:1;"></span><span style="font-size:7pt; color:#a0aec0;">Vence: ___/___</span></div>
        <div class="urgent-row"><span class="urgent-box-sq"></span><span style="flex:1;"></span><span style="font-size:7pt; color:#a0aec0;">Vence: ___/___</span></div>
      </div>
    </div>

    <div class="inventory-grid">
      <!-- FREEZER -->
      <div class="inv-col">
        <div class="inv-col-header">
          <span>🧊 FREEZER</span>
          <span style="font-size: 7pt; font-weight: normal; color:#718096;">Carnes, sobras, porciones</span>
        </div>
        <div class="inv-col-titles">
          <span></span><span>Alimento</span><span>Porc.</span><span>Fecha</span>
        </div>
        {make_rows_inventory(11)}
      </div>

      <!-- HELADERA -->
      <div class="inv-col">
        <div class="inv-col-header">
          <span>❄️ HELADERA</span>
          <span style="font-size: 7pt; font-weight: normal; color:#718096;">Lácteos, verduras, abiertos</span>
        </div>
        <div class="inv-col-titles">
          <span></span><span>Alimento</span><span>Cant.</span><span>Vence</span>
        </div>
        {make_rows_inventory(11)}
      </div>

      <!-- ALACENA -->
      <div class="inv-col">
        <div class="inv-col-header">
          <span>🥫 ALACENA</span>
          <span style="font-size: 7pt; font-weight: normal; color:#718096;">Legumbres, pastas, latas</span>
        </div>
        <div class="inv-col-titles">
          <span></span><span>Alimento</span><span>Stock</span><span>Vence</span>
        </div>
        {make_rows_inventory(11)}
      </div>
    </div>
  </section>

  <!-- ==================== PLANTILLA 3 ==================== -->
  <section class="sheet">
    <div>
      <div class="header">
        <div class="header-left">
          <span class="tag">Plantilla 3 · Estrategia Salvavidas</span>
          <h1 class="title">Mis 5 Comidas de Emergencia</h1>
        </div>
        <div class="header-right">
          Para días difíciles o sin tiempo<br>
          <strong>Saso Digital · Edición 2026</strong>
        </div>
      </div>
      <div class="instructions">
        <strong>💡 Cómo usarlo:</strong> Definí 5 platos rápidos (≤ 15 minutos) que a tu familia le gusten y cuyos ingredientes siempre estén en tu alacena o freezer. El día que se caiga el plan, elegí uno de esta lista en vez de delivery.
      </div>
    </div>

    <div class="emergency-cards">
      <!-- PLATO 1 -->
      <div class="emer-card">
        <div class="emer-header">
          <span class="emer-num">PLATO COMODÍN 1:</span>
          <span class="emer-name-line"></span>
          <span class="emer-time">⏱️ Tiempo total: _____ min</span>
        </div>
        <div class="emer-body">
          <div>
            <div class="emer-col-title">🥫 Ingredientes comodín (que siempre tengo):</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
          <div>
            <div class="emer-col-title">📝 Cómo lo resuelvo en 10-15 min:</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
        </div>
      </div>

      <!-- PLATO 2 -->
      <div class="emer-card">
        <div class="emer-header">
          <span class="emer-num">PLATO COMODÍN 2:</span>
          <span class="emer-name-line"></span>
          <span class="emer-time">⏱️ Tiempo total: _____ min</span>
        </div>
        <div class="emer-body">
          <div>
            <div class="emer-col-title">🥫 Ingredientes comodín (que siempre tengo):</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
          <div>
            <div class="emer-col-title">📝 Cómo lo resuelvo en 10-15 min:</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
        </div>
      </div>

      <!-- PLATO 3 -->
      <div class="emer-card">
        <div class="emer-header">
          <span class="emer-num">PLATO COMODÍN 3:</span>
          <span class="emer-name-line"></span>
          <span class="emer-time">⏱️ Tiempo total: _____ min</span>
        </div>
        <div class="emer-body">
          <div>
            <div class="emer-col-title">🥫 Ingredientes comodín (que siempre tengo):</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
          <div>
            <div class="emer-col-title">📝 Cómo lo resuelvo en 10-15 min:</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
        </div>
      </div>

      <!-- PLATO 4 -->
      <div class="emer-card">
        <div class="emer-header">
          <span class="emer-num">PLATO COMODÍN 4:</span>
          <span class="emer-name-line"></span>
          <span class="emer-time">⏱️ Tiempo total: _____ min</span>
        </div>
        <div class="emer-body">
          <div>
            <div class="emer-col-title">🥫 Ingredientes comodín (que siempre tengo):</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
          <div>
            <div class="emer-col-title">📝 Cómo lo resuelvo en 10-15 min:</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
        </div>
      </div>

      <!-- PLATO 5 -->
      <div class="emer-card">
        <div class="emer-header">
          <span class="emer-num">PLATO COMODÍN 5:</span>
          <span class="emer-name-line"></span>
          <span class="emer-time">⏱️ Tiempo total: _____ min</span>
        </div>
        <div class="emer-body">
          <div>
            <div class="emer-col-title">🥫 Ingredientes comodín (que siempre tengo):</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
          <div>
            <div class="emer-col-title">📝 Cómo lo resuelvo en 10-15 min:</div>
            <div class="emer-lines"><div class="emer-line"></div><div class="emer-line"></div></div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== PLANTILLA 4A: LISTA DE COMPRAS (PARTE 1) ==================== -->
  <section class="sheet">
    <div>
      <div class="header">
        <div class="header-left">
          <span class="tag">Plantilla 4 · Hoja 1 de 2</span>
          <h1 class="title">Lista de Compras · Frescos y Proteínas</h1>
        </div>
        <div class="header-right">
          Semana: _____ / _____<br>
          <strong>Casilleros: [ ] Ya lo tengo · [ ] Comprar</strong>
        </div>
      </div>
      <div class="instructions">
        <strong>🛒 Cómo usarla:</strong> Marcá primero con un tilde en <strong>[ ] Ya lo tengo</strong> lo que revisaste en tu inventario. Luego anotá en la línea lo que necesitás comprar y tildá <strong>[ ] Comprar</strong> en el súper o verdulería.
      </div>
    </div>

    <div class="shop-grid-3col">
      <!-- VERDULERÍA Y FRUTAS (17 RENGLONES) -->
      <div class="shop-box">
        <div class="shop-box-title">
          <span>🥕 Verdulería y Frutas</span>
          <span class="shop-box-legend">[Tengo] [Comprar]</span>
        </div>
        {make_rows_checkbox(17, "Verdulería")}
      </div>

      <!-- CARNES, POLLO, PESCADO Y HUEVOS (17 RENGLONES) -->
      <div class="shop-box">
        <div class="shop-box-title">
          <span>🥩 Carnes, Pollo, Pescado</span>
          <span class="shop-box-legend">[Tengo] [Comprar]</span>
        </div>
        {make_rows_checkbox(17, "Carnes")}
      </div>

      <!-- LÁCTEOS Y REFRIGERADOS (17 RENGLONES) -->
      <div class="shop-box">
        <div class="shop-box-title">
          <span>🧀 Lácteos y Quesos</span>
          <span class="shop-box-legend">[Tengo] [Comprar]</span>
        </div>
        {make_rows_checkbox(17, "Lácteos")}
      </div>
    </div>

    <div class="shop-tip-box">
      💡 <strong>Tip para frescos:</strong> Comprá carnes y pescados al final del recorrido para cuidar la cadena de frío. Verificá fechas de vencimiento de lácteos y quesos antes de pagar.
    </div>
  </section>

  <!-- ==================== PLANTILLA 4B: LISTA DE COMPRAS (PARTE 2) ==================== -->
  <section class="sheet">
    <div>
      <div class="header">
        <div class="header-left">
          <span class="tag">Plantilla 4 · Hoja 2 de 2</span>
          <h1 class="title">Lista de Compras · Almacén, Panificados, Freezer y Varios</h1>
        </div>
        <div class="header-right">
          Semana: _____ / _____<br>
          <strong>Casilleros: [ ] Ya lo tengo · [ ] Comprar</strong>
        </div>
      </div>
      <div class="instructions">
        <strong>🛒 Continuación de tu lista:</strong> Rubros de despensa seca, panificados, congelados y artículos varios para completar tu compra sin olvidar nada.
      </div>
    </div>

    <div class="shop-grid-4col">
      <!-- ALMACÉN Y PASTAS (17 RENGLONES) -->
      <div class="shop-box">
        <div class="shop-box-title">
          <span>🥫 Almacén y Pastas</span>
          <span class="shop-box-legend">[Tengo] [Comprar]</span>
        </div>
        {make_rows_checkbox(17, "Almacén")}
      </div>

      <!-- PANIFICADOS (17 RENGLONES) -->
      <div class="shop-box">
        <div class="shop-box-title">
          <span>🍞 Panificados y Tapas</span>
          <span class="shop-box-legend">[Tengo] [Comprar]</span>
        </div>
        {make_rows_checkbox(17, "Panificados")}
      </div>

      <!-- FREEZER (17 RENGLONES) -->
      <div class="shop-box">
        <div class="shop-box-title">
          <span>🧊 Freezer y Congelados</span>
          <span class="shop-box-legend">[Tengo] [Comprar]</span>
        </div>
        {make_rows_checkbox(17, "Freezer")}
      </div>

      <!-- OTROS / DESPENSA / LIMPIEZA (17 RENGLONES) -->
      <div class="shop-box">
        <div class="shop-box-title">
          <span>✨ Otros y Limpieza</span>
          <span class="shop-box-legend">[Tengo] [Comprar]</span>
        </div>
        {make_rows_checkbox(17, "Otros")}
      </div>
    </div>

    <div class="shop-tip-box">
      💡 <strong>Tip para despensa:</strong> Revisá los paquetes abiertos de arroz, polenta y fideos en tu alacena antes de salir para no comprar duplicados.
    </div>
  </section>

  <!-- ==================== PLANTILLA 5 ==================== -->
  <section class="sheet">
    <div>
      <div class="header">
        <div class="header-left">
          <span class="tag">Plantilla 5 · Motivación y Equipo</span>
          <h1 class="title">Nuestro Compromiso Familiar de 30 Días</h1>
        </div>
        <div class="header-right">
          Un pacto para comer mejor y sin estrés<br>
          <strong>Saso Digital · Edición 2026</strong>
        </div>
      </div>
    </div>

    <div class="pledge-card">
      <div>
        <h2 class="pledge-title">«En esta casa comemos rico, casero y en paz»</h2>
        <p class="pledge-sub">Nos comprometemos a acompañar el plan durante los próximos 30 días, compartiendo la mesa y simplificando la rutina diaria.</p>

        <div class="pledge-date-row">
          <span>Fecha de inicio del desafío:</span>
          <span class="pledge-date-line">___ / ___ / ________</span>
        </div>

        <div class="pledge-rules">
          <div class="pledge-rule-item">
            <span>🤝</span>
            <span><strong>Compartir la carga mental:</strong> la cocina no es tarea de una sola persona; todos podemos poner la mesa, guardar las sobras o lavar los platos.</span>
          </div>
          <div class="pledge-rule-item">
            <span>🥦</span>
            <span><strong>Curiosidad en el plato:</strong> probamos al menos un bocado de preparaciones nuevas antes de decir que no nos gusta, sin presiones ni enojos.</span>
          </div>
          <div class="pledge-rule-item">
            <span>💡</span>
            <span><strong>Flexibilidad y buen humor:</strong> si un día el plan cambia o sale una comida comodín de emergencia, lo celebramos sin culpa.</span>
          </div>
        </div>
      </div>

      <div>
        <div style="font-size: 8.5pt; font-weight: 700; color: #3D405B; margin-bottom: 2mm;">
          ✍️ Firmas de los integrantes del hogar:
        </div>
        <div class="pledge-signatures">
          <div class="pledge-sig-box">Firma 1:</div>
          <div class="pledge-sig-box">Firma 2:</div>
          <div class="pledge-sig-box">Firma 3:</div>
          <div class="pledge-sig-box">Firma 4:</div>
        </div>

        <div class="pledge-reward">
          <strong>🎉 Al completar los 30 días, nos regalamos este momento familiar:</strong>
          <div class="pledge-reward-line"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== PLANTILLA 6: CALENDARIO MENSUAL PARA LA HELADERA ==================== -->
  <section class="sheet">
    <div>
      <div class="header">
        <div class="header-left">
          <span class="tag">Plantilla 6 · Vista Mensual Completa</span>
          <h1 class="title">Calendario de 30 Días para la Heladera</h1>
        </div>
        <div class="header-right">
          Todo el mes de un vistazo<br>
          <strong>Saso Digital · Edición 2026</strong>
        </div>
      </div>
      <div class="instructions">
        <strong>📌 Pegalo en la heladera:</strong> Tené a la vista el almuerzo y la cena de cada día. Las etiquetas amarillas te avisan con anticipación qué día cocinar <strong>pollo extra</strong> o <strong>arroz extra</strong> para la comida siguiente.
      </div>
    </div>

    <div class="cal-grid-month">
      {"".join(f'''
      <div class="cal-day-card">
        <div class="cal-day-header">
          <span class="cal-day-num-badge">Día {d["dia"]}</span>
          {f'<span class="cal-batch-badge">{d["badge"]}</span>' if d["badge"] else ""}
        </div>
        <div>
          <div class="cal-meal-slot">
            <strong>☀️ Almuerzo</strong>
            {d["alm"]}
          </div>
          <div class="cal-meal-slot">
            <strong>🌙 Cena</strong>
            {d["cen"]}
          </div>
        </div>
      </div>
      ''' for d in dias_cal)}
    </div>

    <div style="background:#fdfaf6; border:1px solid #e2e8f0; border-radius:4px; padding:2mm 3mm; font-size:7.5pt; color:#666; display:flex; justify-content:space-between;">
      <span>🍗 <strong>Base de pollo:</strong> se cocina los días 6 (900 g crudos) y 21 (1,3 kg crudos).</span>
      <span>🍚 <strong>Arroz extra:</strong> se cocinan 450 g secos los días 3 y 24.</span>
      <span>🍎 <strong>Postre diario:</strong> fruta fresca o postre dulce según la semana.</span>
    </div>
  </section>

</body>
</html>"""
    return html

def compilar_pdf():
    html_content = generar_html()
    html_file = SALIDA / "pack_imprimibles.html"
    pdf_file = SALIDA / "30-dias-sin-preguntarte-que-cocinar_pack-imprimibles.pdf"
    
    html_file.write_text(html_content, encoding="utf-8")
    print(f"HTML generado en: {html_file}")
    
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
    
    with open(SALIDA / "chrome_imprimibles.log", "w") as log_file:
        subprocess.run(cmd, stdout=log_file, stderr=log_file, check=True)
    
    # Actualizar metadatos PDF
    reader = pypdf.PdfReader(str(pdf_file))
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    metadata = {
        "/Title": "Pack de imprimibles · 30 días sin preguntarte qué cocinar",
        "/Author": "Saso Digital",
        "/Subject": "Pack de plantillas imprimibles para planificación y compras",
        "/Creator": "Saso Digital",
        "/Producer": "Saso Digital",
    }
    writer.add_metadata(metadata)
    with open(pdf_file, "wb") as f_out:
        writer.write(f_out)

    print(f"PDF generado con éxito: {pdf_file} ({pdf_file.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    compilar_pdf()
