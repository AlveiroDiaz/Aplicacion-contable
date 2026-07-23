const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface PeriodoResponse {
  id: string;
  empresa_id: string;
  anio: number;
  mes: number;
  cerrado: boolean;
}

export interface PeriodoCerrarRequest {
  empresa_id: string;
  anio: number;
  mes: number;
}

export interface PeriodoCerrarResponse extends PeriodoResponse {}

export const PeriodoService = {
  listar: async (empresaId?: string, cerrado?: boolean): Promise<PeriodoResponse[]> => {
    const params = new URLSearchParams();
    if (empresaId) params.set("empresa_id", empresaId);
    if (cerrado !== undefined) params.set("cerrado", String(cerrado));

    const response = await fetch(`${API_URL}/periodos/?${params.toString()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al listar periodos");
    }

    return data;
  },

  cerrar: async (payload: PeriodoCerrarRequest): Promise<PeriodoCerrarResponse> => {
    const response = await fetch(`${API_URL}/periodos/cerrar`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al cerrar el periodo");
    }

    return data;
  },
};
