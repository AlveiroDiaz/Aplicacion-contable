"use client";

import { usePlanCuentas } from "../../hooks/usePlanCuentas";
import { AlertService } from "../../services/alertService";

export default function PlanCuentasPage() {
  const plan = usePlanCuentas();

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Plan de Cuentas</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Administra las cuentas contables por empresa.
          </p>
        </div>
        <button
          onClick={plan.abrirNuevo}
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Nueva Cuenta
        </button>
      </div>

      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Empresa</h2>
        <div className="flex flex-col">
          <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Seleccione una empresa</label>
          <select
            value={plan.empresaId}
            onChange={(e) => plan.setEmpresaId(e.target.value)}
            className="w-full max-w-md rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
          >
            <option value="" disabled>Seleccione...</option>
            {plan.empresas.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.razon_social}
              </option>
            ))}
          </select>
        </div>
      </div>

      {plan.mostrarFormulario && (
        <div className="mb-6 rounded-2xl border border-blue-200 bg-blue-50/50 p-6 shadow-sm dark:border-blue-900 dark:bg-blue-950/30">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            {plan.cuentaEditar ? "Editar Cuenta" : "Nueva Cuenta"}
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="flex flex-col">
              <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Código</label>
              <input
                type="text"
                value={plan.form.codigo}
                onChange={(e) => plan.updateForm("codigo", e.target.value)}
                disabled={!!plan.cuentaEditar}
                placeholder="Ej. 110505"
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20 disabled:opacity-60"
              />
            </div>

            <div className="flex flex-col md:col-span-2">
              <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Nombre</label>
              <input
                type="text"
                value={plan.form.nombre}
                onChange={(e) => plan.updateForm("nombre", e.target.value)}
                placeholder="Ej. Caja General"
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
              />
            </div>

            <div className="flex flex-col">
              <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Naturaleza</label>
              <select
                value={plan.form.naturaleza}
                onChange={(e) => plan.updateForm("naturaleza", e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
              >
                <option value="DEBITO">Débito</option>
                <option value="CREDITO">Crédito</option>
              </select>
            </div>

            <div className="flex flex-col">
              <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Cuenta Padre</label>
              <select
                value={plan.form.parent_codigo}
                onChange={(e) => plan.updateForm("parent_codigo", e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
              >
                <option value="">Sin cuenta padre</option>
                {plan.cuentas.map((c) => (
                  <option key={c.codigo} value={c.codigo}>
                    {c.codigo} - {c.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col">
              <label className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Estado</label>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={plan.form.activa}
                  onChange={(e) => plan.updateForm("activa", e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-700"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Activa</span>
              </div>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-end gap-3">
            <button
              onClick={plan.cerrarFormulario}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Cancelar
            </button>
            <button
              onClick={plan.guardar}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              {plan.cuentaEditar ? "Guardar Cambios" : "Crear Cuenta"}
            </button>
          </div>
        </div>
      )}

      <div className="rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-gray-600 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-400">
                <th className="px-4 py-3 font-medium">Código</th>
                <th className="px-4 py-3 font-medium">Nombre</th>
                <th className="px-4 py-3 font-medium">Naturaleza</th>
                <th className="px-4 py-3 font-medium">Cuenta Padre</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {plan.loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                    Cargando cuentas...
                  </td>
                </tr>
              ) : plan.cuentas.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                    No hay cuentas registradas para esta empresa.
                  </td>
                </tr>
              ) : (
                plan.cuentas.map((cuenta) => (
                  <tr key={cuenta.codigo} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900 dark:text-gray-100">
                      {cuenta.codigo}
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                      {cuenta.nombre}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          cuenta.naturaleza === "DEBITO"
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                            : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                        }`}
                      >
                        {cuenta.naturaleza === "DEBITO" ? "Débito" : "Crédito"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                      {cuenta.parent_codigo || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          cuenta.activa
                            ? "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300"
                            : "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                        }`}
                      >
                        {cuenta.activa ? "Activa" : "Inactiva"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => plan.abrirEditar(cuenta)}
                          className="rounded-lg p-1.5 text-gray-600 transition hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                          title="Editar"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => plan.desactivar(cuenta.codigo)}
                          className="rounded-lg p-1.5 text-red-600 transition hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950"
                          title="Desactivar"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                          </svg>
                        </button>
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
