import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

function isProtectedPath(pathname: string) {
  return pathname === "/" || pathname === "/projects" || pathname.startsWith("/projects/");
}

function redirectWithCookies(
  request: NextRequest,
  response: NextResponse,
  destination: string,
) {
  const redirectResponse = NextResponse.redirect(new URL(destination, request.url));
  response.cookies.getAll().forEach((cookie) => redirectResponse.cookies.set(cookie));
  return redirectResponse;
}

function isHttpUrl(value: string | undefined): value is string {
  if (!value) return false;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request });
  const protectedPath = isProtectedPath(request.nextUrl.pathname);

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  if (!isHttpUrl(supabaseUrl) || !supabaseKey) {
    return protectedPath
      ? redirectWithCookies(request, response, "/request-access?error=access_check_unavailable")
      : response;
  }

  const supabase = createServerClient(supabaseUrl, supabaseKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });

  // Refresh tokens first so redirects and downstream requests carry current cookies.
  let user = null;
  let authServiceUnavailable = false;
  try {
    const { data, error } = await supabase.auth.getUser();
    user = data.user;
    authServiceUnavailable = Boolean(error);
  } catch {
    authServiceUnavailable = true;
  }

  if (!protectedPath) return response;

  if (!user) {
    const destination = authServiceUnavailable
      ? "/request-access?error=access_check_unavailable"
      : "/request-access";
    return redirectWithCookies(request, response, destination);
  }

  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.access_token) {
    return redirectWithCookies(request, response, "/request-access");
  }

  const apiBase = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1").replace(/\/+$/, "");
  try {
    const approvalResponse = await fetch(`${apiBase}/auth/access`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
      cache: "no-store",
    });

    if (approvalResponse.ok) return response;
    if (approvalResponse.status === 401 || approvalResponse.status === 403) {
      return redirectWithCookies(request, response, "/request-access");
    }
  } catch {
    // Fail closed if Supabase approval cannot be confirmed by the backend.
  }

  return redirectWithCookies(
    request,
    response,
    "/request-access?error=access_check_unavailable",
  );
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
