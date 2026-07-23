import { useState, useEffect } from "react";
import { Empresa, EmpresaService } from "../services/empresaService";
import { PlanCuenta, PlanCuentaCreate, PlanCuentaUpdate, PlanCuentaService } from "../services/planCuentaService";
import { AlertService } from "../services/alertService";

export function usePlanCuentas() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [empresaId, setEmpresaId] = useState("");
  const [cuentas, setCuentas] = useState<PlanCuenta[]>([]);
  const [loading, setLoading] = useState(false);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [cuentaEditar, setCuentaEditar] = useState<PlanCuenta | null>(null);

  const [form, setForm] = useState<PlanCuentaCreate>({
    codigo: "",
    empresa_id: "",
    nombre: "",
    naturaleza: "DEBITO",
    activa: true,
    parent_codigo: "",
  });

  useEffect(() => {
    EmpresaService.obtenerTodas()
      .then((data) => {
        setEmpresas(data);
        if (data.length > 0) setEmpresaId(data[0].id);
      })
      .catch(() => AlertService.error("No se pudieron cargar las empresas"));
  }, []);

  useEffect(() => {
    if (!empresaId) return;
    cargarCuentas();
  }, [empresaId]);

  const cargarCuentas = async () => {
    setLoading(true);
    try {
      const data = await PlanCuentaService.obtenerPorEmpresa(empresaId);
      setCuentas(data);
    } catch (error: any) {
      AlertService.error(error.message || "Error al cargar cuentas");
    } finally {
      setLoading(false);
    }
  };

  const abrirNuevo = () => {
    setCuentaEditar(null);
    setForm({
      codigo: "",
      empresa_id: empresaId,
      nombre: "",
      naturaleza: "DEBITO",
      activa: true,
      parent_codigo: "",
    });
    setMostrarFormulario(true);
  };

  const abrirEditar = (cuenta: PlanCuenta) => {
    setCuentaEditar(cuenta);
    setForm({
      codigo: cuenta.codigo,
      empresa_id: cuenta.empresa_id,
      nombre: cuenta.nombre,
      naturaleza: cuenta.naturaleza as "DEBITO" | "CREDITO",
      activa: cuenta.activa,
      parent_codigo: cuenta.parent_codigo || "",
    });
    setMostrarFormulario(true);
  };

  const guardar = async () => {
    try {
      if (!form.codigo || !form.nombre) {
        AlertService.error("Código y nombre son requeridos.");
        return;
      }

      if (cuentaEditar) {
        const payload: PlanCuentaUpdate = {
          nombre: form.nombre,
          naturaleza: form.naturaleza,
          activa: form.activa,
          parent_codigo: form.parent_codigo || undefined,
        };
        await PlanCuentaService.actualizar(empresaId, form.codigo, payload);
        AlertService.success("Cuenta actualizada correctamente");
      } else {
        await PlanCuentaService.crear({
          ...form,
          empresa_id: empresaId,
          parent_codigo: form.parent_codigo || undefined,
        });
        AlertService.success("Cuenta creada correctamente");
      }

      setMostrarFormulario(false);
      cargarCuentas();
    } catch (error: any) {
      AlertService.error(error.message || "Error al guardar la cuenta");
    }
  };

  const desactivar = async (codigo: string) => {
    try {
      await PlanCuentaService.desactivar(empresaId, codigo);
      AlertService.success("Cuenta desactivada correctamente");
      cargarCuentas();
    } catch (error: any) {
      AlertService.error(error.message || "Error al desactivar la cuenta");
    }
  };

  const cerrarFormulario = () => {
    setMostrarFormulario(false);
    setCuentaEditar(null);
  };

  const updateForm = (field: keyof PlanCuentaCreate, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return {
    empresas,
    empresaId,
    setEmpresaId,
    cuentas,
    loading,
    mostrarFormulario,
    cuentaEditar,
    form,
    updateForm,
    abrirNuevo,
    abrirEditar,
    guardar,
    desactivar,
    cerrarFormulario,
  };
}
