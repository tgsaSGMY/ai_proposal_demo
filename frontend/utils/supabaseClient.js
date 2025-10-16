import { createClient } from "@supabase/supabase-js";

// 从 .env 文件或运行时配置中获取
const supabaseUrl =
  process.env.SUPABASE_URL || useRuntimeConfig().public.supabaseUrl;
const supabaseAnonKey =
  process.env.SUPABASE_ANON_KEY || useRuntimeConfig().public.supabaseAnonKey;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase URL and Anon Key must be provided.");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
