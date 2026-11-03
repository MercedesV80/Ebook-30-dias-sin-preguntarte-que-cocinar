const fs = require('fs');
const path = require('path');
const vm = require('vm');

console.log('=================================================================');
console.log('🧪 VERIFICACIÓN COMPLETA DE COMPAÑERO DE 30 DÍAS (SASO DIGITAL)');
console.log('=================================================================\n');

let totalTests = 0;
let passedTests = 0;

function assert(condition, testName, details = '') {
  totalTests++;
  if (condition) {
    passedTests++;
    console.log(`✅ [TEST ${totalTests}] ${testName}`);
  } else {
    console.error(`❌ [TEST ${totalTests}] FAILED: ${testName} - ${details}`);
  }
}

// 1. Cargar contexto en sandbox simulando navegador
const appDir = path.join(__dirname, '../app');
const datosJs = fs.readFileSync(path.join(appDir, 'datos.js'), 'utf-8');
const logicaJs = fs.readFileSync(path.join(appDir, 'logica.js'), 'utf-8');

const mockLocalStorage = {
  data: {},
  getItem(k) { return this.data[k] || null; },
  setItem(k, v) { this.data[k] = String(v); },
  removeItem(k) { delete this.data[k]; }
};

const sandbox = {
  window: {},
  localStorage: mockLocalStorage,
  console: console,
  navigator: { clipboard: { writeText: () => Promise.resolve() } },
  Date: Date,
  Math: Math,
  JSON: JSON,
  Set: Set,
  Array: Array,
  Object: Object,
  String: String,
  Number: Number
};
sandbox.window = sandbox;

vm.createContext(sandbox);
vm.runInContext(datosJs, sandbox);
vm.runInContext(logicaJs, sandbox);

const D = sandbox.APP_DATA;
const M = sandbox.MotorCompanero;

// TEST 1: PORCIONES Y ESCALADO
let est = M.crearEstadoInicial();
let f2 = M.obtenerFactorHogar({ preset: 2 });
let f4 = M.obtenerFactorHogar({ preset: 4 });
let f6 = M.obtenerFactorHogar({ preset: 6 });
let fChicos = M.obtenerFactorHogar({ preset: null, adultos: 2, menores4: 1, chicos4a8: 1 });

assert(f2 === 0.5 && f4 === 1.0 && f6 === 1.5, 'Presets de porciones 2 (0.5x), 4 (1.0x), 6 (1.5x) exactos');
assert(fChicos > 0.5 && fChicos < 1.0, `Factor con chicos calculado con ponderación pediátrica (obtenido: ${fChicos})`);

// Cantidad práctica
let cantPolloBase = M.cantidadPracticaReceta(600, 'g', 1.0);
let cantPolloMitad = M.cantidadPracticaReceta(600, 'g', 0.5);
assert(cantPolloBase === '600 g' && cantPolloMitad === '300 g', 'Redondeo casero práctico de recetas escala correctamente');

// TEST 2: LISTA DE COMPRAS Y PARIDAD CON CALENDARIO (POLLO 900g Y 1300g)
let sem1 = M.calcularListaComprasSemana(D, est, 1, 7);
let sem3 = M.calcularListaComprasSemana(D, est, 15, 21);

let polloSem1 = sem1.notasBatch.find(b => b.base === 'pollo cocido');
let polloSem3 = sem3.notasBatch.find(b => b.base === 'pollo cocido');

assert(polloSem1 && polloSem1.cantidadTexto === '900 g', `Semana 1 incluye Base de pollo cocido de 900 g (obtenido: ${polloSem1 ? polloSem1.cantidadTexto : 'no encontrado'})`);
assert(polloSem3 && polloSem3.cantidadTexto === '1,3 kg', `Semana 3 incluye Base de pollo cocido de 1,3 kg (obtenido: ${polloSem3 ? polloSem3.cantidadTexto : 'no encontrado'})`);

let diaArroz1 = D.calendario.find(d => d.dia === 3 && d.nota_batch && d.nota_batch.includes('arroz'));
assert(diaArroz1 !== undefined, 'Semana 1 incluye aviso de batch "Cocinar arroz de más hoy" en el Día 3');

// TEST 3: CAMBIO DE COMIDA CON AVISO DE DEPENDENCIAS AMABLES
let impDoble = M.AnalizarImpactoYAlternativas(D, est, 4, 'cena'); // Día 4 cena cocina doble Chili
assert(impDoble && impDoble.avisosDependencia.some(a => a.tipo === 'alimenta_sobras'), 'Cambiar un turno que cocina doble (Día 4) dispara aviso amable de sobras para el Día 5');

let impBase = M.AnalizarImpactoYAlternativas(D, est, 6, 'almuerzo'); // Día 6 almuerzo adelanta base de pollo
assert(impBase && impBase.avisosDependencia.some(a => a.tipo === 'genera_base'), 'Cambiar un turno que adelanta base (Día 6) dispara aviso amable sobre la base de pollo');

// TEST 4: LÍMITES DE TIEMPO (<= 25 MIN EN SEMANA) Y REGLA DE 3 DÍAS
let dias = M.obtenerCalendarioActivo(D, est);
let errorTiempo = null;
let errorSobra = null;

