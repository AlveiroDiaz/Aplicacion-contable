import { useState, useEffect, useCallback } from "react";
import { Empresa, EmpresaService } from "../services/empresaService";
import { PlanCuenta, PlanCuentaService } from "../services/planCuentaService";
import { Tercero, TerceroService } from "../services/terceroService";
import { AlertService } from "../services/alertService";

export interface Movimiento {
  id: string;
  cuenta_codigo: string;
  tercero_id: string | null;
  debito: number;
  credito: number;
  descripcion: string;
}

export function useComprobante() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [empresaId, setEmpresaId] = useState("");
  const [fecha, setFecha] = useState("2026-07-22");
  const [descripcion, setDescripcion] = useState("Registro contable inicial");
  const [movimientos, setMovimientos] = useState<Movimiento[]>([
    { id: "1", cuenta_codigo: "", tercero_id: null, debito: 0, credito: 0, descripcion: "" },
    { id: "2", cuenta_codigo: "", tercero_id: null, debito: 0, credito: 0, descripcion: "" },
  ]);
  const [cuentas, setCuentas] = useState<PlanCuenta[]>([]);
  const [terceros, setTerceros] = useState<Tercero[]>([]);

  useEffect(() => {
    const cargarEmpresas = async () => {
      try {
        const data = await EmpresaService.obtenerTodas();
        setEmpresas(data);
        if (data.length > 0) setEmpresaId(data[0].id);
      } catch {
        AlertService.error("No se pudieron cargar las empresas");
      }
    };
    cargarEmpresas();
  }, []);

  useEffect(() => {
    const cargarTerceros = async () => {
      try {
        const data = await TerceroService.listar();
        setTerceros(data);
      } catch {
        AlertService.error("No se pudieron cargar los terceros");
      }
    };
    cargarTerceros();
  }, []);

  useEffect(() => {
    if (!empresaId) return;
    const cargarCuentas = async () => {
      try {
        const data = await PlanCuentaService.obtenerPorEmpresa(empresaId);
        setCuentas(data);
      } catch {
        AlertService.error("No se pudieron cargar las cuentas");
      }
    };
    cargarCuentas();
  }, [empresaId]);

  const totalDebito = movimientos.reduce((sum, mov) => sum + Number(mov.debito), 0);
  const totalCredito = movimientos.reduce((sum, mov) => sum + Number(mov.credito), 0);
  const diferencia = totalDebito - totalCredito;
  const esValido = diferencia === 0 && totalDebito > 0;

  const generarId = () => Math.random().toString(36).slice(2, 9);

  const agregarLinea = useCallback(() => {
    setMovimientos((prev) => [
      ...prev,
      { id: generarId(), cuenta_codigo: "", tercero_id: null, debito: 0, credito: 0, descripcion: "" },
    ]);
  }, []);

  const eliminarLinea = useCallback((id: string) => {
    setMovimientos((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const actualizarLinea = useCallback((id: string, campo: keyof Movimiento, valor: string | number | null) => {
    setMovimientos((prev) =>
      prev.map((mov) => {
        if (mov.id !== id) return mov;

        if (campo === "debito" && Number(valor) > 0) {
          return { ...mov, debito: Number(valor), credito: 0 };
        }

        if (campo === "credito" && Number(valor) > 0) {
          return { ...mov, credito: Number(valor), debito: 0 };
        }

        if (campo === "debito" && Number(valor) === 0) {
          return { ...mov, debito: 0 };
        }

        if (campo === "credito" && Number(valor) === 0) {
          return { ...mov, credito: 0 };
        }

        return { ...mov, [campo]: valor };
      })
    );
  }, []);

  return {
    empresas, empresaId, setEmpresaId,
    fecha, setFecha,
    descripcion, setDescripcion,
    movimientos, setMovimientos, agregarLinea, eliminarLinea, actualizarLinea, cuentas, terceros,
    totalDebito, totalCredito, diferencia, esValido
  };
}
