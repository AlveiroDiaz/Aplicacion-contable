const API_URL = process.env.NEXT_PUBLIC_API_URL;

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

    const response = await fetch(`${API_URL}/terceros/?${params.toString()}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al listar terceros");
    return data;
  },

  crear: async (payload: TerceroCreate): Promise<Tercero> => {
    const response = await fetch(`${API_URL}/terceros/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al crear el tercero");
    return data;
  },
};
