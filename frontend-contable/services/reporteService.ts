const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface MovimientoLibroMayor {
  fecha: string;
  comprobante_consecutivo: string;
  descripcion_comprobante: string;
  descripcion_movimiento: string | null;
  debito: number;
  credito: number;
}

export interface LibroMayorResponse {
  cuenta_codigo: string;
  cuenta_nombre: string;
  total_debito: number;
  total_credito: number;
  saldo_final: number;
  movimientos: MovimientoLibroMayor[];
}

export const ReporteService = {
  obtenerLibroMayor: async (
    empresaId: string,
    cuentaCodigo: string,
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<LibroMayorResponse> => {
    const params = new URLSearchParams({
      empresa_id: empresaId,
      cuenta_codigo: cuentaCodigo,
    });

    if (fechaInicio) params.append("fecha_inicio", fechaInicio);
    if (fechaFin) params.append("fecha_fin", fechaFin);

    const response = await fetch(`${API_URL}/reportes/libro-mayor?${params.toString()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("No se pudo obtener el libro mayor para la cuenta indicada.");
    }

    return response.json();
  },
};