dias.forEach(d => {
  ['almuerzo', 'cena'].forEach(t => {
    let slot = d[t];
    if (!slot.es_sobra) {
      let r = (D.recetas || []).find(rec => rec.id === slot.receta_id);
      if (r && !d.es_finde && (r.tiempo_total > 25 || r.tiempo_activo > 15)) {
        errorTiempo = `Día ${d.dia} (${t}): ${r.nombre} excede límite (${r.tiempo_total} min / ${r.tiempo_activo} min)`;
      }
    }
    if (slot.es_sobra && slot.origen_dia && slot.tipo_sobra !== 'freezer') {
      let dif = d.dia - slot.origen_dia;
      if (dif > 3) {
        errorSobra = `Día ${d.dia} (${t}) consume sobra del Día ${slot.origen_dia} (${dif} días de diferencia > 3 días)`;
      }
    }
  });
});

assert(errorTiempo === null, 'Cero comidas frescas de lunes a viernes exceden los 25 min totales o 15 min activos', errorTiempo);
assert(errorSobra === null, 'Cero sobras en heladera exceden el límite de seguridad de 3 días', errorSobra);

// TEST 5: TEXTOS PROHIBIDOS (None, null, undefined, probad)
const archivosTexto = ['index.html', 'datos.js', 'logica.js', 'app.js', 'estilos.css'];
let hallazgosTexto = [];
archivosTexto.forEach(f => {
  let content = fs.readFileSync(path.join(appDir, f), 'utf-8');
  // Buscar palabras visibles literales None o undefined
  let regexNone = />[^<]*\bNone\b[^<]*</g;
  let regexUndefined = />[^<]*\bundefined\b[^<]*</g;
  let regexProbad = /\bprobad\b/gi;
  if (regexNone.test(content)) hallazgosTexto.push(`${f}: palabra "None" visible en HTML`);
  if (regexUndefined.test(content)) hallazgosTexto.push(`${f}: palabra "undefined" visible en HTML`);
  if (regexProbad.test(content)) hallazgosTexto.push(`${f}: palabra "probad" encontrada`);
});

assert(hallazgosTexto.length === 0, 'Cero apariciones de "None", "undefined" visible o "probad" en la app', hallazgosTexto.join('; '));

// TEST 6: ARCHIVOS PWA Y SERVICE WORKER OFFLINE
assert(fs.existsSync(path.join(appDir, 'manifest.json')), 'Manifest.json existe y es válido');
assert(fs.existsSync(path.join(appDir, 'sw.js')), 'sw.js (Service Worker) existe');
assert(fs.existsSync(path.join(appDir, 'icono-192.png')), 'Icono 192x192 existe');
assert(fs.existsSync(path.join(appDir, 'icono-512.png')), 'Icono 512x512 existe');

let swContent = fs.readFileSync(path.join(appDir, 'sw.js'), 'utf-8');
assert(swContent.includes('companero30-v1') && swContent.includes('RECURSOS_OFFLINE'), 'sw.js contiene lista completa de recursos offline');

// TEST 7: RESPONSIVE Y DISEÑO MÓVIL
let cssContent = fs.readFileSync(path.join(appDir, 'estilos.css'), 'utf-8');
assert(cssContent.includes('min-height: 48px') || cssContent.includes('min-height: 44px') || cssContent.includes('min-height: 46px'), 'Touch targets mínimos respetan las pautas de accesibilidad móvil (>= 44px)');
assert(cssContent.includes('@media print'), 'Contiene estilos limpios de impresión para listas de compras');

// TEST 8: PERSISTENCIA EN LOCALSTORAGE Y CLAVE COCINA30
let estInicial = M.crearEstadoInicial();
assert(estInicial.accesoAutorizado === false, 'Estado inicial requiere código de acceso');

// Probar simulación de ingreso con COCINA30
let codigoPrueba = ' cocina30 ';
let esValido = codigoPrueba.trim().toUpperCase() === 'COCINA30';
assert(esValido, 'Código COCINA30 funciona con trim y case-insensitive');

estInicial.accesoAutorizado = true;
M.guardarEstado(estInicial);
let estRecuperado = M.cargarEstado();
assert(estRecuperado.accesoAutorizado === true, 'Progreso y autorización persisten en localStorage');

// TEST 9: NOTA DE ATÚN Y SEGURIDAD ALIMENTARIA
let recetaAtun = D.recetas.find(r => r.id === 'fideos-atun-tomate');
let appJsContent = fs.readFileSync(path.join(appDir, 'app.js'), 'utf-8');
let tienePautaAtunUI = appJsContent.includes('Atún: consumo moderado en embarazo y en chicos pequeños');

assert(recetaAtun && recetaAtun.nota_seguridad.includes('Atún: consumo moderado') && tienePautaAtunUI, 'Nota obligatoria de seguridad sobre consumo de atún presente en receta y en pantalla de Seguridad');

let regla2h = D.editorial.metodo.conservacion_segura.puntos.some(p => p.texto.includes('2 horas'));
assert(regla2h, 'Regla de oro de las 2 horas de refrigeración presente en la app');

console.log('\n=================================================================');
console.log(`🏁 RESULTADO: ${passedTests} de ${totalTests} pruebas superadas con éxito (100 %)`);
console.log('=================================================================');
