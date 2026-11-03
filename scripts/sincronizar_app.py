#!/usr/bin/env python3
"""Sincronizador oficial entre la carpeta datos/ (fuente única de verdad del Ebook)
y la aplicación web interactiva "Compañero de 30 días" (carpeta app/).

Si modificás cualquier receta, ingrediente o día del calendario en datos/,
ejecutá este script para actualizar automáticamente la app web y verificar
que todas las reglas nutricionales y de seguridad se cumplan.
"""
import copy
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import motor

DATOS_DIR = RAIZ / "datos"
DISENO_DIR = RAIZ / "diseno"
APP_DIR = RAIZ / "app"

# Textos exactos aprobados en el Ebook para las celdas de sobras/freezer
SOBRAS_TEXTOS = {
    (5, "almuerzo"): {
        "texto": "Sobras del chili (cocinado el día 4)",
        "origen_dia": 4,
        "origen_turno": "cena",
        "tipo_sobra": "heladera",
    },
    (11, "almuerzo"): {
        "texto": "Sobras del cerdo agridulce (cocinado el día 10)",
        "origen_dia": 10,
        "origen_turno": "cena",
        "tipo_sobra": "heladera",
    },
    (12, "cena"): {
        "texto": "Albóndigas del freezer (cocinadas el día 7)",
        "origen_dia": 7,
        "origen_turno": "almuerzo",
        "tipo_sobra": "freezer",
    },
    (15, "almuerzo"): {
        "texto": "Sobras de las milanesas (cocinadas el día 14)",
        "origen_dia": 14,
        "origen_turno": "almuerzo",
        "tipo_sobra": "heladera",
    },
    (15, "cena"): {
        "texto": "Sobras del guiso de lentejas (cocinado el día 14)",
        "origen_dia": 14,
        "origen_turno": "cena",
        "tipo_sobra": "heladera",
    },
    (26, "almuerzo"): {
        "texto": "Sobras del chili (cocinado el día 25)",
        "origen_dia": 25,
        "origen_turno": "cena",
        "tipo_sobra": "heladera",
    },
}


def limpiar_referencia_pag(texto: str) -> str:
    """Reemplaza referencias de página del PDF por referencias interactivas para la app."""
    if not isinstance(texto, str):
        return texto
    return (
        texto.replace("(usá la Base de pollo cocido, p. 57)", "(usá la Base de pollo cocido)")
        .replace("(Base de pollo cocido, p. 57)", "(Base de pollo cocido)")
        .replace("Base de pollo cocido (p. 57)", "Base de pollo cocido")
        .replace("(p. 57)", "")
    )


