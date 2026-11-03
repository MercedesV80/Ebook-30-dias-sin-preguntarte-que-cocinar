"""Motor del ebook: carga datos, valida reglas y calcula listas de compras.

Uso:  python3 scripts/motor.py        (muestra el informe de validaciones)
"""
import json, re, math
from collections import defaultdict, OrderedDict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
SECTORES = ["verduras y frutas", "carnes y huevos", "lácteos", "almacén", "panificados", "freezer"]
MAX_TOTAL_SEMANA, MAX_ACTIVO_SEMANA = 25, 15
DIAS_MAX_BASE = 3


def cargar():
    r = json.loads((DATOS / "recetas.json").read_text(encoding="utf-8"))
    c = json.loads((DATOS / "calendario.json").read_text(encoding="utf-8"))
    recetas = OrderedDict((x["id"], x) for x in r["recetas"])
    return r["config"], recetas, c


def nombre_dia(n):
    return DIAS_SEMANA[(n - 1) % 7]


def es_finde(n):
    return nombre_dia(n) in ("sábado", "domingo")


def comidas(cal):
    """Lista ordenada de (dia, momento, entrada)."""
    out = []
    for d in cal["dias"]:
        for m in ("almuerzo", "cena"):
            out.append((d["dia"], m, d[m]))
    return out


def calcular_bases(config, recetas, cal):
    """Para cada comida que genera una base, cuánto debe producir según los usos de los próximos 3 días."""
    lista = comidas(cal)
    produccion = {}  # (dia, momento) -> {base, cantidad, crudo}
    asignacion = {}  # (dia, momento) del uso -> (dia, momento) del origen
    for i, (dia, mom, e) in enumerate(lista):
        rid = e.get("receta")
        if not rid:
            continue
        ub = recetas[rid].get("usa_base")
        if not ub:
            continue
        origen = None
        for j in range(i - 1, -1, -1):
            d2, m2, e2 = lista[j]
            if dia - d2 > DIAS_MAX_BASE:
                break
            r2 = e2.get("receta")
            if r2 and recetas[r2].get("genera_base") == ub["base"]:
                origen = (d2, m2)
                break
        if origen:
            asignacion[(dia, mom)] = origen
            p = produccion.setdefault(origen, {"base": ub["base"], "cantidad": 0, "usos": []})
            p["cantidad"] += ub["cantidad"]
            p["usos"].append((dia, mom, rid))
    for k, p in produccion.items():
        b = config["bases"][p["base"]]
        if p["base"] == "pollo cocido":
            if p["cantidad"] <= 600:
                p["crudo"] = 900
            else:
                p["crudo"] = 1300
        else:
            p["crudo"] = int(math.ceil(p["cantidad"] / b["rinde"] / 50.0) * 50)
        p["ingrediente_crudo"] = b["ingrediente_crudo"]
        p["sector"] = b["sector"]
    return produccion, asignacion


def factor(e):
    return e.get("porciones", 4) / 4.0


def lista_compras(config, recetas, cal, desde, hasta):
    produccion, _ = calcular_bases(config, recetas, cal)
    tot = defaultdict(float)  # (sector, item, unidad) -> cantidad
    detalle = defaultdict(list)
    def sumar(rid, f, origen):
        for ing in recetas[rid]["ingredientes"]:
            if ing.get("es_base"):
                continue
            k = (ing["sector"], ing["item"], ing["unidad"])
            tot[k] += ing["cantidad"] * f
            detalle[k].append(origen)
    for d in cal["dias"]:
        if not (desde <= d["dia"] <= hasta):
            continue
        for m in ("almuerzo", "cena"):
            e = d[m]
            if "receta" in e:
                sumar(e["receta"], factor(e), f"día {d['dia']} {m}")
                p = produccion.get((d["dia"], m))
                if p:
                    k = (p["sector"], p["ingrediente_crudo"], "g")
                    tot[k] += p["crudo"]
                    detalle[k].append(f"día {d['dia']} base extra")
            sumar(d.get(f"postre_{m}", "fruta-estacion"), 1, f"día {d['dia']} postre")
    return tot, detalle


def semanas():
    return [(1, 7), (8, 14), (15, 21), (22, 28), (29, 30)]


UNIDADES_ALACENA = {"cda", "cdita", "pizca"}
# Plural de unidades sueltas
PLURAL = {"unidad": "unidades", "diente": "dientes", "atado": "atados", "planta": "plantas", "lata": "latas",
          "rebanada": "rebanadas", "paquete (2 tapas)": "paquetes (2 tapas c/u)"}


