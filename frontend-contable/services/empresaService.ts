import { apiFetch } from "./apiClient";

export interface Empresa {
  id: string;
  nit: string;
  razon_social: string;
  activa: boolean;
}

export const EmpresaService = {
  obtenerTodas: async (): Promise<Empresa[]> => {
    const response = await apiFetch(`/empresas/`, {
      method: "GET",
    });

    if (!response.ok) {
      throw new Error("Error al obtener el listado de empresas");
    }

    return response.json();
  }
};
