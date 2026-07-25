import { apiFetch } from "./apiClient";

export interface ExogenaGeneratePayload {
  empresa_id: string;
  anio_gravable: number;
  umbral_uvt: number;
  fecha_inicio?: string;
  fecha_fin?: string;
}

export interface ExogenaHistoryItem {
  id: string;
  empresa_id: string;
  anio_gravable: number;
  fecha_generacion: string;
  parametros: Record<string, any>;
  registros: number;
  // Decimal en el backend: FastAPI los serializa como string, no number
  // (evita el paso por punto flotante en el JSON). Convertir con
  // Number(...) solo al momento de mostrarlos.
  total_valor_bruto: string;
  total_retencion: string;
}

export const ExogenaService = {
  generar: async (payload: ExogenaGeneratePayload): Promise<{ blob: Blob; filename: string }> => {
    const response = await apiFetch(`/exogena/generar`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      throw new Error(errorBody?.detail || "Error al generar el archivo de exógena.");
    }

    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") || "";
    const filenameMatch = disposition.match(/filename=(.+)$/);
    const filename = filenameMatch ? filenameMatch[1].replace(/"/g, "") : `exogena-${payload.empresa_id}-${payload.anio_gravable}.xml`;
    return { blob, filename };
  },

  obtenerHistorial: async (): Promise<ExogenaHistoryItem[]> => {
    const response = await apiFetch(`/exogena/historial`, {
      method: "GET",
    });

    if (!response.ok) {
      throw new Error("Error al cargar el historial de exógena.");
    }

    return response.json();
  },

  redescargar: async (id: string): Promise<{ blob: Blob; filename: string }> => {
    const response = await apiFetch(`/exogena/historial/${id}/archivo`, {
      method: "GET",
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      throw new Error(errorBody?.detail || "Error al descargar el archivo de exógena.");
    }

    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") || "";
    const filenameMatch = disposition.match(/filename=(.+)$/);
    const filename = filenameMatch ? filenameMatch[1].replace(/"/g, "") : `exogena-${id}.xml`;
    return { blob, filename };
  },
};