def num(x):
    """Número en formato argentino: 1.250 / 1,5."""
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}".replace(",", ".")
    return f"{x:.2f}".rstrip("0").replace(".", ",")


def cantidad_legible(cant, unidad):
    if unidad == "g":
        return f"{num(cant / 1000)} kg" if cant >= 1000 else f"{num(cant)} g"
    if unidad == "ml":
        return f"{num(cant / 1000)} litros" if cant >= 1000 else f"{num(cant)} ml"
    if unidad == "cdita":
        return f"{num(cant)} cucharaditas" if cant > 1 else "1 cucharadita"
    if unidad == "cda":
        return f"{num(cant)} cucharadas" if cant > 1 else "1 cucharada"
    u = unidad if cant == 1 else PLURAL.get(unidad, unidad)
    return f"{num(cant)} {u}"


def lista_para_imprimir(config, tot):
    """Agrupa la suma exacta por sector y la traduce a envases del súper.

    Devuelve (sectores, alacena):
      sectores = [(sector, [{"item", "texto", "detalle"}])]
      alacena  = [item, ...]   (condimentos que se usan por cucharada: solo hay que revisar que haya)
    """
    pres = config.get("presentaciones", {})
    por_sector = defaultdict(list)
    alacena = set()
    for (sector, item, unidad), cant in tot.items():
        if unidad in UNIDADES_ALACENA:
            alacena.add(item)
            continue
        if item in pres:
            p = pres[item]
            n = int(math.ceil(round(cant / p["tamano"], 6)))
            texto = f"{n} {p['envase'] if n == 1 else p['envases']}"
            detalle = f"usás {cantidad_legible(cant, unidad)}"
        else:
            texto = cantidad_legible(cant, unidad)
            detalle = ""
        por_sector[sector].append({"item": item, "texto": texto, "detalle": detalle})
    # Lo que figura con envase también por cucharada (ej. azúcar mascabo) no hace falta repetirlo en alacena
    con_envase = {x["item"] for v in por_sector.values() for x in v}
    alacena -= con_envase
    sectores = [(s, sorted(por_sector[s], key=lambda x: x["item"])) for s in SECTORES if por_sector.get(s)]
    return sectores, sorted(alacena)


# Campos técnicos que nunca se imprimen (identificadores, categorías internas, notas para quien edita)
CAMPOS_TECNICOS = {"id", "receta", "sobra_de", "del_freezer", "sector", "unidad", "base", "genera_base", "es_base",
                   "momento", "tipo", "proteina", "dificultad", "nota", "dia_inicio", "ingrediente_crudo"}


def textos_visibles(o, clave=None):
    """Recorre el JSON y devuelve solo los textos que lee la clienta."""
    if isinstance(o, str):
        if clave not in CAMPOS_TECNICOS and not (clave or "").startswith("postre_"):
            yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in CAMPOS_TECNICOS:
                yield from textos_visibles(v, k)
    elif isinstance(o, list):
        for v in o:
            yield from textos_visibles(v, clave)


_DICC = None


