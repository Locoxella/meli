import argparse
import json
import sys
from pathlib import Path
from .auth import MeliAuth
from .client import MeliClient
from .exceptions import MeliError, MeliAPIError, MeliAuthError


def handle_auth(args):
    auth = MeliAuth()
    if args.action == "login":
        auth.start_local_login_flow(port=args.port)
    elif args.action == "url":
        print("\nURL de autorizacion para abrir en tu navegador:")
        print(auth.get_auth_url())
        print()
    elif args.action == "exchange":
        raw_code = args.code
        # Si el usuario pego la URL completa con ?code=TG-... o solo el codigo
        code = auth.extract_code(raw_code)
        tokens = auth.exchange_code_for_token(code)
        print("\n¡Tokens obtenidos y guardados exitosamente!")
        print(f"User ID: {tokens.get('user_id')}")
        print(f"Validez: {tokens.get('expires_in')} segundos (6 horas)\n")
    elif args.action == "status":
        tokens = auth.load_tokens()
        if not tokens:
            print("No hay tokens guardados. Ejecuta 'melikit auth url' o 'login'.")
            return
        print(f"Token presente. Expira en timestamp: {tokens.get('expires_at')}")
        try:
            client = MeliClient(auth=auth)
            me = client.get_me()
            print(f"Usuario: {me.get('nickname')} (ID: {me.get('id')})")
            print(f"Email: {me.get('email')}")
            print(f"Pais: {me.get('country_id')}")
        except Exception as e:
            print(f"Aviso: No se pudo consultar /users/me: {e}")


def handle_category(args):
    client = MeliClient(site_id=args.site)
    if args.action == "predict":
        results = client.predict_category(args.title)
        if not results:
            print(f"No se encontraron categorias sugeridas para '{args.title}'.")
            return
        print(f"\nCategorias sugeridas para '{args.title}':")
        for i, res in enumerate(results, 1):
            print(f"\n{i}. [{res.get('category_id')}] {res.get('category_name')}")
            print(f"   Dominio: {res.get('domain_name')} ({res.get('domain_id')})")
            if res.get("attributes"):
                print("   Atributos sugeridos:")
                for attr in res.get("attributes"):
                    print(f"    - {attr.get('name')}: {attr.get('value_name')}")
    elif args.action == "attributes":
        attrs = client.get_category_attributes(args.category_id)
        required = [a for a in attrs if a.get("tags", {}).get("required")]
        print(f"\nAtributos obligatorios para {args.category_id} ({len(required)} encontrados):")
        for a in required:
            print(f" - [{a.get('id')}] {a.get('name')} (Tipo: {a.get('value_type')})")
        print(f"\nTotal de atributos disponibles: {len(attrs)} (Usa --all para ver todos)")
        if getattr(args, "all", False):
            print("\nTodos los atributos:")
            for a in attrs:
                req_str = " (OBLIGATORIO)" if a.get("tags", {}).get("required") else ""
                print(f" - [{a.get('id')}] {a.get('name')}{req_str}")


