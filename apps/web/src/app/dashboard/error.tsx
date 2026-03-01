"use client"
import { Button } from "@/components/ui/button"

export default function DashboardError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="container mx-auto px-4 py-20 text-center">
      <h2 className="text-xl font-semibold mb-2">Erro ao carregar dashboard</h2>
      <p className="text-muted-foreground mb-4">{error.message}</p>
      <Button onClick={reset} aria-label="Tentar carregar o dashboard novamente">
        Tentar novamente
      </Button>
    </div>
  )
}
