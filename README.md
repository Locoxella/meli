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
pip install -r requirements.txt
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
python -m melikit auth login
```
El script abrirá un servidor local en el puerto configurado y te mostrará el enlace para autorizar en el navegador. Al completar el login, guardará de forma segura los tokens en `.meli_tokens.json` y se encargará de refrescarlos automáticamente cada vez que expiren.

Para revisar el estado de tu sesión:
```bash
python -m melikit auth status
```

---

## 📦 Gestión de Publicaciones

### 1. Predecir Categoría
```bash
python -m melikit category predict "Auriculares Bluetooth Sony WH-1000XM4"
```

### 2. Consultar Atributos Requeridos por Categoría
```bash
python -m melikit category attributes MLA3697
```
*(Usa `--all` para listar todos los atributos opcionales y recomendados).*

### 3. Crear una Publicación
Prepara tu archivo JSON basándote en [`templates/item_template.json`](templates/item_template.json) y ejecuta:
```bash
python -m melikit item create --file mi_producto.json
```

### 4. Consultar y Modificar Publicaciones
```bash
# Ver detalles de una publicación
python -m melikit item get --item-id MLA123456789

# Pausar o reactivar
python -m melikit item status --item-id MLA123456789 --status paused
python -m melikit item status --item-id MLA123456789 --status active

# Cambiar precio o stock
python -m melikit item price --item-id MLA123456789 --price 45000
python -m melikit item stock --item-id MLA123456789 --quantity 10
```

---

## 📚 Documentación
- Consulta la [Guía Técnica de la API de Mercado Libre](docs/MELI_API_GUIDE.md) para detalles sobre la estructura de requests, esquemas de variación y políticas de publicación.
