"use client";

import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { ReporteService, LibroMayorResponse } from "../../services/reporteService";
import { Empresa, EmpresaService } from "../../services/empresaService";
import { PlanCuenta, PlanCuentaService } from "../../services/planCuentaService";
import { AlertService } from "../../services/alertService";

export default function ReportesPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [empresaId, setEmpresaId] = useState("");
  const [cuentaCodigo, setCuentaCodigo] = useState("");
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [reporte, setReporte] = useState<LibroMayorResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [cuentas, setCuentas] = useState<PlanCuenta[]>([]);
  const [abierto, setAbierto] = useState(false);
  const [indiceActivo, setIndiceActivo] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);

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
    PlanCuentaService.obtenerPorEmpresa(empresaId)
      .then((data) => setCuentas(data))
      .catch(() => AlertService.error("Error al cargar las cuentas"));
  }, [empresaId]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setAbierto(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const consultar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!empresaId || !cuentaCodigo.trim()) {
      AlertService.error("Selecciona una empresa y escribe un código de cuenta.");
      return;
    }

    setLoading(true);
    try {
      const data = await ReporteService.obtenerLibroMayor(
        empresaId,
        cuentaCodigo.trim(),
        fechaInicio || undefined,
        fechaFin || undefined
      );
      setReporte(data);
      AlertService.success("Libro mayor consultado con éxito");
    } catch (error: any) {
      AlertService.error(error.message || "Cuenta no encontrada o sin movimientos");
      setReporte(null);
    } finally {
      setLoading(false);
    }
  };

  const coincidencias = useMemo(() => {
    const q = cuentaCodigo.trim().toLowerCase();
    if (!q) return [];
    return cuentas
      .filter((c) => c.codigo.toLowerCase().includes(q) || c.nombre.toLowerCase().includes(q))
      .slice(0, 8);
  }, [cuentaCodigo, cuentas]);

  const cuentaSeleccionada = useMemo(() => {
    return cuentas.find((c) => c.codigo === cuentaCodigo) || null;
  }, [cuentaCodigo, cuentas]);

  const seleccionar = useCallback((cuenta: PlanCuenta) => {
    setCuentaCodigo(cuenta.codigo);
    setAbierto(false);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!abierto && e.key === "ArrowDown") {
      setAbierto(true);
      return;
    }
    if (!abierto) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIndiceActivo((prev) => Math.min(prev + 1, coincidencias.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setIndiceActivo((prev) => Math.max(prev - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (coincidencias[indiceActivo]) {
        seleccionar(coincidencias[indiceActivo]);
      }
    } else if (e.key === "Escape") {
      setAbierto(false);
    }
  };

  const formatearMonto = (valor: string | number) => {
    return Number(valor).toLocaleString("es-CO", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const esPositivo = (valor: string | number) => Number(valor) >= 0;

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Libro Mayor</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Consulta los movimientos de una cuenta y su saldo acumulado por rango de fechas.
        </p>
      </div>

      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Filtros de consulta</h2>
        <form onSubmit={consultar} className="grid grid-cols-1 gap-4 md:grid-cols-4">
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

          <div className="flex flex-col">
            <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Código de Cuenta</label>
            <div ref={wrapperRef} className="relative">
              <input
                type="text"
                value={cuentaCodigo}
                onChange={(e) => {
                  setCuentaCodigo(e.target.value);
                  setAbierto(true);
                  setIndiceActivo(0);
                }}
                onFocus={() => setAbierto(true)}
                onKeyDown={handleKeyDown}
                placeholder="Buscar cuenta..."
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 pr-9 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
              />
              <span className="pointer-events-none absolute inset-y-0 right-2 flex items-center text-gray-400">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </span>
              {abierto && (
                <div
                  className="absolute left-0 right-0 top-full z-50 mt-1.5 max-h-64 overflow-auto rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900"
                >
                  {coincidencias.length === 0 ? (
                    <p className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">Sin resultados, escribe el código manualmente.</p>
                  ) : (
                    coincidencias.map((c, i) => {
                      const activo = i === indiceActivo;
                      const seleccionado = cuentaSeleccionada?.codigo === c.codigo;
                      return (
                        <div
                          key={c.codigo}
                          onMouseDown={(e) => {
                            e.preventDefault();
                            seleccionar(c);
                          }}
                          onMouseEnter={() => setIndiceActivo(i)}
                          className={`cursor-pointer px-4 py-2.5 text-sm transition-colors ${
                            activo
                              ? "bg-blue-50 dark:bg-blue-950/50"
                              : seleccionado
                              ? "bg-blue-50/60 dark:bg-blue-950/30"
                              : "hover:bg-gray-100 dark:hover:bg-gray-800"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-semibold text-blue-600 dark:text-blue-400 text-xs">{c.codigo}</span>
                            <span className="text-gray-400 text-xs">·</span>
                            <span className="text-gray-700 dark:text-gray-300 truncate">{c.nombre}</span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              )}
            </div>
            {cuentaSeleccionada && !abierto && (
              <p className="mt-1 truncate text-xs text-gray-500 dark:text-gray-400">
                {cuentaSeleccionada.nombre}
              </p>
            )}
          </div>

          <div className="flex flex-col">
            <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Fecha inicio</label>
            <input
              type="date"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
            />
          </div>

          <div className="flex flex-col">
            <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Fecha fin</label>
            <input
              type="date"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
            />
          </div>

          <div className="flex items-end md:col-span-4">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Consultando..." : "Consultar Mayor"}
            </button>
          </div>
        </form>
      </div>

      {reporte && (
        <>
          <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                  {reporte.cuenta_codigo} - {reporte.cuenta_nombre}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Movimientos registrados para esta cuenta
                </p>
              </div>
              <div className="mt-2 sm:mt-0 sm:text-right">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Saldo Final</p>
                <p className={`text-2xl font-bold ${esPositivo(reporte.saldo_final) ? "text-green-700 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                  $ {formatearMonto(reporte.saldo_final)}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-800">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Débitos</p>
                <p className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">$ {formatearMonto(reporte.total_debito)}</p>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-800">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Créditos</p>
                <p className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">$ {formatearMonto(reporte.total_credito)}</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-gray-600 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-400">
                    <th className="px-4 py-3 font-medium">Fecha</th>
                    <th className="px-4 py-3 font-medium">Comprobante</th>
                    <th className="px-4 py-3 font-medium">Descripción</th>
                    <th className="px-4 py-3 font-medium">Tercero</th>
                    <th className="px-4 py-3 font-medium text-right">Débito</th>
                    <th className="px-4 py-3 font-medium text-right">Crédito</th>
                    <th className="px-4 py-3 font-medium text-right">Saldo acumulado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                  {reporte.movimientos.map((mov, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{mov.fecha}</td>
                      <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900 dark:text-gray-100">
                        {mov.comprobante_consecutivo}
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        {mov.descripcion_movimiento || mov.descripcion_comprobante}
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        {mov.tercero ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-gray-900 dark:text-gray-100">
                        {Number(mov.debito) ? "$ " + formatearMonto(mov.debito) : "—"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-gray-900 dark:text-gray-100">
                        {Number(mov.credito) ? "$ " + formatearMonto(mov.credito) : "—"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-gray-900 dark:text-gray-100">
                        $ {formatearMonto(mov.saldo_acumulado)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-gray-200 bg-gray-50 font-bold dark:border-gray-800 dark:bg-gray-800">
                    <td colSpan={4} className="px-4 py-3 text-right text-gray-900 dark:text-gray-100">
                      Totales:
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-900 dark:text-gray-100">
                      $ {formatearMonto(reporte.total_debito)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-900 dark:text-gray-100">
                      $ {formatearMonto(reporte.total_credito)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-900 dark:text-gray-100">
                      $ {formatearMonto(reporte.saldo_final)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </>
      )}

      {!reporte && !loading && (
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
            Selecciona una empresa y un código de cuenta para consultar el libro mayor.
          </p>
        </div>
      )}
    </div>
  );
}
