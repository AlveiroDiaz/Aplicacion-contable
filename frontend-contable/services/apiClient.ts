import { AuthService } from "./authService";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Envuelve fetch para inyectar el header Authorization en cada llamada al
// backend, en un solo lugar, en vez de repetirlo en cada service. Si el
// backend responde 401 (token ausente/vencido/inválido), cierra la sesión
// local y manda al usuario de vuelta al login.
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = AuthService.obtenerToken();
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (response.status === 401 && typeof window !== "undefined") {
    AuthService.cerrarSesion();
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }

  return response;
}
