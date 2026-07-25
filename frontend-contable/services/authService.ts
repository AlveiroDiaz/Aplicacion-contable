const API_URL = process.env.NEXT_PUBLIC_API_URL;
const TOKEN_COOKIE = "motor_contable_token";
const USUARIO_STORAGE_KEY = "motor_contable_usuario";

export interface Usuario {
  id: string;
  username: string;
  nombre?: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}

export const AuthService = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Usuario o contraseña incorrectos.");
    }

    return data;
  },

  // El token se guarda en una cookie (no solo en localStorage) para que
  // middleware.ts pueda leerla en el servidor y proteger las rutas antes
  // de que la página llegue a renderizarse en el navegador.
  guardarSesion: (data: LoginResponse) => {
    document.cookie = `${TOKEN_COOKIE}=${data.access_token}; path=/; max-age=${60 * 60 * 12}; samesite=lax`;
    localStorage.setItem(USUARIO_STORAGE_KEY, JSON.stringify(data.usuario));
  },

  obtenerToken: (): string | null => {
    if (typeof document === "undefined") return null;
    const match = document.cookie.match(new RegExp(`(?:^|; )${TOKEN_COOKIE}=([^;]*)`));
    return match ? decodeURIComponent(match[1]) : null;
  },

  obtenerUsuario: (): Usuario | null => {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem(USUARIO_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  cerrarSesion: () => {
    document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0`;
    localStorage.removeItem(USUARIO_STORAGE_KEY);
  },
};
