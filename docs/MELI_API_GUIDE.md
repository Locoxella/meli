# Guía Completa de Integración con la API de Mercado Libre

Esta guía detalla el funcionamiento de la API oficial de Mercado Libre (MELI), el flujo de autenticación OAuth 2.0 y cómo crear y administrar publicaciones de productos.

---

## 1. Requisitos Previos y Creación de la Aplicación

Para interactuar con la API en nombre de un vendedor o cuenta de Mercado Libre:

1. Ingresa a [Mercado Libre Developers](https://developers.mercadolibre.com.ar/).
2. Inicia sesión con tu cuenta de Mercado Libre.
3. Dirígete a **Mis Aplicaciones** (`DevCenter`) y haz clic en **Crear nueva aplicación**.
4. Completa los datos requeridos:
   - **Nombre de la App**: Por ejemplo `MiGestorMeli`.
   - **URI de redirección (Redirect URI)**: Define una URL local o pública donde recibirás el código de autorización, por ejemplo:
     ```
     http://localhost:8080/callback
     ```
   - **Permisos (Scopes)**: Asegúrate de habilitar lectura (`read`), escritura (`write`) y acceso offline (`offline_access`).
5. Guarda tu aplicación y copia:
   - **`APP ID`** (o `client_id`)
   - **`CLIENT SECRET`**

---

## 2. Flujo de Autenticación OAuth 2.0

Mercado Libre utiliza el flujo estándar de Authorization Code:

```
+----------------+          +-----------------------+          +----------------------+
|  Tu Aplicación |  ----->  |  Navegador (Usuario)  |  ----->  |  Mercado Libre Auth  |
+----------------+          +-----------------------+          +----------------------+
        |                                                                 |
        | 1. Inicia servidor local en puerto 8080                         |
        | 2. Redirige al login de MeLi                                    |
        |                                                                 |
        | <------------------ 3. Redirección con ?code=TG-... ------------|
        |                                                                 |
        | 4. POST /oauth/token (code + client_id + client_secret) ------->|
        | <------------------ 5. Devuelve access_token + refresh_token --|
```

### Duración de Tokens
- **`access_token`**: Válido por 6 horas (21600 segundos).
- **`refresh_token`**: Permite solicitar un nuevo `access_token` sin intervención del usuario.
- `melikit` gestiona este refresco automáticamente cuando restan menos de 5 minutos de vigencia.

---

## 3. Ciclo de Vida de las Publicaciones (`/items`)

### A. Descubrimiento de Categoría
Antes de publicar, consulta el recurso de Domain Discovery para clasificar tu producto:
```http
GET https://api.mercadolibre.com/sites/MLA/domain_discovery/search?q=Nombre+del+producto
```

### B. Atributos de la Categoría
Cada categoría tiene atributos obligatorios (por ejemplo `BRAND`, `MODEL` o especificaciones técnicas) que deben enviarse dentro del arreglo `attributes`:
```http
GET https://api.mercadolibre.com/categories/{category_id}/attributes
```

### C. Creación del Ítem
Se envía una petición `POST` al endpoint `/items`:
```http
POST https://api.mercadolibre.com/items
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Payload representativo:**
```json
{
  "title": "Auriculares Bluetooth Sony WH-1000XM4 Negro",
  "category_id": "MLA3697",
  "price": 350000,
  "currency_id": "ARS",
  "available_quantity": 5,
  "buying_mode": "buy_it_now",
  "condition": "new",
  "listing_type_id": "gold_special",
  "pictures": [
    {
      "source": "https://http2.mlstatic.com/..."
    }
  ],
  "attributes": [
    {
      "id": "BRAND",
      "value_name": "Sony"
    },
    {
      "id": "MODEL",
      "value_name": "WH-1000XM4"
    }
  ]
}
```

### D. Modificación y Gestión
- **Cambiar Estado** (`active`, `paused`, `closed`):
  ```http
  PUT https://api.mercadolibre.com/items/{item_id}
  {"status": "paused"}
  ```
- **Modificar Stock o Precio**:
  ```http
  PUT https://api.mercadolibre.com/items/{item_id}
  {"price": 380000, "available_quantity": 3}
  ```

---

## 4. Prácticas Recomendadas y Reglas de la API

1. **Condición del Ítem**: Aunque `condition: "new"` se mantiene por retrocompatibilidad, la API ahora procesa la condición mediante el atributo `ITEM_CONDITION` dentro de `attributes`.
2. **Dimensiones y Pesos de Envío**: Si se configuran paquetes para Mercado Envíos, los campos `SELLER_PACKAGE_HEIGHT`, `SELLER_PACKAGE_WIDTH`, etc. deben enviarse estrictamente como strings numéricos enteros (ejemplo: `"15"` en lugar de `"15cm"`).
3. **Imágenes**: Deben ser URLs públicas accesibles por los servidores de Mercado Libre con resolución mínima recomendada de 500x500 px (óptimo 1200x1200 px con fondo blanco puro).
