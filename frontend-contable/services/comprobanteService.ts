const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface ComprobanteResponse {
  id: string;
  empresa_id: string;
  periodo_id: string;
  consecutivo: string;
  fecha: string;
  descripcion: string;
  estado: string;
  revertido: boolean;
  created_at?: string;
  movimientos?: {
    id: string;
    cuenta_codigo: string;
    debito: number;
    credito: number;
    descripcion?: string;
  }[];
}

export interface ComprobanteReverseResponse {
  mensaje: string;
  comprobante_original_id: string;
  comprobante_original_consecutivo: string;
  comprobante_nuevo_id: string;
  comprobante_nuevo_consecutivo: string;
}

export const ComprobanteService = {
  contabilizar: async (payload: any) => {
    const response = await fetch(`${API_URL}/comprobantes/contabilizar`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al comunicarse con el servidor");
    }

    return data;
  },

  listar: async (empresaId?: string, consecutivo?: string): Promise<ComprobanteResponse[]> => {
    const params = new URLSearchParams();
    if (empresaId) params.set("empresa_id", empresaId);
    if (consecutivo) params.set("consecutivo", consecutivo);

    const response = await fetch(`${API_URL}/comprobantes/?${params.toString()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al listar comprobantes");
    }

    return data;
  },

  obtener: async (id: string): Promise<ComprobanteResponse> => {
    const response = await fetch(`${API_URL}/comprobantes/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al obtener comprobante");
    }

    return data;
  },

  revertir: async (id: string): Promise<ComprobanteReverseResponse> => {
    const response = await fetch(`${API_URL}/comprobantes/${id}/revertir`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al revertir comprobante");
    }

    return data;
  },
};
