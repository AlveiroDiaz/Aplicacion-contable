const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface Empresa {
  id: string;
  nit: string;
  razon_social: string;
  activa: boolean;
}

export const EmpresaService = {
  obtenerTodas: async (): Promise<Empresa[]> => {
    // Apuntamos al endpoint que acabas de probar
    const response = await fetch(`${API_URL}/empresas/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Error al obtener el listado de empresas");
    }

    return response.json();
  }
};