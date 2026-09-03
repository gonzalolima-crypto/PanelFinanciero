# Panel Financiero — Guía de uso

Guía paso a paso, sin dar por sentado nada técnico. Cuatro secciones:

1. [Cómo generar tu clave de Groq](#1-cómo-generar-tu-clave-de-groq) (gratis)
2. [Cómo levantar la app en tu computadora](#2-cómo-levantar-la-app-en-tu-computadora)
3. [Cómo hacer ajustes comunes](#3-cómo-hacer-ajustes-comunes)
4. [Cómo publicarla en internet (Fly.io)](#4-cómo-publicarla-en-internet-flyio) — recién cuando me confirmes que está todo OK

> **Nota:** tu clave de Groq ya quedó cargada en el archivo `.env`, así que
> para probar en tu computadora **podés saltear la sección 1**. Esos pasos
> están por si algún día necesitás generar otra (o para el despliegue).

---

## 1. Cómo generar tu clave de Groq

La "clave" (API Key) es como una contraseña que le permite a la app usar los
modelos de inteligencia artificial de **Groq** para:

- entender lo que dictás por voz,
- transcribir audios,
- leer los PDF de resúmenes de tarjeta y tickets.

Es **gratis** para uso personal (tiene un límite de consultas por minuto, ver
más abajo).

1. Entrá a **https://console.groq.com** desde tu navegador.
2. Registrate / iniciá sesión (podés usar tu cuenta de Google).
3. En el menú de la izquierda, entrá a **"API Keys"**.
4. Hacé clic en **"Create API Key"**.
5. Ponele un nombre cualquiera (por ejemplo `panel-financiero`) y confirmá.
6. Aparece la clave: un texto largo que empieza con **`gsk_...`**.
   **Copiala en ese momento** (después no se vuelve a mostrar completa).
7. Guardala en un lugar seguro y pegala en el archivo `.env`
   (línea `GROQ_API_KEY=`, ver sección 2).

> **Importante:** esa clave es personal. No la compartas ni la subas a internet.
> Si creés que se filtró, entrá a la misma página, borrá la clave vieja
> ("Delete") y generá una nueva.

### Límite de la cuota gratuita

El plan gratuito de Groq limita cuántas consultas podés hacer **por minuto**.
En uso normal (cargar un movimiento por voz, subir un resumen cada tanto) no lo
vas a notar. Si subís varios PDF seguidos podés ver el mensaje *"Groq está
limitando las consultas"*: esperá un minuto y reintentá.

---

## 2. Cómo levantar la app en tu computadora

### Requisito único: tener Python instalado

Ya lo tenés (Python 3.12). Si algún día lo necesitás en otra máquina:
descargalo de **https://www.python.org/downloads/** y, en el instalador,
**tildá la casilla "Add Python to PATH"** antes de continuar.

### Primera vez

1. Abrí la carpeta **`Proyecto Panel Financiero`** en el Explorador de Windows.
2. Hacé doble clic en **`iniciar.bat`**.
   - La primera vez tarda unos minutos: está descargando lo que necesita.
3. Abrí el archivo **`.env`** con el **Bloc de notas**
   (clic derecho → Abrir con → Bloc de notas). Ya viene con tu clave de Groq.
   Completá una línea más si querés proteger el panel:

   ```
   APP_PASSWORD=elegí-una-contraseña
   ```

   Si la dejás vacía, el panel se abre sin pedir nada (está bien para probar en
   tu casa; ponele contraseña antes de publicarlo).

   Guardá el archivo (Archivo → Guardar) y cerralo.
4. Volvé a hacer doble clic en **`iniciar.bat`**.

### Uso normal (de acá en adelante)

- Doble clic en **`iniciar.bat`**.
- **Esperá hasta 1 minuto**: el navegador se abre **solo** en
  **http://127.0.0.1:8000** cuando la app está lista.
  (Si no se abre, escribí `http://127.0.0.1:8000` a mano en el navegador.)
- **No cierres la ventana negra** mientras usás el panel: esa ventana *es* la app.
- Para **apagar** la app: cerrá la ventana negra.

### Probar desde el celular (misma red WiFi)

Con la app corriendo en la compu:

1. En la ventana negra, buscá la línea `Desde el celular ... http://<IP-de-esta-PC>:8000`.
2. Averiguá la IP de la compu: abrí PowerShell y escribí `ipconfig`; mirá
   *"Dirección IPv4"* (algo como `192.168.0.15`).
3. En el celular (conectado a la misma WiFi), abrí el navegador y entrá a
   `http://192.168.0.15:8000` (con la IP que te haya dado).

### ¿Qué es cada cosa que ves?

| Elemento | Qué hace |
|---|---|
| **Resumen del mes** (el "recibo") | Totales de ingresos, gastos, impuestos y ahorro del mes elegido. |
| **Cargar por voz** (🎤) | Tocás el micrófono, decís el movimiento (ej: *"pagué 15 mil de impuesto municipal"*) y la IA completa el formulario. Revisás y tocás "Agregar". |
| **o subir un audio grabado** | Para el celular o navegadores sin dictado en vivo: subís un audio (por ejemplo una nota de voz) y se transcribe en el servidor con Whisper. |
| **Adjuntar comprobante** (📎) | Subís un **PDF** de resumen de tarjeta (Visa/Mastercard) o de un ticket. La IA extrae los consumos, los agrupás por categoría, destildás lo que no quieras y confirmás. |
| **Cargar movimiento** | Carga manual de siempre. |
| **Gráficos** | Se actualizan solos con cada movimiento. |
| **Movimientos** | La lista del mes, con botón "borrar" en cada fila. |

### Sobre los comprobantes: por ahora, PDF

Con la configuración actual de Groq, la lectura de comprobantes funciona con
**archivos PDF** (que es como vienen los resúmenes del banco). Anda muy bien con
los resúmenes de Visa y Mastercard.

Si tenés una **foto** de un ticket (JPG/PNG), convertila a PDF antes de subirla:
en el celular, al ver la foto, usá **Compartir → Imprimir → Guardar como PDF**;
en Windows, abrí la imagen y usá **Imprimir → "Microsoft Print to PDF"**.
(Si más adelante querés subir fotos directamente, se puede activar: pedímelo.)

### En qué mes se cargan los consumos de un resumen de tarjeta

Cuando subís un **resumen de tarjeta**, todos los consumos se imputan al
**mes en que lo pagás**, es decir el de la **fecha de vencimiento** del resumen
(no el mes en que hiciste cada compra). Es donde realmente te impacta el gasto.

- En la pantalla de revisión se muestra la fecha de vencimiento detectada y
  "→ se carga en \<mes\>". Si el resumen tiene un formato que la app no reconoce,
  te pide que elijas vos esa fecha antes de cargar.
- En la tabla **Movimientos** vas a ver la **fecha real de cada compra**, con una
  aclaración chica "se paga \<mes\>" cuando cae en otro mes.
- Esto **solo** aplica a los resúmenes en PDF. Los "gastos con tarjeta" que
  cargás a mano o por voz usan la fecha que vos ponés.

### Pesos y dólares (dos monedas)

El panel maneja las dos monedas por separado:

- El **Resumen del mes** tiene un bloque **En pesos ($)** y otro **En dólares (US$)**,
  cada uno con sus ingresos, gastos, tarjeta y ahorro.
- Cada movimiento tiene su moneda. En la carga manual elegís **$ ARS** o **US$ USD**.
- Al subir un resumen, los consumos en dólares se cargan con su **valor literal en
  dólares** (ej. Spotify US$ 2,99), no convertidos a pesos.
- Los **gráficos** van siempre en pesos (los consumos en dólares se ven en el
  bloque US$ del resumen).

### Reconciliación con el resumen de la tarjeta

Al subir un resumen, antes de confirmar ves un recuadro **"Reconciliación con tu
resumen"** que muestra:

- Consumos en pesos y en dólares, y las **devoluciones/reintegros** (que restan).
- **"Se carga al panel"**: el neto que van a sumar tus gastos de tarjeta.
- **Cargos del resumen** (IIBB, IVA RG, Percepción RG 5617 / impuesto dólar
  tarjeta, etc.): se listan para que los veas, pero **no se cargan** como gasto.
- El **SALDO ACTUAL** del resumen (lo que pagás en el banco).
- Un tilde verde si los consumos cargados coinciden con el total de consumos del
  resumen.

Así podés cuadrar: `consumos que carga el panel + cargos del resumen = SALDO ACTUAL`.

### ¿Dónde quedan mis datos?

En un archivo de base de datos local: **`data/panel.db`**.
Esa carpeta `data/` **no se sube al repositorio** (está en `.gitignore`),
así que tus datos personales nunca salen de tu computadora hasta que
publiques la app. Para hacer una copia de seguridad, copiá `data/panel.db`.

---

## 3. Cómo hacer ajustes comunes

Si querés que los haga yo, alcanza con que me digas qué querés. Abajo, dónde
vive cada cosa por si querés tocarlo.

### Categorías de gasto

Las categorías para **gasto diario** y **gasto con tarjeta** son (en este orden):
Compra de Super, Colegio, Gastos Delfi, Gastos Lu, Delivery, Gastos Autos,
Gastos Viajes, Regalos, Ropa, Gastos Padres, Alimentos, Transporte, Salud, Ocio,
Servicios, Hogar, Suscripciones, Otros.

- Al **importar un resumen**, la app trata de adivinar la categoría por el nombre
  del comercio (COTO → Compra de Super, YPF/peajes → Gastos Autos, Netflix →
  Suscripciones, etc.). Lo que no reconoce cae en "Otros".
- En la pantalla de revisión, **cada consumo tiene un desplegable** para cambiarle
  la categoría antes de cargar (tocá el monto del grupo para expandirlo).
- Para **agregar/quitar/renombrar** categorías: `app/static/js/app.js` (constante
  `CATS_GASTO`, arriba) y `app/llm.py` (constante `CATS_GASTO` y, si querés que
  la app las adivine sola, el mapa `_CAT_KEYWORDS`). Pedímelo y lo hago.

### Categorías de "Impuesto pagado"

Además de impuestos, este tipo se usa para servicios y facturas recurrentes:
Luz, Gas, VTV, ARBA, Municipal, Aysa, Expensas, Luz Edificio, Carga Celular,
Ganancias, IIBB, Monotributo, ABL/Municipal, Patente, Otros.
Al dictarlo por voz ("pagué la luz", "cargué el celular") la app lo reconoce y
elige la categoría sola. Se editan en `CATS.impuesto` (app.js) y `CATS_IMPUESTO`
(llm.py).

### Cambiar el objetivo de ahorro por defecto (hoy 20%)

`app/db.py` → `DEFAULT_CONFIG = {"goalPct": "20"}`.
(Si ya usaste la app, cambialo desde el propio panel, en el campo `%`.)

### Cambiar el modelo de IA que se usa

`.env`:

- `GROQ_TEXT_MODEL` — interpreta la voz y los PDF (hoy `openai/gpt-oss-120b`).
- `GROQ_TRANSCRIBE_MODEL` — transcribe audios (hoy `whisper-large-v3-turbo`).
- `GROQ_VISION_MODEL` — para leer fotos JPG/PNG. Vacío por ahora (tu cuenta de
  Groq no tiene un modelo con visión). Si algún día lo activás, poné acá el
  nombre y las fotos empiezan a funcionar sin tocar nada más.

Para ver qué modelos tenés disponibles: `https://console.groq.com/docs/models`.

### Agregar un tipo de movimiento nuevo, cambiar colores, etc.

Pedímelo con el detalle y lo hago (toca varios archivos coordinados).
Los colores están en `app/static/css/styles.css`, bloque `:root`.

### Después de cualquier cambio

Cerrá la ventana negra y volvé a abrir `iniciar.bat`.

---

## 4. Cómo publicarla en internet (Render + Neon, gratis)

Todo por la web, sin instalar nada. Son dos servicios, ambos con plan gratuito
y **sin tarjeta de crédito**:

| Servicio | Para qué | Por qué |
|---|---|---|
| **Neon** | Guardar los datos (base Postgres) | El disco de Render se borra en cada reinicio; en Neon los datos quedan. |
| **Render** | Correr la app | Te da la dirección web pública. |

El código ya está preparado: en tu computadora sigue usando el archivo local
`data/panel.db`, y en Render usa Neon automáticamente (por la variable
`DATABASE_URL`).

---

### 4.1 Crear la base de datos en Neon (5 min)

1. Entrá a **https://neon.tech** y hacé clic en **"Sign up"**.
2. Registrate con **GitHub** o **Google** (no pide tarjeta).
3. Te crea un proyecto solo. Si te pregunta:
   - **Project name**: `panel-financiero`
   - **Postgres version**: la que venga por defecto
   - **Region**: elegí una de **US East** (es la más cercana a Render)
4. Al terminar te muestra un recuadro **"Connection string"** con un texto largo
   que empieza con `postgresql://`. Hacé clic en **Copy**.
   - Si no lo ves: menú izquierdo → **Dashboard** → botón **Connect**.
5. **Guardalo** en una nota: lo vas a pegar en el paso 4.3.

> Ese texto es la llave de tu base de datos. No lo compartas.

---

### 4.2 Crear la cuenta de Render (2 min)

1. Entrá a **https://render.com** → **"Get Started"**.
2. Registrate **con GitHub** (así Render puede leer tu repositorio).
3. Cuando te pida permisos sobre GitHub, autorizá el repositorio
   **`PanelFinanciero`** (o "All repositories", como prefieras).

---

### 4.3 Crear el servicio (5 min)

1. En el panel de Render, arriba a la derecha: **New +** → **Blueprint**.
2. En la lista de repositorios, elegí **`gonzalolima-crypto/PanelFinanciero`**
   → **Connect**.
3. Render lee solo el archivo `render.yaml` del proyecto y te muestra el servicio
   **panel-financiero**. Te va a pedir completar **3 valores**:

   | Campo | Qué poner |
   |---|---|
   | `DATABASE_URL` | El texto largo que copiaste de Neon (paso 4.1) |
   | `GROQ_API_KEY` | Tu clave de Groq (la que empieza con `gsk_`) |
   | `APP_PASSWORD` | La contraseña que vas a usar para entrar al panel |

   (`SECRET_KEY` la genera Render sola, no la toques.)
4. Ponele un nombre al Blueprint (por ejemplo `panel-financiero`) y hacé clic en
   **Apply** / **Create**.

---

### 4.4 Esperar y entrar

- El primer deploy tarda **5 a 10 minutos** (instala Python y las librerías).
  Vas viendo el progreso en la pestaña **Logs**.
- Cuando termine, arriba te muestra la dirección:
  **`https://panel-financiero-XXXX.onrender.com`**
- Abrila. Te pide la contraseña (`APP_PASSWORD`) y ya estás adentro.
- Esa dirección la podés abrir **desde el celular o desde cualquier lado**.

---

### 4.5 Algo importante del plan gratuito

La app **se "duerme" después de 15 minutos sin usarla**. La primera vez que
entrás después de un rato tarda **entre 30 y 60 segundos** en despertar (parece
colgada, pero está arrancando). Después anda normal.

Si eso te molesta, el plan pago de Render (US$7/mes) la mantiene siempre
despierta. No hace falta cambiar nada del código.

---

### 4.6 Llevar los datos que tengas en tu computadora (opcional)

Si ya cargaste movimientos en local y los querés en la app publicada:

1. Abrí el archivo `.env` con el Bloc de notas y pegá la cadena de Neon en la
   línea `DATABASE_URL=` (la misma del paso 4.1). Guardá.
2. En PowerShell, parado en la carpeta del proyecto:

   ```powershell
   .venv\Scripts\python.exe migrar_a_postgres.py
   ```

3. **Volvé a dejar `DATABASE_URL=` vacía** en el `.env` para que en tu compu se
   siga usando la base local.

---

### 4.7 Actualizar la app más adelante

Cada vez que se cambie algo del código:

```bash
git add -A
git commit -m "descripción del cambio"
git push
```

Render detecta el push y **redespliega solo**. No hay que hacer nada más.

---

### Problemas frecuentes

| Síntoma | Solución |
|---|---|
| Tarda 40 seg en abrir la primera vez | Normal: el plan gratuito duerme la app (ver 4.5). |
| "Application failed to respond" | Todavía está arrancando. Esperá 1 minuto y recargá. Si sigue, mirá **Logs** en Render y pasame el error. |
| El deploy falla en el build | Pestaña **Logs** → copiá el error y pasámelo. |
| Entra pero se pierden los movimientos | `DATABASE_URL` quedó vacía o mal. En Render: **Environment** → verificá que esté la cadena de Neon completa. |
| Error de conexión a la base | Si la cadena de Neon termina en `&channel_binding=require`, probá borrando esa parte. |
| La voz / comprobantes dan error | Falta o está mal `GROQ_API_KEY` en **Environment**. |
| "Groq está limitando las consultas" | Es el tope gratuito por minuto. Esperá un minuto y reintentá. |
| Olvidaste la contraseña del panel | Render → **Environment** → cambiá `APP_PASSWORD` → **Save** (redespliega solo). |

---

### Alternativa: Fly.io

El proyecto también trae `Dockerfile` y `fly.toml` listos para
[Fly.io](https://fly.io) (~US$2/mes, con disco propio y sin dormirse, usando
SQLite). Si algún día querés migrar, pedímelo y te paso los pasos.

---

## Estructura del proyecto (referencia rápida)

```
Proyecto Panel Financiero/
├── iniciar.bat            ← doble clic para usar la app en tu PC
├── run.py                 ← arranque en modo desarrollo
├── wsgi.py                ← arranque en producción (gunicorn)
├── requirements.txt       ← librerías de Python
├── .env                   ← TUS claves (no se sube al repo)
├── .env.example           ← plantilla del .env
├── Dockerfile / fly.toml  ← configuración de despliegue
├── app/
│   ├── __init__.py        ← arma la aplicación Flask
│   ├── config.py          ← lee la configuración del entorno
│   ├── db.py              ← base de datos SQLite (esquema)
│   ├── models.py          ← alta/baja/consulta de movimientos
│   ├── auth.py            ← contraseña única / sesión
│   ├── routes.py          ← la página y la API /api/*
│   ├── llm.py             ← integración con Groq (voz, audio, comprobantes)
│   ├── templates/         ← index.html y login.html
│   └── static/            ← estilos, JavaScript y Chart.js
├── tests/                 ← pruebas automáticas (pytest)
└── data/                  ← base de datos y comprobantes (local, no se sube)
```

Ver `ESPECIFICACION.md` para el detalle funcional y técnico.
