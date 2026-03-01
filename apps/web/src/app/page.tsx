import Link from "next/link"
import {
  BarChart3,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Code2,
  CheckCircle2,
} from "lucide-react"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <header className="sticky top-0 z-50 border-b border-slate-100 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600">
              <BarChart3 className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-semibold text-slate-900">
              Radar Trabalhista
            </span>
          </div>
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="#features"
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Funcionalidades
            </Link>
            <Link
              href="#pricing"
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Planos
            </Link>
            <Link
              href="/docs"
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              API Docs
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Entrar
            </Link>
            <Link
              href="/dashboard"
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 transition-colors"
            >
              Ver Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden bg-white">
        {/* Grid pattern background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#f1f5f9_1px,transparent_1px),linear-gradient(to_bottom,#f1f5f9_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_110%)]" />

        <div className="relative mx-auto max-w-5xl px-6 py-24 text-center sm:py-32">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
            Dados atualizados mensalmente via CAGED
          </div>

          <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
            Inteligência do{" "}
            <span className="text-blue-600">Mercado de Trabalho</span>{" "}
            Brasileiro
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-500">
            Dados do CAGED, RAIS e CNJ integrados em uma plataforma. Monitor de
            admissões, demissões e compliance trabalhista com análise por setor,
            UF e porte de empresa.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
            >
              Acessar Dashboard
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/docs"
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Ver documentação API
            </Link>
          </div>

          {/* Social proof */}
          <p className="mt-8 text-xs text-slate-400">
            Fontes: MTE · PDET · CNJ · Receita Federal
          </p>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="bg-slate-50 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-slate-900 sm:text-3xl">
              Tudo que você precisa
            </h2>
            <p className="mt-3 text-slate-500">
              Dados governamentais processados e prontos para análise
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: TrendingUp,
                title: "Monitor CAGED",
                description:
                  "Acompanhe admissões, demissões e saldo de empregos por setor, UF e ocupação com dados mensais do CAGED.",
                features: ["Série histórica 5 anos", "Filtros por CNAE e UF", "Export CSV"],
                soon: false,
              },
              {
                icon: ShieldCheck,
                title: "Compliance Score",
                description:
                  "Avalie o risco trabalhista de CNPJs cruzando dados do CNJ, MTE, RAIS e Receita Federal.",
                features: ["Score 0-100 por CNPJ", "Alertas de risco", "Histórico de autuações"],
                soon: true,
              },
              {
                icon: Code2,
                title: "API REST",
                description:
                  "Acesso programático a todos os dados via API REST com autenticação por API key e rate limiting por plano.",
                features: ["OpenAPI / Swagger", "Plano Free disponível", "SDKs em breve"],
                soon: true,
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="relative rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
              >
                {feature.soon && (
                  <span className="absolute right-4 top-4 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                    Em breve
                  </span>
                )}
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
                  <feature.icon className="h-5 w-5 text-blue-600" />
                </div>
                <h3 className="text-base font-semibold text-slate-900">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm text-slate-500 leading-relaxed">
                  {feature.description}
                </p>
                <ul className="mt-4 space-y-1.5">
                  {feature.features.map((f) => (
                    <li
                      key={f}
                      className="flex items-center gap-2 text-xs text-slate-600"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-blue-500" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-slate-900 py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">
            Pronto para começar?
          </h2>
          <p className="mt-4 text-slate-400">
            Acesse o dashboard gratuitamente. Sem cadastro necessário para o
            Monitor CAGED.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/dashboard"
              className="rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 hover:bg-slate-100 transition-colors"
            >
              Acessar Dashboard
            </Link>
            <Link
              href="/docs"
              className="rounded-lg border border-slate-700 px-5 py-2.5 text-sm font-semibold text-slate-300 hover:border-slate-600 transition-colors"
            >
              Documentação API
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-100 bg-white py-8">
        <div className="mx-auto max-w-6xl px-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-5 w-5 items-center justify-center rounded bg-blue-600">
              <BarChart3 className="h-3 w-3 text-white" />
            </div>
            <span className="text-xs text-slate-500">
              Radar Trabalhista © 2026
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/privacy"
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              Privacidade
            </Link>
            <Link
              href="/terms"
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              Termos
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
