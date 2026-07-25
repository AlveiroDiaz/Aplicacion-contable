"""
Escenario 6: dos solicitudes contabilizando al mismo tiempo sobre el mismo
período no deben producir consecutivos duplicados.

Esta prueba necesita dos conexiones/transacciones REALES corriendo en
paralelo (dos hilos, cada uno con su propia Session), así que no puede vivir
dentro de la transacción con SAVEPOINT que usan los demás tests (esa
transacción usa una única conexión y serializaría todo de forma artificial,
sin probar nada). Por eso monta y limpia sus propios datos directamente
contra la base de pruebas.

`contabilizar_comprobante` bloquea la fila del período con
SELECT ... FOR UPDATE antes de calcular el consecutivo; esta prueba es la
verificación de que ese bloqueo realmente serializa a los dos hilos.
"""
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.models.comprobante import Comprobante, MovimientoContable
from app.models.cuenta import PlanCuentas
from app.models.empresa import Empresa
from app.models.periodo import PeriodoContable
from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate
from app.services.comprobante_service import contabilizar_comprobante

SessionFactory = sessionmaker(bind=engine)


@pytest.fixture()
def datos_compartidos():
    session = SessionFactory()
    empresa = Empresa(nit="900999888", dv="1", razon_social="Empresa Concurrencia", activa=True)
    session.add(empresa)
    session.flush()
    periodo = PeriodoContable(empresa_id=empresa.id, anio=2025, mes=6, cerrado=False)
    cuenta_debito = PlanCuentas(codigo="CD-1", empresa_id=empresa.id, nombre="Debito test", naturaleza="DEBITO", activa=True)
    cuenta_credito = PlanCuentas(codigo="CC-1", empresa_id=empresa.id, nombre="Credito test", naturaleza="CREDITO", activa=True)
    session.add_all([periodo, cuenta_debito, cuenta_credito])
    session.commit()

    ids = {"empresa_id": empresa.id, "periodo_id": periodo.id}
    session.close()

    yield ids

    cleanup = SessionFactory()
    comprobante_ids = [
        c.id for c in cleanup.query(Comprobante.id).filter(Comprobante.periodo_id == ids["periodo_id"])
    ]
    if comprobante_ids:
        cleanup.query(MovimientoContable).filter(MovimientoContable.comprobante_id.in_(comprobante_ids)).delete(synchronize_session=False)
        cleanup.query(Comprobante).filter(Comprobante.id.in_(comprobante_ids)).delete(synchronize_session=False)
    cleanup.query(PeriodoContable).filter(PeriodoContable.id == ids["periodo_id"]).delete(synchronize_session=False)
    cleanup.query(PlanCuentas).filter(PlanCuentas.empresa_id == ids["empresa_id"]).delete(synchronize_session=False)
    cleanup.query(Empresa).filter(Empresa.id == ids["empresa_id"]).delete(synchronize_session=False)
    cleanup.commit()
    cleanup.close()


def _contabilizar_en_hilo(empresa_id, indice, resultados):
    session = SessionFactory()
    try:
        comprobante_in = ComprobanteCreate(
            empresa_id=empresa_id,
            fecha="2025-06-10",
            descripcion=f"Comprobante concurrente {indice}",
            movimientos=[
                MovimientoCreate(cuenta_codigo="CD-1", debito=Decimal("1000"), credito=Decimal("0")),
                MovimientoCreate(cuenta_codigo="CC-1", debito=Decimal("0"), credito=Decimal("1000")),
            ],
        )
        comprobante = contabilizar_comprobante(session, comprobante_in)
        session.commit()
        resultados[indice] = comprobante.consecutivo
    except Exception as exc:  # se reporta en el test principal, no aquí
        session.rollback()
        resultados[indice] = exc
    finally:
        session.close()


def test_dos_contabilizaciones_concurrentes_no_generan_consecutivos_duplicados(datos_compartidos):
    import threading

    resultados = [None, None]
    hilos = [
        threading.Thread(target=_contabilizar_en_hilo, args=(datos_compartidos["empresa_id"], i, resultados))
        for i in range(2)
    ]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    for resultado in resultados:
        assert not isinstance(resultado, Exception), f"Una contabilización concurrente falló: {resultado}"

    assert resultados[0] != resultados[1]
    assert set(resultados) == {"COMP-202506-00001", "COMP-202506-00002"}
