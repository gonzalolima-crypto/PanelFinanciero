# Panel Financiero — Guía de uso

Esta guía está escrita paso a paso, sin dar por sentado nada técnico.
Tenés cuatro secciones:

1. [Cómo generar tu clave de Gemini](#1-cómo-generar-tu-clave-de-gemini) (gratis)
2. [Cómo levantar la app en tu computadora](#2-cómo-levantar-la-app-en-tu-computadora)
3. [Cómo hacer ajustes comunes](#3-cómo-hacer-ajustes-comunes)
4. [Cómo publicarla en internet (Fly.io)](#4-cómo-publicarla-en-internet-flyio) — recién cuando me confirmes que está todo OK

---

## 1. Cómo generar tu clave de Gemini

La "clave" (API Key) es como una contraseña que le permite a la app usar la
inteligencia artificial de Google para entender lo que dictás por voz y para
leer los comprobantes. Es **gratis** para uso personal.

1. Entrá a **https://aistudio.google.com/apikey** desde tu navegador.
2. Iniciá sesión con tu cuenta de Google (la misma del correo, por ejemplo).
3. Si es la primera vez, te va a pedir aceptar los términos. Aceptá.
4. Vas a ver un botón que dice **"Create API key" / "Crear clave de API"**. Hacé clic.
5. Si te pregunta en qué proyecto crearla, elegí el que te ofrece por defecto
   (algo como *"Gemini API"* o *"My first project"*) y confirmá.
6. En unos segundos aparece un cuadro con la clave: es un texto largo que
   empieza con **`AIza...`**. Hacé clic en **"Copiar"**.
7. Guardala en un lugar seguro (por ejemplo, una nota privada). La vas a pegar
   en el archivo `.env` en el paso 2.

> **Importante:** esa clave es personal. No la compartas ni la subas a internet.
> La app la guarda solo en tu computadora (archivo `.env`, que nunca se sube al
> repositorio).

Si alguna vez creés que se filtró, volvé a esa misma página, borrá la clave
vieja ("Delete") y generá una nueva.

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
   - Se va a crear un archivo llamado **`.env`**. Es normal.
3. Cuando termine, abrí el archivo **`.env`** con el **Bloc de notas**
   (clic derecho → Abrir con → Bloc de notas) y completá dos líneas:

   ```
   APP_PASSWORD=elegí-una-contraseña
   GEMINI_API_KEY=pegá-acá-la-clave-que-copiaste-en-el-paso-1
   ```

   - `APP_PASSWORD`: la contraseña para entrar al panel. Si la dejás vacía,
     el panel se abre sin pedir nada (solo para probar en tu casa).
   - `GEMINI_API_KEY`: la clave `AIza...` del paso 1.

   Guardá el archivo (Archivo → Guardar) y cerralo.
4. Volvé a hacer doble clic en **`iniciar.bat`**.

### Uso normal (de acá en adelante)

- Doble clic en **`iniciar.bat`**.
- Se abre solo el navegador en **http://localhost:8000**.
  (Si no se abre, escribí esa dirección a mano en el navegador.)
- Para **apagar** la app: cerrá la ventana negra que quedó abierta.

### ¿Qué es cada cosa que ves?

| Elemento | Qué hace |
|---|---|
| **Resumen del mes** (el "recibo") | Totales de ingresos, gastos, impuestos y ahorro del mes elegido. |
| **Cargar por voz** (🎤) | Tocás el micrófono, decís el movimiento y la IA completa el formulario. Revisás y tocás "Agregar". |
| **o subir un audio grabado** | Para celulares o navegadores sin dictado en vivo: subís un audio (por ejemplo una nota de voz) y se transcribe en el servidor. |
| **Adjuntar comprobante** (📎) | Subís una **foto de un ticket** o un **PDF de resumen de tarjeta**. La IA extrae los consumos, los agrupás por categoría, destildás lo que no quieras y confirmás. |
| **Cargar movimiento** | Carga manual de siempre. |
| **Gráficos** | Se actualizan solos con cada movimiento. |
| **Movimientos** | La lista del mes, con botón "borrar" en cada fila. |

### ¿Dónde quedan mis datos?

En un archivo de base de datos local: **`data/panel.db`**.
Los comprobantes que subís quedan en **`data/uploads/`**.
Esa carpeta `data/` **no se sube al repositorio** (está en `.gitignore`),
así que tus datos personales nunca salen de tu computadora hasta que
publiques la app.

Para hacer una copia de seguridad, copiá el archivo `data/panel.db` a otro lado.

---

## 3. Cómo hacer ajustes comunes

Todo esto son cambios chicos. Si querés que los haga yo, alcanzá con que me
digas qué querés; abajo te dejo dónde vive cada cosa por si querés tocarlo.

### Cambiar las categorías (por tipo de movimiento)

Están **en dos lugares que tienen que coincidir**:

- Backend: `app/llm.py`, arriba de todo (`CATS_GASTO`, `CATS_IMPUESTO`, `CATS_INGRESO_EXTRA`).
- Frontend: `app/static/js/app.js`, la constante `CATS` al principio del archivo.

### Cambiar el objetivo de ahorro por defecto (hoy 20%)

`app/db.py` → `DEFAULT_CONFIG = {"goalPct": "20"}`.
(Si ya usaste la app, cambialo desde el propio panel, en el campo `%`.)

### Agregar un tipo de movimiento nuevo (además de los 5 actuales)

Hay que tocar varios archivos coordinados (`app/models.py` `VALID_TYPES`,
`app/llm.py` el prompt, `app/static/js/app.js` `CATS` y `TYPE_LABEL`, y los
estilos de la etiqueta en `app/static/css/styles.css`). Pedímelo y lo hago.

### Cambiar los colores / el aspecto

`app/static/css/styles.css`, bloque `:root` de arriba (las variables `--bg`,
`--green`, etc.).

### Cambiar el modelo de IA

`.env` → `GEMINI_MODEL`. Por defecto `gemini-2.0-flash` (rápido y gratis).

### Después de cualquier cambio

Cerrá la ventana negra y volvé a abrir `iniciar.bat`.

---

## 4. Cómo publicarla en internet (Fly.io)

> Hacé esto **solo cuando me confirmes que probaste todo en local y está OK**.
> Ya dejé configurados el `Dockerfile` y el `fly.toml`. Vos corrés unos pocos
> comandos desde tu cuenta; yo te acompaño.

### 4.1 Crear las cuentas

1. **GitHub**: creá una cuenta gratis en https://github.com/signup si no tenés.
2. **Fly.io**: creá una cuenta gratis en https://fly.io/app/sign-up
   (te va a pedir una tarjeta para validar identidad; el plan que vamos a usar
   no tiene costo para este tamaño de app, pero la tarjeta es obligatoria en el
   alta).

### 4.2 Subir el código a GitHub

Yo te dejo el proyecto listo con `git` inicializado. Para subirlo:

```bash
# (una sola vez) crear el repositorio remoto e ir subiendo
git remote add origin https://github.com/TU-USUARIO/panel-financiero.git
git branch -M main
git push -u origin main
```

Si preferís, se puede crear el repo desde la web de GitHub ("New repository",
**privado**) y GitHub te muestra esos mismos comandos.

### 4.3 Instalar la herramienta de Fly

En PowerShell:

```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

Cerrá y volvé a abrir PowerShell. Probá que quedó instalada:

```bash
fly version
```

### 4.4 Iniciar sesión y crear la app

```bash
fly auth login
```

(se abre el navegador para confirmar)

Después, **parado en la carpeta del proyecto**:

```bash
fly launch --no-deploy
```

- Cuando pregunte si querés copiar la configuración existente (`fly.toml`), decí **Yes**.
- Elegí un nombre para la app (por ejemplo `panel-financiero-gonza`). Ese nombre
  define la dirección final: `https://panel-financiero-gonza.fly.dev`.
- Región: `eze` (Buenos Aires), ya viene puesta.
- Si pregunta por base de datos / Redis: **No**.

### 4.5 Cargar los secretos (claves)

```bash
fly secrets set APP_PASSWORD="tu-contraseña-fuerte"
fly secrets set SECRET_KEY="pega-acá-40-caracteres-al-azar"
fly secrets set GEMINI_API_KEY="tu-clave-AIza..."
```

### 4.6 Crear el disco donde viven los datos

```bash
fly volumes create panel_data --region eze --size 1
```

(1 GB es más que suficiente.)

### 4.7 Publicar

```bash
fly deploy
```

Cuando termine:

```bash
fly open
```

Se abre `https://TU-APP.fly.dev` — esa dirección la podés abrir desde el
celular o desde cualquier lado. Te va a pedir la contraseña (`APP_PASSWORD`).

### 4.8 Actualizar la app más adelante

Cada vez que cambies algo:

```bash
git add -A
git commit -m "descripción del cambio"
git push
fly deploy
```

### Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `fly deploy` falla al construir | Corré `fly deploy --verbose` y pasame el error. |
| La app abre pero la voz/comprobantes dan error | Faltó `fly secrets set GEMINI_API_KEY=...`. Verificá con `fly secrets list`. |
| Los datos se borraron tras un deploy | El volumen no quedó montado. Verificá `fly volumes list` y que el `fly.toml` tenga la sección `[mounts]`. |
| "Gemini está limitando las consultas" | Es el tope gratuito. Esperá unos minutos y reintentá. |

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
│   ├── llm.py             ← integración con Gemini (voz y comprobantes)
│   ├── templates/         ← index.html y login.html
│   └── static/            ← estilos, JavaScript y Chart.js
├── tests/                 ← pruebas automáticas (pytest)
└── data/                  ← base de datos y comprobantes (local, no se sube)
```

Ver `ESPECIFICACION.md` para el detalle funcional y técnico.
