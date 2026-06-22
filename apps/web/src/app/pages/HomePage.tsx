import { ArrowRight, LayoutDashboard, Shield, Sparkles, Star } from 'lucide-react';
import { Link } from 'react-router';

const features = [
  {
    icon: LayoutDashboard,
    label: 'Dashboard Operacional',
    description:
      'Visão geral das operações com métricas em tempo real, alertas e status das integrações de segurança.',
    path: '/dashboard',
  },
  {
    icon: Sparkles,
    label: 'Copiloto Técnico',
    description:
      'Suporte técnico com IA para troubleshooting, consulta de documentação e criação automática de chamados via RAG.',
    path: '/technical',
  },
  {
    icon: Shield,
    label: 'Governança de IA',
    description:
      'Relatórios de conformidade, auditoria e governança de uso responsável de IA em cibersegurança.',
    path: '/governance',
  },
];

export function HomePage() {
  return (
    <div className="flex min-h-full flex-col bg-background">
      {/* Hero */}
      <section
        className="relative overflow-hidden px-12 py-24 text-center"
        style={{
          background:
            'linear-gradient(135deg, #13141a 0%, #13141a 40%, #0c1e36 80%, #0c2444 100%)',
        }}
      >
        {/* Glow decoration */}
        <div
          className="pointer-events-none absolute -right-32 -top-32 h-[500px] w-[500px] rounded-full opacity-30"
          style={{
            background: 'radial-gradient(circle, #0ea5e960 0%, transparent 70%)',
          }}
        />

        <div className="relative">
          {/* Badge */}
          <div className="mb-8 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm">
            <Star className="h-3 w-3 fill-white" />
            <span>NeoIA Security &nbsp;•&nbsp; Plataforma de IA para Cibersegurança</span>
          </div>

          {/* Headline */}
          <h1 className="mx-auto mb-5 max-w-2xl text-5xl font-extrabold leading-tight tracking-tight text-foreground">
            Centro de Operações de
            <br />
            Segurança com IA
          </h1>

          {/* Subtitle */}
          <p className="mx-auto mb-5 max-w-lg text-base leading-7 text-muted-foreground">
            Plataforma unificada de IA para operações e governança em cibersegurança
          </p>

          {/* Stats */}
          <p className="mb-10 text-sm text-foreground/70">
            <span className="font-bold text-foreground">1.247+</span> Eventos Processados
            &nbsp;&nbsp;
            <span className="font-bold text-foreground">99,8%</span> Disponibilidade
            &nbsp;&nbsp;
            <span className="font-bold text-foreground">4</span> Integrações Ativas
          </p>

          {/* CTA */}
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-7 py-3 text-sm font-semibold text-white shadow transition-colors hover:bg-primary/90"
          >
            Acessar Dashboard
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="flex-1 px-12 py-16">
        <div className="mb-10 text-center">
          <h2 className="mb-2 text-2xl font-bold text-foreground">
            Principais Funcionalidades
          </h2>
          <p className="mx-auto max-w-md text-sm leading-6 text-muted-foreground">
            Ferramentas de IA integradas para operações e governança em cibersegurança
          </p>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {features.map((feature) => (
            <div
              key={feature.path}
              className="flex flex-col rounded-xl border border-border bg-card p-6 shadow-sm"
            >
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <feature.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mb-2 text-sm font-bold text-foreground">{feature.label}</h3>
              <p className="mb-5 flex-1 text-xs leading-6 text-muted-foreground">
                {feature.description}
              </p>
              <Link
                to={feature.path}
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
              >
                Acessar <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
