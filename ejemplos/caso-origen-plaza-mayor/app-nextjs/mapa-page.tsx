import BannerSlot from "@/components/BannerSlot";
import PageHeader from "@/components/PageHeader";
import LockedModule from "@/components/LockedModule";
import Mapa3D from "@/components/mapa/Mapa3D";
import { getAccess } from "@/lib/access";
import { VENUE_NAME_KEY, venueNameFrom } from "@/lib/appConfig";
import {
  MAPA_RECORRIDO_KEY,
  parseRecorrido,
  type StandPublico,
} from "@/lib/mapa3d";
import { createClient } from "@/lib/supabase/server";

const TITLE = "Mapa del recinto";

/**
 * MAPA — mapa 3D navegable del recinto (reemplaza al plano por zonas de la
 * Fase 5/30). Abierto sin sesión — solo depende del modo vitrina.
 *
 * La sede sale de app_config (Fase 32): cambiar de recinto no debe exigir un
 * deploy. Si la clave no está sembrada, venueNameFrom() cae al texto histórico.
 *
 * El modelo (public/mapa3d/mapa.glb) y sus datos (public/mapa3d/datos.json)
 * se generan fuera de la app desde el plano técnico de la feria; aquí solo se
 * cruzan los stands del plano con
 * stands_publico (vista pública, regla 7) para pintar en cada pin la empresa
 * y su logo del directorio.
 */
export default async function MapaPage({
  searchParams,
}: {
  searchParams: Promise<{ stand?: string | string[] }>;
}) {
  const [a, sp] = await Promise.all([getAccess(), searchParams]);
  const standParam = Array.isArray(sp.stand) ? sp.stand[0] : sp.stand;

  if (!a.configured) {
    return <LockedModule title={TITLE} reason="ticket" configured={false} />;
  }

  const supabase = await createClient();
  const [{ data: venueCfg }, { data: recorridoCfg }, { data: standsDb }] =
    await Promise.all([
      supabase
        .from("app_config")
        .select("value")
        .eq("key", VENUE_NAME_KEY)
        .maybeSingle(),
      supabase
        .from("app_config")
        .select("value")
        .eq("key", MAPA_RECORRIDO_KEY)
        .maybeSingle(),
      // Todos los stands del plano, también los que siguen a la venta (nombre null).
      supabase
        .from("stands_publico")
        .select(
          "id,codigo,nombre,pabellon,tipo_stand,logo_url,directorio_descripcion",
        ),
    ]);
  const venueName = venueNameFrom(venueCfg?.value);

  return (
    <div className="flex flex-col">
      <PageHeader
        title={TITLE}
        subtitle={`${venueName} · mapa 3D a escala`}
        backHref="/inicio"
      />
      <BannerSlot
        placement="module_top"
        moduleKey="mapa"
        edition={a.currentEdition}
        className="mb-4"
      />
      <Mapa3D
        standsDb={(standsDb ?? []) as StandPublico[]}
        venueName={venueName}
        recorridoCfg={parseRecorrido(recorridoCfg?.value)}
        initialStand={standParam?.slice(0, 20) ?? null}
      />
    </div>
  );
}
