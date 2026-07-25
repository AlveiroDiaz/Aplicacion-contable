import { NextRequest, NextResponse } from "next/server";

const TOKEN_COOKIE = "motor_contable_token";
const RUTAS_PUBLICAS = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (RUTAS_PUBLICAS.some((ruta) => pathname.startsWith(ruta))) {
    return NextResponse.next();
  }

  const token = request.cookies.get(TOKEN_COOKIE)?.value;
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Corre en todo excepto assets estáticos de Next y el favicon; la
  // validación real del token (firma/expiración) la hace el backend en
  // cada llamada, esto solo evita que se vea la app sin cookie de sesión.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
