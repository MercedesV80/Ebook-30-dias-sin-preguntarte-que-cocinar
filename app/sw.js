/* ==========================================================================
   COMPAÑERO DE 30 DÍAS · SERVICE WORKER (PWA OFFLINE COMPLETO)
   Garantiza funcionamiento 100% sin conexión en celular
   ========================================================================== */

const CACHE_NAME = "companero30-v1";

const RECURSOS_OFFLINE = [
  "./",
  "./index.html",
  "./estilos.css",
  "./datos.js",
  "./logica.js",
  "./app.js",
  "./manifest.json",
  "./icono-192.png",
  "./icono-512.png",
  "./icono-apple.png",
  "./fuentes/Fraunces.ttf",
  "./fuentes/NunitoSans.ttf",
  "./ilustraciones/albondigas-salsa.png",
  "./ilustraciones/arroz-salteado-huevo.png",
  "./ilustraciones/berenjenas-parmesana.png",
  "./ilustraciones/cerdo-agridulce.png",
  "./ilustraciones/cerdo-manzanas-pure.png",
  "./ilustraciones/chili-carne-porotos.png",
  "./ilustraciones/crema-calabaza-garbanzos.png",
  "./ilustraciones/crumble-manzana.png",
  "./ilustraciones/ensalada-atun-papa.png",
  "./ilustraciones/ensalada-porotos-choclo.png",
  "./ilustraciones/fajitas-carne.png",
  "./ilustraciones/fideos-atun-tomate.png",
  "./ilustraciones/fideos-bolognesa-lentejas.png",
  "./ilustraciones/fideos-pollo-brocoli.png",
  "./ilustraciones/guiso-lentejas.png",
  "./ilustraciones/hamburguesas-caseras.png",
  "./ilustraciones/huevos-salsa-criolla.png",
  "./ilustraciones/medallones-garbanzos.png",
  "./ilustraciones/merluza-criolla.png",
  "./ilustraciones/merluza-crocante-horno.png",
  "./ilustraciones/milanesas-pollo-horno.png",
  "./ilustraciones/minestrone-porotos.png",
  "./ilustraciones/pastel-papa-calabaza.png",
  "./ilustraciones/pizza-pan-arabe.png",
  "./ilustraciones/polenta-espinaca-queso.png",
  "./ilustraciones/pollo-horno-batatas.png",
  "./ilustraciones/pollo-limon-sarten.png",
  "./ilustraciones/portada.png",
  "./ilustraciones/quesadillas-pollo-choclo.png",
  "./ilustraciones/tarta-pollo-choclo.png",
  "./ilustraciones/tortilla-papa-espinaca.png",
  "./ilustraciones/wok-pollo-arroz.png",
  "./ilustraciones/wraps-hummus.png",
  "./ilustraciones/zapallitos-rellenos.png"
];

// Instalación: cachear todos los recursos para modo avión / sin señal
self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(RECURSOS_OFFLINE);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

// Activación: limpiar caches viejos y tomar control inmediato
self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.map(function (key) {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

// Intercepción de solicitudes: servir primero desde cache, fallback a red
self.addEventListener("fetch", function (event) {
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then(function (cachedResponse) {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then(function (networkResponse) {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== "basic") {
          return networkResponse;
        }
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then(function (cache) {
          cache.put(event.request, responseToCache);
        });
        return networkResponse;
      }).catch(function () {
        // Si está offline y navega a una ruta HTML, devolver index.html
        if (event.request.mode === "navigate") {
          return caches.match("./index.html");
        }
      });
    })
  );
});

