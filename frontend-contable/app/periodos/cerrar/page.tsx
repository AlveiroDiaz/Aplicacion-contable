"use client";

import { useState, useEffect } from "react";
import { PeriodoService, PeriodoResponse } from "../../../services/periodoService";
import { Empresa, EmpresaService } from "../../../services/empresaService";
import { AlertService } from "../../../services/alertService";

export default function CerrarPeriodoPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [empresaId, setEmpresaId] = useState("");
  const [periodos, setPeriodos] = useState<PeriodoResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [cerrandoId, setCerrarId] = useState<string | null>(null);

  useEffect(() => {
    EmpresaService.obtenerTodas()
      .then((data) => {
        setEmpresas(data);
        if (data.length > 0) setEmpresaId(data[0].id);
      })
      .catch(() => AlertService.error("Error al cargar las empresas"));
  }, []);

  useEffect(() => {
    if (!empresaId) return;
    setLoading(true);
    PeriodoService.listar(empresaId)
      .then((data) => setPeriodos(data))
      .catch(() => AlertService.error("Error al cargar los períodos"))
      .finally(() => setLoading(false));
  }, [empresaId]);

  const cerrarPeriodo = async (periodo: PeriodoResponse) => {
    const confirmacion = window.confirm(
      `¿Estás seguro de cerrar el período ${periodo.anio}-${String(periodo.mes).padStart(2, "0")}?\n\nDespués del cierre no se podrán registrar nuevos comprobantes para este período.`
    );
    if (!confirmacion) return;

    setCerrarId(periodo.id);
    try {
      await PeriodoService.cerrar({
        empresa_id: periodo.empresa_id,
        anio: periodo.anio,
        mes: periodo.mes,
      });
      AlertService.success("Período cerrado con éxito");
      setPeriodos((prev) =>
        prev.map((p) => (p.id === periodo.id ? { ...p, cerrado: true } : p))
      );
    } catch (error: any) {
      AlertService.error(error.message || "Error al cerrar el período");
    } finally {
      setCerrarId(null);
    }
  };

  const formatearPeriodo = (anio: number, mes: number) => {
    const meses = [
      "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ];
    return `${meses[mes - 1]} ${anio}`;
  };

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Cierre de Período</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Cierra períodos contables una vez estén completamente registrados. Una vez cerrado, no se podrán crear nuevos comprobantes para ese mes.
        </p>
      </div>

      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Filtros</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="flex flex-col">
            <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Empresa</label>
            <select
              value={empresaId}
              onChange={(e) => setEmpresaId(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
            >
              {empresas.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.razon_social}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-gray-600 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-400">
                <th className="px-4 py-3 font-medium">Período</th>
                <th className="px-4 py-3 font-medium">Año</th>
                <th className="px-4 py-3 font-medium">Mes</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                    Cargando períodos...
                  </td>
                </tr>
              ) : periodos.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                    No hay períodos registrados para esta empresa.
                  </td>
                </tr>
              ) : (
                periodos.map((periodo) => (
                  <tr key={periodo.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                      {formatearPeriodo(periodo.anio, periodo.mes)}
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{periodo.anio}</td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{periodo.mes}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          periodo.cerrado
                            ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                            : "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300"
                        }`}
                      >
                        {periodo.cerrado ? "Cerrado" : "Abierto"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {!periodo.cerrado && (
                        <button
                          onClick={() => cerrarPeriodo(periodo)}
                          disabled={cerrandoId === periodo.id}
                          className="rounded-lg px-3 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-950"
                        >
                          {cerrandoId === periodo.id ? "Cerrando..." : "Cerrar período"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
