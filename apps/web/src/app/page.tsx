import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, ShieldCheck, Code2, ArrowRight } from "lucide-react"
import Link from "next/link"

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Radar Trabalhista</h1>
          <Link href="/dashboard">
            <Button size="sm">Ver Dashboard</Button>
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h2 className="text-4xl font-bold tracking-tight mb-4">
          Inteligência do Mercado de Trabalho Brasileiro
        </h2>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
          Dados do CAGED, RAIS e CNJ integrados em um só lugar.
          Monitor de admissões, demissões e compliance trabalhista em tempo real.
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link href="/dashboard">
            <Button size="lg">
              Acessar Dashboard <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Button variant="outline" size="lg">Ver documentação da API</Button>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 pb-20">
        <div className="grid md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <BarChart3 className="h-8 w-8 text-primary mb-2" aria-hidden="true" />
              <CardTitle>Monitor de Mercado</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground">
              Acompanhe admissões, demissões e saldo de empregos por setor, UF e ocupação com dados mensais do CAGED.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <ShieldCheck className="h-8 w-8 text-primary mb-2" aria-hidden="true" />
              <CardTitle>Score de Compliance</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground">
              Avalie o risco trabalhista de CNPJs cruzando dados do CNJ, MTE, RAIS e Receita Federal. Em breve.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Code2 className="h-8 w-8 text-primary mb-2" aria-hidden="true" />
              <CardTitle>API Pública</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground">
              Acesso programático a todos os dados via API REST com autenticação por API key. Plano Free disponível.
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}
