import argparse
import json
import sys
from pathlib import Path
from .auth import MeliAuth
from .client import MeliClient


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
            print("No hay tokens guardados. Ejecuta 'python -m melikit auth url' o 'login'.")
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
    if args.action == "get":
        item = client.get_item(args.item_id)
        print(json.dumps(item, indent=2, ensure_ascii=False))
    elif args.action == "validate":
        path = Path(args.file)
        if not path.exists():
            print(f"Archivo no encontrado: {path}")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = client.validate_item(data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == "create":
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
        res = client.change_status(args.item_id, args.status)
        print(f"Estado del item {args.item_id} actualizado a: {res.get('status')}")
    elif args.action == "price":
        res = client.update_price(args.item_id, args.price)
        print(f"Precio del item {args.item_id} actualizado a: {res.get('price')}")
    elif args.action == "stock":
        res = client.update_stock(args.item_id, args.quantity)
        print(f"Stock del item {args.item_id} actualizado a: {res.get('available_quantity')}")


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
    p_item.add_argument("action", choices=["get", "validate", "create", "status", "price", "stock"])
    p_item.add_argument("--item-id", help="ID de la publicacion (ej. MLA123456789)")
    p_item.add_argument("--file", help="Ruta al archivo JSON con datos del item")
    p_item.add_argument("--status", choices=["active", "paused", "closed"], help="Nuevo estado del item")
    p_item.add_argument("--price", type=float, help="Nuevo precio")
    p_item.add_argument("--quantity", type=int, help="Nueva cantidad de stock")
    p_item.set_defaults(func=handle_item)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
