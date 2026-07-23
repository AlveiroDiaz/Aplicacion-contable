export default function Home() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center p-6 text-center">
      <div className="max-w-3xl rounded-2xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Motor Contable</h1>
          <p className="mt-2 text-lg font-semibold text-blue-600 dark:text-blue-400">Prueba técnica</p>
        </header>
        <main>
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Qué hace esta plataforma</h2>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Esta aplicación es una solución contable para gestionar empresas, registrar asientos y administrar el plan de cuentas desde una interfaz moderna.
          </p>
          <ul className="mt-4 space-y-3 text-left text-gray-600 dark:text-gray-400 sm:text-base">
            <li>• Registro y consulta de comprobantes contables.</li>
            <li>• Gestión de plan de cuentas.</li>
            <li>• Cierre de periodos y generación de reportes financieros.</li>
          </ul>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Backend: FastAPI + PostgreSQL. Frontend: Next.js + TypeScript.
          </p>
        </main>
        <footer className="mt-8">
          <p className="text-sm text-gray-500 dark:text-gray-500">
            Esta página inicial es una presentación de la prueba técnica. Navega por las secciones desde el menú lateral en las páginas internas.
          </p>
        </footer>
      </div>
    </div>
  );
}
