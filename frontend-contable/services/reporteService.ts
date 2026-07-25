const API_URL = process.env.NEXT_PUBLIC_API_URL;

// El backend expone estos campos como Decimal, que FastAPI serializa a
// JSON como STRING (ej. "1190000.00"), no como número, precisamente para
// no perder precisión pasando por punto flotante en el wire format. Se
// tipan como string aquí a propósito: conviértelos con Number(...) solo
// en el último momento, para mostrarlos.
export interface MovimientoLibroMayor {
  fecha: string;
  comprobante_consecutivo: string;
  descripcion_comprobante: string;
  descripcion_movimiento: string | null;
  tercero: string | null;
  debito: string;
  credito: string;
  saldo_acumulado: string;
}

export interface LibroMayorResponse {
  cuenta_codigo: string;
  cuenta_nombre: string;
  total_debito: string;
  total_credito: string;
  saldo_final: string;
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