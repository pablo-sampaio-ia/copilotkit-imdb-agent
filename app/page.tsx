import { HomeLayout } from "../components/HomeLayout";
import { intelligenceApiKey } from "../lib/runtime-config";

// Lê as variáveis de ambiente a cada requisição, e não só no build.
export const dynamic = "force-dynamic";

// Componente de servidor: decide se a lista de threads existe (ela depende do
// CopilotKit Intelligence) e entrega o resto para o componente de cliente.
export default function Home() {
  return <HomeLayout threadsEnabled={Boolean(intelligenceApiKey)} />;
}
