const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface PlanCuenta {
  codigo: string;
  empresa_id: string;
  nombre: string;
  naturaleza: string;
  activa: boolean;
  parent_codigo?: string;
}

export interface PlanCuentaCreate {
  codigo: string;
  empresa_id: string;
  nombre: string;
  naturaleza: string;
  activa?: boolean;
  parent_codigo?: string;
}

export interface PlanCuentaUpdate {
  nombre?: string;
  naturaleza?: string;
  activa?: boolean;
  parent_codigo?: string;
}

export const PlanCuentaService = {
  crear: async (payload: PlanCuentaCreate): Promise<PlanCuenta> => {
    const response = await fetch(`${API_URL}/cuentas/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al crear la cuenta");
    return data;
  },

  obtenerPorEmpresa: async (empresaId: string): Promise<PlanCuenta[]> => {
    const response = await fetch(`${API_URL}/cuentas/?empresa_id=${empresaId}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) throw new Error("Error al obtener cuentas");
    return response.json();
  },

  obtenerPorCodigo: async (empresaId: string, codigo: string): Promise<PlanCuenta> => {
    const response = await fetch(`${API_URL}/cuentas/${encodeURIComponent(codigo)}?empresa_id=${empresaId}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al obtener la cuenta");
    return data;
  },

  actualizar: async (empresaId: string, codigo: string, payload: PlanCuentaUpdate): Promise<PlanCuenta> => {
    const response = await fetch(`${API_URL}/cuentas/${encodeURIComponent(codigo)}?empresa_id=${empresaId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al actualizar la cuenta");
    return data;
  },

  desactivar: async (empresaId: string, codigo: string): Promise<void> => {
    const response = await fetch(`${API_URL}/cuentas/${encodeURIComponent(codigo)}?empresa_id=${empresaId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al desactivar la cuenta");
  },
};