def handle_item(args):
    client = MeliClient()
    if args.action == "list":
        res = client.list_user_items(status=args.status, limit=args.limit, offset=args.offset)
        results = res.get("results", [])
        paging = res.get("paging", {})
        print(f"\nPublicaciones del usuario (Total: {paging.get('total', len(results))}):")
        for item_id in results:
            print(f" - {item_id}")
        if not results:
            print(" No se encontraron publicaciones con los filtros indicados.")
        print()
    elif args.action == "get":
        if not args.item_id:
            print("Error: Debes especificar --item-id.")
            sys.exit(1)
        item = client.get_item(args.item_id)
        print(json.dumps(item, indent=2, ensure_ascii=False))
    elif args.action == "validate":
        if not args.file:
            print("Error: Debes especificar --file.")
            sys.exit(1)
        path = Path(args.file)
        if not path.exists():
            print(f"Archivo no encontrado: {path}")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = client.validate_item(data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == "create":
        if not args.file:
            print("Error: Debes especificar --file.")
            sys.exit(1)
        path = Path(args.file)
        if not path.exists():
            print(f"Archivo no encontrado: {path}")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        created = client.create_item(data)
        print("¡Publicacion creada exitosamente!")
        print(f"ID: {created.get('id')}")
        print(f"Permalink: {created.get('permalink')}")
        print(f"Estado: {created.get('status')}")
    elif args.action == "status":
        if not args.item_id or not args.status:
            print("Error: Debes especificar --item-id y --status.")
            sys.exit(1)
        res = client.change_status(args.item_id, args.status)
        print(f"Estado del item {args.item_id} actualizado a: {res.get('status')}")
    elif args.action == "price":
        if not args.item_id or args.price is None:
            print("Error: Debes especificar --item-id y --price.")
            sys.exit(1)
        res = client.update_price(args.item_id, args.price)
        print(f"Precio del item {args.item_id} actualizado a: {res.get('price')}")
    elif args.action == "stock":
        if not args.item_id or args.quantity is None:
            print("Error: Debes especificar --item-id y --quantity.")
            sys.exit(1)
        res = client.update_stock(args.item_id, args.quantity)
        print(f"Stock del item {args.item_id} actualizado a: {res.get('available_quantity')}")
    elif args.action == "description":
        if not args.item_id:
            print("Error: Debes especificar --item-id.")
            sys.exit(1)
        if args.text or args.file:
            text = args.text
            if args.file:
                path = Path(args.file)
                if not path.exists():
                    print(f"Archivo no encontrado: {path}")
                    sys.exit(1)
                text = path.read_text(encoding="utf-8")
            res = client.update_item_description(args.item_id, text)
            print(f"Descripción del item {args.item_id} actualizada con éxito.")
        else:
            desc = client.get_item_description(args.item_id)
            print(json.dumps(desc, indent=2, ensure_ascii=False))


def handle_picture(args):
    client = MeliClient()
    if args.action == "upload":
        path = Path(args.file)
        if not path.exists():
            print(f"Archivo no encontrado: {path}")
            sys.exit(1)
        print(f"Subiendo imagen {path.name} a Mercado Libre...")
        res = client.upload_picture(path)
        print("¡Imagen subida exitosamente!")
        print(f"Picture ID: {res.get('id')}")
        print(f"Tamaño máximo: {res.get('max_size')}")


def handle_image(args):
    from .ai_publisher import PublicationPipeline
    pipeline = PublicationPipeline(output_dir=args.output)
    if args.action == "clean":
        print(f"Procesando imagen {args.input}...")
        output_file = pipeline.process_image(args.input, filename_prefix=args.prefix)
        print(f"¡Imagen procesada con fondo blanco puro y guardada en:\n  {output_file}")


def main():
    parser = argparse.ArgumentParser(prog="melikit", description="Herramienta CLI para Mercado Libre")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Auth
    p_auth = subparsers.add_parser("auth", help="Gestion de autenticacion OAuth 2.0")
    p_auth.add_argument("action", choices=["login", "url", "exchange", "status"])
    p_auth.add_argument("--code", help="Codigo de autorizacion o URL completa con ?code=...")
    p_auth.add_argument("--port", type=int, default=8080, help="Puerto local para recibir redirect_uri si usas login")
    p_auth.set_defaults(func=handle_auth)

    # Category
    p_cat = subparsers.add_parser("category", help="Predictor y consulta de categorias")
    p_cat.add_argument("action", choices=["predict", "attributes"])
    p_cat.add_argument("title_or_id", help="Titulo del producto o Category ID")
    p_cat.add_argument("--site", default="MLA", help="Site ID (MLA, MLB, MLM, etc.)")
    p_cat.add_argument("--all", action="store_true", help="Mostrar todos los atributos")

    def wrap_cat(args):
        if args.action == "predict":
            args.title = args.title_or_id
        else:
            args.category_id = args.title_or_id
        handle_category(args)

    p_cat.set_defaults(func=wrap_cat)

    # Item
    p_item = subparsers.add_parser("item", help="Gestion de publicaciones")
    p_item.add_argument("action", choices=["list", "get", "validate", "create", "status", "price", "stock", "description"])
    p_item.add_argument("--item-id", help="ID de la publicacion (ej. MLA123456789)")
    p_item.add_argument("--file", help="Ruta al archivo JSON con datos del item o archivo de texto para descripción")
    p_item.add_argument("--text", help="Texto de la descripción")
    p_item.add_argument("--status", choices=["active", "paused", "closed"], help="Estado del item (para status o filtro en list)")
    p_item.add_argument("--price", type=float, help="Nuevo precio")
    p_item.add_argument("--quantity", type=int, help="Nueva cantidad de stock")
    p_item.add_argument("--limit", type=int, default=50, help="Límite de publicaciones para list (default: 50)")
    p_item.add_argument("--offset", type=int, default=0, help="Desplazamiento para list (default: 0)")
    p_item.set_defaults(func=handle_item)

    # Picture
    p_pic = subparsers.add_parser("picture", help="Subida y gestión de imágenes en Mercado Libre")
    p_pic.add_argument("action", choices=["upload"])
    p_pic.add_argument("--file", required=True, help="Ruta al archivo de imagen local")
    p_pic.set_defaults(func=handle_picture)

    # Image (AI / Visión)
    p_img = subparsers.add_parser("image", help="Limpieza y preparación de fotos de producto con IA")
    p_img.add_argument("action", choices=["clean"])
    p_img.add_argument("--input", required=True, help="Ruta a la foto original")
    p_img.add_argument("--output", default="processed_images", help="Carpeta destino (default: processed_images)")
    p_img.add_argument("--prefix", default="item", help="Prefijo para el archivo generado")
    p_img.set_defaults(func=handle_image)

    args = parser.parse_args()
    try:
        args.func(args)
    except (MeliAPIError, MeliAuthError) as e:
        print(f"\n[Error de Mercado Libre] {e}", file=sys.stderr)
        sys.exit(1)
    except MeliError as e:
        print(f"\n[Error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
