import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = new Set(["/login", "/register"]);

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/" || PUBLIC_PATHS.has(pathname)) {
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|gsicon.png|icon.png).*)",
  ],
};
