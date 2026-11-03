# 📱 Compañero de 30 días · Guía simple para la creadora

¡Hola! Esta carpeta contiene la aplicación web interactiva **«Compañero de 30 días»** creada para acompañar tu ebook *«30 días sin preguntarte qué cocinar»* (Saso Digital · Edición 2026).

Está diseñada en **HTML, CSS y JavaScript puros** (sin frameworks complicados ni servidores que pagar) para que puedas publicarla gratis en **Vercel** exactamente igual que tu proyecto *"¿Qué Cocino?"*.

---

## 🚀 1. Cómo publicarla en Vercel en 3 pasos simples

1. Entrá a tu cuenta de **[Vercel](https://vercel.com/)**.
2. Hacé clic en **"Add New... > Project"** y seleccioná el repositorio de GitHub de este ebook.
3. En la configuración del proyecto:
   - **Root Directory:** elegí la carpeta `app` (o escribí `app` y guardá).
   - Dejá el resto de los campos como están y hacé clic en **"Deploy"**.

¡Listo! En menos de un minuto Vercel te dará un link privado (por ejemplo: `https://companero30.vercel.app`).

---

## 🔒 2. Cómo funciona el código de acceso y sus limitaciones (explicado simple)

- **El código actual es:** `COCINA30` (funciona en mayúsculas o minúsculas).
- **Cómo lo vive tu clienta:**
  Cuando entra por primera vez desde su celular o compu, ve una pantalla linda y cálida que le pide el código. Una vez que lo ingresa, **no se lo vuelve a pedir más** en ese dispositivo y puede usar la app todos los días, incluso en modo avión o sin señal.
- **Limitación en lenguaje simple:**
  Como esta app **no tiene base de datos ni cobra costo de mantenimiento mensual** (para que sea gratis y privada para tus clientas), la verificación del código se hace directamente en el navegador del teléfono.
  Esto significa que alguien con conocimientos avanzados de programación podría inspeccionar el archivo y ver el código. Sin embargo, para tus clientas reales es la barrera perfecta: protege tu link privado, evita que curiosos lo usen sin comprar el ebook y permite que la app funcione **100 % sin conexión a internet**.

### ¿Cómo cambiar el código si alguna vez querés usar otro?
Abrí el archivo [app/app.js](file:///Users/mervictorio/Documents/GitHub/Ebook%2030%20dias%20sin%20preguntarte%20que%20cocinar/app/app.js) y buscá la línea que dice:
```javascript
if (val === "COCINA30") {
```
Cambiá `"COCINA30"` por la palabra que quieras (en mayúsculas, por ejemplo `"SASO2026"`), guardás el archivo, ¡y listo!

---

## 🔄 3. Si en el futuro cambiás una receta en el ebook, ¿cómo se actualiza la app?

No tenés que copiar nada a mano:
1. Modificás los datos en la carpeta `datos/` (por ejemplo `recetas.json`).
2. Abrís la terminal y ejecutás este comando:
   ```bash
   python3 scripts/sincronizar_app.py
   ```
3. Ese comando actualiza automáticamente la app, copia las ilustraciones necesarias y recalcula las listas de compras sin que tengas que programar nada.

---

## 📲 4. Cómo la instalan tus clientas en su celular

En la pantalla de bienvenida (y dentro de la app) tienen la ayuda visual:
- **En iPhone (Safari):** tocan el botón de abajo con la flechita hacia arriba (**Compartir**) y eligen **"Agregar a inicio"**.
- **En Android (Chrome):** tocan los tres puntitos arriba a la derecha y eligen **"Instalar aplicación"** o **"Agregar a la pantalla principal"**.

Les queda un ícono redondo con la portada del libro y abre a pantalla completa como cualquier aplicación de la App Store o Google Play.

---

## 🛡️ 5. Respaldo de seguridad y verificación
El sistema cuenta con un verificador automatizado de calidad. Podés correrlo en cualquier momento con:
```bash
node scripts/verificar_app.js
```
Chequea que no haya palabras raras como "None" o "undefined", que las porciones escalen bien, que los tiempos de cocción de lunes a viernes no superen los 25 minutos y que se respeten todas las normas de seguridad alimentaria.

