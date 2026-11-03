#!/usr/bin/env python3
"""Genera una vista previa web interactiva y editorial completa del ebook."""
import json
import math
from pathlib import Path
from collections import defaultdict, OrderedDict
import sys

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import motor

DATOS = RAIZ / "datos"
DISENO = RAIZ / "diseno"
SALIDA = RAIZ / "salida"

def render_html():
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

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{config.get("titulo", "30 días sin preguntarte qué cocinar")} · Edición Completa</title>
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
      --text-dark: #2c2f2e;
      --text-muted: #5e6462;
      --accent-terracotta: #c85a32;
      --accent-terracotta-light: #fbeee8;
      --accent-sage: #3f6b53;
      --accent-sage-light: #edf4ef;
      --accent-mustard: #d4972c;
      --accent-mustard-light: #fdf6e9;
      --border-soft: #e7dfd5;
      --shadow-sm: 0 2px 8px rgba(0,0,0,0.04);
      --shadow-md: 0 6px 18px rgba(0,0,0,0.06);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Nunito Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-cream);
      color: var(--text-dark);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}

    /* Top Nav */
    .top-nav {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(250, 247, 242, 0.96);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border-soft);
      padding: 0.8rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.8rem;
    }}
    .nav-brand {{
      font-family: 'Fraunces', serif;
      font-weight: 700;
      font-size: 1.15rem;
      color: var(--accent-terracotta);
      text-decoration: none;
    }}
    .nav-links {{
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }}
    .nav-links a {{
      text-decoration: none;
      color: var(--text-dark);
      font-weight: 600;
      font-size: 0.85rem;
      transition: color 0.2s;
    }}
    .nav-links a:hover {{
      color: var(--accent-terracotta);
    }}

    .container {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 2.5rem 1.5rem;
    }}

    /* Hero / Cover Section */
    .hero-card {{
      background: var(--bg-card);
      border-radius: 16px;
      border: 1px solid var(--border-soft);
      box-shadow: var(--shadow-md);
      overflow: hidden;
      margin-bottom: 3.5rem;
      display: grid;
      grid-template-columns: 1fr 1.2fr;
    }}
    @media (max-width: 768px) {{
      .hero-card {{ grid-template-columns: 1fr; }}
    }}
    .hero-img-wrap {{
      background: #eee6db;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }}
    .hero-img-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      max-height: 540px;
    }}
    .hero-body {{
      padding: 3rem;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .badge {{
      display: inline-block;
      align-self: flex-start;
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.08em;
      padding: 0.35rem 0.75rem;
      border-radius: 50px;
      background: var(--accent-terracotta-light);
      color: var(--accent-terracotta);
      margin-bottom: 1.2rem;
    }}
    h1.hero-title {{
      font-family: 'Fraunces', serif;
      font-size: 2.6rem;
      font-weight: 700;
      line-height: 1.15;
      color: var(--text-dark);
      margin-bottom: 1rem;
    }}
    p.hero-subtitle {{
      font-size: 1.15rem;
      color: var(--text-muted);
      margin-bottom: 1.5rem;
    }}
    .hero-meta {{
      font-size: 0.85rem;
      color: var(--text-muted);
      border-top: 1px solid var(--border-soft);
      padding-top: 1.2rem;
      line-height: 1.5;
    }}

    /* Section Headers */
    .section-head {{
      text-align: center;
      max-width: 760px;
      margin: 0 auto 2.5rem;
    }}
    .section-head h2 {{
      font-family: 'Fraunces', serif;
      font-size: 2.1rem;
      color: var(--text-dark);
      margin-bottom: 0.6rem;
    }}
    .section-head p {{
      color: var(--text-muted);
      font-size: 1.05rem;
    }}

    /* Content Cards / Text layout */
    .content-box {{
      background: var(--bg-card);
      border-radius: 12px;
      border: 1px solid var(--border-soft);
      padding: 2.2rem;
      margin-bottom: 2rem;
      box-shadow: var(--shadow-sm);
    }}
    .content-box h3 {{
      font-family: 'Fraunces', serif;
      font-size: 1.45rem;
      color: var(--accent-terracotta);
      margin-bottom: 1rem;
    }}
    .content-box p {{
      font-size: 0.98rem;
      margin-bottom: 1rem;
      color: #3b403d;
    }}

    .highlight-card {{
      background: #fdfaf5;
      border-left: 4px solid var(--accent-terracotta);
      padding: 1.2rem 1.5rem;
      border-radius: 0 10px 10px 0;
      margin: 1.2rem 0;
    }}
    .highlight-card ul {{
      padding-left: 1.2rem;
    }}
    .highlight-card li {{
      font-size: 0.92rem;
      margin-bottom: 0.4rem;
      color: #2b2e2c;
    }}

    /* Level Cards */
    .level-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.2rem;
      margin: 1.5rem 0;
    }}
    .level-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-soft);
      border-radius: 10px;
      padding: 1.4rem;
      box-shadow: var(--shadow-sm);
    }}
    .level-card h4 {{
      font-family: 'Fraunces', serif;
      color: var(--accent-sage);
      font-size: 1.15rem;
      margin-bottom: 0.5rem;
    }}
    .level-card p {{
      font-size: 0.9rem;
      color: var(--text-muted);
      margin: 0;
    }}

    /* 6 Steps Grid */
    .steps-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.2rem;
      margin: 1.5rem 0;
    }}
    .step-item {{
      background: var(--bg-card);
      border: 1px solid var(--border-soft);
      border-radius: 10px;
      padding: 1.4rem;
      display: flex;
      gap: 1rem;
      align-items: flex-start;
    }}
    .step-num {{
      background: var(--accent-terracotta);
      color: #fff;
      font-family: 'Fraunces', serif;
      font-weight: 700;
      font-size: 1.1rem;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .step-content h4 {{
      font-size: 1.05rem;
      color: var(--text-dark);
      margin-bottom: 0.3rem;
    }}
    .step-content p {{
      font-size: 0.88rem;
      color: var(--text-muted);
      margin: 0;
    }}

    /* Plate formula */
    .plate-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.2rem;
      margin: 1.5rem 0;
    }}
    @media (max-width: 768px) {{
      .plate-grid {{ grid-template-columns: 1fr; }}
    }}
    .plate-card {{
      background: #fdfbf7;
      border: 1px solid var(--border-soft);
      border-radius: 10px;
      padding: 1.4rem;
      text-align: center;
    }}
    .plate-card h4 {{
      font-family: 'Fraunces', serif;
      color: var(--accent-sage);
      font-size: 1.2rem;
      margin-bottom: 0.5rem;
    }}
    .plate-card p {{
      font-size: 0.88rem;
      color: var(--text-muted);
      margin: 0;
    }}

    /* Safety Cards */
    .safety-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.2rem;
      margin: 1.5rem 0;
    }}
    .safety-card {{
      background: var(--accent-sage-light);
      border: 1px solid #d2e4d7;
      border-radius: 10px;
      padding: 1.3rem;
    }}
    .safety-card h4 {{
      font-family: 'Fraunces', serif;
      color: var(--accent-sage);
      font-size: 1.1rem;
      margin-bottom: 0.4rem;
    }}
    .safety-card p {{
      font-size: 0.88rem;
      color: #1e382b;
      margin: 0;
    }}

    /* Emergency Plans */
    .plan-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.2rem;
      margin: 1.5rem 0;
    }}
    .plan-card {{
      background: var(--bg-card);
      border-radius: 10px;
      border: 1px solid var(--border-soft);
      padding: 1.4rem;
      box-shadow: var(--shadow-sm);
    }}
    .plan-card.plan-a {{ border-top: 4px solid var(--accent-sage); }}
    .plan-card.plan-b {{ border-top: 4px solid var(--accent-mustard); }}
    .plan-card.plan-c {{ border-top: 4px solid var(--accent-terracotta); }}
    .plan-card h4 {{
      font-family: 'Fraunces', serif;
      font-size: 1.15rem;
      margin-bottom: 0.5rem;
    }}
    .plan-card.plan-a h4 {{ color: var(--accent-sage); }}
    .plan-card.plan-b h4 {{ color: var(--accent-mustard); }}
    .plan-card.plan-c h4 {{ color: var(--accent-terracotta); }}
    .plan-card p {{
      font-size: 0.9rem;
      color: var(--text-muted);
      margin: 0;
    }}

    /* Calendar Grid */
    .cal-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 1.2rem;
      margin-bottom: 4rem;
    }}
    .cal-day {{
      background: var(--bg-card);
      border: 1px solid var(--border-soft);
      border-radius: 10px;
      padding: 1.2rem;
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }}
    .cal-day.weekend {{
      background: #fdfaf5;
      border-color: #ebdcc8;
    }}
    .day-num {{
      font-family: 'Fraunces', serif;
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--accent-terracotta);
      border-bottom: 1px dashed var(--border-soft);
      padding-bottom: 0.4rem;
      display: flex;
      justify-content: space-between;
    }}
    .day-meal {{ font-size: 0.88rem; }}
    .meal-label {{
      font-weight: 800;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      display: block;
    }}
    .meal-title {{ font-weight: 600; color: var(--text-dark); }}
    .meal-tag {{
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      margin-top: 0.2rem;
    }}
    .tag-sobra {{ background: #fef3c7; color: #92400e; }}
    .tag-freezer {{ background: #e0f2fe; color: #075985; }}
    .tag-doble {{ background: #dcfce7; color: #166534; }}

    /* Recipe Cards */
    .recipe-filter {{
      display: flex;
      gap: 0.8rem;
      justify-content: center;
      margin-bottom: 2rem;
      flex-wrap: wrap;
    }}
    .filter-btn {{
      padding: 0.5rem 1.2rem;
      border-radius: 50px;
      border: 1px solid var(--border-soft);
      background: var(--bg-card);
      font-weight: 700;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn.active {{
      background: var(--accent-terracotta);
      color: #fff;
      border-color: var(--accent-terracotta);
    }}

    .recipe-card {{
      background: var(--bg-card);
      border-radius: 14px;
      border: 1px solid var(--border-soft);
      box-shadow: var(--shadow-sm);
      margin-bottom: 2rem;
      padding: 2rem;
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }}
    .recipe-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
      border-bottom: 1px solid var(--border-soft);
      padding-bottom: 1rem;
    }}
    .recipe-title {{
      font-family: 'Fraunces', serif;
      font-size: 1.6rem;
      color: var(--text-dark);
    }}
    .recipe-badges {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}
    .pill {{
      font-size: 0.78rem;
      font-weight: 700;
      padding: 0.25rem 0.65rem;
      border-radius: 50px;
      background: #f4ede3;
      color: var(--text-dark);
    }}
    .pill.time {{ background: var(--accent-sage-light); color: var(--accent-sage); }}
    .pill.cal {{ background: var(--accent-terracotta-light); color: var(--accent-terracotta); }}

    .recipe-img-wrap {{
      max-width: 360px;
      margin: 1.2rem auto;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid var(--border-soft);
      background: var(--bg-cream);
      box-shadow: var(--shadow-sm);
      display: flex;
      justify-content: center;
      align-items: center;
    }}
    .recipe-img {{
      max-width: 100%;
      max-height: 320px;
      width: auto;
      height: auto;
      object-fit: contain;
      display: block;
      border-radius: 10px;
    }}

    @media print {{
      .recipe-img-wrap {{
        max-width: 220px;
        margin: 0.8rem auto;
      }}
      .recipe-img {{
        max-height: 200px;
      }}
    }}

    .recipe-body-grid {{
      display: grid;
      grid-template-columns: 1fr 1.6fr;
      gap: 2rem;
    }}
    @media (max-width: 768px) {{
      .recipe-body-grid {{ grid-template-columns: 1fr; }}
    }}
    .ing-list {{ list-style: none; }}
    .ing-list li {{
      font-size: 0.92rem;
      padding: 0.35rem 0;
      border-bottom: 1px dotted var(--border-soft);
      display: flex;
      justify-content: space-between;
    }}
    .steps-list {{ padding-left: 1.2rem; }}
    .steps-list li {{
      font-size: 0.95rem;
      margin-bottom: 0.7rem;
      padding-left: 0.3rem;
    }}

    .recipe-cue {{
      background: var(--accent-sage-light);
      border-left: 4px solid var(--accent-sage);
      padding: 0.8rem 1.2rem;
      border-radius: 0 8px 8px 0;
      font-size: 0.9rem;
      color: #1f3b2c;
      margin-top: 1rem;
    }}
    .variants-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      margin-top: 1rem;
    }}
    @media (max-width: 600px) {{
      .variants-grid {{ grid-template-columns: 1fr; }}
    }}
    .variant-box {{
      background: #fdfbf7;
      border: 1px solid var(--border-soft);
      border-radius: 8px;
      padding: 0.9rem;
      font-size: 0.88rem;
    }}
    .variant-box strong {{
      display: block;
      color: var(--accent-terracotta);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.3rem;
    }}

    /* Shopping List */
    .shop-week {{
      background: var(--bg-card);
      border-radius: 12px;
      border: 1px solid var(--border-soft);
      padding: 1.8rem;
      margin-bottom: 2rem;
      box-shadow: var(--shadow-sm);
    }}
    .shop-week h3 {{
      font-family: 'Fraunces', serif;
      font-size: 1.4rem;
      color: var(--accent-terracotta);
      margin-bottom: 1.2rem;
      border-bottom: 2px solid var(--accent-terracotta-light);
      padding-bottom: 0.5rem;
    }}
    .sectors-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 1.5rem;
    }}
    .sector-col h4 {{
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 800;
      color: var(--accent-sage);
      margin-bottom: 0.6rem;
    }}
    .shop-item {{
      font-size: 0.88rem;
      padding: 0.3rem 0;
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
    }}
    .shop-item input[type="checkbox"] {{
      margin-top: 0.25rem;
      accent-color: var(--accent-terracotta);
      cursor: pointer;
    }}
    .alacena-box {{
      margin-top: 1.5rem;
      background: #fbf8f2;
      border-radius: 8px;
      padding: 1rem;
      font-size: 0.86rem;
      border-left: 3px solid var(--accent-mustard);
    }}

    /* Footer */
    footer {{
      text-align: center;
      padding: 3rem 1.5rem;
      color: var(--text-muted);
      font-size: 0.88rem;
      border-top: 1px solid var(--border-soft);
      margin-top: 4rem;
    }}
  </style>
</head>
<body>

  <!-- Top Nav -->
  <nav class="top-nav">
    <a href="#" class="nav-brand">Saso Digital</a>
    <div class="nav-links">
      <a href="#introduccion">Introducción</a>
      <a href="#metodo">El Método</a>
      <a href="#seguridad">Conservación</a>
      <a href="#calendario">Calendario</a>
      <a href="#recetario">Recetario</a>
      <a href="#compras">Compras</a>
      <a href="#estrategias">Estrategias</a>
      <a href="visor.html" style="background: var(--accent-terracotta); color: #ffffff !important; padding: 0.25rem 0.75rem; border-radius: 6px; font-weight: 700;">📖 Visor A4</a>
    </div>
  </nav>

  <div class="container">

    <!-- Hero / Portada -->
    <section class="hero-card">
      <div class="hero-img-wrap">
        <img src="../diseno/ilustraciones/portada.png" alt="Portada {config.get('titulo')}">
      </div>
      <div class="hero-body">
        <span class="badge">Edición 2026 · Guía Maestra</span>
        <h1 class="hero-title">{config.get("titulo")}</h1>
        <p class="hero-subtitle">{config.get("subtitulo")}</p>
        <div class="hero-meta">
          <p><strong>{config.get("nota_porciones")}</strong></p>
          <p style="margin-top: 0.5rem; font-size: 0.78rem;">{config.get("aviso_profesional")}</p>
        </div>
      </div>
    </section>

    <!-- INTRODUCCIÓN EDITORIAL COMPLETA -->
    <section id="introduccion" style="margin-bottom: 4rem;">
      <div class="section-head">
        <h2>{ed.get("introduccion", {}).get("antes_de_empezar", {}).get("titulo", "Antes de empezar")}</h2>
        <p>Una base sólida para organizarte con tranquilidad y permiso para adaptarla cuando la vida real se imponga.</p>
      </div>

      <div class="content-box">
        {"".join(f"<p>{p}</p>" for p in ed.get("introduccion", {}).get("antes_de_empezar", {}).get("parrafos", []))}

        <div class="highlight-card">
          <strong style="color:var(--accent-terracotta); text-transform:uppercase; font-size:0.8rem; letter-spacing:0.05em; display:block; margin-bottom:0.5rem;">Tres principios para no abandonar:</strong>
          <ul>
            {"".join(f"<li>{c}</li>" for c in ed.get("introduccion", {}).get("antes_de_empezar", {}).get("claves", []))}
          </ul>
        </div>
      </div>

      <!-- Cómo usar esta guía según tu tiempo -->
      <div class="content-box">
        <h3>{ed.get("introduccion", {}).get("como_usar_guia", {}).get("titulo", "Cómo usar esta guía")}</h3>
        <p>{ed.get("introduccion", {}).get("como_usar_guia", {}).get("descripcion", "")}</p>

        <div class="level-grid">
          {"".join(f'''
          <div class="level-card">
            <h4>⏱️ {n["tiempo"]}</h4>
            <p>{n["accion"]}</p>
          </div>
          ''' for n in ed.get("introduccion", {}).get("como_usar_guia", {}).get("niveles", []))}
        </div>
      </div>

      <!-- El círculo de la improvisación -->
      <div class="content-box">
        <h3>{ed.get("introduccion", {}).get("circulo_improvisacion", {}).get("titulo", "El círculo de la improvisación")}</h3>
        <p>{ed.get("introduccion", {}).get("circulo_improvisacion", {}).get("bajada", "")}</p>
        <div style="background:#fdfaf5; border-radius:10px; padding:1.2rem; border:1px solid #ebdcc8;">
          <strong style="font-size:0.82rem; color:#92400e; text-transform:uppercase; letter-spacing:0.05em; display:block; margin-bottom:0.6rem;">Las 5 trampas cotidianas que este sistema elimina:</strong>
          <ul style="padding-left:1.2rem; font-size:0.92rem; color:#451a03;">
            {"".join(f"<li style='margin-bottom:0.35rem;'>{t}</li>" for t in ed.get("introduccion", {}).get("circulo_improvisacion", {}).get("trampas", []))}
          </ul>
        </div>
      </div>
    </section>

    <!-- EL MÉTODO & SISTEMA -->
    <section id="metodo" style="margin-bottom: 4rem;">
      <div class="section-head">
        <h2>{ed.get("metodo", {}).get("los_15_minutos", {}).get("titulo", "El método de los 15 minutos")}</h2>
        <p>{ed.get("metodo", {}).get("los_15_minutos", {}).get("descripcion", "")}</p>
      </div>

      <div class="steps-grid">
        {"".join(f'''
        <div class="step-item">
          <div class="step-num">{p["paso"]}</div>
          <div class="step-content">
            <h4>{p["titulo"]}</h4>
            <p>{p["detalle"]}</p>
          </div>
        </div>
        ''' for p in ed.get("metodo", {}).get("los_15_minutos", {}).get("pasos", []))}
      </div>

      <!-- Fórmula del plato práctico -->
      <div class="content-box" style="margin-top:2.5rem;">
        <h3>{ed.get("metodo", {}).get("formula_plato", {}).get("titulo", "La fórmula de un plato práctico")}</h3>
        <p>{ed.get("metodo", {}).get("formula_plato", {}).get("bajada", "")}</p>
        <div class="plate-grid">
          {"".join(f'''
          <div class="plate-card">
            <h4>{c["nombre"]}</h4>
            <p>{c["rol"]}</p>
          </div>
          ''' for c in ed.get("metodo", {}).get("formula_plato", {}).get("componentes", []))}
        </div>
      </div>

      <!-- Compras estratégicas -->
      <div class="content-box">
        <h3>{ed.get("metodo", {}).get("compras_estrategicas", {}).get("titulo", "Antes de ir al súper")}</h3>
        <ul style="padding-left:1.2rem; font-size:0.95rem; color:#3b403d;">
          {"".join(f"<li style='margin-bottom:0.5rem;'>{c}</li>" for c in ed.get("metodo", {}).get("compras_estrategicas", {}).get("consejos", []))}
        </ul>
      </div>
    </section>

    <!-- SEGURIDAD Y CONSERVACIÓN -->
    <section id="seguridad" style="margin-bottom: 4rem;">
      <div class="section-head">
        <h2>{ed.get("metodo", {}).get("conservacion_segura", {}).get("titulo", "Conservación y seguridad en el hogar")}</h2>
        <p>Pautas de higiene, refrigeración y temperaturas recomendadas por manuales bromatológicos para cocinar de más con total tranquilidad.</p>
      </div>

      <div class="safety-grid">
        {"".join(f'''
        <div class="safety-card">
          <h4>🛡️ {pt["titulo"]}</h4>
          <p>{pt["texto"]}</p>
        </div>
        ''' for pt in ed.get("metodo", {}).get("conservacion_segura", {}).get("puntos", []))}
      </div>
    </section>

    <!-- CALENDARIO DE 30 DÍAS -->
    <section id="calendario" style="margin-bottom: 4rem;">
      <div class="section-head">
        <h2>Menú Planificado · 30 Días</h2>
        <p>Almuerzo y cena coordinados con rotación de proteínas (carnes, pescado, pollo, legumbres y huevos) sin repeticiones pesadas.</p>
      </div>

      <div class="cal-grid">
"""

    for d in cal["dias"]:
        dia_num = d["dia"]
        nombre_d = motor.nombre_dia(dia_num).capitalize()
        es_fin = motor.es_finde(dia_num)
        
        # Almuerzo
        alm = d["almuerzo"]
        if "receta" in alm:
            r_alm = recetas[alm["receta"]]
            alm_txt = r_alm["nombre"]
            alm_tag = f'<span class="meal-tag tag-doble">x{alm.get("porciones", 4)} porc.</span>' if alm.get("porciones", 4) > 4 else ""
        elif "sobra_de" in alm:
            alm_txt = recetas[alm["sobra_de"]]["nombre"]
            alm_tag = '<span class="meal-tag tag-sobra">Sobra lista</span>'
        elif "del_freezer" in alm:
            alm_txt = recetas[alm["del_freezer"]]["nombre"]
            alm_tag = '<span class="meal-tag tag-freezer">Del freezer</span>'
        else:
            alm_txt = "Almuerzo libre"
            alm_tag = ""

        # Cena
        cena = d["cena"]
        if "receta" in cena:
            r_cena = recetas[cena["receta"]]
            cena_txt = r_cena["nombre"]
            cena_tag = f'<span class="meal-tag tag-doble">x{cena.get("porciones", 4)} porc.</span>' if cena.get("porciones", 4) > 4 else ""
        elif "sobra_de" in cena:
            cena_txt = recetas[cena["sobra_de"]]["nombre"]
            cena_tag = '<span class="meal-tag tag-sobra">Sobra lista</span>'
        elif "del_freezer" in cena:
            cena_txt = recetas[cena["del_freezer"]]["nombre"]
            cena_tag = '<span class="meal-tag tag-freezer">Del freezer</span>'
        else:
            cena_txt = "Cena libre"
            cena_tag = ""

        postre = d.get("postre_cena")
        postre_html = f'<div style="font-size:0.75rem; color:#78716c; margin-top:0.3rem;">🍰 {recetas[postre]["nombre"]}</div>' if postre else ""

        html += f"""
        <div class="cal-day {'weekend' if es_fin else ''}">
          <div class="day-num">
            <span>Día {dia_num}</span>
            <small style="font-weight:400; font-family:'Nunito Sans'; font-size:0.8rem;">{nombre_d}</small>
          </div>
          <div class="day-meal">
            <span class="meal-label">Almuerzo</span>
            <span class="meal-title">{alm_txt}</span>
            {alm_tag}
          </div>
          <div class="day-meal">
            <span class="meal-label">Cena</span>
            <span class="meal-title">{cena_txt}</span>
            {cena_tag}
            {postre_html}
          </div>
        </div>
        """

    html += """
      </div>
    </section>

    <!-- RECETARIO COMPLETO (45 FICHAS) -->
    <section id="recetario" style="margin-bottom: 4rem;">
      <div class="section-head">
        <h2>Recetario Completo · 45 Fichas</h2>
        <p>Recetas probadas de ≤ 8 ingredientes cotidianos, con pasos sencillos y adaptaciones familiares.</p>
      </div>

      <div class="recipe-filter">
        <button class="filter-btn active" onclick="filtrar('todos')">Todas (45)</button>
        <button class="filter-btn" onclick="filtrar('principal')">Platos Principales (32)</button>
        <button class="filter-btn" onclick="filtrar('desayuno_merienda')">Desayunos y Viandas (5)</button>
        <button class="filter-btn" onclick="filtrar('postre')">Postres (7)</button>
        <button class="filter-btn" onclick="filtrar('basico')">Básicos (1)</button>
      </div>

      <div id="recetas-container">
"""

    for r in recetas.values():
        img_file = DISENO / "ilustraciones" / f"{r['id']}.png"
        img_html = ""
        if img_file.exists():
            img_html = f'''
            <div class="recipe-img-wrap">
              <img class="recipe-img" src="../diseno/ilustraciones/{r["id"]}.png" alt="{r["nombre"]}">
            </div>'''

        ing_items = "".join(f"<li><span>{i['item']}</span> <strong>{i['cantidad']} {i['unidad']}</strong></li>" for i in r["ingredientes"])
        pasos_items = "".join(f"<li>{p}</li>" for p in r["pasos"])

        senales = f'<div class="recipe-cue"><strong>👀 Señal de cocción:</strong> {r["senales_coccion"]}</div>' if r.get("senales_coccion") else ""
        
        chicos = f'<div class="variant-box"><strong>👶 Versión chicos</strong>{r["version_chicos"]}</div>' if r.get("version_chicos") else ""
        adultos = f'<div class="variant-box"><strong>🌶️ Variante adultos</strong>{r["variante_adultos"]}</div>' if r.get("variante_adultos") else ""
        variants_html = f'<div class="variants-grid">{chicos}{adultos}</div>' if (chicos or adultos) else ""
        
        sobra = f'<div style="font-size:0.84rem; color:#6b7280; margin-top:0.8rem;">🧊 <strong>Conservación:</strong> {r["si_te_sobra"]}</div>' if r.get("si_te_sobra") else ""

        calorias = f'<span class="pill cal">~{r["nutricion"]["kcal"]} kcal</span>' if r.get("nutricion") else ""

        html += f"""
        <article class="recipe-card" data-tipo="{r['tipo']}">
          <div>
            <div class="recipe-header">
              <div>
                <h3 class="recipe-title">{r['nombre']}</h3>
                <div style="font-size:0.85rem; color:#857f77; margin-top:0.2rem;">Proteína: {r['proteina']} · Dificultad: {r['dificultad']}</div>
              </div>
              <div class="recipe-badges">
                <span class="pill time">⏱️ {r['tiempo_total']} min (activo: {r['tiempo_activo']}m)</span>
                {calorias}
              </div>
            </div>

            {img_html}

            <div class="recipe-body-grid" style="margin-top: 1.5rem;">
              <div>
                <h4 style="font-size:0.85rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--accent-sage); margin-bottom:0.6rem;">Ingredientes (4 porciones)</h4>
                <ul class="ing-list">
                  {ing_items}
                </ul>
                {sobra}
              </div>

              <div>
                <h4 style="font-size:0.85rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--accent-sage); margin-bottom:0.6rem;">Preparación</h4>
                <ol class="steps-list">
                  {pasos_items}
                </ol>
                {senales}
                {variants_html}
              </div>
            </div>
          </div>
        </article>
        """

    html += """
      </div>
    </section>

    <!-- LISTAS DE COMPRAS SEMANALES -->
    <section id="compras" style="margin-bottom: 4rem;">
      <div class="section-head">
        <h2>Listas de Compras Semanales</h2>
        <p>Calculadas automáticamente con las sumas exactas del calendario, traducidas a envases de góndola.</p>
      </div>
"""

    for s in semanas_info:
        html += f"""
        <div class="shop-week">
          <h3>Semana · Días {s['desde']} a {s['hasta']}</h3>
          <div class="sectors-grid">
        """
        for sector, items in s["sectores"]:
            html += f"""
            <div class="sector-col">
              <h4>{sector}</h4>
            """
            for it in items:
                det = f" <small style='color:#78716c;'>({it['detalle']})</small>" if it["detalle"] else ""
                html += f"""
                <label class="shop-item">
                  <input type="checkbox">
                  <span><strong>{it['item']}</strong>: {it['texto']}{det}</span>
                </label>
                """
            html += "</div>"
        
        if s["alacena"]:
            alacena_str = ", ".join(s["alacena"])
            html += f"""
            <div style="grid-column: 1 / -1;" class="alacena-box">
              <strong>🧂 Revisá en tu alacena si tenés:</strong> {alacena_str}
            </div>
            """
        html += """
          </div>
        </div>
        """

    # ESTRATEGIAS PRÁCTICAS
    html += f"""
    </section>

    <section id="estrategias" style="margin-bottom: 4rem;">
      <div class="section-head">
        <h2>Estrategias Prácticas & Herramientas</h2>
        <p>Soluciones para días difíciles, multiplicación de comidas y pautas para sostener el hábito sin frustraciones.</p>
      </div>

      <!-- Planes de emergencia -->
      <div class="content-box">
        <h3>{ed.get("estrategias", {}).get("comidas_emergencia", {}).get("titulo", "Comidas de emergencia")}</h3>
        <p>Tener un protocolo de emergencia evita llamar al delivery o improvisar con alimentos ultraprocesados cuando llegás sin energía:</p>

        <div class="plan-grid">
          {"".join(f'''
          <div class="plan-card {'plan-a' if i==0 else ('plan-b' if i==1 else 'plan-c')}">
            <h4>{p["plan"]}</h4>
            <p>{p["detalle"]}</p>
          </div>
          ''' for i, p in enumerate(ed.get("estrategias", {}).get("comidas_emergencia", {}).get("planes", [])))}
        </div>
      </div>

      <!-- Una base, tres comidas -->
      <div class="content-box">
        <h3>{ed.get("estrategias", {}).get("aprovechamiento", {}).get("titulo", "Una base, tres comidas diferentes")}</h3>
        <ul style="padding-left:1.2rem; font-size:0.95rem; color:#3b403d;">
          {"".join(f"<li style='margin-bottom:0.6rem;'>{p}</li>" for p in ed.get("estrategias", {}).get("aprovechamiento", {}).get("pautas", []))}
        </ul>
      </div>

      <!-- Compromiso -->
      <div class="content-box" style="background:#fcf9f2; border-left:4px solid var(--accent-sage);">
        <h3 style="color:var(--accent-sage);">{ed.get("estrategias", {}).get("compromiso", {}).get("titulo", "Tu compromiso de 30 días")}</h3>
        <p style="font-size:1.02rem; color:#2c302e; line-height:1.7;">{ed.get("estrategias", {}).get("compromiso", {}).get("texto", "")}</p>
      </div>
    </section>

    <footer>
      <p><strong>{config.get("marca")}</strong> · {config.get("edicion")}</p>
      <p style="margin-top:0.4rem; font-size:0.8rem;">{config.get("copyright")}</p>
    </footer>

  </div>

  <script>
    function filtrar(tipo) {{
      const cards = document.querySelectorAll('.recipe-card');
      const btns = document.querySelectorAll('.filter-btn');
      btns.forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');

      cards.forEach(c => {{
        if (tipo === 'todos' || c.getAttribute('data-tipo') === tipo || (tipo === 'desayuno_merienda' && ['desayuno', 'merienda', 'desayuno_merienda'].includes(c.getAttribute('data-tipo')))) {{
          c.style.display = 'grid';
        }} else {{
          c.style.display = 'none';
        }}
      }});
    }}
  </script>
</body>
</html>
"""
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "index.html").write_text(html, encoding="utf-8")
    print("✅ Vista previa completa generada exitosamente en:", SALIDA / "index.html")

if __name__ == "__main__":
    render_html()
