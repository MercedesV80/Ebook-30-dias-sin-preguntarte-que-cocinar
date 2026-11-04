/* ==========================================================================
   COMPAÑERO DE 30 DÍAS · CONTROLADOR DE INTERFAZ MÓVIL (FASE 3)
   ========================================================================== */

(function () {
  "use strict";

  const M = window.MotorCompanero;
  const D = window.APP_DATA;
  let estado = M.cargarEstado();

  // Estado de navegación de la interfaz
  const ui = {
    pantalla: "hoy", // 'hoy' | 'calendario' | 'compras' | 'extras' | 'seguridad' | 'hoy_no_puedo' | 'ficha_receta'
    pantallaAnterior: "hoy",
    mostrarPanelPorciones: false,
    diaActivo: estado.diaSeleccionado || 1,
    semanaCalendario: Math.ceil((estado.diaSeleccionado || 1) / 7),
    semanaCompras: 1, // 1..5 o 'extras'
    recetaAbiertaId: "pollo-horno-batatas",
    contextoFicha: null, // { dia, turno } si se abrió desde un turno específico
    turnoCambioAbierto: null, // "dia_turno"
    ingredientesHoyNoPuedo: ["queso", "tomate", "huevo"], // preseleccionados de ejemplo
    mostrarFormReceta: false,
    borradorReceta: null,
    contextoAsignarAlGuardar: null // { dia, turno, mantenerDoble } si se abrió el formulario desde "Cambiar comida"
  };

  function crearBorradorRecetaVacio() {
    return {
      id: null,
      nombre: "",
      proteina: "pollo",
      tiempo_total: 20,
      tiempo_activo: 10,
      apta_chicos: true,
      version_chicos: "",
      ingredientes: [
        { item: "", cantidad: 400, unidad: "g", sector: "carnes y huevos" },
        { item: "", cantidad: 2, unidad: "unidad", sector: "verduras y frutas" }
      ],
      pasosTexto: ""
    };
  }

  function mapaRecetas() {
    const map = {};
    (D.recetas || []).forEach(r => { map[r.id] = r; });
    if (estado && Array.isArray(estado.misRecetas)) {
      estado.misRecetas.forEach(r => { map[r.id] = r; });
    }
    return map;
  }

  // =========================================================================
  // NAVEGACIÓN PRINCIPAL Y CONTROLES GLOBALES
  // =========================================================================

  window.irAPantalla = function (nombrePantalla) {
    if (nombrePantalla !== "ficha_receta") {
      ui.pantallaAnterior = nombrePantalla;
    }
    ui.pantalla = nombrePantalla;
    ui.turnoCambioAbierto = null;
    renderizarApp();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  window.volverDeFicha = function () {
    ui.pantalla = ui.pantallaAnterior || "hoy";
    renderizarApp();
  };

  window.abrirFichaReceta = function (recetaId, diaNum, turno) {
    if (!recetaId) return;
    if (ui.pantalla !== "ficha_receta") {
      ui.pantallaAnterior = ui.pantalla;
    }
    ui.recetaAbiertaId = recetaId;
    ui.contextoFicha = (diaNum && turno) ? { dia: diaNum, turno: turno } : null;
    ui.pantalla = "ficha_receta";
    renderizarApp();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  window.togglePanelPorciones = function () {
    ui.mostrarPanelPorciones = !ui.mostrarPanelPorciones;
    renderizarApp();
  };

  window.aplicarPresetPorciones = function (personas) {
    estado.porciones.preset = personas;
    estado.porciones.adultos = personas;
    estado.porciones.menores4 = 0;
    estado.porciones.chicos4a8 = 0;
    M.guardarEstado(estado);
    renderizarApp();
  };

  window.ajustarIntegranteHogar = function (tipo, delta) {
    estado.porciones.preset = null;
    if (tipo === "adultos") {
      estado.porciones.adultos = Math.max(1, Math.min(10, estado.porciones.adultos + delta));
    } else if (tipo === "menores4") {
      estado.porciones.menores4 = Math.max(0, Math.min(6, estado.porciones.menores4 + delta));
      if (estado.porciones.menores4 > 0) estado.modoChicos = true;
    } else if (tipo === "chicos4a8") {
      estado.porciones.chicos4a8 = Math.max(0, Math.min(6, estado.porciones.chicos4a8 + delta));
      if (estado.porciones.chicos4a8 > 0) estado.modoChicos = true;
    }
    M.guardarEstado(estado);
    renderizarApp();
  };

  window.toggleModoChicosGlobal = function () {
    estado.modoChicos = !estado.modoChicos;
    M.guardarEstado(estado);
    renderizarApp();
  };

  // =========================================================================
  // ACCIONES DE PROGRESO, FECHA DE INICIO Y TURNOS HECHOS
  // =========================================================================

  window.cambiarDiaHoy = function (nuevoDia) {
    const d = Math.max(1, Math.min(30, Number(nuevoDia) || 1));
    ui.diaActivo = d;
    ui.semanaCalendario = Math.min(5, Math.ceil(d / 7));
    estado.diaSeleccionado = d;
    ui.turnoCambioAbierto = null;
    M.guardarEstado(estado);
    renderizarApp();
  };

  window.guardarFechaInicio = function (valorFecha) {
    estado.fechaInicio = valorFecha || null;
    M.guardarEstado(estado);
    renderizarApp();
  };

  window.accionRetomarDesdeHoy = function () {
    const diaRetomado = M.retomarDesdeHoy(estado);
    ui.diaActivo = diaRetomado;
    ui.semanaCalendario = Math.min(5, Math.ceil(diaRetomado / 7));
    renderizarApp();
  };

  window.toggleTurnoHecho = function (diaNum, turno) {
    const clave = `${diaNum}_${turno}`;
    estado.comidasHechas[clave] = !estado.comidasHechas[clave];
    M.guardarEstado(estado);
    renderizarApp();
  };

  window.toggleCambioTurno = function (diaNum, turno) {
    const clave = `${diaNum}_${turno}`;
    ui.turnoCambioAbierto = ui.turnoCambioAbierto === clave ? null : clave;
    renderizarApp();
  };

  window.confirmarCambioTurno = function (diaNum, turno, nuevaRecetaId, mantenerDoble) {
    M.ejecutarCambioComida(D, estado, diaNum, turno, nuevaRecetaId, {
      mantenerCocinaDoble: mantenerDoble
    });
    ui.turnoCambioAbierto = null;
    renderizarApp();
  };

  window.restaurarTurnoOriginal = function (diaNum, turno) {
    delete estado.cambiosCalendario[`${diaNum}_${turno}`];
    const origDia = D.calendario.find(x => x.dia === diaNum);
    if (origDia && origDia[turno].alimenta_sobras) {
      origDia[turno].alimenta_sobras.forEach(dest => {
        delete estado.cambiosCalendario[`${dest.dia}_${dest.turno}`];
      });
    }
    M.guardarEstado(estado);
    ui.turnoCambioAbierto = null;
    renderizarApp();
  };

  // =========================================================================
  // RENDERIZADO DEL BLOQUE DE UN TURNO (USADO EN "HOY" Y EN "CALENDARIO")
  // =========================================================================

  function renderizarTarjetaTurno(diaObj, turno, recetasMap, factorHogar, mostrarImagen) {
    const slot = diaObj[turno];
    const rec = recetasMap[slot.receta_id];
    const claveTurno = `${diaObj.dia}_${turno}`;
    const estaHecha = !!estado.comidasHechas[claveTurno];
    const fueCambiada = !!estado.cambiosCalendario[claveTurno];
    const iconoTurno = turno === "almuerzo" ? "☀️ Almuerzo" : "🌙 Cena";

    let titulo = rec ? rec.nombre : "Comida planificada";
    if (slot.es_sobra && slot.texto_sobra) {
      titulo = slot.texto_sobra;
    }

    let badges = "";
    if (slot.cocina_doble) {
      badges += `<span class="tag-chip batch">🍲 ${slot.etiqueta_doble || "x8 porciones (cocinar doble)"}</span>`;
    }
    if (slot.es_sobra) {
      badges += `<span class="tag-chip batch">♻️ Aprovechamiento (${slot.tipo_sobra === "freezer" ? "Freezer" : "Heladera máx. 3 días"})</span>`;
    }
    if (rec) {
      badges += `<span class="tag-chip protein">⏱️ ${rec.tiempo_total} min (${rec.tiempo_activo} min act.) · ${rec.proteina}</span>`;
      if ((rec.etiquetas || []).includes("apta para chicos")) {
        badges += `<span class="tag-chip kids">👶 Apta para chicos</span>`;
      }
    }
    if (fueCambiada) {
      badges += `<span class="tag-chip" style="background:#E0F2FE; color:#0369A1;">✨ Modificada</span>`;
    }

    // Si el Modo con chicos está activo, mostrar el anticipo de la versión chicos
    let notaChicosResumen = "";
    if (estado.modoChicos && rec && rec.version_chicos) {
      notaChicosResumen = `
        <div style="margin: 0 16px 12px; padding: 8px 12px; background: var(--accent-sage-light); border-left: 3.5px solid var(--accent-sage); border-radius: 6px; font-size: 0.86rem; color: var(--accent-sage-dark);">
          <strong>👶 Versión chicos:</strong> ${rec.version_chicos}
        </div>`;
    }

    // Miniatura de foto en la pantalla HOY
    let thumbHtml = "";
    if (mostrarImagen && rec && rec.tiene_imagen && rec.imagen_url) {
      thumbHtml = `<img src="${rec.imagen_url}" alt="${rec.nombre}" class="today-meal-thumb" loading="lazy">`;
    }

    // Panel desplegable para cambiar comida
    let panelCambioHtml = "";
    if (ui.turnoCambioAbierto === claveTurno) {
      const analisis = M.AnalizarImpactoYAlternativas(D, estado, diaObj.dia, turno);
      const avisosHtml = analisis.avisosDependencia.map(av => `
        <div class="dependency-alert">
          <strong>💡 Aviso amable sobre tus sobras / organización:</strong>
          <div>${av.mensaje}</div>
          <div style="margin-top:5px; font-weight:700; color:#92400E;">👉 Solución: ${av.solucionPropuesta}</div>
        </div>
      `).join("");

      const reglaTxt = diaObj.es_finde
        ? "Fin de semana"
        : "Lunes a viernes (máx. 25 min totales)";

      const altsHtml = analisis.alternativas.map(alt => {
        const rAlt = alt.receta;
        return `
          <div class="alt-option-card">
            <div class="alt-option-info">
              <h4>${rAlt.nombre}</h4>
              <div class="alt-option-meta">✅ ${alt.motivo} (${rAlt.tiempo_activo} min activos)</div>
            </div>
            <div>
              ${slot.cocina_doble ? `
                <button type="button" class="btn-primary-sm" onclick="confirmarCambioTurno(${diaObj.dia}, '${turno}', '${rAlt.id}', true)">
                  Elegir y cocinar doble (x8)
                </button>
              ` : `
                <button type="button" class="btn-primary-sm" onclick="confirmarCambioTurno(${diaObj.dia}, '${turno}', '${rAlt.id}', false)">
                  Elegir opción
                </button>
              `}
            </div>
          </div>
        `;
      }).join("");

      const misRecetasList = estado.misRecetas || [];
      let bloqueMisRecetasHtml = "";
      if (misRecetasList.length > 0) {
        const filasPropias = misRecetasList.map(rp => `
          <div class="alt-option-card" style="border-color: var(--accent-terracotta);">
            <div class="alt-option-info">
              <h4>📒 ${rp.nombre}</h4>
              <div class="alt-option-meta">🏷️ Tu receta personal · ${rp.proteina} · ${rp.tiempo_total} min</div>
            </div>
            <div>
              ${slot.cocina_doble ? `
                <button type="button" class="btn-primary-sm" onclick="confirmarCambioTurno(${diaObj.dia}, '${turno}', '${rp.id}', true)">
                  Elegir y cocinar doble (x8)
                </button>
              ` : `
                <button type="button" class="btn-primary-sm" onclick="confirmarCambioTurno(${diaObj.dia}, '${turno}', '${rp.id}', false)">
                  Elegir mi receta
                </button>
              `}
            </div>
          </div>
        `).join("");
        bloqueMisRecetasHtml = `
          <div style="font-size:0.86rem; font-weight:800; color:var(--accent-terracotta-dark); margin:12px 0 8px;">
            📒 O elegí una de tus recetas familiares guardadas:
          </div>
          ${filasPropias}
        `;
      }

      panelCambioHtml = `
        <div class="swap-panel" style="padding: 12px 16px 16px;">
          ${avisosHtml}
          <div style="font-size:0.86rem; font-weight:800; color:var(--accent-sage-dark); margin-bottom:8px;">
            🔄 3 alternativas equivalentes (${reglaTxt}, sin repetir platos cercanos):
          </div>
          ${altsHtml}
          ${bloqueMisRecetasHtml}
          <div style="margin-top:10px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; padding-top:8px; border-top:1px dashed var(--border-soft);">
            <span style="font-size:0.84rem; color:var(--text-muted);">¿Querés cocinar un plato propio que no está acá?</span>
            <button type="button" class="btn-secondary" style="min-height:36px; padding:6px 12px; font-size:0.82rem;" onclick="abrirCreadorRecetaDesdeTurno(${diaObj.dia}, '${turno}', ${!!slot.cocina_doble})">
              ➕ Crear y usar mi propia receta
            </button>
          </div>
        </div>
      `;
    }

    return `
      <div class="today-meal-card ${estaHecha ? "meal-done" : ""}">
        <div class="today-meal-top">
          ${thumbHtml}
          <div style="flex:1;">
            <div class="day-slot-header">
              <span class="slot-moment-badge">${iconoTurno}</span>
              ${fueCambiada ? `<button type="button" class="btn-tengo" onclick="restaurarTurnoOriginal(${diaObj.dia}, '${turno}')">↩️ Restaurar original</button>` : ""}
            </div>
            <h3 class="slot-recipe-name">${titulo}</h3>
            <div class="slot-badges-row" style="margin-bottom:0;">${badges}</div>
          </div>
        </div>
        ${notaChicosResumen}
        <div class="today-meal-actions">
          <button type="button" class="btn-hecho-slot ${estaHecha ? "done" : ""}" onclick="toggleTurnoHecho(${diaObj.dia}, '${turno}')">
            ${estaHecha ? "✅ Hecho" : "✓ Marcar hecho"}
          </button>
          ${rec ? `
            <button type="button" class="btn-secondary" onclick="abrirFichaReceta('${rec.id}', ${diaObj.dia}, '${turno}')">
              📖 Ver receta
            </button>
          ` : ""}
          <button type="button" class="btn-secondary" onclick="toggleCambioTurno(${diaObj.dia}, '${turno}')">
            ${ui.turnoCambioAbierto === claveTurno ? "✕ Cerrar" : "🔄 Cambiar"}
          </button>
        </div>
        ${panelCambioHtml}
      </div>
    `;
  }

  // =========================================================================
  // 1. PANTALLA "HOY" (+ PROGRESO SIN CULPA)
  // =========================================================================

  function renderizarPantallaHoy(calActivo, recetasMap, factorHogar) {
    const prog = M.calcularProgresoSinCulpa(estado);
    const diaObj = calActivo.find(x => x.dia === ui.diaActivo) || calActivo[0];

    // Avisos de Batch Cooking del día (Base de pollo o Arroz extra)
    let alertasBatchHoy = "";
    ["almuerzo", "cena"].forEach(t => {
      const b = diaObj[t].batch_base;
      if (b) {
        const cantEscalada = M.cantidadLegibleCompra(b.cantidad_cruda * factorHogar, "g");
        const usosTxt = b.usos_dias.map(u => `Día ${u.dia} (${u.turno})`).join(", ");
        alertasBatchHoy += `
          <div class="base-link-banner" style="margin-bottom: 14px;">
            <div>
              <strong>${b.base === "pollo cocido" ? "🍗 Cocinar base de pollo hoy" : "🍚 Cocinar arroz de más hoy"} (${cantEscalada} crudos)</strong>
              <div style="font-size: 0.85rem; color: var(--text-muted);">
                Dejás resuelta la base para: <b>${usosTxt}</b> (dura máximo 3 días en heladera).
              </div>
            </div>
            ${b.base === "pollo cocido" ? `
              <button type="button" class="base-link-btn" onclick="abrirFichaReceta('base-pollo-cocido')">
                Ver Receta Base →
              </button>
            ` : ""}
          </div>`;
      }
    });

    // Tarjeta amable si se salteó días ("Retomar desde hoy" sin culpa)
    let bannerRetomar = "";
    if (prog.hayDiasSalteados) {
      bannerRetomar = `
        <div class="info-box cue-green" style="display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-top:10px; margin-bottom:0;">
          <div style="flex:1; min-width:200px;">
            <strong>🌿 ¿Tuviste días movidos? No pasa nada</strong>
            El plan se adapta a tu vida real. Podés retomar tranquilamente desde tu próximo día pendiente (Día ${prog.proximoDiaPendiente}) sin perder lo que ya hiciste.
          </div>
          <button type="button" class="btn-primary-sm" onclick="accionRetomarDesdeHoy()">
            🌱 Retomar desde hoy
          </button>
        </div>`;
    }

    // Banner rápido de seguridad con chicos si el Modo con chicos está activo
    let bannerModoChicosHoy = "";
    if (estado.modoChicos) {
      bannerModoChicosHoy = `
        <div class="info-box cue-green" style="display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:14px;">
          <div>
            <strong>👶 Modo con chicos activado</strong>
            En cada comida ves destacada la adaptación infantil.
          </div>
          <button type="button" class="btn-tengo active" onclick="irAPantalla('seguridad')">
            Ver guía de seguridad y selectividad →
          </button>
        </div>`;
    }

    return `
      <!-- BOTÓN DE EMERGENCIA: HOY NO PUEDO -->
      <button type="button" class="sos-banner-btn" onclick="irAPantalla('hoy_no_puedo')">
        <div>
          ⚡ ¿Llegaste cansada? Tocá «Hoy no puedo»
          <small>3 comidas en 15 minutos o menos con lo que tenés + Plan C sin cocción</small>
        </div>
        <span style="font-size:1.4rem;">→</span>
      </button>

      <!-- SELECTOR DEL DÍA ACTIVO (HOY) -->
      <div class="control-panel" style="padding: 12px 14px; margin-bottom: 14px;">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
          <button type="button" class="btn-secondary" style="min-height:40px; padding:6px 10px;" onclick="cambiarDiaHoy(${diaObj.dia - 1})" ${diaObj.dia <= 1 ? "disabled" : ""}>
            ◀ Ant.
          </button>
          <div style="text-align:center;">
            <span style="font-size:0.75rem; font-weight:800; text-transform:uppercase; color:var(--accent-terracotta); display:block;">
              Semana ${diaObj.semana} · ${diaObj.es_finde ? "Fin de semana" : "Día de semana (≤ 25 min)"}
            </span>
            <select aria-label="Seleccionar día" onchange="cambiarDiaHoy(this.value)" style="border:none; background:transparent; font-family:'Fraunces', serif; font-size:1.25rem; font-weight:700; color:var(--text-dark); cursor:pointer; text-align:center;">
              ${calActivo.map(d => `<option value="${d.dia}" ${d.dia === diaObj.dia ? "selected" : ""}>Día ${d.dia} · ${d.nombre_dia}</option>`).join("")}
            </select>
          </div>
          <button type="button" class="btn-secondary" style="min-height:40px; padding:6px 10px;" onclick="cambiarDiaHoy(${diaObj.dia + 1})" ${diaObj.dia >= 30 ? "disabled" : ""}>
            Sig. ▶
          </button>
        </div>
      </div>

      ${bannerModoChicosHoy}
      ${alertasBatchHoy}

      <!-- TARJETAS DE ALMUERZO Y CENA DE HOY -->
      ${renderizarTarjetaTurno(diaObj, "almuerzo", recetasMap, factorHogar, true)}
      ${renderizarTarjetaTurno(diaObj, "cena", recetasMap, factorHogar, true)}

      <!-- TARJETA DE PROGRESO DE LOS 30 DÍAS (SIN CULPA) -->
      <section class="progress-card" aria-label="Tu progreso en el plan">
        <div class="progress-header">
          <strong style="color:var(--accent-sage-dark); font-size:0.95rem;">🌱 Tu recorrido de 30 días (sin culpa)</strong>
          <span style="font-size:0.85rem; font-weight:800; color:var(--accent-terracotta-dark);">
            ${prog.comidasResueltas} de ${prog.totalComidas} comidas (${prog.porcentaje} %)
          </span>
        </div>
        <div class="progress-bar-track">
          <div class="progress-bar-fill" style="width: ${prog.porcentaje}%;"></div>
        </div>
        <div class="progress-encourage">${prog.mensajeAnimo}</div>

        <div class="date-config-row">
          <div>
            <label for="inputFechaInicio" style="font-weight:700; display:block;">📆 Fecha de inicio de tu mes:</label>
            <small style="color:var(--text-muted);">El plan asume que el Día 1 es lunes (así los platos más largos caen en finde).</small>
          </div>
          <input type="date" id="inputFechaInicio" class="date-input" value="${estado.fechaInicio || ""}" onchange="guardarFechaInicio(this.value)">
        </div>
        ${bannerRetomar}
      </section>
    `;
  }

  // =========================================================================
  // 2. PANTALLA "CALENDARIO DE 30 DÍAS" (VISTA POR SEMANA Y VISTA DE HOY)
  // =========================================================================

  window.seleccionarSemanaCalendario = function (numSem) {
    ui.semanaCalendario = numSem;
    ui.turnoCambioAbierto = null;
    renderizarApp();
  };

  function renderizarPantallaCalendario(calActivo, recetasMap, factorHogar) {
    const semanas = M.rangosSemanas();
    const semActual = semanas.find(s => s.numero === ui.semanaCalendario) || semanas[0];

    const tabsSemanas = semanas.map(s => {
      const act = s.numero === semActual.numero ? "active" : "";
      return `<button type="button" class="sample-tab-btn ${act}" onclick="seleccionarSemanaCalendario(${s.numero})">Semana ${s.numero} (Días ${s.desde}-${s.hasta})</button>`;
    }).join("");

    const diasSemana = calActivo.filter(d => d.dia >= semActual.desde && d.dia <= semActual.hasta);

    const htmlDias = diasSemana.map(d => {
      const esHoy = d.dia === ui.diaActivo;
      let badgeBatch = "";
      ["almuerzo", "cena"].forEach(t => {
        if (d[t].batch_base) {
          const b = d[t].batch_base;
          const cantEsc = M.cantidadLegibleCompra(b.cantidad_cruda * factorHogar, "g");
          badgeBatch += `<div class="info-box cue-brown" style="margin-bottom:10px; padding:8px 12px;">
            <strong>${b.base === "pollo cocido" ? "🍗" : "🍚"} Batch cooking del día:</strong> Cocinar ${b.base} (${cantEsc} de ${b.ingrediente_crudo} crudo).
          </div>`;
        }
      });

      return `
        <div style="margin-bottom: 22px; padding: 14px; border-radius: var(--radius-md); background: ${esHoy ? "#FFF9F5" : "var(--bg-subtle)"}; border: 2px solid ${esHoy ? "var(--accent-terracotta)" : "var(--border-soft)"};">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; flex-wrap:wrap; gap:6px;">
            <h3 style="margin:0; font-size:1.15rem;">
              Día ${d.dia} · ${d.nombre_dia}
              ${esHoy ? `<span class="tag-chip protein" style="margin-left:6px;">📍 Tu día activo</span>` : ""}
            </h3>
            ${!esHoy ? `<button type="button" class="btn-tengo" onclick="cambiarDiaHoy(${d.dia}); irAPantalla('hoy');">Ver en Hoy →</button>` : ""}
          </div>
          ${badgeBatch}
          ${renderizarTarjetaTurno(d, "almuerzo", recetasMap, factorHogar, false)}
          ${renderizarTarjetaTurno(d, "cena", recetasMap, factorHogar, false)}
        </div>
      `;
    }).join("");

    return `
      <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:12px; flex-wrap:wrap;">
        <h2 style="margin:0; font-size:1.35rem;">📅 Calendario de 30 días</h2>
        <button type="button" class="btn-primary-sm" onclick="irAPantalla('hoy')">
          📍 Ir a Hoy (Día ${ui.diaActivo})
        </button>
      </div>

      <div class="week-selector-bar">${tabsSemanas}</div>
      ${htmlDias}
    `;
  }

  // =========================================================================
  // 3. PANTALLA "¡HOY NO PUEDO!" (≤ 15 MINUTOS + FILTRO INGREDIENTES + PLAN C)
  // =========================================================================

  window.toggleIngredienteComodin = function (idComodin) {
    const idx = ui.ingredientesHoyNoPuedo.indexOf(idComodin);
    if (idx >= 0) {
      ui.ingredientesHoyNoPuedo.splice(idx, 1);
    } else {
      if (ui.ingredientesHoyNoPuedo.length >= 5) {
        ui.ingredientesHoyNoPuedo.shift(); // mantener de 3 a 5 ingredientes ágiles
      }
      ui.ingredientesHoyNoPuedo.push(idComodin);
    }
    renderizarApp();
  };

  window.usarComidaEmergenciaHoy = function (recetaId, turno) {
    M.ejecutarCambioComida(D, estado, ui.diaActivo, turno, recetaId, { mantenerCocinaDoble: false });
    irAPantalla("hoy");
  };

  function renderizarPantallaHoyNoPuedo(factorHogar) {
    const chipsHtml = M.INGREDIENTES_COMODIN.map(c => {
      const sel = ui.ingredientesHoyNoPuedo.includes(c.id) ? "selected" : "";
      return `<button type="button" class="pantry-chip-btn ${sel}" onclick="toggleIngredienteComodin('${c.id}')">${c.etiqueta}</button>`;
    }).join("");

    const sugerencias = M.recomendarHoyNoPuedo(D, ui.ingredientesHoyNoPuedo, estado);

    const tarjetasRapid = sugerencias.map(item => {
      const r = item.receta;
      const matchTxt = item.coincidencias.length > 0
        ? `✅ Usa de tu casa: <b>${item.coincidencias.join(", ")}</b>`
        : `⚡ Se resuelve en ${r.tiempo_total} min totales`;

      return `
        <div class="day-slot-card">
          <div class="day-slot-header">
            <span class="tag-chip protein">⏱️ ${r.tiempo_total} min (${r.tiempo_activo} min activos)</span>
            ${(r.etiquetas || []).includes("apta para chicos") ? `<span class="tag-chip kids">👶 Apta para chicos</span>` : ""}
          </div>
          <h3 class="slot-recipe-name">${r.nombre}</h3>
          <div style="font-size:0.9rem; color:var(--accent-sage-dark); margin-bottom:10px;">${matchTxt}</div>
          ${r.nota_seguridad ? `<div class="info-box cue-orange" style="padding:8px 10px; font-size:0.84rem;">🐟 <strong>Nota:</strong> ${r.nota_seguridad}</div>` : ""}
          <div class="slot-actions-row">
            <button type="button" class="btn-primary-sm" onclick="abrirFichaReceta('${r.id}')">
              📖 Ver receta rápida
            </button>
            <button type="button" class="btn-secondary" onclick="usarComidaEmergenciaHoy('${r.id}', 'almuerzo')">
              Usar en Almuerzo de hoy
            </button>
            <button type="button" class="btn-secondary" onclick="usarComidaEmergenciaHoy('${r.id}', 'cena')">
              Usar en Cena de hoy
            </button>
          </div>
        </div>
      `;
    }).join("");

    const planesEmergencia = (D.editorial.estrategias && D.editorial.estrategias.comidas_emergencia && D.editorial.estrategias.comidas_emergencia.planes) || [];
    const planB = planesEmergencia.find(p => p.plan.includes("Plan B")) || {};
    const planC = planesEmergencia.find(p => p.plan.includes("Plan C")) || {};

    return `
      <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:12px;">
        <h2 style="margin:0; font-size:1.35rem;">⚡ Hoy no puedo (Rescate en ≤ 15 min)</h2>
        <button type="button" class="btn-secondary" onclick="irAPantalla('hoy')">← Volver a Hoy</button>
      </div>

      <div class="control-panel">
        <div class="control-panel-title">
          <span>🧺 Tocá de 3 a 5 ingredientes que tengas a mano en casa:</span>
          <small style="color:var(--text-muted);">${ui.ingredientesHoyNoPuedo.length} elegidos</small>
        </div>
        <div class="pantry-chips-grid">${chipsHtml}</div>
      </div>

      <h3 style="font-size:1.1rem; margin: 16px 0 10px;">🍳 3 comidas de 15 minutos o menos priorizadas para vos:</h3>
      ${tarjetasRapid}

      <!-- PLAN C SIN COCCIÓN Y PLAN B DEL EBOOK -->
      <div class="safety-card" style="border: 2px solid var(--accent-terracotta); background: #FFFBF7; margin-top: 18px;">
        <h3>🛋️ ${planC.plan || "Plan C · Agotamiento total (Comida sin cocción)"}</h3>
        <p style="margin: 0 0 10px 0; font-size: 0.96rem;">
          Cuando no hay energía ni para prender una hornalla, resolvé con alimentos listos, seguros y nutritivos sin culpa:
        </p>
        <div class="safety-rule-item">
          <strong>🥗 Opción 1 · Ensalada completa de alacena (0 min de fuego)</strong>
          ${planC.detalle || "Legumbres en lata bien enjuagadas en colador con choclo, tomate en cubos, queso fresco y aceite de oliva."}
        </div>
        <div class="safety-rule-item">
          <strong>🥪 Opción 2 · Sándwich o pan árabe completo</strong>
          Pan árabe o integral con queso, tomate, hojas verdes lavadas y huevo duro o hummus.
        </div>
        <div class="safety-rule-item">
          <strong>⚡ ${planB.plan || "Plan B · 10 a 15 minutos"}</strong>
          ${planB.detalle || ""}
        </div>
      </div>
    `;
  }

  // =========================================================================
  // 4. PANTALLA "LISTA DE COMPRAS SEMANAL"
  // =========================================================================

  window.seleccionarSemanaComprasUI = function (sem) {
    ui.semanaCompras = sem;
    renderizarApp();
  };

  window.toggleItemCompraUI = function (claveSemana, itemId, campo) {
    if (!estado.comprasEstado[claveSemana]) {
      estado.comprasEstado[claveSemana] = {};
    }
    const actual = estado.comprasEstado[claveSemana][itemId] || { tengo: false, comprado: false };
    actual[campo] = !actual[campo];
    if (campo === "tengo" && actual.tengo) actual.comprado = false;
    estado.comprasEstado[claveSemana][itemId] = actual;
    M.guardarEstado(estado);
    renderizarApp();
  };

  function obtenerContextoComprasActual() {
    if (ui.semanaCompras === "extras") {
      return {
        titulo: "Lista de Compras · Ciclo de Extras (Desayunos, Colaciones y Viandas)",
        claveEstado: "sem_extras",
        datos: M.calcularListaComprasExtras(D, estado)
      };
    }
    const infoSem = M.rangosSemanas().find(x => x.numero === Number(ui.semanaCompras)) || M.rangosSemanas()[0];
    return {
      titulo: `Lista de Compras · ${infoSem.titulo}`,
      claveEstado: `sem_${infoSem.numero}`,
      datos: M.calcularListaComprasSemana(D, estado, infoSem.desde, infoSem.hasta)
    };
  }

  window.copiarWhatsAppUI = function () {
    const ctx = obtenerContextoComprasActual();
    const estSem = estado.comprasEstado[ctx.claveEstado] || {};
    const descPorc = M.describirPorcionesHogar(estado.porciones);
    const txt = M.formatearListaWhatsApp(ctx.titulo, ctx.datos, estSem, descPorc);
    const box = document.getElementById("boxWhatsAppPreview");
    const pre = document.getElementById("preWhatsAppText");
    if (pre && box) {
      pre.textContent = txt;
      box.style.display = "block";
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(() => {
        alert("✅ ¡Lista copiada al portapapeles! Ya podés pegarla en WhatsApp.");
      }).catch(() => {});
    }
  };

  window.verTextoWhatsAppUI = function () {
    const ctx = obtenerContextoComprasActual();
    const estSem = estado.comprasEstado[ctx.claveEstado] || {};
    const descPorc = M.describirPorcionesHogar(estado.porciones);
    const txt = M.formatearListaWhatsApp(ctx.titulo, ctx.datos, estSem, descPorc);
    const box = document.getElementById("boxWhatsAppPreview");
    const pre = document.getElementById("preWhatsAppText");
    if (pre && box) {
      pre.textContent = txt;
      box.style.display = "block";
    }
  };

  function renderizarPantallaCompras() {
    const botonesSem = M.rangosSemanas().map(s => {
      const act = Number(ui.semanaCompras) === s.numero ? "active" : "";
      return `<button type="button" class="sample-tab-btn ${act}" onclick="seleccionarSemanaComprasUI(${s.numero})">Semana ${s.numero} (Días ${s.desde}-${s.hasta})</button>`;
    });
    botonesSem.push(
      `<button type="button" class="sample-tab-btn ${ui.semanaCompras === "extras" ? "active" : ""}" onclick="seleccionarSemanaComprasUI('extras')">🍎 Extras (Ciclo A, B, C)</button>`
    );

    const ctx = obtenerContextoComprasActual();
    const estSem = estado.comprasEstado[ctx.claveEstado] || {};

    let batchBannerHtml = "";
    if (ctx.datos.notasBatch && ctx.datos.notasBatch.length > 0) {
      const detalles = ctx.datos.notasBatch.map(b =>
        `<li>Día ${b.dia} (${b.turno}): <b>${b.ingrediente} (${b.cantidadTexto})</b> para tu base de <i>${b.base}</i> (ya sumado en el rubro abajo).</li>`
      ).join("");
      batchBannerHtml = `
        <div class="info-box cue-brown" style="margin-bottom:14px;">
          <strong>🍗 Batch cooking incluido en esta semana:</strong>
          <ul style="margin:6px 0 0 0; padding-left:20px;">${detalles}</ul>
        </div>`;
    }

    const rubrosHtml = ctx.datos.rubros.map(rubro => {
      if (!rubro.items || rubro.items.length === 0) return "";
      const pendientes = rubro.items.filter(it => {
        const st = estSem[it.id] || {};
        return !st.tengo && !st.comprado;
      }).length;

      const filas = rubro.items.map(it => {
        const st = estSem[it.id] || { tengo: false, comprado: false };
        const rowClass = st.tengo ? "status-tengo" : (st.comprado ? "status-comprado" : "");
        const tick = st.comprado ? "✓" : "";
        const idSafe = it.id.replace(/'/g, "\\'");

        return `
          <div class="shop-row ${rowClass}">
            <div class="shop-item-main" onclick="toggleItemCompraUI('${ctx.claveEstado}', '${idSafe}', 'comprado')">
              <span class="ing-checkbox" style="${st.comprado ? "background:var(--accent-sage);" : ""}">${tick}</span>
              <div class="shop-item-text">
                <strong>${it.item}</strong>: <span class="shop-item-qty">${it.texto}</span>
                ${it.detalle ? `<span class="shop-item-detail">(${it.detalle})</span>` : ""}
              </div>
            </div>
            <button type="button" class="btn-tengo ${st.tengo ? "active" : ""}" onclick="toggleItemCompraUI('${ctx.claveEstado}', '${idSafe}', 'tengo')">
              ${st.tengo ? "✓ Ya lo tengo" : "Ya lo tengo"}
            </button>
          </div>`;
      }).join("");

      return `
        <div class="shop-sector-card">
          <h3 class="shop-sector-title">
            <span>${rubro.titulo}</span>
            <small style="font-size:0.78rem; color:var(--text-muted); font-weight:600;">${pendientes} pendientes</small>
          </h3>
          <div>${filas}</div>
        </div>`;
    }).join("");

    return `
      <h2 style="margin:0 0 10px 0; font-size:1.35rem;">🛒 ${ctx.titulo}</h2>
      <div class="week-selector-bar">${botonesSem.join("")}</div>

      <div class="shop-actions-bar">
        <button type="button" class="btn-primary-sm" onclick="copiarWhatsAppUI()">
          📲 Copiar para WhatsApp
        </button>
        <button type="button" class="btn-secondary" onclick="verTextoWhatsAppUI()">
          👁️ Ver texto WhatsApp
        </button>
        <button type="button" class="btn-secondary" onclick="window.print()">
          🖨️ Vista de impresión limpia
        </button>
      </div>

      <div id="boxWhatsAppPreview" style="display:none; margin-bottom:16px;" class="control-panel no-print">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <strong style="color:var(--accent-sage-dark);">📲 Texto listo para pegar en WhatsApp:</strong>
          <button type="button" class="btn-tengo" onclick="document.getElementById('boxWhatsAppPreview').style.display='none'">Cerrar ✕</button>
        </div>
        <pre id="preWhatsAppText" style="background:var(--bg-cream); padding:12px; border-radius:8px; border:1px solid var(--border-soft); white-space:pre-wrap; font-family:inherit; font-size:0.88rem; margin:0;"></pre>
      </div>

      ${batchBannerHtml}
      ${rubrosHtml}
    `;
  }

  // =========================================================================
  // 5. PANTALLA "EXTRAS: CICLO DE 3 DÍAS (A, B, C) Y POSTRES"
  // =========================================================================

  function renderizarPantallaExtras() {
    const extEd = D.editorial.semana_extras || {};
    const definicionCiclos = [
      {
        dia: "Día A",
        items: [
          { momento: "☀️ Desayuno / Merienda", id: "tostadas-queso-tomate" },
          { momento: "🥕 Colación", id: "palitos-verdura-hummus" },
          { momento: "🥡 Vianda", id: "vianda-sandwich-arabe" }
        ]
      },
      {
        dia: "Día B",
        items: [
          { momento: "☀️ Desayuno / Merienda", id: "avena-nocturna" },
          { momento: "🍫 Colación", id: "bolitas-avena-banana" },
          { momento: "🥡 Vianda", id: "vianda-bowl-pollo-arroz", nota: "Usá la Base de pollo cocido de los días marcados; si no tenés, reemplazá por la vianda de lentejas." }
        ]
      },
      {
        dia: "Día C",
        items: [
          { momento: "☀️ Desayuno / Merienda", id: "panqueques-banana" },
          { momento: "🥤 Colación", id: "licuado-banana" },
          { momento: "🥡 Vianda", id: "vianda-ensalada-lentejas" }
        ]
      }
    ];

    const recetasMap = mapaRecetas();
    const postresRecetas = D.recetas.filter(r => r.tipo === "postre");

    const htmlCiclos = definicionCiclos.map(c => {
      const filas = c.items.map(it => {
        const r = recetasMap[it.id];
        if (!r) return "";
        return `
          <div class="cycle-slot-row">
            <div>
              <span style="font-size:0.76rem; font-weight:800; color:var(--accent-sage-dark); text-transform:uppercase; display:block;">
                ${it.momento} · ⏱️ ${r.tiempo_total} min
              </span>
              <strong style="font-size:1rem;">${r.nombre}</strong>
              ${it.nota ? `<div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">💡 ${it.nota}</div>` : ""}
            </div>
            <button type="button" class="btn-secondary" style="min-height:38px; padding:6px 10px; font-size:0.84rem;" onclick="abrirFichaReceta('${r.id}')">
              📖 Receta
            </button>
          </div>`;
      }).join("");

      return `
        <div class="cycle-card">
          <span class="cycle-day-badge">${c.dia}</span>
          ${filas}
        </div>`;
    }).join("");

    const htmlPostres = postresRecetas.map(r => `
      <div class="alt-option-card">
        <div class="alt-option-info">
          <h4>🍨 ${r.nombre}</h4>
          <div class="alt-option-meta">⏱️ ${r.tiempo_total} min (${r.tiempo_activo} min activos) · Dificultad: ${r.dificultad}</div>
        </div>
        <button type="button" class="btn-secondary" style="min-height:38px; padding:6px 12px;" onclick="abrirFichaReceta('${r.id}')">
          📖 Ver receta
        </button>
      </div>
    `).join("");

    return `
      <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:10px; flex-wrap:wrap;">
        <h2 style="margin:0; font-size:1.35rem;">🍎 ${extEd.titulo || "Ciclo de 3 Días (A, B, C)"}</h2>
        <button type="button" class="btn-primary-sm" onclick="seleccionarSemanaComprasUI('extras'); irAPantalla('compras');">
          🛒 Lista de compras de Extras
        </button>
      </div>

      <div class="info-box cue-green" style="margin-bottom:14px;">
        <strong>💡 Cómo usar este ciclo:</strong>
        ${extEd.aclaracion_uso || "Repetí el ciclo durante la semana o mezclá libremente cualquier opción de cada columna."}
      </div>

      ${htmlCiclos}

      <div class="cycle-card" style="background:#FFFBF7; border-color:var(--accent-mustard);">
        <h3 style="margin:0 0 6px 0; font-size:1.15rem; color:var(--accent-terracotta-dark);">🍐 Regla semanal de postres</h3>
        <p style="margin:0 0 12px 0; font-size:0.94rem;">
          <strong>${extEd.regla_postres || "Fruta fresca de estación 4 o 5 días por semana; postre dulce casero 2 o 3 veces por semana."}</strong>
        </p>
        ${htmlPostres}
      </div>
    `;
  }

  // =========================================================================
  // 6. PANTALLA "SEGURIDAD ALIMENTARIA Y PAUTAS CON CHICOS"
  // =========================================================================

  function renderizarPantallaSeguridad() {
    const cons = (D.editorial.metodo && D.editorial.metodo.conservacion_segura) || {};
    const segChicos = (D.editorial.metodo && D.editorial.metodo.seguridad_chicos) || {};
    const conChicos = D.editorial.con_chicos_en_casa || {};
    const sodio = D.editorial.pauta_sodio || {};

    const puntosConservacion = (cons.puntos || []).map(p => `
      <div class="safety-rule-item">
        <strong>🛡️ ${p.titulo}</strong>
        ${p.texto}
      </div>
    `).join("");

    const pautasMenores4 = ((segChicos.menores_4_anos && segChicos.menores_4_anos.pautas) || []).map(p => `
      <li style="margin-bottom:6px;">${p}</li>
    `).join("");

    const pautas4a8 = ((segChicos.de_4_a_8_anos && segChicos.de_4_a_8_anos.pautas) || []).map(p => `
      <li style="margin-bottom:6px;">${p}</li>
    `).join("");

    const consejosSelectivos = (conChicos.consejos || []).map(c => `
      <div class="safety-rule-item">
        <strong>${c.numero}. ${c.titulo}</strong>
        ${c.texto}
      </div>
    `).join("");

    return `
      <h2 style="margin:0 0 12px 0; font-size:1.35rem;">🛡️ Seguridad alimentaria y familia</h2>

      <!-- NOTA OBLIGATORIA DEL ATÚN -->
      <div class="info-box cue-orange" style="margin-bottom:14px;">
        <strong>🐟 Pauta sobre el consumo de atún (en recetas y calendario):</strong>
        Atún: consumo moderado en embarazo y en chicos pequeños; ante dudas, consultá con tu profesional de salud.
      </div>

      <!-- CONSERVACIÓN SEGURA (REGLA 2 HORAS, 3 DÍAS, ARROZ, TEMPERATURAS, DESCONGELAMIENTO) -->
      <div class="safety-card">
        <h3>🧊 ${cons.titulo || "Pautas generales de seguridad alimentaria y conservación"}</h3>
        ${puntosConservacion}
      </div>

      <!-- SEGURIDAD CON CHICOS EN CASA (PREVENCIÓN DE ATRAGANTAMIENTO Y MIEL) -->
      <div class="safety-card">
        <h3>👶 ${segChicos.titulo || "Seguridad con chicos: prevención de atragantamiento"}</h3>
        <p style="font-size:0.92rem; color:var(--text-muted); margin-top:0;">${segChicos.bajada || ""}</p>
        <div class="info-box cue-orange" style="margin-bottom:10px;">
          <strong>⚠️ ${(segChicos.menores_4_anos && segChicos.menores_4_anos.rango) || "Menores de 4 años"}</strong>
          <ul style="margin:6px 0 0 0; padding-left:18px;">${pautasMenores4}</ul>
        </div>
        <div class="info-box cue-green" style="margin-bottom:10px;">
          <strong>🧒 ${(segChicos.de_4_a_8_anos && segChicos.de_4_a_8_anos.rango) || "De 4 a 8 años"}</strong>
          <ul style="margin:6px 0 0 0; padding-left:18px;">${pautas4a8}</ul>
        </div>
        <div style="font-size:0.84rem; color:var(--text-muted);">${segChicos.aviso_pediatra || ""}</div>
      </div>

      <!-- CON CHICOS EN CASA: COMER EN PAZ Y SIN PELEAS -->
      <div class="safety-card">
        <h3>💚 ${conChicos.titulo || "Con chicos en casa: comer en paz y sin peleas"}</h3>
        <p style="font-size:0.92rem; color:var(--text-muted); margin-top:0;">${conChicos.bajada || ""}</p>
        ${consejosSelectivos}
      </div>

      <!-- ATENCIÓN AL SODIO -->
      <div class="safety-card">
        <h3>🧂 ${sodio.titulo || "Atención al sodio en la cocina cotidiana"}</h3>
        <p style="margin:0; font-size:0.94rem;">${sodio.texto || ""}</p>
      </div>
    `;
  }

  // =========================================================================
  // 8. PANTALLA "MIS RECETAS" (RECETARIO FAMILIAR PERSONAL)
  // =========================================================================

  window.abrirNuevaMiReceta = function () {
    ui.borradorReceta = crearBorradorRecetaVacio();
    ui.contextoAsignarAlGuardar = null;
    ui.mostrarFormReceta = true;
    renderizarApp();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  window.abrirCreadorRecetaDesdeTurno = function (diaNum, turno, mantenerDoble) {
    ui.borradorReceta = crearBorradorRecetaVacio();
    ui.contextoAsignarAlGuardar = { dia: diaNum, turno: turno, mantenerDoble: mantenerDoble };
    ui.mostrarFormReceta = true;
    ui.pantallaAnterior = ui.pantalla;
    ui.pantalla = "mis_recetas";
    renderizarApp();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  window.abrirEditarMiReceta = function (recetaId) {
    const rec = (estado.misRecetas || []).find(r => r.id === recetaId);
    if (!rec) return;
    ui.borradorReceta = {
      id: rec.id,
      nombre: rec.nombre,
      proteina: rec.proteina || "pollo",
      tiempo_total: rec.tiempo_total || 20,
      tiempo_activo: rec.tiempo_activo || 10,
      apta_chicos: (rec.etiquetas || []).includes("apta para chicos"),
      version_chicos: rec.version_chicos || "",
      ingredientes: JSON.parse(JSON.stringify(rec.ingredientes || [])),
      pasosTexto: (rec.pasos || []).join("\n")
    };
    ui.contextoAsignarAlGuardar = null;
    ui.mostrarFormReceta = true;
    ui.pantalla = "mis_recetas";
    renderizarApp();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  window.cerrarFormMiReceta = function () {
    ui.mostrarFormReceta = false;
    ui.borradorReceta = null;
    if (ui.contextoAsignarAlGuardar) {
      const volverA = ui.pantallaAnterior || "hoy";
      ui.contextoAsignarAlGuardar = null;
      irAPantalla(volverA);
      return;
    }
    renderizarApp();
  };

  function sincronizarBorradorDesdeDOM() {
    if (!ui.borradorReceta) return;
    const elNombre = document.getElementById("inpRecetaNombre");
    const elProt = document.getElementById("inpRecetaProteina");
    const elTotal = document.getElementById("inpRecetaTiempoTotal");
    const elAct = document.getElementById("inpRecetaTiempoActivo");
    const elChicos = document.getElementById("inpRecetaAptaChicos");
    const elVerChicos = document.getElementById("inpRecetaVersionChicos");
    const elPasos = document.getElementById("inpRecetaPasos");

    if (elNombre) ui.borradorReceta.nombre = elNombre.value;
    if (elProt) ui.borradorReceta.proteina = elProt.value;
    if (elTotal) ui.borradorReceta.tiempo_total = Number(elTotal.value) || 20;
    if (elAct) ui.borradorReceta.tiempo_activo = Number(elAct.value) || 10;
    if (elChicos) ui.borradorReceta.apta_chicos = elChicos.checked;
    if (elVerChicos) ui.borradorReceta.version_chicos = elVerChicos.value;
    if (elPasos) ui.borradorReceta.pasosTexto = elPasos.value;

    (ui.borradorReceta.ingredientes || []).forEach((ing, idx) => {
      const iItem = document.getElementById(`inpIngItem_${idx}`);
      const iCant = document.getElementById(`inpIngCant_${idx}`);
      const iUni = document.getElementById(`inpIngUni_${idx}`);
      const iSec = document.getElementById(`inpIngSec_${idx}`);
      if (iItem) ing.item = iItem.value;
      if (iCant) ing.cantidad = Number(iCant.value) || 1;
      if (iUni) ing.unidad = iUni.value;
      if (iSec) ing.sector = iSec.value;
    });
  }

  window.agregarRenglonIngredienteUI = function () {
    sincronizarBorradorDesdeDOM();
    if (!ui.borradorReceta) return;
    ui.borradorReceta.ingredientes.push({
      item: "",
      cantidad: 1,
      unidad: "unidad",
      sector: "verduras y frutas"
    });
    renderizarApp();
  };

  window.quitarRenglonIngredienteUI = function (idx) {
    sincronizarBorradorDesdeDOM();
    if (!ui.borradorReceta || ui.borradorReceta.ingredientes.length <= 1) return;
    ui.borradorReceta.ingredientes.splice(idx, 1);
    renderizarApp();
  };

  window.guardarMiRecetaUI = function () {
    sincronizarBorradorDesdeDOM();
    const b = ui.borradorReceta;
    if (!b || !String(b.nombre || "").trim()) {
      alert("Por favor escribí el nombre de tu plato antes de guardar.");
      const elNombre = document.getElementById("inpRecetaNombre");
      if (elNombre) elNombre.focus();
      return;
    }

    const pasosArray = String(b.pasosTexto || "")
      .split(/\n+/)
      .map(s => s.trim())
      .filter(s => s !== "");

    const guardada = M.guardarRecetaPersonal(estado, {
      id: b.id,
      nombre: b.nombre,
      proteina: b.proteina,
      tiempo_total: b.tiempo_total,
      tiempo_activo: b.tiempo_activo,
      apta_chicos: b.apta_chicos,
      version_chicos: b.version_chicos,
      ingredientes: b.ingredientes,
      pasos: pasosArray
    });

    ui.mostrarFormReceta = false;
    ui.borradorReceta = null;

    if (ui.contextoAsignarAlGuardar) {
      const ctx = ui.contextoAsignarAlGuardar;
      ui.contextoAsignarAlGuardar = null;
      M.ejecutarCambioComida(D, estado, ctx.dia, ctx.turno, guardada.id, {
        mantenerCocinaDoble: ctx.mantenerDoble
      });
      ui.turnoCambioAbierto = null;
      irAPantalla(ui.pantallaAnterior || "hoy");
      return;
    }

    renderizarApp();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  window.borrarMiRecetaUI = function (recetaId) {
    const rec = (estado.misRecetas || []).find(r => r.id === recetaId);
    if (!rec) return;
    if (!confirm(`¿Querés borrar tu receta «${rec.nombre}»?`)) return;
    M.eliminarRecetaPersonal(estado, recetaId);
    if (ui.pantalla === "ficha_receta" && ui.recetaAbiertaId === recetaId) {
      ui.pantalla = "mis_recetas";
    }
    renderizarApp();
  };

  window.usarMiRecetaEnHoyUI = function (recetaId, turno) {
    const calActivo = M.obtenerCalendarioActivo(D, estado);
    const diaObj = calActivo.find(x => x.dia === ui.diaActivo) || calActivo[0];
    const mantenerDoble = !!(diaObj && diaObj[turno] && diaObj[turno].cocina_doble);
    M.ejecutarCambioComida(D, estado, ui.diaActivo, turno, recetaId, {
      mantenerCocinaDoble: mantenerDoble
    });
    irAPantalla("hoy");
  };

  window.respaldarMisRecetasWhatsAppUI = function () {
    const descPorc = M.describirPorcionesHogar(estado.porciones);
    const txt = M.formatearMisRecetasWhatsApp(estado, descPorc);
    const box = document.getElementById("boxBackupMisRecetas");
    const pre = document.getElementById("preBackupMisRecetas");
    if (box && pre) {
      pre.textContent = txt;
      box.style.display = "block";
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(() => {
        alert("✅ ¡Tus recetas se copiaron al portapapeles! Ya podés pegarlas en tu WhatsApp o notas como respaldo.");
      }).catch(() => {});
    }
  };

  function renderizarPantallaMisRecetas(factorHogar) {
    const lista = estado.misRecetas || [];

    let formHtml = "";
    if (ui.mostrarFormReceta && ui.borradorReceta) {
      const b = ui.borradorReceta;
      const opcionesSector = M.RUBROS_ORDEN.map(r =>
        `<option value="${r.id}">${r.titulo}</option>`
      ).join("");

      const renglonesIng = (b.ingredientes || []).map((ing, idx) => `
        <div style="display:grid; grid-template-columns: 1.5fr 0.7fr 0.9fr 1.2fr auto; gap:6px; margin-bottom:8px; align-items:center;" class="ing-form-row">
          <input type="text" id="inpIngItem_${idx}" placeholder="Ej: zapallitos, huevos..." value="${(ing.item || "").replace(/"/g, "&quot;")}"
            style="min-height:40px; padding:6px 10px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit; font-size:0.9rem; width:100%;">
          <input type="number" step="0.25" min="0.25" id="inpIngCant_${idx}" value="${ing.cantidad || 1}" title="Cantidad para 4 porciones"
            style="min-height:40px; padding:6px 8px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit; font-size:0.9rem; width:100%;">
          <select id="inpIngUni_${idx}" style="min-height:40px; padding:6px 6px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit; font-size:0.86rem; background:var(--bg-card); width:100%;">
            ${["g", "unidad", "ml", "lata", "atado", "diente", "paquete (2 tapas)", "cda", "cdita", "pizca"].map(u => `<option value="${u}" ${ing.unidad === u ? "selected" : ""}>${u}</option>`).join("")}
          </select>
          <select id="inpIngSec_${idx}" style="min-height:40px; padding:6px 6px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit; font-size:0.84rem; background:var(--bg-card); width:100%;">
            ${M.RUBROS_ORDEN.map(r => `<option value="${r.id}" ${ing.sector === r.id ? "selected" : ""}>${r.titulo}</option>`).join("")}
          </select>
          <button type="button" class="btn-tengo" style="min-height:40px; padding:0 10px;" onclick="quitarRenglonIngredienteUI(${idx})" title="Quitar ingrediente">✕</button>
        </div>
      `).join("");

      const bannerAsignacion = ui.contextoAsignarAlGuardar ? `
        <div class="info-box cue-green" style="margin-bottom:12px;">
          <strong>✨ Guardar y usar en el Día ${ui.contextoAsignarAlGuardar.dia} (${ui.contextoAsignarAlGuardar.turno}):</strong>
          Al guardar esta receta se asignará automáticamente a ese día y sus ingredientes se sumarán a tu Lista de Compras semanal.
        </div>
      ` : "";

      formHtml = `
        <div class="control-panel" style="border: 2px solid var(--accent-terracotta); background: #FFFBF7; margin-bottom: 18px;">
          <div class="control-panel-title">
            <span style="font-size:1.05rem;">${b.id ? "✏️ Editar mi receta" : "➕ Agregar mi receta familiar (en 1 minuto)"}</span>
            <button type="button" class="btn-tengo" onclick="cerrarFormMiReceta()">Cancelar ✕</button>
          </div>

          ${bannerAsignacion}

          <div style="display:grid; gap:12px;">
            <div>
              <label for="inpRecetaNombre" style="font-weight:800; font-size:0.88rem; display:block; margin-bottom:4px;">🍽️ Nombre del plato *</label>
              <input type="text" id="inpRecetaNombre" placeholder="Ej: Tarta de zapallitos de la abuela" value="${(b.nombre || "").replace(/"/g, "&quot;")}"
                style="width:100%; min-height:44px; padding:8px 12px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit; font-size:0.98rem;">
            </div>

            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:10px;">
              <div>
                <label for="inpRecetaProteina" style="font-weight:800; font-size:0.84rem; display:block; margin-bottom:4px;">🥩 Proteína / Base principal</label>
                <select id="inpRecetaProteina" style="width:100%; min-height:42px; padding:6px 10px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit; background:var(--bg-card); font-weight:700;">
                  ${["pollo", "carne", "huevo", "legumbres", "pescado", "cerdo", "queso y verdura"].map(p => `<option value="${p}" ${b.proteina === p ? "selected" : ""}>${p}</option>`).join("")}
                </select>
              </div>
              <div>
                <label for="inpRecetaTiempoTotal" style="font-weight:800; font-size:0.84rem; display:block; margin-bottom:4px;">⏱️ Tiempo total (min)</label>
                <input type="number" min="5" max="180" id="inpRecetaTiempoTotal" value="${b.tiempo_total || 20}"
                  style="width:100%; min-height:42px; padding:6px 10px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit;">
              </div>
              <div>
                <label for="inpRecetaTiempoActivo" style="font-weight:800; font-size:0.84rem; display:block; margin-bottom:4px;">👩‍🍳 Tiempo activo (min)</label>
                <input type="number" min="5" max="120" id="inpRecetaTiempoActivo" value="${b.tiempo_activo || 10}"
                  style="width:100%; min-height:42px; padding:6px 10px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit;">
              </div>
            </div>

            <div>
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
                <label style="font-weight:800; font-size:0.88rem;">🛒 Ingredientes (calculados para 4 porciones base):</label>
                <small style="color:var(--text-muted);">La app los escalará sola según las porciones de tu hogar y los sumará a Compras</small>
              </div>
              ${renglonesIng}
              <button type="button" class="btn-secondary" style="min-height:38px; padding:6px 12px; font-size:0.85rem;" onclick="agregarRenglonIngredienteUI()">
                + Sumar otro ingrediente
              </button>
            </div>

            <div>
              <label for="inpRecetaPasos" style="font-weight:800; font-size:0.88rem; display:block; margin-bottom:4px;">👩‍🍳 Pasos o notas de preparación (1 paso por renglón, opcional):</label>
              <textarea id="inpRecetaPasos" rows="3" placeholder="Ej: Rehogar la cebolla y los zapallitos.&#10;Batir 3 huevos con queso y volcar en la tarta.&#10;Hornear 20 min hasta dorar."
                style="width:100%; padding:8px 12px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit; font-size:0.92rem;">${b.pasosTexto || ""}</textarea>
            </div>

            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:10px; align-items:center;">
              <label style="display:flex; align-items:center; gap:8px; font-weight:700; cursor:pointer; background:var(--accent-sage-light); padding:10px 12px; border-radius:8px;">
                <input type="checkbox" id="inpRecetaAptaChicos" ${b.apta_chicos ? "checked" : ""} style="width:18px; height:18px;">
                <span>👶 Es apta para chicos</span>
              </label>
              <input type="text" id="inpRecetaVersionChicos" placeholder="Nota opcional para chicos (ej: separar antes de condimentar)" value="${(b.version_chicos || "").replace(/"/g, "&quot;")}"
                style="width:100%; min-height:42px; padding:6px 10px; border-radius:8px; border:1.5px solid var(--border-soft); font-family:inherit; font-size:0.88rem;">
            </div>

            <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:4px;">
              <button type="button" class="btn-primary-sm" style="flex:1; min-height:46px; font-size:0.98rem;" onclick="guardarMiRecetaUI()">
                💾 ${ui.contextoAsignarAlGuardar ? `Guardar y usar en Día ${ui.contextoAsignarAlGuardar.dia}` : "Guardar en Mis Recetas"}
              </button>
              <button type="button" class="btn-secondary" onclick="cerrarFormMiReceta()">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      `;
    }

    const tarjetasHtml = lista.length === 0 ? `
      <div class="control-panel" style="text-align:center; padding:26px 18px;">
        <div style="font-size:2.2rem; margin-bottom:6px;">📒</div>
        <h3 style="margin:0 0 6px 0;">Todavía no agregaste recetas propias</h3>
        <p style="color:var(--text-muted); font-size:0.94rem; max-width:460px; margin:0 auto 14px;">
          Sumá acá los clásicos de tu familia (la tarta favorita, el pastel de papas o las fajitas de los viernes). Vas a poder elegirlos al cambiar cualquier comida del calendario y sus ingredientes se sumarán solos a tu Lista de Compras.
        </p>
        ${!ui.mostrarFormReceta ? `
          <button type="button" class="btn-primary-sm" onclick="abrirNuevaMiReceta()">
            ➕ Agregar mi primera receta
          </button>
        ` : ""}
      </div>
    ` : lista.map(r => {
      const ingsPreview = (r.ingredientes || []).slice(0, 4).map(i =>
        `${i.item} (${M.cantidadPracticaReceta(i.cantidad, i.unidad, factorHogar)})`
      ).join(" · ");

      return `
        <div class="today-meal-card">
          <div class="today-meal-top">
            <div style="flex:1;">
              <div class="day-slot-header">
                <span class="tag-chip batch">🏷️ Tu receta personal</span>
                <span class="tag-chip protein">⏱️ ${r.tiempo_total} min · ${r.proteina}</span>
                ${(r.etiquetas || []).includes("apta para chicos") ? `<span class="tag-chip kids">👶 Apta para chicos</span>` : ""}
              </div>
              <h3 class="slot-recipe-name">${r.nombre}</h3>
              <div style="font-size:0.86rem; color:var(--text-muted);">
                🛒 <strong>Para tu hogar (${M.describirPorcionesHogar(estado.porciones)}):</strong> ${ingsPreview}${(r.ingredientes || []).length > 4 ? "..." : ""}
              </div>
            </div>
          </div>
          <div class="today-meal-actions">
            <button type="button" class="btn-primary-sm" onclick="abrirFichaReceta('${r.id}')">
              📖 Ver receta
            </button>
            <button type="button" class="btn-secondary" onclick="usarMiRecetaEnHoyUI('${r.id}', 'almuerzo')">
              ☀️ Usar en Almuerzo (Día ${ui.diaActivo})
            </button>
            <button type="button" class="btn-secondary" onclick="usarMiRecetaEnHoyUI('${r.id}', 'cena')">
              🌙 Usar en Cena (Día ${ui.diaActivo})
            </button>
            <button type="button" class="btn-tengo" onclick="abrirEditarMiReceta('${r.id}')">
              ✏️ Editar
            </button>
            <button type="button" class="btn-tengo" onclick="borrarMiRecetaUI('${r.id}')">
              🗑️
            </button>
          </div>
        </div>
      `;
    }).join("");

    return `
      <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:12px; flex-wrap:wrap;">
        <div>
          <h2 style="margin:0; font-size:1.35rem;">📒 Mis recetas familiares (${lista.length})</h2>
          <small style="color:var(--text-muted);">Todo tu recetario organizado en un solo lugar, conectado al calendario y a tus compras.</small>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          ${!ui.mostrarFormReceta ? `
            <button type="button" class="btn-primary-sm" onclick="abrirNuevaMiReceta()">
              ➕ Agregar mi receta
            </button>
          ` : ""}
          ${lista.length > 0 ? `
            <button type="button" class="btn-secondary" onclick="respaldarMisRecetasWhatsAppUI()">
              📲 Respaldar en WhatsApp
            </button>
          ` : ""}
        </div>
      </div>

      <div id="boxBackupMisRecetas" style="display:none; margin-bottom:16px;" class="control-panel no-print">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <strong style="color:var(--accent-sage-dark);">📲 Copia de respaldo de Mis Recetas (pegala en tu WhatsApp o notas):</strong>
          <button type="button" class="btn-tengo" onclick="document.getElementById('boxBackupMisRecetas').style.display='none'">Cerrar ✕</button>
        </div>
        <pre id="preBackupMisRecetas" style="background:var(--bg-cream); padding:12px; border-radius:8px; border:1px solid var(--border-soft); white-space:pre-wrap; font-family:inherit; font-size:0.88rem; margin:0;"></pre>
      </div>

      ${formHtml}
      ${tarjetasHtml}

      <div class="info-box cue-fridge" style="margin-top:16px;">
        <strong>🛡️ Recordatorio de seguridad alimentaria para tus recetas caseras:</strong>
        Las recetas propias se guardan en la memoria de este dispositivo. Recordá siempre refrigerar las comidas cocidas antes de las 2 horas y consumir las sobras de heladera dentro de los 3 días como máximo.
      </div>
    `;
  }

  // =========================================================================
  // 7. FICHA COMPLETA DE RECETA
  // =========================================================================

  window.toggleIngredienteEnFicha = function (recetaId, idx) {
    const k = `${recetaId}_${idx}`;
    estado.ingredientesRecetaTildados[k] = !estado.ingredientesRecetaTildados[k];
    M.guardarEstado(estado);
    renderizarApp();
  };

  window.toggleHechoDesdeFicha = function (recetaId) {
    if (ui.contextoFicha && ui.contextoFicha.dia && ui.contextoFicha.turno) {
      const k = `${ui.contextoFicha.dia}_${ui.contextoFicha.turno}`;
      estado.comidasHechas[k] = !estado.comidasHechas[k];
    } else {
      estado.comidasHechas[recetaId] = !estado.comidasHechas[recetaId];
    }
    M.guardarEstado(estado);
    renderizarApp();
  };

  function renderizarPantallaFicha(recetasMap, factorHogar) {
    const r = recetasMap[ui.recetaAbiertaId] || D.recetas[0];
    const esBase = r.id === "base-pollo-cocido";
    const esPersonal = !!r.es_personal;
    const aptaChicos = (r.etiquetas || []).includes("apta para chicos");

    const heroHtml = (r.tiene_imagen && r.imagen_url)
      ? `<div class="recipe-hero"><img src="${r.imagen_url}" alt="${r.nombre}"></div>`
      : `<div class="recipe-hero-placeholder"><span style="font-size: 2.2rem;">${esPersonal ? "📒" : "🍲"}</span><div style="font-weight: 800; color: var(--accent-sage-dark); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px;">${esBase ? "Receta Base de Batch Cooking" : (esPersonal ? "Tu Receta Familiar Personal" : "Preparación Casera")}</div></div>`;

    let chipsHtml = `<span class="tag-chip protein">Proteína: ${r.proteina}</span>`;
    if (esPersonal) chipsHtml += `<span class="tag-chip batch">🏷️ Tu receta personal</span>`;
    if (esBase) chipsHtml += `<span class="tag-chip batch">Batch Cooking</span>`;
    if (aptaChicos) chipsHtml += `<span class="tag-chip kids">👶 Apta para chicos</span>`;

    let bannerUsaBase = "";
    if (r.usa_base && r.usa_base.base === "pollo cocido") {
      const cantPollo = M.cantidadPracticaReceta(r.usa_base.cantidad, "g", factorHogar);
      bannerUsaBase = `
        <div class="base-link-banner">
          <div>
            <strong>🍗 Usa Base de pollo cocido (${cantPollo})</strong>
            <div style="font-size: 0.84rem; color: var(--text-muted);">Adelantada en tu heladera o freezer según las marcas del calendario.</div>
          </div>
          <button type="button" class="base-link-btn" onclick="abrirFichaReceta('base-pollo-cocido')">Ver Receta Base →</button>
        </div>`;
    }

    const ingsHtml = (r.ingredientes || []).map((ing, idx) => {
      const k = `${r.id}_${idx}`;
      const checked = estado.ingredientesRecetaTildados[k] ? "checked" : "";
      const tick = estado.ingredientesRecetaTildados[k] ? "✓" : "";
      const cantStr = M.cantidadPracticaReceta(ing.cantidad, ing.unidad, factorHogar);
      return `
        <li class="ing-item ${checked}" onclick="toggleIngredienteEnFicha('${r.id}', ${idx})">
          <div class="ing-left"><span class="ing-checkbox">${tick}</span><span>${ing.item}</span></div>
          <span class="ing-qty">${cantStr}</span>
        </li>`;
    }).join("");

    const pasosHtml = (r.pasos || []).map((paso, idx) => `<li class="step-item"><span class="step-num">${idx + 1}</span><div>${paso}</div></li>`).join("");
    const rindeHtml = r.rinde ? `<div class="info-box cue-brown"><strong>⚖️ Rendimiento y medidas:</strong>${r.rinde}</div>` : "";
    const senalesHtml = r.senales_coccion ? `<div class="info-box cue-brown"><strong>👀 Señal de cocción${r.temperatura_referencia ? ` · 🌡️ ${r.temperatura_referencia}` : ""}:</strong>${r.senales_coccion}</div>` : "";
    const notaSegHtml = r.nota_seguridad ? `<div class="info-box cue-orange"><strong>🐟 Nota de seguridad alimentaria:</strong>${r.nota_seguridad}</div>` : "";
    const acompVerdeHtml = r.acompanamiento_verde ? `<div class="info-box cue-green"><strong>🥗 Acompañamiento fresco sugerido:</strong>${r.acompanamiento_verde}</div>` : "";
    const kidsHighlightClass = estado.modoChicos ? "kids-highlighted" : "";
    const variantesHtml = (r.version_chicos || r.variante_adultos) ? `
      <div class="variants-grid">
        ${r.version_chicos ? `<div class="variant-card ${kidsHighlightClass}"><strong>👶 Versión chicos ${estado.modoChicos ? "(Destacado)" : ""}</strong>${r.version_chicos}</div>` : ""}
        ${r.variante_adultos ? `<div class="variant-card"><strong>🌶️ Variante adultos</strong>${r.variante_adultos}</div>` : ""}
      </div>` : "";
    const sobraHtml = r.si_te_sobra ? `<div class="info-box cue-fridge"><strong>🧊 Conservación y sobras (máximo 3 días):</strong>${r.si_te_sobra}</div>` : "";
    const kcalTexto = r.nutricion && r.nutricion.kcal ? `~${r.nutricion.kcal} kcal` : "Variable";

    const claveHecho = (ui.contextoFicha && ui.contextoFicha.dia)
      ? `${ui.contextoFicha.dia}_${ui.contextoFicha.turno}`
      : r.id;
    const estaHecha = !!estado.comidasHechas[claveHecho];

    return `
      <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">
        <button type="button" class="btn-secondary" onclick="volverDeFicha()">
          ← Volver
        </button>
        ${esPersonal ? `
          <div style="display:flex; gap:8px;">
            <button type="button" class="btn-secondary" onclick="abrirEditarMiReceta('${r.id}')">✏️ Editar mi receta</button>
            <button type="button" class="btn-tengo" onclick="borrarMiRecetaUI('${r.id}')">🗑️ Borrar</button>
          </div>
        ` : ""}
      </div>
      <article class="recipe-card">
        ${heroHtml}
        <div class="recipe-body">
          <div class="recipe-tags-row">${chipsHtml}</div>
          <h2 class="recipe-title">${r.nombre}</h2>
          <div class="recipe-meta-grid">
            <div class="meta-pill"><span class="meta-pill-label">⏱️ Tiempo total</span><span class="meta-pill-val">${r.tiempo_total} min</span></div>
            <div class="meta-pill"><span class="meta-pill-label">👩‍🍳 Tiempo activo</span><span class="meta-pill-val">${r.tiempo_activo} min</span></div>
            <div class="meta-pill"><span class="meta-pill-label">🔥 Energía</span><span class="meta-pill-val">${kcalTexto} <small style="font-weight:600; font-size:0.7rem; display:block; color:var(--text-muted);">estimación por porción de adulto</small></span></div>
          </div>
          ${bannerUsaBase}
          ${estado.modoChicos ? variantesHtml : ""}
          <div class="section-subtitle">
            <span>🛒 Ingredientes (${M.describirPorcionesHogar(estado.porciones)})</span>
            <small style="font-weight:600; text-transform:none; color:var(--text-muted);">Tocá para tildar</small>
          </div>
          <ul class="ing-list">${ingsHtml}</ul>
          <div class="section-subtitle">
            <span>👩‍🍳 Paso a paso simple</span>
            <small style="font-weight:600; text-transform:none; color:var(--text-muted);">Dificultad: ${r.dificultad}</small>
          </div>
          <ol class="steps-list">${pasosHtml}</ol>
          ${rindeHtml}
          ${senalesHtml}
          ${!estado.modoChicos ? variantesHtml : ""}
          ${notaSegHtml}
          ${acompVerdeHtml}
          ${sobraHtml}
          <button type="button" class="done-meal-btn ${estaHecha ? "completed" : ""}" onclick="toggleHechoDesdeFicha('${r.id}')">
            <span>${estaHecha ? "✅ ¡Comida resuelta! (Tocá para desmarcar)" : "✓ Marcar esta comida como hecha"}</span>
          </button>
        </div>
      </article>
    `;
  }

  // =========================================================================
  // 9. PWA, INSTALACIÓN Y CONTROL DE ACCESO (GATE COCINA30)
  // =========================================================================

  let deferredPrompt = null;
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("./sw.js?v=3").then(function (reg) {
        if (reg) {
          reg.update();
          console.log("Service Worker activo v3:", reg.scope);
        }
      }).catch(function (err) {
        console.log("Fallo al registrar Service Worker:", err);
      });
    });
  }

  window.addEventListener("beforeinstallprompt", function (e) {
    if (e && e.preventDefault) e.preventDefault();
    deferredPrompt = e;
    const btnInstalar = document.getElementById("btnInstalarPWA");
    if (btnInstalar) {
      btnInstalar.style.display = "inline-flex";
    }
  });

  window.instalarPWAUI = function () {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function () {
        deferredPrompt = null;
        const btnInstalar = document.getElementById("btnInstalarPWA");
        if (btnInstalar) btnInstalar.style.display = "none";
      });
    } else {
      alert("Para instalar esta app en tu pantalla de inicio:\n\n• En iPhone (Safari): tocá el botón Compartir (el ícono de la cajita con una flecha hacia arriba) y elegí 'Agregar a inicio'.\n• En Android (Chrome): tocá los tres puntitos arriba a la derecha y elegí 'Instalar aplicación' o 'Agregar a la pantalla principal'.\n\n¡Listo! Te va a quedar como una app en tu celular que podés usar sin internet.");
    }
  };

  // Huella criptográfica SHA-256 del código de acceso.
  // El código real NO queda escrito en texto plano en ninguna parte de la app.
  const HASH_ACCESO_PERMITIDO = "40c084f81ae1f8786818417d87a0dd1b314cc8d8069c1b6046fa5d087c944e4d";

  async function calcularSha256(texto) {
    if (window.crypto && window.crypto.subtle && window.crypto.subtle.digest) {
      const buffer = new TextEncoder().encode(texto);
      const hashBuffer = await window.crypto.subtle.digest("SHA-256", buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
    }
    return "";
  }

  window.toggleVisibilidadPasswordUI = function () {
    const inp = document.getElementById("inputCodigoAcceso");
    const btn = document.getElementById("btnTogglePassword");
    if (!inp) return;
    if (inp.type === "password") {
      inp.type = "text";
      if (btn) btn.textContent = "🙈";
    } else {
      inp.type = "password";
      if (btn) btn.textContent = "👁️";
    }
  };

  window.verificarCodigoAccesoUI = async function (e) {
    if (e && e.preventDefault) e.preventDefault();
    const inp = document.getElementById("inputCodigoAcceso");
    const err = document.getElementById("msgErrorAcceso");
    if (!inp) return;
    const val = String(inp.value || "").trim().toUpperCase();
    const hashIngresado = await calcularSha256(val);

    if (hashIngresado === HASH_ACCESO_PERMITIDO) {
      estado.accesoAutorizado = true;
      M.guardarEstado(estado);
      renderizarApp();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      if (err) {
        err.style.display = "block";
        err.textContent = "Revisá el código que te enviamos";
      }
      inp.focus();
    }
  };

  function renderizarPantallaAcceso() {
    return `
      <div class="access-gate-wrapper">
        <div class="access-gate-card">
          <img src="ilustraciones/portada.png" alt="30 días sin preguntarte qué cocinar" class="access-gate-thumb">
          <span class="brand-badge">Saso Digital · Edición 2026</span>
          <h2 class="access-gate-title">Compañero de 30 días</h2>
          <p class="access-gate-text">
            Ingresá el código de acceso exclusivo que recibiste con tu ebook para desbloquear la app:
          </p>

          <form class="access-form-box" onsubmit="verificarCodigoAccesoUI(event)">
            <label for="inputCodigoAcceso" class="access-label">
              🔑 Código de acceso:
            </label>

            <div class="access-input-group">
              <input 
                type="password" 
                id="inputCodigoAcceso" 
                class="access-input" 
                placeholder="Escribí tu código acá" 
                autocomplete="off" 
                autocapitalize="characters" 
                autocorrect="off" 
                spellcheck="false" 
                required 
                autofocus
              >
              <button 
                type="button" 
                id="btnTogglePassword" 
                class="btn-toggle-eye" 
                onclick="toggleVisibilidadPasswordUI()" 
                aria-label="Ver u ocultar código"
                title="Ver u ocultar código"
              >
                👁️
              </button>
            </div>

            <button type="submit" class="btn-access-submit" id="btnEntrarAcceso">
              <span>Entrar</span>
              <span style="font-size: 1.2rem;">→</span>
            </button>

            <div id="msgErrorAcceso" class="access-error-msg">
              Revisá el código que te enviamos
            </div>

            <div class="access-hint-text">
              💡 Solo te lo pedimos la primera vez en cada dispositivo. Al entrar, no te lo volverá a pedir.
            </div>
          </form>

          <div class="pwa-helper-card">
            <h4>📱 Instalar en tu pantalla de inicio</h4>
            <p style="font-size:0.86rem; color:var(--text-muted); margin:0 0 8px 0; line-height:1.4;">
              Podés usar esta app como una aplicación móvil real, con ícono propio en tu celular y funcionando 100% sin conexión a internet.
            </p>
            <button type="button" id="btnInstalarPWA" class="btn-pwa-install" onclick="instalarPWAUI()">
              📲 Instalar app en mi celular
            </button>
          </div>

          <div style="margin-top:20px; font-size:0.78rem; color:var(--text-muted); line-height:1.4;">
            🔒 <strong>Acceso privado:</strong> Esta aplicación no es indexada por buscadores y guarda tus datos únicamente en la memoria de tu dispositivo para proteger tu privacidad.
          </div>
        </div>
      </div>
    `;
  }

  // =========================================================================
  // RENDERIZADO GENERAL DE LA APP
  // =========================================================================

  function renderizarApp() {
    const headerEl = document.querySelector(".top-header");
    const navEl = document.querySelector(".bottom-nav");
    const footerEl = document.querySelector(".legal-footer");
    const panelPorc = document.getElementById("panelPorcionesGlobal");
    const mainCont = document.getElementById("mainContenidoApp");

    // Si aún no ingresó el código de acceso en esta primera visita:
    if (!estado.accesoAutorizado) {
      if (headerEl) headerEl.style.display = "none";
      if (navEl) navEl.style.display = "none";
      if (footerEl) footerEl.style.display = "none";
      if (panelPorc) panelPorc.style.display = "none";
      if (mainCont) mainCont.innerHTML = renderizarPantallaAcceso();
      return;
    }

    if (headerEl) headerEl.style.display = "";
    if (navEl) navEl.style.display = "";
    if (footerEl) footerEl.style.display = "";

    // Actualizar cabecera
    const btnKids = document.getElementById("btnModoChicos");
    const txtKids = document.getElementById("txtModoChicos");
    if (btnKids && txtKids) {
      btnKids.classList.toggle("active", estado.modoChicos);
      txtKids.textContent = estado.modoChicos ? "👶 Con chicos: ON" : "👶 Con chicos";
    }

    const txtPorcionesBtn = document.getElementById("txtResumenPorcionesHeader");
    if (txtPorcionesBtn) {
      txtPorcionesBtn.textContent = M.describirPorcionesHogar(estado.porciones);
    }

    // Panel desplegable de porciones
    if (panelPorc) {
      panelPorc.style.display = ui.mostrarPanelPorciones ? "block" : "none";
      document.getElementById("valAdultos").textContent = estado.porciones.adultos;
      document.getElementById("valMenores4").textContent = estado.porciones.menores4;
      document.getElementById("valChicos4a8").textContent = estado.porciones.chicos4a8;
      [2, 4, 6].forEach(n => {
        const b = document.getElementById(`preset${n}`);
        if (b) b.classList.toggle("active", estado.porciones.preset === n);
      });
    }

    // Actualizar pestañas activas de la barra inferior
    ["hoy", "calendario", "compras", "mis_recetas", "extras", "seguridad"].forEach(tabId => {
      const btn = document.getElementById(`tabBottom_${tabId}`);
      if (btn) {
        const esActiva = (ui.pantalla === tabId) || (ui.pantalla === "ficha_receta" && ui.pantallaAnterior === tabId);
        btn.classList.toggle("active", esActiva);
      }
    });

    const calActivo = M.obtenerCalendarioActivo(D, estado);
    const recetasMap = mapaRecetas();
    const factorHogar = M.obtenerFactorHogar(estado.porciones);

    if (ui.pantalla === "hoy") {
      mainCont.innerHTML = renderizarPantallaHoy(calActivo, recetasMap, factorHogar);
    } else if (ui.pantalla === "calendario") {
      mainCont.innerHTML = renderizarPantallaCalendario(calActivo, recetasMap, factorHogar);
    } else if (ui.pantalla === "hoy_no_puedo") {
      mainCont.innerHTML = renderizarPantallaHoyNoPuedo(factorHogar);
    } else if (ui.pantalla === "compras") {
      mainCont.innerHTML = renderizarPantallaCompras();
    } else if (ui.pantalla === "mis_recetas") {
      mainCont.innerHTML = renderizarPantallaMisRecetas(factorHogar);
    } else if (ui.pantalla === "extras") {
      mainCont.innerHTML = renderizarPantallaExtras();
    } else if (ui.pantalla === "seguridad") {
      mainCont.innerHTML = renderizarPantallaSeguridad();
    } else if (ui.pantalla === "ficha_receta") {
      mainCont.innerHTML = renderizarPantallaFicha(recetasMap, factorHogar);
    }
  }

  // Inicialización al cargar (compatible con carga diferida o instantánea)
  function inicializarApp() {
    const avisoEl = document.getElementById("textoAvisoLegal");
    if (avisoEl) avisoEl.textContent = D.meta.aviso_profesional;
    renderizarApp();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarApp);
  } else {
    inicializarApp();
  }

})();

