"use client";

import { useState, useEffect } from "react";
import { ComprobanteService, ComprobanteResponse, ComprobanteReverseResponse } from "../../../services/comprobanteService";
import { Empresa, EmpresaService } from "../../../services/empresaService";
import { AlertService } from "../../../services/alertService";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function ListaComprobantesPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [empresaId, setEmpresaId] = useState("");
  const [comprobantes, setComprobantes] = useState<ComprobanteResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [revertingId, setRevertingId] = useState<string | null>(null);
  const [searchConsecutivo, setSearchConsecutivo] = useState("");
  const router = useRouter();

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
    ComprobanteService.listar(empresaId)
      .then((data) => setComprobantes(data))
      .catch(() => AlertService.error("Error al cargar los comprobantes"))
      .finally(() => setLoading(false));
  }, [empresaId]);

  const buscar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!empresaId) {
      AlertService.error("Selecciona una empresa primero.");
      return;
    }
    setLoading(true);
    try {
      const data = await ComprobanteService.listar(empresaId, searchConsecutivo || undefined);
      setComprobantes(data);
    } catch {
      AlertService.error("Error al buscar comprobantes");
    } finally {
      setLoading(false);
    }
  };

  const revertir = async (comprobante: ComprobanteResponse) => {
    const confirmacion = window.confirm(
      `¿Estás seguro de revertir el comprobante ${comprobante.consecutivo}?\n\nSe generará un nuevo comprobante inverso en el mismo período.`
    );
    if (!confirmacion) return;

    setRevertingId(comprobante.id);
    try {
      const resultado: ComprobanteReverseResponse = await ComprobanteService.revertir(comprobante.id);
      AlertService.success(
        `Reversión exitosa. Nuevo comprobante: ${resultado.comprobante_nuevo_consecutivo}`
      );
      setComprobantes((prev) =>
        prev.map((c) => (c.id === comprobante.id ? { ...c, revertido: true } : c))
      );
    } catch (error: any) {
      AlertService.error(error.message || "Error al revertir el comprobante");
    } finally {
      setRevertingId(null);
    }
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString("es-CO", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Comprobantes Contables</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Consulta, busca y revierte comprobantes por empresa.
          </p>
        </div>
        <Link
          href="/comprobantes/nuevo"
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Nuevo Comprobante
        </Link>
      </div>

      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Filtros</h2>
        <form onSubmit={buscar} className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
            <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Buscar por consecutivo</label>
            <input
              type="text"
              value={searchConsecutivo}
              onChange={(e) => setSearchConsecutivo(e.target.value)}
              placeholder="Ej. COMP-202601-00001"
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 md:w-auto"
            >
              {loading ? "Buscando..." : "Buscar"}
            </button>
          </div>
        </form>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-gray-600 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-400">
                <th className="px-4 py-3 font-medium">Consecutivo</th>
                <th className="px-4 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium">Descripción</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium">Revertido</th>
                <th className="px-4 py-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                    Cargando comprobantes...
                  </td>
                </tr>
              ) : comprobantes.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                    No hay comprobantes para esta empresa.
                  </td>
                </tr>
              ) : (
                comprobantes.map((comp) => (
                  <tr key={comp.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900 dark:text-gray-100">
                      {comp.consecutivo || <span className="italic text-gray-400 dark:text-gray-500">Sin asignar</span>}
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                      {formatearFecha(comp.fecha)}
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                      {comp.descripcion}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          comp.estado === "CONTABILIZADO"
                            ? "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300"
                            : comp.estado === "ANULADO"
                            ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                            : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300"
                        }`}
                      >
                        {comp.estado}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          comp.revertido
                            ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                            : "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                        }`}
                      >
                        {comp.revertido ? "Sí" : "No"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => router.push(`/comprobantes/nuevo?view=${comp.id}`)}
                          className="rounded-lg p-1.5 text-gray-600 transition hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                          title={comp.estado === "BORRADOR" ? "Editar borrador" : "Ver detalle"}
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                            <circle cx="12" cy="12" r="3" />
                          </svg>
                        </button>
                        {comp.estado === "CONTABILIZADO" && !comp.revertido && (
                          <button
                            onClick={() => revertir(comp)}
                            disabled={revertingId === comp.id}
                            className="rounded-lg p-1.5 text-red-600 transition hover:bg-red-50 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-950"
                            title="Revertir comprobante"
                          >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                              <polyline points="1 4 1 10 7 10" />
                              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                            </svg>
                          </button>
                        )}
                      </div>
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
