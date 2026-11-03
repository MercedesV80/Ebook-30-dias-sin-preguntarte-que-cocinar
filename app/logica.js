/* ==========================================================================
   COMPAÑERO DE 30 DÍAS · MOTOR LÓGICO (FASE 2)
   Porciones, Redondeo Casero, Cambio de Comidas, Dependencias y Compras
   ========================================================================== */

(function (global) {
  "use strict";

  const STORAGE_KEY = "companero30_estado_v1";
  const DIAS_MAX_BASE = 3;
  const MAX_TOTAL_SEMANA = 25;
  const MAX_ACTIVO_SEMANA = 15;

  const UNIDADES_ALACENA = new Set(["cda", "cdita", "pizca"]);
  const PLURAL_UNIDADES = {
    "unidad": "unidades",
    "diente": "dientes",
    "atado": "atados",
    "planta": "plantas",
    "lata": "latas",
    "rebanada": "rebanadas",
    "paquete (2 tapas)": "paquetes (2 tapas c/u)"
  };

  // Mapeo de los sectores internos del JSON a los 7 rubros visibles pedidos
  const RUBROS_ORDEN = [
    { id: "verduras y frutas", titulo: "🥕 Verdulería y frutas" },
    { id: "carnes y huevos", titulo: "🥩 Carnes, pollo, pescado y huevos" },
    { id: "lácteos", titulo: "🧀 Lácteos" },
    { id: "almacén", titulo: "🥫 Almacén" },
    { id: "panificados", titulo: "🍞 Panificados" },
    { id: "freezer", titulo: "🧊 Freezer" },
    { id: "otros", titulo: "🧂 Otros y básicos de alacena" }
  ];

  // Estado persistente del usuario en localStorage
  function crearEstadoInicial() {
    return {
      accesoAutorizado: false,
      fechaInicio: null, // YYYY-MM-DD
      diaSeleccionado: 1,
      semanaSeleccionada: 1,
      modoChicos: false,
      porciones: {
        preset: 4, // 2, 4, 6 o null si es personalizado
        adultos: 4,
        menores4: 0,
        chicos4a8: 0
      },
      // Cambios de comida realizados por el usuario: clave "dia_turno" -> { receta_id, cocina_doble, es_sobra, texto_sobra, ... }
      cambiosCalendario: {},
      // Comidas marcadas como hechas: clave "dia_turno" -> true
      comidasHechas: {},
      // Ingredientes tildados dentro de una receta: clave "recetaId_idx" -> true
      ingredientesRecetaTildados: {},
      // Estado de la lista de compras: clave "semana_rubro_item" -> { tengo: bool, comprado: bool }
      comprasEstado: {},
      // Recetas personales agregadas por la usuaria
      misRecetas: [],
      // Espacio reservado para Segunda Etapa (no activo aún)
      segundaEtapa: {
        favoritos: [],
        notasRecetas: {},
        heladeraItems: [],
        recordatoriosActivos: false
      }
    };
  }

  function cargarEstado() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return crearEstadoInicial();
      const parsed = JSON.parse(raw);
      return Object.assign(crearEstadoInicial(), parsed, {
        porciones: Object.assign(crearEstadoInicial().porciones, parsed.porciones || {})
      });
    } catch (e) {
      return crearEstadoInicial();
    }
  }

  function guardarEstado(estado) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(estado));
    } catch (e) {
      console.warn("No se pudo guardar en localStorage:", e);
    }
  }

  // =========================================================================
  // 1. CÁLCULO DE PORCIONES Y REDONDEO CASERO PRÁCTICO
  // =========================================================================

  function obtenerFactorHogar(porcionesObj) {
    const p = porcionesObj || { preset: 4, adultos: 4, menores4: 0, chicos4a8: 0 };
    if (p.preset === 2) return 0.5;
    if (p.preset === 4) return 1.0;
    if (p.preset === 6) return 1.5;
    // Equivalencia del ebook: menores de 4 años = 1/3 a 1/2 (promedio 0.42); 4 a 8 años = 1/2 a 2/3 (promedio 0.58)
    const equivAdultos = (Number(p.adultos || 0) * 1.0) +
                         (Number(p.menores4 || 0) * 0.42) +
                         (Number(p.chicos4a8 || 0) * 0.58);
    return Math.max(0.25, Math.round((equivAdultos / 4.0) * 100) / 100);
  }

  function describirPorcionesHogar(porcionesObj) {
    const p = porcionesObj || { preset: 4, adultos: 4, menores4: 0, chicos4a8: 0 };
    const factor = obtenerFactorHogar(p);
    const factorStr = String(factor).replace(".", ",");
    if (p.preset) {
      return `${p.preset} personas (factor ${factorStr}x)`;
    }
    const partes = [`${p.adultos} adulto${p.adultos === 1 ? "" : "s"}`];
    if (p.menores4 > 0) partes.push(`${p.menores4} menor${p.menores4 === 1 ? "" : "es"} de 4 años`);
    if (p.chicos4a8 > 0) partes.push(`${p.chicos4a8} chico${p.chicos4a8 === 1 ? "" : "s"} (4-8 años)`);
    return `${partes.join(" + ")} (factor ${factorStr}x)`;
  }

  function formatearFraccionCasera(valor) {
    if (valor <= 0) return "0";
    const entero = Math.floor(valor);
    const frac = valor - entero;
    let fracTxt = "";
    if (frac >= 0.88) {
      return String(entero + 1);
    } else if (frac >= 0.63) {
      fracTxt = "3/4";
    } else if (frac >= 0.38) {
      fracTxt = "1/2";
    } else if (frac >= 0.15) {
      fracTxt = "1/4";
    }
    if (entero === 0) {
      return fracTxt || "1/4";
    }
    return fracTxt ? `${entero} y ${fracTxt}` : String(entero);
  }

  // Redondeo para mostrar dentro de la ficha de receta (medidas caseras prácticas)
  function cantidadPracticaReceta(cantidadBase, unidad, factorHogar) {
    const f = typeof factorHogar === "number" ? factorHogar : 1.0;
    const val = cantidadBase * f;

    if (unidad === "g") {
      if (val >= 1000) {
        const kg = Math.round((val / 1000) * 20) / 20; // pasos de 0,05 kg (50 g)
        return `${String(kg).replace(".", ",")} kg`;
      }
      let red;
      if (val < 40) {
        red = Math.max(5, Math.round(val / 5) * 5);
      } else if (val < 200) {
        red = Math.round(val / 10) * 10;
      } else {
        red = Math.round(val / 25) * 25;
      }
      return `${red} g`;
    }

    if (unidad === "ml") {
      if (val >= 1000) {
        const lt = Math.round((val / 1000) * 20) / 20;
        return `${String(lt).replace(".", ",")} litros`;
      }
      const red = val < 100 ? Math.max(10, Math.round(val / 10) * 10) : Math.round(val / 25) * 25;
      return `${red} ml`;
    }

    if (unidad === "cda" || unidad === "cdita") {
      const fTxt = formatearFraccionCasera(val);
      if (unidad === "cdita") {
        return fTxt === "1" ? "1 cucharadita" : `${fTxt} cucharaditas`;
      }
      return fTxt === "1" ? "1 cucharada" : `${fTxt} cucharadas`;
    }

    if (unidad === "pizca") {
      return "1 pizca";
    }

    const fTxt = formatearFraccionCasera(val);
    const nombreUnidad = (fTxt === "1" || fTxt === "1/4" || fTxt === "1/2" || fTxt === "3/4")
      ? unidad
      : (PLURAL_UNIDADES[unidad] || unidad);
    return `${fTxt} ${nombreUnidad}`;
  }

  // Formato exacto estilo Ebook (motor.py) para las sumas semanales de compras
  function numeroArgentino(x) {
    if (Math.abs(x - Math.round(x)) < 1e-6) {
      return Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }
    // Redondear a medidas prácticas si quedó decimal por el factor de chicos
    const limpio = Math.round(x * 100) / 100;
    return limpio.toFixed(2).replace(/\.?0+$/, "").replace(".", ",");
  }

  function cantidadLegibleCompra(cant, unidad) {
    if (unidad === "g") {
      const c = Math.round(cant / 5) * 5;
      return c >= 1000 ? `${numeroArgentino(c / 1000)} kg` : `${numeroArgentino(c)} g`;
    }
    if (unidad === "ml") {
      const c = Math.round(cant / 5) * 5;
      return c >= 1000 ? `${numeroArgentino(c / 1000)} litros` : `${numeroArgentino(c)} ml`;
    }
    if (unidad === "cdita") {
      return cant > 1 ? `${formatearFraccionCasera(cant)} cucharaditas` : "1 cucharadita";
    }
    if (unidad === "cda") {
      return cant > 1 ? `${formatearFraccionCasera(cant)} cucharadas` : "1 cucharada";
    }
    // Si es unidad contable (cebollas, huevos, latas), en la lista de compras redondeamos hacia arriba si hay fracción
    const cantCompra = Math.ceil(cant - 1e-6);
    const u = cantCompra === 1 ? unidad : (PLURAL_UNIDADES[unidad] || unidad);
    return `${numeroArgentino(cantCompra)} ${u}`;
  }

  // =========================================================================
  // 2. CALENDARIO ACTIVO Y MOTOR DE DEPENDENCIAS (SOBRAS Y BASES)
  // =========================================================================

  function mapaRecetas(appData, estado) {
    const map = {};
    (appData.recetas || []).forEach(r => { map[r.id] = r; });
    if (estado && Array.isArray(estado.misRecetas)) {
      estado.misRecetas.forEach(r => { map[r.id] = r; });
    }
    return map;
  }

  // Devuelve una copia del calendario de 30 días aplicando los cambios del usuario
  function obtenerCalendarioActivo(appData, estado) {
    const cambios = (estado && estado.cambiosCalendario) || {};
    const recetasPorId = mapaRecetas(appData, estado);

    const dias = appData.calendario.map(diaOrig => {
      const d = JSON.parse(JSON.stringify(diaOrig));
      ["almuerzo", "cena"].forEach(turno => {
        const clave = `${d.dia}_${turno}`;
        if (cambios[clave]) {
          Object.assign(d[turno], cambios[clave]);
        }
      });
      return d;
    });

    // Recalcular bases dinámicamente igual que motor.calcular_bases
    const lista = [];
    dias.forEach(d => {
      lista.push({ dia: d.dia, turno: "almuerzo", slot: d.almuerzo, diaObj: d });
      lista.push({ dia: d.dia, turno: "cena", slot: d.cena, diaObj: d });
    });

    const produccion = {}; // "dia_turno" -> { base, cantidad, crudo, usos: [] }
    const asignacion = {}; // "dia_turno" -> { dia, turno }

    for (let i = 0; i < lista.length; i++) {
      const item = lista[i];
      if (item.slot.es_sobra) continue;
      const rid = item.slot.receta_id || item.slot.receta;
      const rec = recetasPorId[rid];
      if (!rec || !rec.usa_base) continue;

      const ub = rec.usa_base;
      let origen = null;
      for (let j = i - 1; j >= 0; j--) {
        const prev = lista[j];
        if (item.dia - prev.dia > DIAS_MAX_BASE) break;
        if (prev.slot.es_sobra) continue;
        const prevRid = prev.slot.receta_id || prev.slot.receta;
        const prevRec = recetasPorId[prevRid];
        // También puede haberse mantenido la producción de base aunque se haya cambiado el plato principal
        const genera = (prevRec && prevRec.genera_base === ub.base) || (prev.slot.forzar_base === ub.base);
        if (genera) {
          origen = { dia: prev.dia, turno: prev.turno };
          break;
        }
      }

      if (origen) {
        const kOrig = `${origen.dia}_${origen.turno}`;
        asignacion[`${item.dia}_${item.turno}`] = origen;
        if (!produccion[kOrig]) {
          produccion[kOrig] = { base: ub.base, cantidad: 0, usos: [] };
        }
        produccion[kOrig].cantidad += ub.cantidad;
        produccion[kOrig].usos.push({ dia: item.dia, turno: item.turno, receta_id: rid });
      }
    }

    Object.keys(produccion).forEach(kOrig => {
      const p = produccion[kOrig];
      const bCfg = appData.config.bases[p.base];
      if (p.base === "pollo cocido") {
        p.crudo = p.cantidad <= 600 ? 900 : 1300;
      } else {
        p.crudo = Math.ceil(p.cantidad / bCfg.rinde / 50.0) * 50;
      }
      p.ingrediente_crudo = bCfg.ingrediente_crudo;
      p.sector = bCfg.sector;
    });

    // Anotar en cada slot del calendario activo
    dias.forEach(d => {
      ["almuerzo", "cena"].forEach(turno => {
        const k = `${d.dia}_${turno}`;
        const p = produccion[k];
        if (p) {
          d[turno].batch_base = {
            base: p.base,
            cantidad_cocida: p.cantidad,
            ingrediente_crudo: p.ingrediente_crudo,
            cantidad_cruda: p.crudo,
            unidad: "g",
            sector: p.sector,
            usos_dias: p.usos
          };
        } else {
          d[turno].batch_base = null;
        }
        d[turno].consume_base_de = asignacion[k] || null;
      });
    });

    return dias;
  }

  // =========================================================================
  // 3. RECOMENDADOR DE CAMBIO DE COMIDA Y AVISO DE DEPENDENCIAS
  // =========================================================================

  function AnalizarImpactoYAlternativas(appData, estado, diaNum, turno) {
    const dias = obtenerCalendarioActivo(appData, estado);
    const recetasPorId = mapaRecetas(appData, estado);
    const diaObj = dias.find(x => x.dia === diaNum);
    if (!diaObj) return null;

    const slotActual = diaObj[turno];
    const recetaActual = recetasPorId[slotActual.receta_id];
    const esFinde = diaObj.es_finde;

    // 1. Detectar dependencias que se ven afectadas al cambiar este turno
    const avisosDependencia = [];

    // Caso A: Este turno cocina doble (x8 porciones) para alimentar sobras de otro día
    if (slotActual.cocina_doble && slotActual.alimenta_sobras && slotActual.alimenta_sobras.length > 0) {
      slotActual.alimenta_sobras.forEach(dest => {
        const tipoTxt = dest.tipo_sobra === "freezer" ? "en el freezer" : "en la heladera (máx. 3 días)";
        avisosDependencia.push({
          tipo: "alimenta_sobras",
          destino_dia: dest.dia,
          destino_turno: dest.turno,
          mensaje: `Esta comida estaba pensada para cocinar doble (x8 porciones) y guardar la mitad ${tipoTxt} para el Día ${dest.dia} (${dest.turno}).`,
          solucionPropuesta: `Al cambiarla, podemos hacer que la nueva receta también se cocine doble para resolver el Día ${dest.dia}, o elegir otra comida rápida para ese día.`
        });
      });
    }

    // Caso B: Este turno generaba una base cocida (pollo cocido o arroz extra) para los próximos 3 días
    if (slotActual.batch_base && slotActual.batch_base.usos_dias.length > 0) {
      const b = slotActual.batch_base;
      const diasUsos = b.usos_dias.map(u => `Día ${u.dia} (${u.turno})`).join(", ");
      avisosDependencia.push({
        tipo: "genera_base",
        base: b.base,
        usos: b.usos_dias,
        mensaje: `En este turno también se adelantaba la base de «${b.base}» que se usa en: ${diasUsos}.`,
        solucionPropuesta: `Si cambiás este plato, te mantenemos igual el recordatorio de dejar lista la base de ${b.base} hoy para no afectar tus comidas de los próximos 3 días.`
      });
    }

    // Caso C: Este turno consumía sobras de un día anterior
    if (slotActual.es_sobra && slotActual.origen_dia) {
      avisosDependencia.push({
        tipo: "es_sobra",
        origen_dia: slotActual.origen_dia,
        origen_turno: slotActual.origen_turno,
        mensaje: `Hoy tocaban las «${slotActual.texto_sobra}».`,
        solucionPropuesta: `Si preferís cocinar algo fresco hoy, recordá consumir esas sobras dentro de los 3 días de cocinadas o guardarlas en el freezer a tiempo.`
      });
    }

    // Caso D: Este turno consumía una base cocida (pollo o arroz) preparada antes
    if (slotActual.consume_base_de && recetaActual && recetaActual.usa_base) {
      const orig = slotActual.consume_base_de;
      avisosDependencia.push({
        tipo: "consume_base",
        origen_dia: orig.dia,
        base: recetaActual.usa_base.base,
        mensaje: `Esta receta usaba una parte de la base de «${recetaActual.usa_base.base}» preparada el Día ${orig.dia}.`,
        solucionPropuesta: `Como las bases cocidas duran máximo 3 días en heladera (hasta el Día ${orig.dia + 3}), si hoy elegís otro plato podés congelar esa porción de base en el freezer.`
      });
    }

    // 2. Recopilar recetas cocinadas en los últimos 2 días y próximos 2 días para no repetir
    const idsCercanos = new Set();
    if (slotActual.receta_id) idsCercanos.add(slotActual.receta_id);

    dias.forEach(d => {
      if (Math.abs(d.dia - diaNum) <= 2) {
        ["almuerzo", "cena"].forEach(t => {
          const rid = d[t].receta_id || d[t].receta;
          if (rid) idsCercanos.add(rid);
        });
      }
    });

    // 3. Filtrar las 32 recetas principales candidatas
    const principales = appData.recetas.filter(r => r.tipo === "principal");
    const candidatas = principales.filter(r => {
      // No repetir lo cocinado en ventana de ±2 días
      if (idsCercanos.has(r.id)) return false;

      // En lunes a viernes: máximo 25 min totales y 15 min activos
      if (!esFinde) {
        if (r.tiempo_total > MAX_TOTAL_SEMANA || r.tiempo_activo > MAX_ACTIVO_SEMANA) {
          return false;
        }
      }

      // Si la candidata requiere una base cocida (pollo o arroz), solo sugerirla si esa base ya está disponible en los 3 días previos
      if (r.usa_base) {
        let baseDisponible = false;
        for (let dPrev = Math.max(1, diaNum - DIAS_MAX_BASE); dPrev <= diaNum; dPrev++) {
          const dObj = dias.find(x => x.dia === dPrev);
          if (!dObj) continue;
          ["almuerzo", "cena"].forEach(tPrev => {
            // No contar el propio turno que se está reemplazando ni turnos posteriores del mismo día
            if (dPrev === diaNum) {
              if (turno === "almuerzo") return;
              if (turno === "cena" && tPrev === "cena") return;
            }
            const sPrev = dObj[tPrev];
            if (sPrev.batch_base && sPrev.batch_base.base === r.usa_base.base) {
              baseDisponible = true;
            }
          });
        }
        if (!baseDisponible) return false;
      }

      return true;
    });

    // Ordenar candidatas priorizando:
    // 1) Misma proteína que la comida original
    // 2) Menor tiempo total (más rápida)
    const protOriginal = recetaActual ? recetaActual.proteina : "";
    candidatas.sort((a, b) => {
      const aMismaProt = a.proteina === protOriginal ? 0 : 1;
      const bMismaProt = b.proteina === protOriginal ? 0 : 1;
      if (aMismaProt !== bMismaProt) return aMismaProt - bMismaProt;
      return a.tiempo_total - b.tiempo_total;
    });

    const tresAlternativas = candidatas.slice(0, 3).map(r => ({
      receta: r,
      motivo: r.proteina === protOriginal
        ? `Misma proteína (${r.proteina}) · ${r.tiempo_total} min`
        : `Alternativa rápida (${r.proteina}) · ${r.tiempo_total} min`
    }));

    return {
      dia: diaNum,
      turno: turno,
      esFinde: esFinde,
      slotActual: slotActual,
      recetaActual: recetaActual,
      avisosDependencia: avisosDependencia,
      alternativas: tresAlternativas
    };
  }

  function ejecutarCambioComida(appData, estado, diaNum, turno, nuevaRecetaId, opcionesResolucion) {
    const opts = opcionesResolucion || {};
    const recetasPorId = mapaRecetas(appData, estado);
    const nuevaRec = recetasPorId[nuevaRecetaId];
    if (!nuevaRec) return estado;

    const dias = obtenerCalendarioActivo(appData, estado);
    const diaObj = dias.find(x => x.dia === diaNum);
    const slotViejo = diaObj[turno];
    const clave = `${diaNum}_${turno}`;

    const nuevoSlot = {
      receta: nuevaRecetaId,
      receta_id: nuevaRecetaId,
      es_sobra: false,
      texto_sobra: null,
      porciones: slotViejo.cocina_doble && opts.mantenerCocinaDoble !== false ? 8 : 4,
      cocina_doble: slotViejo.cocina_doble && opts.mantenerCocinaDoble !== false,
      etiqueta_doble: (slotViejo.cocina_doble && opts.mantenerCocinaDoble !== false) ? "x8 porciones (cocinar doble)" : ""
    };

    // Si este turno generaba una base para otros días, conservamos la marca forzar_base para no romper los días siguientes
    if (slotViejo.batch_base && slotViejo.batch_base.usos_dias.length > 0) {
      nuevoSlot.forzar_base = slotViejo.batch_base.base;
    }

    estado.cambiosCalendario[clave] = nuevoSlot;

    // Si este turno alimentaba sobras en otro día:
    if (slotViejo.alimenta_sobras && slotViejo.alimenta_sobras.length > 0) {
      slotViejo.alimenta_sobras.forEach(dest => {
        const claveDest = `${dest.dia}_${dest.turno}`;
        if (opts.mantenerCocinaDoble !== false) {
          // Actualizar el texto de la sobra en el día destino con el nombre de la nueva receta
          const nombreCorto = nuevaRec.nombre.split(" con ")[0].toLowerCase();
          const tipoTexto = dest.tipo_sobra === "freezer"
            ? `del freezer (cocinado el día ${diaNum})`
            : `(cocinado el día ${diaNum})`;
          estado.cambiosCalendario[claveDest] = {
            sobra_de: nuevaRecetaId,
            receta_id: nuevaRecetaId,
            es_sobra: true,
            texto_sobra: `Sobras de ${nombreCorto} ${tipoTexto}`,
            origen_dia: diaNum,
            origen_turno: turno,
            tipo_sobra: dest.tipo_sobra
          };
        }
      });
    }

    guardarEstado(estado);
    return estado;
  }

  // =========================================================================
  // 4. GENERADOR DE LISTAS DE COMPRAS SEMANALES Y DE EXTRAS
  // =========================================================================

  function rangosSemanas() {
    return [
      { numero: 1, desde: 1, hasta: 7, titulo: "Semana 1 (Días 1 a 7)" },
      { numero: 2, desde: 8, hasta: 14, titulo: "Semana 2 (Días 8 a 14)" },
      { numero: 3, desde: 15, hasta: 21, titulo: "Semana 3 (Días 15 a 21)" },
      { numero: 4, desde: 22, hasta: 28, titulo: "Semana 4 (Días 22 a 28)" },
      { numero: 5, desde: 29, hasta: 30, titulo: "Cierre de mes (Días 29 y 30)" }
    ];
  }

  function calcularListaComprasSemana(appData, estado, desde, hasta) {
    const dias = obtenerCalendarioActivo(appData, estado);
    const recetasPorId = mapaRecetas(appData, estado);
    const factorHogar = obtenerFactorHogar(estado ? estado.porciones : null);
    const pres = appData.config.presentaciones || {};

    // Acumulador: clave "sector||item||unidad" -> { sector, item, unidad, cantidad, origenes: [] }
    const tot = {};

    function sumarIngrediente(sector, item, unidad, cant, origenTxt) {
      const k = `${sector}||${item}||${unidad}`;
      if (!tot[k]) {
        tot[k] = { sector, item, unidad, cantidad: 0, origenes: [] };
      }
      tot[k].cantidad += cant;
      if (origenTxt && !tot[k].origenes.includes(origenTxt)) {
        tot[k].origenes.push(origenTxt);
      }
    }

    function sumarReceta(rid, factorSlot, origenTxt) {
      const rec = recetasPorId[rid];
      if (!rec) return;
      (rec.ingredientes || []).forEach(ing => {
        if (ing.es_base) return; // La base se suma como ingrediente crudo en el día que se cocina
        sumarIngrediente(ing.sector, ing.item, ing.unidad, ing.cantidad * factorSlot * factorHogar, origenTxt);
      });
    }

    const notasBatchSemana = [];
    const comidasFreezerSemana = [];

    dias.forEach(d => {
      if (d.dia < desde || d.dia > hasta) return;

      ["almuerzo", "cena"].forEach(turno => {
        const slot = d[turno];
        if (!slot.es_sobra && slot.receta_id) {
          const factorDoble = slot.cocina_doble ? 2.0 : (slot.porciones ? slot.porciones / 4.0 : 1.0);
          sumarReceta(slot.receta_id, factorDoble, `Día ${d.dia} (${turno})`);

          // Si este turno produce una base cocida (pollo o arroz extra), sumar el ingrediente crudo igual que motor.py
          if (slot.batch_base) {
            const b = slot.batch_base;
            const cantCrudaEscalada = b.cantidad_cruda * factorHogar;
            sumarIngrediente(b.sector, b.ingrediente_crudo, "g", cantCrudaEscalada, `Día ${d.dia} (base de ${b.base})`);
            notasBatchSemana.push({
              dia: d.dia,
              turno: turno,
              base: b.base,
              ingrediente: b.ingrediente_crudo,
              cantidadTexto: cantidadLegibleCompra(cantCrudaEscalada, "g")
            });
          }
        } else if (slot.es_sobra && slot.tipo_sobra === "freezer") {
          comidasFreezerSemana.push({
            dia: d.dia,
            turno: turno,
            texto: slot.texto_sobra
          });
        }

        // Sumar el postre del turno (fruta-estacion o postre dulce) igual que motor.py
        const postreId = d[`postre_${turno}`] || "fruta-estacion";
        sumarReceta(postreId, 1.0, `Día ${d.dia} postre`);
      });
    });

    return construirRubrosParaUI(tot, pres, comidasFreezerSemana, notasBatchSemana);
  }

  function calcularListaComprasExtras(appData, estado) {
    const factorHogar = obtenerFactorHogar(estado ? estado.porciones : null);
    const pres = appData.config.presentaciones || {};
    const tot = {};

    const extrasRecetas = appData.recetas.filter(r =>
      ["desayuno", "colacion", "vianda", "postre"].includes(r.tipo)
    );

    extrasRecetas.forEach(r => {
      (r.ingredientes || []).forEach(ing => {
        const k = `${ing.sector}||${ing.item}||${ing.unidad}`;
        if (!tot[k]) {
          tot[k] = { sector: ing.sector, item: ing.item, unidad: ing.unidad, cantidad: 0, origenes: [] };
        }
        tot[k].cantidad += ing.cantidad * factorHogar;
        tot[k].origenes.push(r.nombre);
      });
    });

    return construirRubrosParaUI(tot, pres, [], []);
  }

  function construirRubrosParaUI(totMap, pres, comidasFreezerSemana, notasBatchSemana) {
    const porSector = {};
    RUBROS_ORDEN.forEach(r => { porSector[r.id] = []; });
    const alacenaSet = new Set();

    Object.values(totMap).forEach(entry => {
      const { sector, item, unidad, cantidad } = entry;
      if (UNIDADES_ALACENA.has(unidad)) {
        alacenaSet.add(item);
        return;
      }

      let texto = "";
      let detalle = "";
      if (pres[item]) {
        const p = pres[item];
        const cantRedondeada = Math.round(cantidad * 1000000) / 1000000;
        const n = Math.max(1, Math.ceil(Math.round((cantRedondeada / p.tamano) * 1000000) / 1000000));
        texto = `${n} ${n === 1 ? p.envase : p.envases}`;
        detalle = `usás ${cantidadLegibleCompra(cantidad, unidad)}`;
      } else {
        texto = cantidadLegibleCompra(cantidad, unidad);
        detalle = "";
      }

      const secDestino = porSector[sector] ? sector : "otros";
      porSector[secDestino].push({
        id: `${secDestino}_${item}`,
        item: item,
        texto: texto,
        detalle: detalle,
        cantidadCruda: cantidad,
        unidad: unidad
      });
    });

    // Quitar de alacena lo que ya figura con envase propio (ej. azúcar mascabo)
    const itemsConEnvase = new Set();
    Object.values(porSector).forEach(lista => {
      lista.forEach(x => itemsConEnvase.add(x.item));
    });

    alacenaSet.forEach(itemAlacena => {
      if (!itemsConEnvase.has(itemAlacena)) {
        porSector["otros"].push({
          id: `otros_${itemAlacena}`,
          item: itemAlacena,
          texto: "Revisar en tu alacena",
          detalle: "se usa por cucharada/pizca",
          esAlacena: true
        });
      }
    });

    // Agregar recordatorios de Freezer si esa semana se baja algo del freezer
    (comidasFreezerSemana || []).forEach(cf => {
      porSector["freezer"].push({
        id: `freezer_dia_${cf.dia}`,
        item: cf.texto,
        texto: `Bajar a heladera 24 h antes (Día ${cf.dia})`,
        detalle: "Ya cocinado y guardado en tu freezer",
        esRecordatorioFreezer: true
      });
    });

    const rubrosFinales = RUBROS_ORDEN.map(r => {
      const itemsOrdenados = (porSector[r.id] || []).sort((a, b) => a.item.localeCompare(b.item, "es"));
      return {
        id: r.id,
        titulo: r.titulo,
        items: itemsOrdenados
      };
    });

    return {
      rubros: rubrosFinales,
      notasBatch: notasBatchSemana
    };
  }

  function formatearListaWhatsApp(tituloLista, resultadoLista, estadoComprasSemana, descripcionPorciones) {
    const est = estadoComprasSemana || {};
    const lineas = [
      `🛒 *${tituloLista.toUpperCase()}*`,
      `👨‍👩‍👧‍👦 _Calculado para: ${descripcionPorciones}_`,
      ""
    ];

    let totalPendientes = 0;
    resultadoLista.rubros.forEach(rubro => {
      const pendientesRubro = rubro.items.filter(it => {
        const st = est[it.id] || {};
        return !st.tengo && !st.comprado;
      });
      if (pendientesRubro.length === 0) return;

      lineas.push(`*${rubro.titulo}*`);
      pendientesRubro.forEach(it => {
        totalPendientes++;
        const det = it.detalle ? ` _(${it.detalle})_` : "";
        lineas.push(`▫️ ${it.item}: *${it.texto}*${det}`);
      });
      lineas.push("");
    });

    if (totalPendientes === 0) {
      lineas.push("🎉 ¡Ya tenés todos los ingredientes cubiertos para esta semana!");
    } else {
      lineas.push("_Generado con Compañero de 30 días · Saso Digital_");
    }

    return lineas.join("\n");
  }

  // =========================================================================
  // 5. HOY NO PUEDO (≤ 15 MINUTOS + FILTRO DE INGREDIENTES + PLAN C)
  // =========================================================================

  const INGREDIENTES_COMODIN = [
    { id: "queso", etiqueta: "🧀 Queso (fresco, fetas o untable)", palabras: ["queso"] },
    { id: "tomate", etiqueta: "🍅 Tomate", palabras: ["tomate"] },
    { id: "pan", etiqueta: "🫓 Pan árabe / Tortillas / Pan", palabras: ["pan árabe", "tortillas", "pan "] },
    { id: "choclo", etiqueta: "🌽 Choclo en lata", palabras: ["choclo"] },
    { id: "legumbres", etiqueta: "🥫 Lentejas / Porotos / Garbanzos (lata)", palabras: ["porotos", "garbanzos", "lentejas"] },
    { id: "arroz_fideos", etiqueta: "🍚 Arroz cocido o Fideos", palabras: ["arroz", "fideos"] },
    { id: "huevo", etiqueta: "🥚 Huevos", palabras: ["huevo"] },
    { id: "atun", etiqueta: "🐟 Atún en lata", palabras: ["atún"] },
    { id: "pollo", etiqueta: "🍗 Pollo cocido", palabras: ["pollo"] },
    { id: "zanahoria", etiqueta: "🥕 Zanahoria", palabras: ["zanahoria"] }
  ];

  function recomendarHoyNoPuedo(appData, idsIngredientesSeleccionados, estado) {
    const seleccionados = new Set(idsIngredientesSeleccionados || []);
    const comodinesActivos = INGREDIENTES_COMODIN.filter(c => seleccionados.has(c.id));

    const todasRecetas = (appData.recetas || []).concat((estado && estado.misRecetas) || []);

    // Candidatas de <= 15 min totales (principales y viandas salvavidas completas)
    const candidatas = todasRecetas.filter(r =>
      r.tiempo_total <= 15 &&
      ["principal", "vianda"].includes(r.tipo)
    );

    const evaluadas = candidatas.map(r => {
      const textoIngs = (r.ingredientes || []).map(i => i.item.toLowerCase()).join(" | ");
      const coincidencias = [];
      comodinesActivos.forEach(c => {
        if (c.palabras.some(pal => textoIngs.includes(pal))) {
          coincidencias.push(c.etiqueta.replace(/^[^\s]+\s/, ""));
        }
      });
      return {
        receta: r,
        puntos: coincidencias.length,
        coincidencias: coincidencias,
        esPrincipal: r.tipo === "principal" ? 1 : 0
      };
    });

    evaluadas.sort((a, b) => {
      if (b.puntos !== a.puntos) return b.puntos - a.puntos;
      if (b.esPrincipal !== a.esPrincipal) return b.esPrincipal - a.esPrincipal;
      return a.receta.tiempo_total - b.receta.tiempo_total;
    });

    return evaluadas.slice(0, 3);
  }

  // =========================================================================
  // 6. PROGRESO SIN CULPA Y "RETOMAR DESDE HOY"
  // =========================================================================

  function calcularProgresoSinCulpa(estado) {
    const hechasMap = (estado && estado.comidasHechas) || {};
    let comidasResueltas = 0;
    const diasConActividad = new Set();

    for (let d = 1; d <= 30; d++) {
      ["almuerzo", "cena"].forEach(t => {
        if (hechasMap[`${d}_${t}`]) {
          comidasResueltas++;
          diasConActividad.add(d);
        }
      });
    }

    const porcentaje = Math.min(100, Math.round((comidasResueltas / 60) * 100));
    let mensajeAnimo = "🌱 Empezá a tu propio ritmo. Cada comida que resolvés sin estrés ya suma tranquilidad a tu semana.";
    if (comidasResueltas >= 60) {
      mensajeAnimo = "🎉 ¡Felicitaciones a todo el hogar! Completaron las 60 comidas del plan comiendo rico, casero y en paz.";
    } else if (comidasResueltas >= 30) {
      mensajeAnimo = "💛 ¡Más de la mitad del recorrido resuelto! Tu cocina ya trabaja a favor de tu tiempo y tranquilidad.";
    } else if (comidasResueltas >= 10) {
      mensajeAnimo = "🌿 ¡Qué buen ritmo familiar! Cada plato planificado es una noche menos preguntándote qué cocinar.";
    } else if (comidasResueltas >= 1) {
      mensajeAnimo = "✨ ¡Excelente comienzo! Recordá que el plan se adapta a tu vida real y no al revés.";
    }

    // Encontrar el primer día que aún tiene alguna comida pendiente
    let proximoDiaPendiente = 1;
    for (let d = 1; d <= 30; d++) {
      if (!hechasMap[`${d}_almuerzo`] || !hechasMap[`${d}_cena`]) {
        proximoDiaPendiente = d;
        break;
      }
    }

    // Si hay fecha de inicio, calcular qué día calendario sería hoy (sin culpa si difiere)
    let diaSegunFecha = null;
    let hayDiasSalteados = false;
    if (estado && estado.fechaInicio) {
      const partes = estado.fechaInicio.split("-");
      if (partes.length === 3) {
        const fIni = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0);
        const diffDias = Math.floor((hoy.getTime() - fIni.getTime()) / (1000 * 60 * 60 * 24)) + 1;
        if (diffDias >= 1 && diffDias <= 60) {
          diaSegunFecha = Math.min(30, diffDias);
          if (diaSegunFecha > proximoDiaPendiente) {
            hayDiasSalteados = true;
          }
        }
      }
    }

    return {
      comidasResueltas,
      totalComidas: 60,
      diasActivos: diasConActividad.size,
      porcentaje,
      mensajeAnimo,
      proximoDiaPendiente,
      diaSegunFecha,
      hayDiasSalteados
    };
  }

  function retomarDesdeHoy(estado) {
    const prog = calcularProgresoSinCulpa(estado);
    const diaRetomar = prog.proximoDiaPendiente || 1;
    // Ajustar la fecha de inicio para que el día pendiente sea exactamente hoy
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const nuevaFechaInicio = new Date(hoy.getTime() - (diaRetomar - 1) * 24 * 60 * 60 * 1000);
    const yyyy = nuevaFechaInicio.getFullYear();
    const mm = String(nuevaFechaInicio.getMonth() + 1).padStart(2, "0");
    const dd = String(nuevaFechaInicio.getDate()).padStart(2, "0");

    estado.fechaInicio = `${yyyy}-${mm}-${dd}`;
    estado.diaSeleccionado = diaRetomar;
    guardarEstado(estado);
    return diaRetomar;
  }

  // =========================================================================
  // 7. GESTIÓN DE "MIS RECETAS" (RECETARIO PERSONAL DEL HOGAR)
  // =========================================================================

  function guardarRecetaPersonal(estado, datosReceta) {
    if (!Array.isArray(estado.misRecetas)) {
      estado.misRecetas = [];
    }
    const id = datosReceta.id || `personal-${Date.now()}`;
    const tiempoTotal = Math.max(1, Number(datosReceta.tiempo_total) || 20);
    const tiempoActivo = Math.max(1, Number(datosReceta.tiempo_activo) || Math.min(15, tiempoTotal));

    const etiquetas = ["receta personal"];
    if (datosReceta.apta_chicos) {
      etiquetas.push("apta para chicos");
    }

    const ingredientesLimpios = (datosReceta.ingredientes || [])
      .filter(i => i && String(i.item || "").trim() !== "")
      .map(i => ({
        item: String(i.item).trim(),
        cantidad: Math.max(0.25, Number(i.cantidad) || 1),
        unidad: i.unidad || "unidad",
        sector: i.sector || "almacén"
      }));

    const pasosLimpios = (datosReceta.pasos || [])
      .map(p => String(p || "").trim())
      .filter(p => p !== "");

    const nueva = {
      id: id,
      es_personal: true,
      nombre: String(datosReceta.nombre || "Mi receta casera").trim(),
      tipo: "principal",
      proteina: datosReceta.proteina || "pollo",
      tiempo_total: tiempoTotal,
      tiempo_activo: tiempoActivo,
      porciones_base: 4,
      dificultad: "fácil",
      etiquetas: etiquetas,
      apta_chicos: !!datosReceta.apta_chicos,
      ingredientes: ingredientesLimpios.length > 0 ? ingredientesLimpios : [
        { item: "Ingredientes a gusto", cantidad: 1, unidad: "unidad", sector: "otros" }
      ],
      pasos: pasosLimpios.length > 0 ? pasosLimpios : [
        "Preparar según tu costumbre familiar y servir caliente."
      ],
      version_chicos: datosReceta.version_chicos ? String(datosReceta.version_chicos).trim() : "",
      variante_adultos: datosReceta.variante_adultos ? String(datosReceta.variante_adultos).trim() : "",
      si_te_sobra: "Refrigerar antes de las 2 horas de cocinado en recipiente tapado. Consumir dentro de los 3 días o llevar al freezer.",
      tiene_imagen: false,
      imagen_url: null
    };

    const idxExistente = estado.misRecetas.findIndex(r => r.id === id);
    if (idxExistente >= 0) {
      estado.misRecetas[idxExistente] = nueva;
    } else {
      estado.misRecetas.unshift(nueva);
    }

    guardarEstado(estado);
    return nueva;
  }

  function eliminarRecetaPersonal(estado, recetaId) {
    if (!Array.isArray(estado.misRecetas)) return;
    estado.misRecetas = estado.misRecetas.filter(r => r.id !== recetaId);
    // Si estaba asignada en algún cambio del calendario, restaurar el turno original
    if (estado.cambiosCalendario) {
      Object.keys(estado.cambiosCalendario).forEach(k => {
        const slot = estado.cambiosCalendario[k];
        if (slot && (slot.receta_id === recetaId || slot.sobra_de === recetaId)) {
          delete estado.cambiosCalendario[k];
        }
      });
    }
    guardarEstado(estado);
  }

  function formatearMisRecetasWhatsApp(estado, descripcionPorciones) {
    const lista = (estado && estado.misRecetas) || [];
    const factor = obtenerFactorHogar(estado ? estado.porciones : null);
    if (lista.length === 0) {
      return "📒 Todavía no tenés recetas propias guardadas en Mis Recetas.";
    }
    const lineas = [
      `📒 *MIS RECETAS FAMILIARES (${lista.length})*`,
      `👨‍👩‍👧‍👦 _Cantidades para: ${descripcionPorciones}_`,
      ""
    ];
    lista.forEach((r, idx) => {
      lineas.push(`*${idx + 1}. ${r.nombre}* (${r.tiempo_total} min · ${r.proteina})`);
      (r.ingredientes || []).forEach(ing => {
        const cantTxt = cantidadPracticaReceta(ing.cantidad, ing.unidad, factor);
        lineas.push(`  • ${ing.item}: ${cantTxt}`);
      });
      if (r.pasos && r.pasos.length > 0) {
        lineas.push(`  _Preparación:_ ${r.pasos.join(" ")}`);
      }
      lineas.push("");
    });
    lineas.push("_Respaldo generado desde Compañero de 30 días · Saso Digital_");
    return lineas.join("\n");
  }

  // Exportar API global
  global.MotorCompanero = {
    STORAGE_KEY,
    RUBROS_ORDEN,
    INGREDIENTES_COMODIN,
    cargarEstado,
    guardarEstado,
    crearEstadoInicial,
    obtenerFactorHogar,
    describirPorcionesHogar,
    cantidadPracticaReceta,
    cantidadLegibleCompra,
    obtenerCalendarioActivo,
    AnalizarImpactoYAlternativas,
    ejecutarCambioComida,
    rangosSemanas,
    calcularListaComprasSemana,
    calcularListaComprasExtras,
    formatearListaWhatsApp,
    recomendarHoyNoPuedo,
    calcularProgresoSinCulpa,
    retomarDesdeHoy,
    guardarRecetaPersonal,
    eliminarRecetaPersonal,
    formatearMisRecetasWhatsApp
  };

})(window);
