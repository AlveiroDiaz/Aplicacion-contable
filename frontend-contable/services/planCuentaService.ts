import { apiFetch } from "./apiClient";

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
    const response = await apiFetch(`/cuentas/`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al crear la cuenta");
    return data;
  },

  obtenerPorEmpresa: async (empresaId: string): Promise<PlanCuenta[]> => {
    const response = await apiFetch(`/cuentas/?empresa_id=${empresaId}`, {
      method: "GET",
    });
    if (!response.ok) throw new Error("Error al obtener cuentas");
    return response.json();
  },

  obtenerPorCodigo: async (empresaId: string, codigo: string): Promise<PlanCuenta> => {
    const response = await apiFetch(`/cuentas/${encodeURIComponent(codigo)}?empresa_id=${empresaId}`, {
      method: "GET",
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al obtener la cuenta");
    return data;
  },

  actualizar: async (empresaId: string, codigo: string, payload: PlanCuentaUpdate): Promise<PlanCuenta> => {
    const response = await apiFetch(`/cuentas/${encodeURIComponent(codigo)}?empresa_id=${empresaId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al actualizar la cuenta");
    return data;
  },

  desactivar: async (empresaId: string, codigo: string): Promise<void> => {
    const response = await apiFetch(`/cuentas/${encodeURIComponent(codigo)}?empresa_id=${empresaId}`, {
      method: "DELETE",
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al desactivar la cuenta");
  },
};