def ortografia(texto):
    """Lista de palabras que no están en el diccionario es_AR ni en palabras_propias.txt (None si falta el diccionario)."""
    global _DICC
    carpeta = RAIZ / "scripts" / "diccionario"
    try:
        if _DICC is None:
            from spylls.hunspell import Dictionary
            _DICC = Dictionary.from_files(str(carpeta / "es_AR"))
    except Exception:
        return None
    propias = set()
    for linea in (carpeta / "palabras_propias.txt").read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            propias.add(linea.lower())
    palabras = set(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", texto))
    return sorted(w for w in palabras
                  if w.lower() not in propias and not _DICC.lookup(w) and not _DICC.lookup(w.lower()))


# ---------------- VALIDACIONES ----------------

def validar(config, recetas, cal):
    res = []  # (ok, titulo, detalle)
    lista = comidas(cal)
    principales = [r for r in recetas.values() if r["tipo"] == "principal"]
    contables = [r for r in recetas.values() if r["tipo"] != "basico"]

    # 1. Existencia
    faltan = []
    for d in cal["dias"]:
        for m in ("almuerzo", "cena"):
            e = d[m]
            rid = e.get("receta") or e.get("sobra_de") or e.get("del_freezer")
            if rid not in recetas:
                faltan.append(f"día {d['dia']} {m}: {rid}")
        for m in ("almuerzo", "cena"):
            p = d.get(f"postre_{m}")
            if p and p not in recetas:
                faltan.append(f"día {d['dia']} postre: {p}")
    res.append((not faltan, "Cada comida del calendario existe en el recetario", faltan or [f"{len(lista)} comidas revisadas"]))

    # 2. Tiempos de días de semana
    malos = []
    for dia, m, e in lista:
        rid = e.get("receta")
        if rid and not es_finde(dia):
            r = recetas[rid]
            if r["tiempo_total"] > MAX_TOTAL_SEMANA or r["tiempo_activo"] > MAX_ACTIVO_SEMANA:
                malos.append(f"día {dia} ({nombre_dia(dia)}) {m}: {r['nombre']} {r['tiempo_total']}/{r['tiempo_activo']} min")
            if r["momento"] == "fin de semana":
                malos.append(f"día {dia}: {r['nombre']} está marcada para fin de semana")
    res.append((not malos, f"Días de semana: máximo {MAX_TOTAL_SEMANA} min totales y {MAX_ACTIVO_SEMANA} activos", malos or ["Todas las comidas de lunes a viernes cumplen"]))

    # 3. Sobras y freezer coherentes
    malos = []
    cocinado = {}
    for dia, m, e in lista:
        if "receta" in e:
            cocinado.setdefault(e["receta"], []).append((dia, e.get("porciones", 4)))
        elif "sobra_de" in e:
            prev = [x for x in cocinado.get(e["sobra_de"], []) if 0 <= dia - x[0] <= DIAS_MAX_BASE and x[1] > 4]
            if not prev:
                malos.append(f"día {dia} {m}: sobra de {e['sobra_de']} sin preparación doble en los 3 días previos")
        elif "del_freezer" in e:
            prev = [x for x in cocinado.get(e["del_freezer"], []) if x[1] > 4]
            if not prev or "para freezer" not in recetas[e["del_freezer"]]["etiquetas"]:
                malos.append(f"día {dia} {m}: freezer de {e['del_freezer']} sin preparación doble previa")
    res.append((not malos, "Sobras y porciones del freezer tienen su 'cociná de más' planificado", malos or ["Todas las sobras tienen origen"]))

    # 4. Bases cocidas
    produccion, asign = calcular_bases(config, recetas, cal)
    malos = []
    for dia, m, e in lista:
        rid = e.get("receta")
        if rid and recetas[rid].get("usa_base") and (dia, m) not in asign:
            malos.append(f"día {dia} {m}: {recetas[rid]['nombre']} necesita {recetas[rid]['usa_base']['base']} sin cocinar antes")
    det = malos or [f"día {k[0]} {k[1]}: cocinar {v['cantidad']} g de {v['base']} extra ({v['crudo']} g de {v['ingrediente_crudo'].lower()} crudo) → usos: " + ", ".join(f"día {u[0]}" for u in v['usos']) for k, v in sorted(produccion.items())]
    res.append((not malos, "Toda receta con base cocida (pollo, arroz) tiene esa base planificada antes (máx. 3 días)", det))

    # 5. Proteína seguida
    malos = []
    prots = []
    for dia, m, e in lista:
        rid = e.get("receta") or e.get("sobra_de") or e.get("del_freezer")
        prots.append((dia, m, recetas[rid]["proteina"]))
    for i in range(2, len(prots)):
        if prots[i][2] == prots[i - 1][2] == prots[i - 2][2]:
            malos.append(f"días {prots[i-2][0]}–{prots[i][0]}: 3 comidas seguidas de {prots[i][2]}")
    res.append((not malos, "No hay más de 2 comidas seguidas con la misma proteína", malos or ["Rotación correcta"]))

    # 6. Reglas de contenido
    malos = []
    for r in recetas.values():
        if r["tipo"] == "basico":
            continue
        if len(r["ingredientes"]) > 8:
            malos.append(f"{r['nombre']}: {len(r['ingredientes'])} ingredientes (máx. 8)")
        if not (3 <= len(r["pasos"]) <= 6) and r["tipo"] == "principal":
            malos.append(f"{r['nombre']}: {len(r['pasos'])} pasos")
        if not (4 <= len(r["pasos"]) <= 6) and r["tipo"] == "principal":
            malos.append(f"{r['nombre']}: {len(r['pasos'])} pasos (4 a 6)")
        for campo in ("senales_coccion", "version_chicos", "variante_adultos", "si_te_sobra"):
            if not r.get(campo):
                malos.append(f"{r['nombre']}: falta {campo}")
    con_huevo = [r["nombre"] for r in contables if any(i["item"] == "Huevo" for i in r["ingredientes"])]
    pescado = [r["nombre"] for r in principales if r["proteina"] == "pescado"]
    legumbre = [r["nombre"] for r in contables if r["proteina"] == "legumbre" or any(k in i["item"].lower() for i in r["ingredientes"] for k in ("lenteja", "garbanzo", "poroto"))]
    if len(con_huevo) > 5: malos.append(f"Recetas con huevo: {len(con_huevo)} (máx. 5)")
    if len(pescado) < 4: malos.append(f"Recetas de pescado: {len(pescado)} (mín. 4)")
    if len(legumbre) < 6: malos.append(f"Recetas con legumbres: {len(legumbre)} (mín. 6)")
    if not (40 <= len(contables) <= 45): malos.append(f"Total de recetas: {len(contables)} (40 a 45)")
    det = malos or [
        f"Total de recetas: {len(contables)} ({len(principales)} principales + {len(contables)-len(principales)} de desayunos, colaciones, viandas y postres)",
        f"Recetas con huevo: {len(con_huevo)} (máx. 5)",
        f"Recetas de pescado: {len(pescado)} (mín. 4)",
        f"Recetas con legumbres: {len(legumbre)} (mín. 6)",
        "Todas tienen ≤ 8 ingredientes, 4 a 6 pasos, señales de cocción, versión chicos, variante adultos y 'si te sobra'",
    ]
    res.append((not malos, "Reglas de contenido del recetario", det))

    # 7. Textos internos / relleno / ortografía (solo sobre los textos que lee la clienta)
    textos = list(textos_visibles(json.loads((DATOS / "recetas.json").read_text(encoding="utf-8"))))
    textos += list(textos_visibles(cal))
    texto = "\n".join(textos)
    patrones = [r"antes de publicar", r"(?-i:\bTODO\b)", r"lorem", r"xxx", r"verificar precios", r"\[[^\]]*\]", r"placeholder", r"\?\?", r"completar"]
    hall = [p for p in patrones if re.search(p, texto, re.I)]
    res.append((not hall, "No quedan notas internas ni textos de relleno", hall or [f"{len(textos)} textos revisados, sin notas de producción"]))

    errores = ortografia(texto)
    res.append((errores is not None and not errores, "Ortografía (diccionario español de Argentina + palabras propias)",
                ["No se pudo cargar el diccionario"] if errores is None else
                [f"Palabra no reconocida: {w}" for w in errores] or ["Sin errores ortográficos"]))

    # 8. Lista de compras = suma exacta
    malos = []
    for a, b in semanas():
        tot, _ = lista_compras(config, recetas, cal, a, b)
        control = defaultdict(float)
        for d in cal["dias"]:
            if a <= d["dia"] <= b:
                for m in ("almuerzo", "cena"):
                    e = d[m]
                    if "receta" in e:
                        for i in recetas[e["receta"]]["ingredientes"]:
                            if i.get("es_base"):
                                continue
                            control[(i["sector"], i["item"], i["unidad"])] += i["cantidad"] * factor(e)
                    for i in recetas[d.get(f"postre_{m}", "fruta-estacion")]["ingredientes"]:
                        control[(i["sector"], i["item"], i["unidad"])] += i["cantidad"]
        for k, v in produccion.items():
            if a <= k[0] <= b:
                control[(v["sector"], v["ingrediente_crudo"], "g")] += v["crudo"]
        if {k: round(v, 3) for k, v in tot.items()} != {k: round(v, 3) for k, v in control.items()}:
            malos.append(f"semana días {a}-{b}: no coincide")
    res.append((not malos, "Las listas de compras coinciden exactamente con la suma del calendario", malos or ["Recalculadas por dos caminos distintos: coinciden en las 5 listas"]))
    return res


if __name__ == "__main__":
    import sys
    config, recetas, cal = cargar()
    if "--listas" in sys.argv:
        for a, b in semanas():
            tot, _ = lista_compras(config, recetas, cal, a, b)
            sectores, alacena = lista_para_imprimir(config, tot)
            print(f"\n=== Lista de compras · días {a} a {b} ===")
            for s, items in sectores:
                print(f"  {s.upper()}")
                for x in items:
                    print(f"    [ ] {x['item']}: {x['texto']}" + (f"  ({x['detalle']})" if x["detalle"] else ""))
            print("  REVISÁ EN TU ALACENA: " + ", ".join(alacena))
        sys.exit()
    for ok, t, det in validar(config, recetas, cal):
        print(("✅ " if ok else "❌ ") + t)
        for x in det:
            print("    · " + x)
