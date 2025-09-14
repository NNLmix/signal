// ...same as earlier minimal version...
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import OpenAI from "https://esm.sh/openai@4.59.1";
export const config = { runtime: "edge" };
Deno.serve(async (req) => {
  try {
    const { prompt, model } = await req.json();
    const apiKey = Deno.env.get("OPENAI_API_KEY");
    if (!apiKey) return new Response(JSON.stringify({ error: "OPENAI_API_KEY is not set" }), { status: 500 });
    const client = new OpenAI({ apiKey });
    const m = model || "gpt-4o-mini";
    const completion = await client.chat.completions.create({
      model: m,
      messages: [{ role: "system", content: "Short answers." }, { role: "user", content: prompt || "" }],
      temperature: 0.2,
    });
    const text = completion.choices?.[0]?.message?.content || "";
    return new Response(JSON.stringify({ model: m, text }), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), { status: 400 });
  }
});