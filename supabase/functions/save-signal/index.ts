import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";
export const config = { runtime: "edge" };
Deno.serve(async (req) => {
  try {
    const body = await req.json();
    const url = Deno.env.get("SUPABASE_URL");
    const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!url || !key) return new Response(JSON.stringify({ error: "secrets missing" }), { status: 500 });
    const supabase = createClient(url, key);
    const payload = {
      symbol: body.symbol,
      time: body.time,
      direction: body.direction,
      entry: body.entry,
      sl: body.sl,
      tp: body.tp,
      size: body.size,
      meta: body.meta ?? {},
    };
    const { data, error } = await supabase.from("trade_signals").insert(payload).select().single();
    if (error) return new Response(JSON.stringify({ error: error.message }), { status: 400 });
    return new Response(JSON.stringify({ ok: true, data }), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), { status: 400 });
  }
});