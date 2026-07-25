import { apiFetch } from "./apiClient";

export interface Tercero {
  id: string;
  tipo_doc?: string;
  num_doc?: string;
  dv?: string;
  nombre?: string;
}

export interface TerceroCreate {
  tipo_doc?: string;
  num_doc: string;
  dv?: string;
  nombre: string;
}

export const TerceroService = {
  listar: async (q?: string): Promise<Tercero[]> => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);

    const response = await apiFetch(`/terceros/?${params.toString()}`, {
      method: "GET",
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al listar terceros");
    return data;
  },

  crear: async (payload: TerceroCreate): Promise<Tercero> => {
    const response = await apiFetch(`/terceros/`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al crear el tercero");
    return data;
  },
};
