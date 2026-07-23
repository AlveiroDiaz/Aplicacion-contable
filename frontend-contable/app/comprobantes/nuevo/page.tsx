"use client";

import { useComprobante } from "../../../hooks/useComprobante";
import { LineaContable } from "../../../components/LineaContable";
import { ComprobanteService, ComprobanteResponse } from "../../../services/comprobanteService";
import { AlertService } from "../../../services/alertService";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function NuevoComprobantePage() {
  const contabilidad = useComprobante();
  const searchParams = useSearchParams();
  const viewId = searchParams.get("view");
  const [loadingComprobante, setLoadingComprobante] = useState(false);
  const [soloLectura, setSoloLectura] = useState(false);

  useEffect(() => {
    if (!viewId) return;
    setLoadingComprobante(true);
    ComprobanteService.obtener(viewId)
      .then((data: ComprobanteResponse) => {
        contabilidad.setEmpresaId(data.empresa_id);
        contabilidad.setFecha(data.fecha);
        contabilidad.setDescripcion(data.descripcion);
        contabilidad.setMovimientos(
          data.movimientos?.map((m) => ({
            id: m.id,
            cuenta_codigo: m.cuenta_codigo,
            debito: m.debito,
            credito: m.credito,
            descripcion: m.descripcion || "",
          })) || []
        );
        setSoloLectura(true);
      })
      .catch(() => AlertService.error("Error al cargar el comprobante"))
      .finally(() => setLoadingComprobante(false));
  }, [viewId]);

  const contabilizar = async () => {
    try {
      if (!contabilidad.empresaId) {
        AlertService.error("Debes seleccionar una empresa antes de contabilizar.");
        return;
      }

      const payload = {
        empresa_id: contabilidad.empresaId,
        fecha: contabilidad.fecha,
        descripcion: contabilidad.descripcion,
        movimientos: contabilidad.movimientos.map((m) => ({
          cuenta_codigo: m.cuenta_codigo,
          debito: Number(m.debito),
          credito: Number(m.credito),
          descripcion: m.descripcion,
        })),
      };

      const data = await ComprobanteService.contabilizar(payload);
      AlertService.success(`¡Comprobante generado! Consecutivo: ${data.consecutivo}`);
    } catch (error: any) {
      console.error("Error en la transacción:", error);
      AlertService.error(error.message || "Ocurrió un error inesperado al contabilizar");
    }
  };

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {soloLectura ? "Visualización de Comprobante" : "Nuevo Comprobante"}
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            {soloLectura
              ? "Consulta la información del comprobante seleccionado."
              : "Completa la información general y agrega los movimientos del asiento contable."}
          </p>
        </div>
        {!soloLectura && (
          <span className="inline-flex items-center gap-2 rounded-lg border border-blue-600 px-3 py-1.5 text-xs font-medium text-blue-600">
            Modo edición
          </span>
        )}
      </div>

      {loadingComprobante ? (
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">Cargando comprobante...</p>
        </div>
      ) : (
        <>
          <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Información general</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="flex flex-col">
                <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Empresa</label>
                <select
                  value={contabilidad.empresaId}
                  onChange={(e) => !soloLectura && contabilidad.setEmpresaId(e.target.value)}
                  disabled={soloLectura}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20 disabled:opacity-70"
                >
                  <option value="" disabled>Seleccione...</option>
                  {contabilidad.empresas.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.razon_social}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col">
                <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Fecha</label>
                <input
                  type="date"
                  value={contabilidad.fecha}
                  onChange={(e) => !soloLectura && contabilidad.setFecha(e.target.value)}
                  disabled={soloLectura}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20 disabled:opacity-70"
                />
              </div>

              <div className="flex flex-col md:col-span-3">
                <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Descripción general</label>
                <input
                  type="text"
                  placeholder="Ej. Compra de insumos..."
                  value={contabilidad.descripcion}
                  onChange={(e) => !soloLectura && contabilidad.setDescripcion(e.target.value)}
                  disabled={soloLectura}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20 disabled:opacity-70"
                />
              </div>
            </div>
          </div>

          <div className="mb-4">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Movimientos</h2>
              {!soloLectura && (
                <button
                  onClick={contabilidad.agregarLinea}
                  className="inline-flex items-center gap-2 rounded-lg border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 transition hover:bg-blue-50 dark:hover:bg-blue-950"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  Agregar línea
                </button>
              )}
            </div>

            <div className="space-y-3">
              {contabilidad.movimientos.map((mov) => (
                <LineaContable
                  key={mov.id}
                  movimiento={mov}
                  onEliminar={contabilidad.eliminarLinea}
                  onActualizar={contabilidad.actualizarLinea}
                  deshabilitarEliminar={soloLectura || contabilidad.movimientos.length <= 2}
                  cuentas={contabilidad.cuentas}
                  deshabilitarCampos={soloLectura}
                />
              ))}
            </div>
          </div>

          <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Resumen</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-800">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Débitos</p>
                <p className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">${contabilidad.totalDebito.toFixed(2)}</p>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-800">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Créditos</p>
                <p className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">${contabilidad.totalCredito.toFixed(2)}</p>
              </div>
              <div
                className={`rounded-xl border p-4 ${
                  contabilidad.diferencia === 0
                    ? "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950"
                    : "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
                }`}
              >
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Diferencia</p>
                <p
                  className={`mt-1 text-xl font-bold ${
                    contabilidad.diferencia === 0 ? "text-green-700 dark:text-green-400" : "text-red-600 dark:text-red-400"
                  }`}
                >
                  ${contabilidad.diferencia.toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {!soloLectura && (
            <div className="flex items-center justify-end">
              <button
                onClick={contabilizar}
                disabled={!contabilidad.esValido}
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Contabilizar comprobante
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
