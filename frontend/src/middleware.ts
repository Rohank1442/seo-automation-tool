import { NextRequest, NextResponse } from "next/server";

function isProtectedPath(pathname: string): boolean {
  return pathname === "/" || pathname === "/projects" || pathname.startsWith("/projects/");
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (!isProtectedPath(pathname)) {
    return NextResponse.next();
  }

  // Check for session token in cookies (supporting both seo_access_token and access_token)
  const token =
    request.cookies.get("seo_access_token")?.value ||
    request.cookies.get("access_token")?.value;

  if (!token) {
    const signInUrl = new URL("/sign-in", request.url);
    return NextResponse.redirect(signInUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
