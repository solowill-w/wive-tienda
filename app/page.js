import { createClient } from "@supabase/supabase-js";

export const dynamic = "force-dynamic";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
);

export default async function Home() {
  const { data, error } = await supabase
    .from("store_settings")
    .select("store_name")
    .eq("id", 1)
    .single();

  return (
    <main style={{ padding: 32 }}>
      <h1>{data?.store_name ?? "WIVE"}</h1>
      <p>{error ? "Error de conexión con la base de datos" : "Conexión con la base de datos: OK"}</p>
    </main>
  );
}
