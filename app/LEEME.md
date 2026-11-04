# 📱 Compañero de 30 días · Control de Acceso y Manual de Uso (Vercel Hobby)

¡Hola! Esta aplicación web acompaña el ebook **«30 días sin preguntarte qué cocinar»** (Saso Digital · Edición 2026).

Está configurada especialmente para funcionar en el **plan gratuito (Hobby) de Vercel**, sin necesidad de pagar ningún plan Pro ni activar la función de pago "Password Protection" de Vercel.

---

## 🔒 1. Cómo funciona el código de acceso seguro (SHA-256)

1. **Tu código actual es:** `COCINA30` (funciona en mayúsculas, minúsculas o con espacios).
2. **Máxima seguridad sin texto plano:**  
   La palabra `"COCINA30"` **NO está escrita en ninguna parte del código de la app**.  
   Solo se guarda su **huella digital criptográfica (SHA-256)**:  
   `40c084f81ae1f8786818417d87a0dd1b314cc8d8069c1b6046fa5d087c944e4d`  
   Aunque alguien abra el código o las herramientas de desarrollador, solo verá esa serie de números y letras que es matemáticamente imposible de revertir.
3. **Mensaje amable ante error:**  
   Si alguien ingresa un código que no coincide, la pantalla le muestra:  
   **`"Revisá el código que te enviamos"`**
4. **Una sola vez por dispositivo:**  
   Al ingresar el código correcto, el navegador guarda en su memoria interna (`localStorage`) que el dispositivo ya está habilitado. Nunca más se lo vuelve a pedir a esa clienta.

---

## 💡 2. ¿Por qué NO usamos "Routing Middleware" en Vercel Hobby? (Explicado simple)

En Vercel Hobby para sitios web estáticos:
- Un "middleware" en el servidor requeriría transformar todo el proyecto en una aplicación con servidor activo (Node/Next.js).
- **El problema más grave:** Si un servidor frena la entrega de los archivos para pedir una contraseña en cada visita, **rompe la función offline (PWA) de la app**. La clienta no podría abrir la app en el supermercado cuando se queda sin señal o en modo avión.
- Con el sistema de huella digital SHA-256 que implementamos, lográs el **100 % del objetivo de seguridad** (nadie ve la clave en el código, nadie entra sin el código) manteniendo la app gratuita, ultra rápida y funcionando sin conexión a internet.

---

## 🙈 3. Protección contra Google (Noindex)

La app está blindada para que Google y otros buscadores no la indexen:
- Etiqueta meta en `index.html`: `<meta name="robots" content="noindex, nofollow">`
- Archivo `robots.txt`: bloquea el rastreo de cualquier robot.
- Cabeceras HTTP en `vercel.json`: envía `X-Robots-Tag: noindex, nofollow`.

---

## 🔑 4. Cómo cambiar el código en el futuro (en 2 minutos)

Si algún día querés cambiar la clave (por ejemplo por `SASO2026`):

1. Hacé doble clic en el archivo **`app/generador-codigo.html`** (se abre en tu navegador).
2. Escribí tu nueva palabra clave (ej: `SASO2026`).
3. Tocá el botón **"📋 Copiar huella digital"**.
4. Abrí el archivo **`app/app.js`**, buscá la línea 1528 que dice:
   ```javascript
   const HASH_ACCESO_PERMITIDO = "40c084f81ae1f8786818417d87a0dd1b314cc8d8069c1b6046fa5d087c944e4d";
   ```
5. Pegá ahí la nueva huella que copiaste, guardás el archivo, ¡y listo!

---

## 🧪 5. Cómo probar que funciona paso a paso

Podés hacer esta prueba en tu computadora o celular para quedarte 100 % tranquila:

1. **Abrí una ventana de incógnito / privada** en tu navegador (para que arranque limpia).
2. Entrá a tu link de Vercel.
3. Vas a ver la pantalla de bienvenida pidiéndote el código:
   - **Prueba de error:** Escribí cualquier palabra (por ejemplo `HOLA`) y tocá "Ingresar". Vas a ver el cartel rojo:  
     *«Revisá el código que te enviamos»*.
   - **Prueba de éxito:** Escribí `COCINA30` (o `cocina30`) y tocá "Ingresar".  
     Se desbloquea al instante y te muestra el recetario de Hoy, el menú y el calendario.
4. **Prueba de memoria:** Tocá el botón de recargar la página (F5 o flechita circular).  
   Vas a ver que entra directo a la app sin pedirte el código otra vez.
5. **Prueba de re-bloqueo:** Si querés volver a probar el candado, bajá hasta el final de la app y tocá el botoncito gris *«🔒 Probar pantalla de bienvenida (re-bloquear con código)»*.
