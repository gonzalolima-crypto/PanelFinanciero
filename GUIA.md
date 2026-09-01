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

### ¿Dónde quedan mis datos?

En un archivo de base de datos local: **`data/panel.db`**.
Esa carpeta `data/` **no se sube al repositorio** (está en `.gitignore`),
así que tus datos personales nunca salen de tu computadora hasta que
publiques la app. Para hacer una copia de seguridad, copiá `data/panel.db`.

---

## 3. Cómo hacer ajustes comunes

Si querés que los haga yo, alcanza con que me digas qué querés. Abajo, dónde
vive cada cosa por si querés tocarlo.

### Cambiar las categorías

Están **en dos lugares que tienen que coincidir**:

- Backend: `app/llm.py`, arriba de todo (`CATS_GASTO`, `CATS_IMPUESTO`, `CATS_INGRESO_EXTRA`).
- Frontend: `app/static/js/app.js`, la constante `CATS` al principio.

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

## 4. Cómo publicarla en internet (Fly.io)

> Hacé esto **solo cuando me confirmes que probaste todo en local y está OK**.
> Ya dejé configurados el `Dockerfile` y el `fly.toml`. Vos corrés unos pocos
> comandos; yo te acompaño.

### 4.1 Crear las cuentas

1. **GitHub**: cuenta gratis en https://github.com/signup (si no tenés).
2. **Fly.io**: cuenta gratis en https://fly.io/app/sign-up
   (pide una tarjeta para validar identidad; el tamaño que vamos a usar no
   tiene costo, pero la tarjeta es obligatoria en el alta).

### 4.2 Subir el código a GitHub

El proyecto ya viene con `git` inicializado. Para subirlo:

```bash
git remote add origin https://github.com/TU-USUARIO/panel-financiero.git
git branch -M main
git push -u origin main
```

(O creá el repo desde la web de GitHub — **privado** — y te muestra estos mismos comandos.)

### 4.3 Instalar la herramienta de Fly

En PowerShell:

```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

Cerrá y volvé a abrir PowerShell. Probá: `fly version`.

### 4.4 Iniciar sesión y crear la app

```bash
fly auth login
```

Después, **parado en la carpeta del proyecto**:

```bash
fly launch --no-deploy
```

- ¿Copiar la configuración existente (`fly.toml`)? → **Yes**.
- Nombre de la app (ej: `panel-financiero-gonza`) → define la dirección
  `https://panel-financiero-gonza.fly.dev`.
- Región: `eze` (Buenos Aires), ya viene puesta.
- ¿Base de datos / Redis? → **No**.

### 4.5 Cargar los secretos (claves)

```bash
fly secrets set APP_PASSWORD="tu-contraseña-fuerte"
fly secrets set SECRET_KEY="pega-acá-40-caracteres-al-azar"
fly secrets set GROQ_API_KEY="tu-clave-gsk_..."
```

### 4.6 Crear el disco donde viven los datos

```bash
fly volumes create panel_data --region eze --size 1
```

### 4.7 Publicar

```bash
fly deploy
fly open
```

Se abre `https://TU-APP.fly.dev` — esa dirección la abrís desde el celular o
desde cualquier lado. Te pide la contraseña (`APP_PASSWORD`).

### 4.8 Actualizar la app más adelante

```bash
git add -A
git commit -m "descripción del cambio"
git push
fly deploy
```

### Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `fly deploy` falla al construir | `fly deploy --verbose` y pasame el error. |
| La voz / comprobantes dan error | Faltó `fly secrets set GROQ_API_KEY=...`. Verificá con `fly secrets list`. |
| Los datos se borraron tras un deploy | El volumen no quedó montado. Verificá `fly volumes list` y la sección `[mounts]` del `fly.toml`. |
| "Groq está limitando las consultas" | Es el tope gratuito por minuto. Esperá un minuto y reintentá. |
| "El modelo configurado no está disponible" | El nombre en `GROQ_TEXT_MODEL` no existe para tu cuenta. Revisá los modelos disponibles en console.groq.com. |

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
