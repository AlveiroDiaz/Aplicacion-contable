import { useState, useMemo, useRef, useEffect, useCallback } from "react";
import { Movimiento } from "../hooks/useComprobante";
import { PlanCuenta } from "../services/planCuentaService";
import { Tercero } from "../services/terceroService";

interface Props {
  movimiento: Movimiento;
  onEliminar: (id: string) => void;
  onActualizar: (id: string, campo: keyof Movimiento, valor: string | number | null) => void;
  deshabilitarEliminar: boolean;
  cuentas?: PlanCuenta[];
  terceros?: Tercero[];
  deshabilitarCampos?: boolean;
}

// El backend (Numeric(20,2) + Field(decimal_places=2)) rechaza más de dos
// decimales al contabilizar; se redondea aquí también para no dejar que el
// usuario escriba un valor que de todos modos se va a rechazar más tarde.
const redondearA2Decimales = (valor: number) => Math.round(valor * 100) / 100;

const inputBase =
  "h-10 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition-all duration-200 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20";

export function LineaContable({ movimiento, onEliminar, onActualizar, deshabilitarEliminar, cuentas = [], terceros = [], deshabilitarCampos = false }: Props) {
  const [abierto, setAbierto] = useState(false);
  const [cuentaSeleccionada, setCuentaSeleccionada] = useState<PlanCuenta | null>(null);
  const [indiceActivo, setIndiceActivo] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const listaRef = useRef<HTMLDivElement>(null);

  const coincidencias = useMemo(() => {
    const q = movimiento.cuenta_codigo.trim().toLowerCase();
    if (!q) return [];
    return cuentas
      .filter((c) => c.codigo.toLowerCase().includes(q) || c.nombre.toLowerCase().includes(q))
      .slice(0, 8);
  }, [movimiento.cuenta_codigo, cuentas]);

  useEffect(() => {
    setIndiceActivo(0);
  }, [movimiento.cuenta_codigo]);

  useEffect(() => {
    const match = cuentas.find((c) => c.codigo === movimiento.cuenta_codigo);
    setCuentaSeleccionada(match || null);
  }, [movimiento.cuenta_codigo, cuentas]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setAbierto(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (abierto && listaRef.current && coincidencias[indiceActivo]) {
      const items = listaRef.current.querySelectorAll("[data-codigo]");
      if (items[indiceActivo]) {
        items[indiceActivo].scrollIntoView({ block: "center" });
      }
    }
  }, [indiceActivo, abierto, coincidencias]);

  const seleccionar = useCallback((cuenta: PlanCuenta) => {
    onActualizar(movimiento.id, "cuenta_codigo", cuenta.codigo);
    setAbierto(false);
  }, [movimiento.id, onActualizar]);

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

  return (
    <div className="flex items-center gap-3 rounded-xl border border-gray-100 bg-white px-4 py-3 shadow-sm transition hover:border-blue-200 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-900/60">
      <div ref={wrapperRef} className="relative min-w-[240px] flex-1">
        <input
          type="text"
          placeholder="Buscar cuenta..."
          value={movimiento.cuenta_codigo}
          onChange={(e) => {
            if (!deshabilitarCampos) {
              onActualizar(movimiento.id, "cuenta_codigo", e.target.value);
              setAbierto(true);
              setCuentaSeleccionada(null);
            }
          }}
          onFocus={() => !deshabilitarCampos && setAbierto(true)}
          onKeyDown={handleKeyDown}
          disabled={deshabilitarCampos}
          className={`${inputBase} w-full pr-9 ${deshabilitarCampos ? 'opacity-70 cursor-not-allowed' : ''}`}
        />
        <span className="pointer-events-none absolute inset-y-0 right-2 flex items-center text-gray-400">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </span>
        {abierto && (
          <div
            ref={listaRef}
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
                    data-codigo={c.codigo}
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
        {cuentaSeleccionada && !abierto && (
          <p className="mt-1 truncate text-xs text-gray-500 dark:text-gray-400">
            {cuentaSeleccionada.nombre}
          </p>
        )}
      </div>

      <select
        value={movimiento.tercero_id ?? ""}
        onChange={(e) => !deshabilitarCampos && onActualizar(movimiento.id, "tercero_id", e.target.value || null)}
        disabled={deshabilitarCampos}
        className={`${inputBase} w-44 ${deshabilitarCampos ? 'opacity-70 cursor-not-allowed' : ''}`}
      >
        <option value="">Sin tercero</option>
        {terceros.map((t) => (
          <option key={t.id} value={t.id}>
            {t.num_doc ? `${t.num_doc} · ${t.nombre}` : t.nombre}
          </option>
        ))}
      </select>

      <div className="relative w-32">
        <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-xs font-medium text-gray-500 dark:text-gray-400">$</span>
        <input
          type="number"
          placeholder="Débito"
          min="0"
          step="0.01"
          value={movimiento.debito || ""}
          onChange={(e) => {
            if (!deshabilitarCampos) {
              const val = redondearA2Decimales(Math.max(0, Number(e.target.value)));
              onActualizar(movimiento.id, "debito", val);
            }
          }}
          disabled={deshabilitarCampos}
          className={`${inputBase} w-full pl-7 text-right ${deshabilitarCampos ? 'opacity-70 cursor-not-allowed' : ''}`}
        />
      </div>

      <div className="relative w-32">
        <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-xs font-medium text-gray-500 dark:text-gray-400">$</span>
        <input
          type="number"
          placeholder="Crédito"
          min="0"
          step="0.01"
          value={movimiento.credito || ""}
          onChange={(e) => {
            if (!deshabilitarCampos) {
              const val = redondearA2Decimales(Math.max(0, Number(e.target.value)));
              onActualizar(movimiento.id, "credito", val);
            }
          }}
          disabled={deshabilitarCampos}
          className={`${inputBase} w-full pl-7 text-right ${deshabilitarCampos ? 'opacity-70 cursor-not-allowed' : ''}`}
        />
      </div>

      <input
        type="text"
        placeholder="Descripción"
        value={movimiento.descripcion}
        onChange={(e) => !deshabilitarCampos && onActualizar(movimiento.id, "descripcion", e.target.value)}
        disabled={deshabilitarCampos}
        className={`${inputBase} flex-1 min-w-[200px] ${deshabilitarCampos ? 'opacity-70 cursor-not-allowed' : ''}`}
      />

      <button
        onClick={() => !deshabilitarCampos && onEliminar(movimiento.id)}
        disabled={deshabilitarEliminar || deshabilitarCampos}
        title="Eliminar línea"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-gray-400 transition-all duration-200 hover:rounded-xl hover:bg-red-50 hover:text-red-600 disabled:opacity-30 disabled:hover:rounded-lg disabled:hover:bg-transparent disabled:hover:text-gray-400 dark:hover:bg-red-950 dark:hover:text-red-400"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4.5 w-4.5">
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          <line x1="10" y1="11" x2="10" y2="17" />
          <line x1="14" y1="11" x2="14" y2="17" />
        </svg>
      </button>
    </div>
  );
}
