// Supabase JS client for direct DB reads and Realtime subscriptions.
// Auth is disabled — the demo backend issues its own demo_session_id cookie
// and the Supabase SDK is used only for catalog reads / channel subscriptions.

import { createClient } from "@supabase/supabase-js";
import type { SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl: string =
  process.env.SUPABASE_URL || useRuntimeConfig().public.supabaseUrl;

const supabaseAnonKey: string =
  process.env.SUPABASE_ANON_KEY || useRuntimeConfig().public.supabaseAnonKey;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase URL and Anon Key must be provided.");
}

export const supabase: SupabaseClient = createClient(
  supabaseUrl,
  supabaseAnonKey,
  {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
      detectSessionInUrl: false,
    },
    db: {
      schema: "ai_proposal_platform",
    },
  },
);