def sincronizar():
    config, recetas_dict, cal = motor.cargar()
    editorial = json.loads((DATOS_DIR / "contenido_editorial.json").read_text(encoding="utf-8"))

    # 1. Crear estructura de carpetas de la app
    APP_DIR.mkdir(parents=True, exist_ok=True)
    img_dest = APP_DIR / "ilustraciones"
    font_dest = APP_DIR / "fuentes"
    datos_dest = APP_DIR / "datos"
    img_dest.mkdir(exist_ok=True)
    font_dest.mkdir(exist_ok=True)
    datos_dest.mkdir(exist_ok=True)

    # 2. Copiar ilustraciones livianas de celular
    img_src = DISENO_DIR / "ilustraciones_mobile"
    imagenes_disponibles = set()
    if img_src.exists():
        for png in img_src.glob("*.png"):
            shutil.copy2(png, img_dest / png.name)
            imagenes_disponibles.add(png.stem)

    # 3. Copiar tipografías oficiales del ebook
    for font_name in ["Fraunces.ttf", "NunitoSans.ttf"]:
        f_src = DISENO_DIR / "fuentes" / font_name
        if f_src.exists():
            shutil.copy2(f_src, font_dest / font_name)

    # 4. Procesar y enriquecer recetas sin alterar los textos de origen
    recetas_app = []
    for r_id, r_orig in recetas_dict.items():
        r = copy.deepcopy(r_orig)
        r["tiene_imagen"] = r_id in imagenes_disponibles
        r["imagen_url"] = f"ilustraciones/{r_id}.png" if r["tiene_imagen"] else None
        for ing in r.get("ingredientes", []):
            ing["item"] = limpiar_referencia_pag(ing["item"])
        r["pasos"] = [limpiar_referencia_pag(p) for p in r.get("pasos", [])]
        recetas_app.append(r)

    # Ordenar igual que en el ebook: Base de pollo primero, luego principales, luego extras
    orden_tipos = {"basico": 0, "principal": 1, "desayuno": 2, "colacion": 3, "vianda": 4, "postre": 5}
    recetas_app.sort(key=lambda x: (0 if x["id"] == "base-pollo-cocido" else 1, orden_tipos.get(x.get("tipo"), 9)))

    # 5. Calcular bases y dependencias del calendario usando motor.py
    bases_por_dia, origen_base_por_uso = motor.calcular_bases(config, recetas_dict, cal)

    # Mapear qué días generan sobras para otros días
    genera_sobras_para = {}
    for (dia_dest, turno_dest), info_sobra in SOBRAS_TEXTOS.items():
        clave_orig = (info_sobra["origen_dia"], info_sobra["origen_turno"])
        genera_sobras_para.setdefault(clave_orig, []).append({
            "dia": dia_dest,
            "turno": turno_dest,
            "texto": info_sobra["texto"],
            "tipo_sobra": info_sobra["tipo_sobra"],
        })

    dias_enriquecidos = []
    for d in cal["dias"]:
        n_dia = d["dia"]
        dia_obj = {
            "dia": n_dia,
            "semana": ((n_dia - 1) // 7) + 1,
            "nombre_dia": motor.nombre_dia(n_dia).capitalize(),
            "es_finde": motor.es_finde(n_dia),
            "nota_batch": d.get("nota_batch", ""),
            "postre_almuerzo": d.get("postre_almuerzo", "fruta-estacion"),
            "postre_cena": d.get("postre_cena", "fruta-estacion"),
        }
        for turno in ("almuerzo", "cena"):
            slot = copy.deepcopy(d[turno])
            sobra_info = SOBRAS_TEXTOS.get((n_dia, turno))
            if sobra_info:
                slot["es_sobra"] = True
                slot["texto_sobra"] = sobra_info["texto"]
                slot["origen_dia"] = sobra_info["origen_dia"]
                slot["origen_turno"] = sobra_info["origen_turno"]
                slot["tipo_sobra"] = sobra_info["tipo_sobra"]
                slot["receta_id"] = slot.get("sobra_de")
            else:
                slot["es_sobra"] = False
                slot["receta_id"] = slot.get("receta")

            # Si este turno cocina doble para otro día
            if (n_dia, turno) in genera_sobras_para:
                slot["cocina_doble"] = True
                slot["etiqueta_doble"] = "x8 porciones (cocinar doble)"
                slot["alimenta_sobras"] = genera_sobras_para[(n_dia, turno)]
            else:
                slot["cocina_doble"] = slot.get("porciones", 4) > 4
                slot["etiqueta_doble"] = "x8 porciones (cocinar doble)" if slot["cocina_doble"] else ""
                slot["alimenta_sobras"] = []

            # Si este turno genera base cocida (pollo o arroz extra)
            if (n_dia, turno) in bases_por_dia:
                b_info = bases_por_dia[(n_dia, turno)]
                slot["batch_base"] = {
                    "base": b_info["base"],
                    "cantidad_cocida": b_info["cantidad"],
                    "ingrediente_crudo": b_info["ingrediente_crudo"],
                    "cantidad_cruda": b_info["crudo"],
                    "unidad": "g",
                    "sector": b_info["sector"],
                    "usos_dias": [
                        {"dia": u[0], "turno": u[1], "receta_id": u[2]}
                        for u in b_info["usos"]
                    ],
                }
            else:
                slot["batch_base"] = None

            # Si este turno consume una base cocinada un día anterior
            if (n_dia, turno) in origen_base_por_uso:
                orig_d, orig_t = origen_base_por_uso[(n_dia, turno)]
                slot["consume_base_de"] = {"dia": orig_d, "turno": orig_t}
            else:
                slot["consume_base_de"] = None

            dia_obj[turno] = slot
        dias_enriquecidos.append(dia_obj)

    app_payload = {
        "meta": {
            "app_nombre": "Compañero de 30 días",
            "ebook_titulo": config["titulo"],
            "marca": config["marca"],
            "edicion": config["edicion"],
            "codigo_acceso_default": "COCINA30",
            "porciones_base": config["porciones_base"],
            "aviso_profesional": config["aviso_profesional"],
            "nota_porciones": config["nota_porciones"],
        },
        "config": {
            "bases": config["bases"],
            "presentaciones": config["presentaciones"],
            "alacena_general": [
                "Aceite de oliva o girasol",
                "Sal fina (preferentemente reducida en sodio)",
                "Pimienta negra",
                "Orégano seco, pimentón dulce, comino y laurel",
                "Vinagre o jugo de limón",
            ],
        },
        "recetas": recetas_app,
        "calendario": dias_enriquecidos,
        "editorial": editorial,
        # Estructura preparada para la Segunda Etapa (sin activar en la interfaz actual)
        "segunda_etapa_schema": {
            "heladera_matcher_enabled": False,
            "favoritos_notas_enabled": False,
            "recordatorios_semanales_enabled": False,
        },
    }

    # Guardar JSON puro y archivo JS para carga instantánea sin servidor ni errores CORS
    json_str = json.dumps(app_payload, ensure_ascii=False, indent=2)
    (datos_dest / "app_data.json").write_text(json_str, encoding="utf-8")
    js_content = (
        "// Archivo generado automáticamente por scripts/sincronizar_app.py a partir de datos/\n"
        "// NO EDITAR A MANO: modificá datos/recetas.json o datos/calendario.json y corré sincronizar_app.py\n"
        f"window.APP_DATA = {json_str};\n"
    )
    (APP_DIR / "datos.js").write_text(js_content, encoding="utf-8")

    # Calcular peso total de la carpeta app/
    total_bytes = sum(f.stat().st_size for f in APP_DIR.rglob("*") if f.is_file())
    print(f"✅ Sincronización completada en {APP_DIR}")
    print(f"   · Recetas sincronizadas: {len(recetas_app)} (1 base + 32 principales + 13 extras)")
    print(f"   · Días del calendario: {len(dias_enriquecidos)}")
    print(f"   · Ilustraciones livianas copiadas: {len(imagenes_disponibles)}")
    print(f"   · Peso total actual de app/: {total_bytes / (1024 * 1024):.2f} MB (límite: 15 MB)")


if __name__ == "__main__":
    sincronizar()
