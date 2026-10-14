export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/callback") {
      const code = url.searchParams.get("code");
      const error = url.searchParams.get("error");
      const errorDescription = url.searchParams.get("error_description");

      if (error) {
        return new Response(
          htmlTemplate("Error de Autorización", `<p style="color: #e53e3e;">${errorDescription || error}</p>`),
          { headers: { "content-type": "text/html;charset=UTF-8" }, status: 400 }
        );
      }

      if (!code) {
        return new Response(
          htmlTemplate("Aviso", "<p>No se recibió ningún código en la solicitud.</p>"),
          { headers: { "content-type": "text/html;charset=UTF-8" }, status: 400 }
        );
      }

      return new Response(
        htmlTemplate(
          "¡Autorización Exitosa!",
          `
          <p>Mercado Libre autorizó la aplicación correctamente.</p>
          <div style="background: #edf2f7; padding: 15px; border-radius: 8px; margin: 20px 0; font-family: monospace; word-break: break-all; border: 1px solid #cbd5e0;">
            <strong>Código de Autorización:</strong><br>
            <span id="authCode">${code}</span>
          </div>
          <button onclick="navigator.clipboard.writeText('${code}').then(() => alert('¡Código copiado al portapapeles!'))"
                  style="background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: bold;">
            Copiar Código
          </button>
          <p style="margin-top: 25px; color: #4a5568; font-size: 13px;">
            Ahora ejecuta en tu terminal:<br>
            <code>python -m melikit auth exchange --code "${code}"</code>
          </p>
          `
        ),
        { headers: { "content-type": "text/html;charset=UTF-8" } }
      );
    }

    if (url.pathname === "/" || url.pathname === "") {
      return new Response(
        htmlTemplate(
          "MeliKit Auth Gateway",
          `
          <p>Servicio Cloudflare activo para autenticación con la API de Mercado Libre en <strong>meli.solucionesaustral.com</strong>.</p>
          <p style="color: #718096; font-size: 14px;">Endpoint de callback: <code>/callback</code></p>
          `
        ),
        { headers: { "content-type": "text/html;charset=UTF-8" } }
      );
    }

    return new Response("Not Found", { status: 404 });
  },
};

function htmlTemplate(title, content) {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} - MeliKit</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #1e293b; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 16px; }
    .card { background: white; border-radius: 16px; padding: 32px; max-width: 500px; width: 100%; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3); text-align: center; }
    h1 { margin-top: 0; font-size: 22px; color: #0f172a; }
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size: 42px; margin-bottom: 10px;">📦</div>
    <h1>${title}</h1>
    ${content}
  </div>
</body>
</html>`;
}
