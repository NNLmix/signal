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
    const { data, error } = await supabase.from("ai_evaluations").insert({
      signal_id: body.signal_id,
      request_prompt: body.request_prompt,
      model: body.model,
      response_text: body.response_text,
      verdict: body.verdict,
      score: body.score,
    }).select().single();
    if (error) return new Response(JSON.stringify({ error: error.message }), { status: 400 });
    return new Response(JSON.stringify({ ok: true, data }), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), { status: 400 });
  }
});