// Repassa ao navegador as imagens geradas por run_python_analysis. O agente
// Python as guarda em disco e as serve em GET /images/{id}; este proxy evita
// expor a porta 8123 ao navegador (e problemas de CORS).
import { agentUrl } from "../../../../lib/runtime-config";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  // O id é um UUID em hexadecimal; recusar qualquer outra coisa evita que o
  // proxy seja usado para alcançar outros caminhos do agente.
  if (!/^[0-9a-f]{32}$/.test(id)) {
    return new Response("Not found", { status: 404 });
  }

  const upstream = await fetch(`${agentUrl}/images/${id}`);
  if (!upstream.ok) {
    return new Response("Not found", { status: 404 });
  }
  return new Response(upstream.body, {
    headers: {
      "Content-Type": "image/png",
      // O conteúdo de um id nunca muda.
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
}
