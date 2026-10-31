# Mercado Libre Toolkit (`melikit`)

<p align="center">
  <img src="docs/logo.png" alt="MeliKit Logo" width="180" style="border-radius: 24px;" />
</p>

Herramienta y biblioteca en Python para automatizar publicaciones, gestionar catálogo y autenticarse con la API oficial de Mercado Libre.

---

## 🚀 Inicio Rápido

### 1. Requisitos e Instalación
```bash
python3 -m venv .venv
source .venv/bin/activate

# Instalación base (CLI y SDK)
pip install -e .

# O con soporte para procesamiento de imágenes con IA y desarrollo de tests:
pip install -e ".[ai,dev]"
```

### 2. Configurar Credenciales
Copia el archivo de ejemplo y completa tus datos de la aplicación creada en [Developers Mercado Libre](https://developers.mercadolibre.com.ar/):
```bash
cp .env.example .env
```
Edita `.env`:
```ini
MELI_APP_ID=tu_client_id
MELI_CLIENT_SECRET=tu_client_secret
MELI_REDIRECT_URI=http://localhost:8080/callback
MELI_SITE_ID=MLA
```

---

## 🔑 Autenticación (OAuth 2.0)

Inicia el flujo interactivo de autorización local:
```bash
melikit auth login
```
El script abrirá un servidor local en el puerto configurado y te mostrará el enlace para autorizar en el navegador. Al completar el login, guardará de forma segura los tokens en `.meli_tokens.json` con permisos restrictivos (`0600`) y se encargará de refrescarlos automáticamente cada vez que expiren.

Para revisar el estado de tu sesión:
```bash
melikit auth status
```

---

## 📦 Gestión de Publicaciones

### 1. Predecir Categoría
```bash
melikit category predict "Auriculares Bluetooth Sony WH-1000XM4"
```

### 2. Consultar Atributos Requeridos por Categoría
```bash
melikit category attributes MLA3697
```
*(Usa `--all` para listar todos los atributos opcionales y recomendados).*

### 3. Crear una Publicación
Prepara tu archivo JSON basándote en [`templates/item_template.json`](templates/item_template.json) y ejecuta:
```bash
melikit item create --file mi_producto.json
```

### 4. Consultar y Modificar Publicaciones
```bash
# Listar tus publicaciones activas o pausadas
melikit item list --status active
melikit item list --status paused

# Ver detalles de una publicación
melikit item get --item-id MLA123456789

# Pausar o reactivar
melikit item status --item-id MLA123456789 --status paused
melikit item status --item-id MLA123456789 --status active

# Cambiar precio o stock
melikit item price --item-id MLA123456789 --price 45000
melikit item stock --item-id MLA123456789 --quantity 10

# Consultar o actualizar la descripción en texto plano
melikit item description --item-id MLA123456789
melikit item description --item-id MLA123456789 --text "Nueva descripción del producto..."
melikit item description --item-id MLA123456789 --file descripcion.txt
```

---

## 🖼️ Imágenes y Preparación con IA

### Subida directa de imágenes a Mercado Libre
Sube imágenes locales para obtener su identificador oficial en MeLi:
```bash
melikit picture upload --file foto_producto.jpg
```

### Remoción de fondo automática (Fondo Blanco Puro 1200x1200)
Procesa y unifica fotos con IA al formato requerido por Mercado Libre:
```bash
melikit image clean --input foto_original.jpg --output processed_images/ --prefix mi_producto
```

---

## 🧪 Pruebas Unitarias
El proyecto cuenta con una suite completa de pruebas con mocks (`pytest` y `responses`):
```bash
pytest -v
```

---

## 📚 Documentación
- Consulta la [Guía Técnica de la API de Mercado Libre](docs/MELI_API_GUIDE.md) para detalles sobre la estructura de requests, esquemas de variación y políticas de publicación.
