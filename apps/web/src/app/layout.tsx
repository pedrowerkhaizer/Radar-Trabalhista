import type { Metadata } from "next"
import "./globals.css"
import { Providers } from "./providers"

export const metadata: Metadata = {
  title: { default: "Radar Trabalhista", template: "%s | Radar Trabalhista" },
  description: "Inteligência do Mercado de Trabalho Brasileiro — dados CAGED, compliance e turnover",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
