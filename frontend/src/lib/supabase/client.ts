import { createBrowserClient } from "@supabase/ssr";

/** Create the browser Supabase client used for email-link sign-in and sign-out. */
export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    throw new Error("Supabase URL and publishable key must be configured.");
  }

  return createBrowserClient(supabaseUrl, supabaseKey);
}
