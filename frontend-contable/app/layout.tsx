import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AlertProvider } from "@/components/AlertProvider";
import { LayoutShell } from "@/components/LayoutShell";

import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Motor Contable",
  description: "Prueba técnica",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <LayoutShell>{children}</LayoutShell>
        <AlertProvider />
      </body>
    </html>
  );
}
