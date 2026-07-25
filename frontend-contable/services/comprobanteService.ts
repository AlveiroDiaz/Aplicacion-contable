import { apiFetch } from "./apiClient";

export interface ComprobanteResponse {
  id: string;
  empresa_id: string;
  periodo_id: string;
  consecutivo: string | null;
  fecha: string;
  descripcion: string;
  estado: string;
  revertido: boolean;
  created_at?: string;
  movimientos?: {
    id: string;
    cuenta_codigo: string;
    tercero_id?: string | null;
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
    const response = await apiFetch(`/comprobantes/contabilizar`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al comunicarse con el servidor");
    }

    return data;
  },

  guardarBorrador: async (payload: any): Promise<ComprobanteResponse> => {
    const response = await apiFetch(`/comprobantes/borrador`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al guardar el borrador");
    }

    return data;
  },

  actualizarBorrador: async (id: string, payload: any): Promise<ComprobanteResponse> => {
    const response = await apiFetch(`/comprobantes/${id}/borrador`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al actualizar el borrador");
    }

    return data;
  },

  contabilizarBorrador: async (id: string) => {
    const response = await apiFetch(`/comprobantes/${id}/contabilizar`, {
      method: "POST",
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al contabilizar el borrador");
    }

    return data;
  },

  listar: async (empresaId?: string, consecutivo?: string): Promise<ComprobanteResponse[]> => {
    const params = new URLSearchParams();
    if (empresaId) params.set("empresa_id", empresaId);
    if (consecutivo) params.set("consecutivo", consecutivo);

    const response = await apiFetch(`/comprobantes/?${params.toString()}`, {
      method: "GET",
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al listar comprobantes");
    }

    return data;
  },

  obtener: async (id: string): Promise<ComprobanteResponse> => {
    const response = await apiFetch(`/comprobantes/${id}`, {
      method: "GET",
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al obtener comprobante");
    }

    return data;
  },

  revertir: async (id: string): Promise<ComprobanteReverseResponse> => {
    const response = await apiFetch(`/comprobantes/${id}/revertir`, {
      method: "POST",
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al revertir comprobante");
    }

    return data;
  },
};
