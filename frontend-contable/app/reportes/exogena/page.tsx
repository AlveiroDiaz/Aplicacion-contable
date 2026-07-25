"use client";

import { useEffect, useMemo, useState } from "react";
import { Empresa, EmpresaService } from "../../../services/empresaService";
import { ExogenaService, ExogenaGeneratePayload, ExogenaHistoryItem } from "../../../services/exogenaService";
import { AlertService } from "../../../services/alertService";

export default function ExogenaPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [empresaId, setEmpresaId] = useState("");
  const [anioGravable, setAnioGravable] = useState(new Date().getFullYear());
  const [umbralUVT, setUmbralUVT] = useState(42);
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [loading, setLoading] = useState(false);
  const [historial, setHistorial] = useState<ExogenaHistoryItem[]>([]);

  useEffect(() => {
    EmpresaService.obtenerTodas()
      .then((data) => {
        setEmpresas(data);
        if (data.length > 0) setEmpresaId(data[0].id);
      })
      .catch(() => AlertService.error("Error al cargar las empresas"));

    ExogenaService.obtenerHistorial()
      .then(setHistorial)
      .catch(() => AlertService.error("Error al cargar el historial de exógena"));
  }, []);

  const descargarXml = async (payload: ExogenaGeneratePayload) => {
    setLoading(true);
    try {
      const { blob, filename } = await ExogenaService.generar(payload);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      window.URL.revokeObjectURL(url);
      AlertService.success("XML generado correctamente.");
    } catch (error: any) {
      AlertService.error(error.message || "Error al generar el XML de exógena.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!empresaId) {
      AlertService.error("Selecciona una empresa primero.");
      return;
    }

    await descargarXml({
      empresa_id: empresaId,
      anio_gravable: Number(anioGravable),
      umbral_uvt: Number(umbralUVT),
      fecha_inicio: fechaInicio || undefined,
      fecha_fin: fechaFin || undefined,
    });
  };

  const fechaActual = new Date().getFullYear();
  const anios = Array.from({ length: 10 }, (_, index) => fechaActual - index);

  const historialOrdenado = useMemo(
    () => [...historial].sort((a, b) => new Date(b.fecha_generacion).getTime() - new Date(a.fecha_generacion).getTime()),
    [historial]
  );

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Exógena</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Genera el archivo XML de exógena y revisa las generaciones anteriores.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Generar XML</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="flex flex-col text-sm font-medium text-gray-700 dark:text-gray-300">
                Empresa
                <select
                  value={empresaId}
                  onChange={(e) => setEmpresaId(e.target.value)}
                  className="mt-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                >
                  {empresas.map((empresa) => (
                    <option key={empresa.id} value={empresa.id}>
                      {empresa.razon_social}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col text-sm font-medium text-gray-700 dark:text-gray-300">
                Año gravable
                <select
                  value={anioGravable}
                  onChange={(e) => setAnioGravable(Number(e.target.value))}
                  className="mt-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                >
                  {anios.map((anio) => (
                    <option key={anio} value={anio}>
                      {anio}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="flex flex-col text-sm font-medium text-gray-700 dark:text-gray-300">
                Umbral en UVT
                <input
                  type="number"
                  min={1}
                  value={umbralUVT}
                  onChange={(e) => setUmbralUVT(Number(e.target.value))}
                  className="mt-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="flex flex-col text-sm font-medium text-gray-700 dark:text-gray-300">
                  Fecha inicio
                  <input
                    type="date"
                    value={fechaInicio}
                    onChange={(e) => setFechaInicio(e.target.value)}
                    className="mt-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  />
                </label>

                <label className="flex flex-col text-sm font-medium text-gray-700 dark:text-gray-300">
                  Fecha fin
                  <input
                    type="date"
                    value={fechaFin}
                    onChange={(e) => setFechaFin(e.target.value)}
                    className="mt-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  />
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
            >
              {loading ? "Generando..." : "Generar XML de exógena"}
            </button>
          </form>
        </section>

        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Historial de generaciones</h2>
          {historialOrdenado.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">No hay generación de exógena registrada todavía.</p>
          ) : (
            <div className="space-y-3">
              {historialOrdenado.map((item) => (
                <div key={item.id} className="rounded-2xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-950">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">Año {item.anio_gravable}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Generado el {new Date(item.fecha_generacion).toLocaleDateString()}</p>
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-300">
                      {item.registros} registros · {item.total_retencion.toLocaleString("es-CO")} COP
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
