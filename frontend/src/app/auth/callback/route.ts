import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/** Exchange Supabase email-link credentials for the cookie-backed app session. */
export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const tokenHash = url.searchParams.get("token_hash");
  const type = url.searchParams.get("type");
  const requestedNext = url.searchParams.get("next");
  const next = requestedNext?.startsWith("/") && !requestedNext.startsWith("//") && !requestedNext.includes("\\")
    ? requestedNext
    : "/";

  const supabase = createClient();
  let authError: Error | null = null;

  if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    authError = error;
  } else if (tokenHash && (type === "invite" || type === "email" || type === "magiclink")) {
    const { error } = await supabase.auth.verifyOtp({
      token_hash: tokenHash,
      type,
    });
    authError = error;
  } else {
    authError = new Error("Missing or unsupported authentication callback credentials.");
  }

  if (authError) {
    return NextResponse.redirect(new URL("/sign-in?error=callback", request.url));
  }

  return NextResponse.redirect(new URL(next, request.url));
}
