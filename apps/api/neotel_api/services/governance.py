from __future__ import annotations

import hashlib
import ipaddress
import os
import random
from pathlib import Path
from uuid import uuid4
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from ..config import Settings
from ..schemas import GovernancePreviewResponse, GovernancePreviewRow, GovernanceReportResponse

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.graphics.shapes import Drawing, Line as ShapeLine, Rect, String
    from reportlab.platypus import (
        Image,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:  # pragma: no cover
    colors = None

_USERS = [
    "joao.silva",
    "maria.souza",
    "ana.lima",
    "carlos.ferreira",
    "patricia.costa",
    "roberto.alves",
    "fernanda.santos",
    "lucas.oliveira",
    "camila.rocha",
    "admin.ti",
    "admin.seguranca",
]

_APPLICATIONS = [
    "Office 365",
    "VPN Corporativa",
    "AWS Console",
    "Salesforce",
    "ServiceNow",
    "Portal RH",
    "Jira",
    "GitHub Enterprise",
    "SAP",
    "Zoom",
]

_AUTH_METHODS = ["OTP", "Push OTP", "FIDO2", "GrIDsure", "Password", "SAML"]
_DEVICES = ["Windows laptop", "macOS laptop", "iPhone", "Android", "VDI", "Service account"]
_LOCATIONS = ["BR-Sao Paulo", "BR-Rio de Janeiro", "BR-Curitiba", "US-Ashburn", "CL-Santiago", "NL-Amsterdam"]
_POLICIES = [
    "MFA Forte para Administradores",
    "Acesso SAML SaaS",
    "Step-up por Risco",
    "Bloqueio por Falhas Repetidas",
    "Aplicacoes Corporativas",
]
_REASONS = {
    "accepted": "Autenticacao concluida conforme politica.",
    "denied": "Politica de acesso bloqueou a tentativa.",
    "failed": "Falha no desafio de autenticacao.",
}

_RISK_SCENARIOS = {
    "unusual_location": "Localizacao incomum",
    "repeated_failures": "Falhas repetidas",
    "push_timeout": "Timeout de push MFA",
    "admin_weak_auth": "Admin com MFA fraco",
    "weak_mfa": "MFA fraco",
    "ok": "OK",
}


class GovernanceService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_preview(self, days: int, events_per_day: int) -> GovernancePreviewResponse:
        logs = self.fetch_sta_logs(days=days, events_per_day=events_per_day)
        analysis = self._analyze_logs(logs)
        recommendations = self._build_recommendations(analysis)
        privacy_issues = self._validate_privacy(logs)
        preview_rows = [
            GovernancePreviewRow(
                timestamp=log["timestamp"],
                principalId=log["user_hash"],
                applicationName=log["application"],
                accessState=self._display_status(log["status"]),
                authResult=self._display_auth_result(log["status"], log["risk_signal"]),
                riskSignal=self._display_risk(log["risk_signal"]),
                source_ip=log["source_ip"],
            )
            for log in logs[:20]
        ]
        metadata = {
            "solution": "SafeNet Trusted Access (STA)",
            "days": days,
            "total_logs": len(logs),
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
        return GovernancePreviewResponse(
            metadata=metadata,
            analysis=analysis,
            preview_rows=preview_rows,
            recommendations=recommendations,
            privacy_issues=privacy_issues,
            risk_score=analysis["risk_score"],
            events_per_day=analysis["events_per_day"],
        )

    def build_report(self, days: int, events_per_day: int) -> GovernanceReportResponse:
        preview = self.build_preview(days=days, events_per_day=events_per_day)
        top_users = ", ".join(
            f"{user} ({count})" for user, count in preview.analysis["top_failed_users"][:3]
        ) or "sem concentração relevante"
        report_markdown = (
            "# Relatório Executivo de Governança\n\n"
            f"- **Período analisado:** {preview.metadata['days']} dias\n"
            f"- **Total de eventos:** {preview.analysis['total_log_entries']}\n"
            f"- **Score de risco:** {preview.analysis['risk_score']}/100\n"
            f"- **Taxa de sucesso:** {preview.analysis['success_rate']:.1f}%\n"
            f"- **Acessos negados:** {preview.analysis['denied_access_count']} ({preview.analysis['denial_rate_pct']:.1f}%)\n"
            f"- **Usuários únicos:** {preview.analysis['unique_users_count']}\n"
            f"- **Aplicações acessadas:** {preview.analysis['unique_apps_count']}\n"
            f"- **Usuários com mais falhas:** {top_users}\n\n"
            "## Eventos por Dia\n\n"
            + "\n".join(
                f"- {date}: {count} eventos"
                for date, count in sorted(preview.analysis["events_per_day"].items())
            )
            + "\n\n## Recomendações\n\n"
            + "\n".join(
                f"- **[{item['priority']}]** {item['policy_name']} — {item['recommended_decision']}"
                for item in preview.recommendations
            )
        )
        return GovernanceReportResponse(
            metadata=preview.metadata,
            analysis=preview.analysis,
            report_markdown=report_markdown,
            recommendations=preview.recommendations,
            privacy_issues=preview.privacy_issues,
            mode="fake_sta",
        )

    def build_summary(self, days: int) -> dict:
        logs = self.fetch_sta_logs(days=days)
        analysis = self._analyze_logs(logs)
        recent_events = [
            {
                "timestamp": log["timestamp"],
                "user": log["user_hash"],
                "user_hash": log["user_hash"],
                "application": log["application"],
                "applicationName": log["application"],
                "action": log["action"],
                "event_type": log["event_type"],
                "status": log["status"],
                "accessState": self._display_status(log["status"]),
                "authResult": self._display_auth_result(log["status"], log["risk_signal"]),
                "authentication_method": log["authentication_method"],
                "risk_signal": log["risk_signal"],
                "riskSignal": self._display_risk(log["risk_signal"]),
                "source_ip": log["source_ip"],
                "location": log["location"],
                "policy_name": log["policy_name"],
                "reason": log["reason"],
                "device": log["device"],
            }
            for log in logs[:25]
        ]
        status_counts = Counter(log["status"] for log in logs)
        risk_counts = Counter(log["risk_signal"] for log in logs if log["risk_signal"] != "ok")
        summary = {
            "solution": "STA",
            "days": days,
            "total_events": analysis["total_log_entries"],
            "authentications": analysis["total_authentications"],
            "access_denied": analysis["denied_access_count"],
            "success_rate": round(analysis["success_rate"], 1),
            "risk_score": analysis["risk_score"],
            "unique_users": analysis["unique_users_count"],
            "events_by_day": [
                {"date": date, "events": count}
                for date, count in sorted(analysis["events_per_day"].items())
            ],
            "status_distribution": [
                {"status": status, "count": status_counts.get(status, 0)}
                for status in ("accepted", "denied", "failed")
            ],
            "top_risks": [
                {"risk_signal": risk, "count": count}
                for risk, count in risk_counts.most_common(6)
            ],
            "recent_events": recent_events,
            "recommendations": self._build_recommendations(analysis),
            "privacy_issues": self._validate_privacy(logs),
            "analysis": analysis,
            "preview_rows": [
                {
                    "timestamp": row["timestamp"],
                    "principalId": row["user_hash"],
                    "applicationName": row["application"],
                    "accessState": self._display_status(row["status"]),
                    "authResult": self._display_auth_result(row["status"], row["risk_signal"]),
                    "riskSignal": self._display_risk(row["risk_signal"]),
                    "source_ip": row["source_ip"],
                }
                for row in logs[:25]
            ],
            "events_per_day": analysis["events_per_day"],
        }
        return summary

    def create_pdf_report(self, solution: str, days: int) -> dict:
        if solution.upper() != "STA":
            raise ValueError("Apenas STA esta disponivel nesta simulacao.")
        logs = self.fetch_sta_logs(days=days)
        summary = self.build_summary(days)
        report_id = uuid4().hex
        filename = f"NeoIASecurity_STA_Relatorio_Executivo_{days}d.pdf"
        output_dir = self._report_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{report_id}_{filename}"
        self._write_pdf(output_path, days, summary, logs)
        return {
            "success": True,
            "report_id": report_id,
            "filename": filename,
            "download_url": f"/api/governance/reports/{report_id}/download",
            "summary": summary,
        }

    def report_path(self, report_id: str) -> Path | None:
        output_dir = self._report_output_dir()
        matches = sorted(output_dir.glob(f"{report_id}_*.pdf"))
        return matches[0] if matches else None

    def report_filename(self, report_id: str) -> str:
        path = self.report_path(report_id)
        if not path:
            return "NeoIASecurity_STA_Relatorio_Executivo.pdf"
        return path.name.replace(f"{report_id}_", "", 1)

    def debug_sta(self, days: int) -> dict:
        logs = self.fetch_sta_logs(days)
        summary = self.build_summary(days)
        return {
            "solution": "STA",
            "days": days,
            "fake_log_count": len(logs),
            "summary_metrics": {
                key: summary[key]
                for key in ("total_events", "authentications", "access_denied", "success_rate", "risk_score", "unique_users")
            },
            "output_dir": str(self._report_output_dir()),
            "privacy_mode": self.settings.governance_privacy_mode,
        }

    def fake_logs_available(self) -> bool:
        return self.settings.governance_use_fake_sta_api

    def report_generation_available(self) -> bool:
        return colors is not None

    def _report_output_dir(self) -> Path:
        return self.settings.governance_report_dir

    def fetch_sta_logs(self, days: int, events_per_day: int | None = None) -> list[dict]:
        count = events_per_day or max(35, min(90, self.settings.governance_default_log_count // max(days, 1)))
        return self._generate_fake_logs(days=days, events_per_day=count)

    def _generate_fake_logs(self, days: int, events_per_day: int) -> list[dict]:
        logs: list[dict] = []
        now = datetime.now(timezone.utc).replace(microsecond=0)
        rng = random.Random(f"sta:{days}:{events_per_day}:{now.date().isoformat()}:{self.settings.governance_hash_salt}")

        for day in range(days):
            base_dt = now - timedelta(days=day)
            for index in range(events_per_day):
                principal_id = rng.choice(_USERS)
                application_name = rng.choice(_APPLICATIONS)

                outcome = rng.choices(
                    ["accepted", "failed", "denied"],
                    weights=[74, 16, 10],
                    k=1,
                )[0]

                hour = rng.randint(0, 23)
                auth_method = rng.choice(_AUTH_METHODS)
                risk_signal = "ok"
                if principal_id.startswith("admin") and auth_method in {"Password", "GrIDsure"}:
                    risk_signal = "admin_weak_auth"
                    outcome = "denied" if rng.random() < 0.45 else outcome
                elif outcome == "denied" and rng.random() < 0.55:
                    risk_signal = "repeated_failures"
                elif outcome == "failed" and auth_method == "Push OTP":
                    risk_signal = "push_timeout"
                elif hour < 6 or hour > 22:
                    risk_signal = "unusual_location"
                elif auth_method == "Password" and rng.random() < 0.3:
                    risk_signal = "weak_mfa"
                elif rng.random() < 0.04:
                    risk_signal = "unusual_location"

                event_dt = base_dt.replace(
                    hour=hour,
                    minute=rng.randint(0, 59),
                    second=rng.randint(0, 59),
                )
                event_type = "authentication" if auth_method != "SAML" else "saml_application_access"
                logs.append(
                    {
                        "timestamp": event_dt.isoformat(),
                        "user": self._stable_hash(principal_id),
                        "user_hash": self._stable_hash(principal_id),
                        "application": application_name,
                        "action": "access_application" if event_type != "authentication" else "authenticate",
                        "event_type": event_type,
                        "status": outcome,
                        "authentication_method": auth_method,
                        "risk_signal": risk_signal,
                        "source_ip": self._mask_ip(f"10.{rng.randint(0,5)}.{rng.randint(1,254)}.{rng.randint(1,254)}"),
                        "location": rng.choice(_LOCATIONS),
                        "policy_name": rng.choice(_POLICIES),
                        "reason": _REASONS[outcome],
                        "device": rng.choice(_DEVICES),
                    }
                )

        logs.sort(key=lambda item: item["timestamp"], reverse=True)
        return logs

    def _analyze_logs(self, logs: list[dict]) -> dict:
        total = len(logs)
        denied = sum(1 for log in logs if log["status"] == "denied")
        failed = sum(1 for log in logs if log["status"] == "failed")
        successes = sum(1 for log in logs if log["status"] == "accepted")
        admin_failures = sum(
            1 for log in logs if log["risk_signal"] == "admin_weak_auth"
        )
        geo_anomalies = sum(
            1 for log in logs if log["risk_signal"] == "unusual_location"
        )
        push_timeouts = sum(1 for log in logs if log["risk_signal"] == "push_timeout")

        unique_users = len({log["user_hash"] for log in logs})
        unique_apps = len({log["application"] for log in logs})

        denial_rate = denied / total if total else 0.0
        failure_rate = failed / total if total else 0.0

        # risk_score 0-100: denial_rate and failure_rate each weighted
        risk_score = int(min(100, denial_rate * 150 + failure_rate * 90 + min(admin_failures * 2, 25) + min(push_timeouts, 15)))

        top_failed_users = Counter(
            log["user_hash"] for log in logs if log["status"] in ("denied", "failed")
        ).most_common(5)

        events_per_day: dict[str, int] = defaultdict(int)
        for log in logs:
            date = log["timestamp"][:10]
            events_per_day[date] += 1

        return {
            "total_log_entries": total,
            "total_authentications": total,
            "denied_access_count": denied,
            "failed_count": failed,
            "success_count": successes,
            "success_rate": (successes / total * 100) if total else 0.0,
            "denial_rate_pct": denial_rate * 100,
            "failure_rate_pct": failure_rate * 100,
            "risk_score": risk_score,
            "unique_users_count": unique_users,
            "unique_apps_count": unique_apps,
            "admin_weak_auth_events": admin_failures,
            "off_hours_events": geo_anomalies,
            "geo_anomaly_events": geo_anomalies,
            "push_timeout_events": push_timeouts,
            "top_failed_users": top_failed_users,
            "events_per_day": dict(sorted(events_per_day.items())),
        }

    def _build_recommendations(self, analysis: dict) -> list[dict]:
        recs = []
        if analysis["admin_weak_auth_events"] > 0:
            recs.append({
                "priority": "Alta",
                "policy_name": "Step-up para administradores",
                "scenario_or_condition": f"{analysis['admin_weak_auth_events']} eventos de admin com falha",
                "recommended_decision": "Exigir MFA forte (FIDO2 ou OTP hardware) e revisão humana imediata",
                "target": "Perfis administrativos",
            })
        if analysis["denial_rate_pct"] > 10:
            recs.append({
                "priority": "Alta",
                "policy_name": "Bloqueio progressivo",
                "scenario_or_condition": f"Taxa de negação de {analysis['denial_rate_pct']:.1f}%",
                "recommended_decision": "Aplicar política de bloqueio temporário após 3 falhas consecutivas",
                "target": "Usuários com repetição de falhas",
            })
        if analysis["push_timeout_events"] > 0:
            recs.append({
                "priority": "Média",
                "policy_name": "Revisao de Push OTP",
                "scenario_or_condition": f"{analysis['push_timeout_events']} timeouts de push MFA",
                "recommended_decision": "Investigar timeouts, fadiga de MFA e aplicar verificacao adicional para repeticoes",
                "target": "Usuarios com falhas de Push OTP",
            })
        if analysis["off_hours_events"] > 0:
            recs.append({
                "priority": "Média",
                "policy_name": "Restrição de horário",
                "scenario_or_condition": f"{analysis['off_hours_events']} acessos fora do horário comercial",
                "recommended_decision": "Revisar política de acesso e exigir step-up fora do horário",
                "target": "Acessos entre 22h-06h",
            })
        if analysis["geo_anomaly_events"] > 0:
            recs.append({
                "priority": "Média",
                "policy_name": "Detecção de anomalia geográfica",
                "scenario_or_condition": f"{analysis['geo_anomaly_events']} acessos de localização incomum",
                "recommended_decision": "Bloquear e notificar usuário afetado para confirmação",
                "target": "Acessos com geo-anomalia detectada",
            })
        if not recs:
            recs.append({
                "priority": "Baixa",
                "policy_name": "Revisão periódica",
                "scenario_or_condition": "Sem alertas críticos no período",
                "recommended_decision": "Manter monitoramento contínuo e revisar políticas mensalmente",
                "target": "Todos os usuários",
            })
        return recs

    def _validate_privacy(self, logs: list[dict]) -> list[str]:
        issues: list[str] = []
        for log in logs[:20]:
            if "." in log["user_hash"] and not log["user_hash"].startswith("user-"):
                issues.append("Usuário não pseudonimizado detectado.")
            if log["source_ip"].count(".") == 3 and "x" not in log["source_ip"]:
                issues.append("IP não mascarado detectado.")
                break
            if "session_id" in log or "tenant_id" in log or "account_id" in log:
                issues.append("Identificador sensivel detectado.")
        return issues

    def _stable_hash(self, value: str) -> str:
        digest = hashlib.sha256(f"{self.settings.governance_hash_salt}:{value}".encode("utf-8")).hexdigest()
        return f"user-{digest[:10]}"

    def _mask_ip(self, ip: str) -> str:
        try:
            parsed = ipaddress.ip_address(ip)
        except ValueError:
            return "0.0.0.0"
        if parsed.version == 4:
            segments = ip.split(".")
            return f"{segments[0]}.{segments[1]}.x.x"
        return "masked-ipv6"

    def _display_status(self, status: str) -> str:
        return {"accepted": "Accepted", "denied": "Denied", "failed": "Failed"}.get(status, "Failed")

    def _display_auth_result(self, status: str, risk_signal: str) -> str:
        if status == "accepted":
            return "Success"
        if risk_signal == "push_timeout":
            return "PushTimeout"
        return "Denied" if status == "denied" else "Failed"

    def _display_risk(self, risk_signal: str) -> str:
        return _RISK_SCENARIOS.get(risk_signal, risk_signal)

    def _write_pdf(self, output_path: Path, days: int, summary: dict, logs: list[dict]) -> None:
        if colors is None:
            raise RuntimeError("ReportLab nao esta disponivel.")
        chart_paths = self._build_chart_images(summary, output_path.parent, output_path.stem)
        chart_drawings = [] if chart_paths else self._build_chart_drawings(summary)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.7 * cm,
            bottomMargin=1.5 * cm,
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=18, leading=22))
        styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
        story = [
            Paragraph("NeoIASecurity / Neotel", styles["Heading2"]),
            Paragraph("Relatório Executivo de Governança - SafeNet Trusted Access", styles["CenterTitle"]),
            Spacer(1, 0.4 * cm),
            Paragraph(f"Período analisado: últimos {days} dias", styles["Normal"]),
            Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]),
            Spacer(1, 0.7 * cm),
            Paragraph("Resumo Executivo", styles["Heading2"]),
            Paragraph(
                f"Foram correlacionados {summary['total_events']} eventos simulados do STA, com "
                f"taxa de sucesso de {summary['success_rate']}%, {summary['access_denied']} acessos negados "
                f"e score de risco {summary['risk_score']}/100. A análise prioriza sinais de MFA fraco, "
                "localização incomum, timeouts de push e falhas repetidas.",
                styles["BodyText"],
            ),
            Spacer(1, 0.4 * cm),
            self._metrics_table(summary),
            Spacer(1, 0.5 * cm),
        ]
        for title, path in chart_paths:
            story.append(Paragraph(title, styles["Heading3"]))
            story.append(Image(str(path), width=16 * cm, height=6 * cm))
            story.append(Spacer(1, 0.25 * cm))
        for title, drawing in chart_drawings:
            story.append(Paragraph(title, styles["Heading3"]))
            story.append(drawing)
            story.append(Spacer(1, 0.25 * cm))
        story.extend([
            Paragraph("Principais Achados", styles["Heading2"]),
            self._bullet_table([
                "Eventos de falha e negação foram correlacionados por usuário pseudonimizado, aplicação e política.",
                "Sinais de risco com maior concentração indicam oportunidades de ajuste de MFA e step-up.",
                "Acessos SAML/OIDC a aplicações como ServiceNow, Jira, Zoom e Office 365 foram considerados na análise.",
            ]),
            Spacer(1, 0.35 * cm),
            Paragraph("Recomendações de Política", styles["Heading2"]),
            self._bullet_table([
                "Fortalecer MFA para usuários administradores.",
                "Preferir FIDO2/passwordless para usuários e aplicações de alto risco.",
                "Revisar timeouts de push e falhas repetidas.",
                "Aplicar step-up authentication para localizações incomuns.",
                "Revisar políticas SAML/OIDC de aplicações críticas.",
                "Monitorar acessos negados recorrentes.",
            ]),
            Spacer(1, 0.35 * cm),
            Paragraph("Nota de Segurança e Privacidade", styles["Heading2"]),
            Paragraph(
                "Este relatório foi gerado a partir de dados fictícios, minimizados e pseudonimizados. "
                "Nenhum log bruto de cliente é enviado para IA. Usuários, IPs e identificadores de sessão "
                "são mascarados ou removidos antes de qualquer correlação executiva.",
                styles["BodyText"],
            ),
            PageBreak(),
            Paragraph("Apêndice - Amostra de Eventos Sanitizados", styles["Heading2"]),
            self._events_table(logs[:12]),
        ])
        doc.build(story, onFirstPage=self._pdf_footer, onLaterPages=self._pdf_footer)
        for _, path in chart_paths:
            try:
                os.remove(path)
            except OSError:
                pass

    def _metrics_table(self, summary: dict) -> Table:
        rows = [
            ["Indicador", "Valor"],
            ["Total de eventos", summary["total_events"]],
            ["Taxa de sucesso", f"{summary['success_rate']}%"],
            ["Acessos negados", summary["access_denied"]],
            ["Score de risco", f"{summary['risk_score']}/100"],
            ["Usuários únicos", summary["unique_users"]],
        ]
        table = Table(rows, colWidths=[8 * cm, 5 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]))
        return table

    def _bullet_table(self, items: list[str]) -> Table:
        table = Table([[f"• {item}"] for item in items], colWidths=[17 * cm])
        table.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def _events_table(self, logs: list[dict]) -> Table:
        rows = [["Data", "Usuário", "App", "Status", "MFA", "Risco", "IP"]]
        for log in logs:
            rows.append([
                log["timestamp"][:16].replace("T", " "),
                log["user_hash"],
                log["application"],
                log["status"],
                log["authentication_method"],
                log["risk_signal"],
                log["source_ip"],
            ])
        table = Table(rows, colWidths=[2.8 * cm, 2.6 * cm, 2.9 * cm, 1.7 * cm, 2.0 * cm, 2.7 * cm, 2.0 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#d1d5db")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def _build_chart_images(self, summary: dict, output_dir: Path, prefix: str) -> list[tuple[str, Path]]:
        if plt is None:
            return []
        charts: list[tuple[str, Path]] = []
        timeline_path = output_dir / f"{prefix}_timeline.png"
        status_path = output_dir / f"{prefix}_status.png"
        risks_path = output_dir / f"{prefix}_risks.png"

        timeline = summary["events_by_day"]
        plt.figure(figsize=(8, 3))
        plt.plot([item["date"][5:] for item in timeline], [item["events"] for item in timeline], marker="o", color="#0ea5e9")
        plt.title("Eventos por dia")
        plt.grid(True, alpha=0.25)
        plt.tight_layout()
        plt.savefig(timeline_path, dpi=140)
        plt.close()
        charts.append(("Linha do tempo de eventos", timeline_path))

        status = summary["status_distribution"]
        plt.figure(figsize=(8, 3))
        plt.bar([item["status"] for item in status], [item["count"] for item in status], color=["#10b981", "#ef4444", "#f59e0b"])
        plt.title("Distribuição por status")
        plt.tight_layout()
        plt.savefig(status_path, dpi=140)
        plt.close()
        charts.append(("Distribuição accepted / denied / failed", status_path))

        risks = summary["top_risks"] or [{"risk_signal": "ok", "count": 0}]
        plt.figure(figsize=(8, 3))
        plt.barh([item["risk_signal"] for item in risks], [item["count"] for item in risks], color="#6366f1")
        plt.title("Principais sinais de risco")
        plt.tight_layout()
        plt.savefig(risks_path, dpi=140)
        plt.close()
        charts.append(("Top sinais de risco", risks_path))
        return charts

    def _build_chart_drawings(self, summary: dict) -> list[tuple[str, Drawing]]:
        return [
            ("Linha do tempo de eventos", self._line_drawing(
                [item["date"][5:] for item in summary["events_by_day"]],
                [item["events"] for item in summary["events_by_day"]],
                colors.HexColor("#0ea5e9"),
            )),
            ("Distribuição accepted / denied / failed", self._bar_drawing(
                [item["status"] for item in summary["status_distribution"]],
                [item["count"] for item in summary["status_distribution"]],
                [colors.HexColor("#10b981"), colors.HexColor("#ef4444"), colors.HexColor("#f59e0b")],
            )),
            ("Top sinais de risco", self._bar_drawing(
                [item["risk_signal"] for item in (summary["top_risks"] or [{"risk_signal": "ok", "count": 0}])],
                [item["count"] for item in (summary["top_risks"] or [{"risk_signal": "ok", "count": 0}])],
                [colors.HexColor("#6366f1")],
            )),
        ]

    def _line_drawing(self, labels: list[str], values: list[int], color) -> Drawing:
        width, height = 450, 155
        left, bottom = 38, 28
        chart_w, chart_h = 380, 95
        drawing = Drawing(width, height)
        drawing.add(ShapeLine(left, bottom, left + chart_w, bottom, strokeColor=colors.HexColor("#9ca3af")))
        drawing.add(ShapeLine(left, bottom, left, bottom + chart_h, strokeColor=colors.HexColor("#9ca3af")))
        if not values:
            return drawing
        max_value = max(values) or 1
        points = []
        for index, value in enumerate(values):
            x = left + (chart_w * index / max(len(values) - 1, 1))
            y = bottom + (chart_h * value / max_value)
            points.append((x, y))
            drawing.add(Rect(x - 2, y - 2, 4, 4, fillColor=color, strokeColor=color))
            if index % max(1, len(labels) // 8) == 0:
                drawing.add(String(x - 12, 10, labels[index], fontSize=6, fillColor=colors.HexColor("#4b5563")))
        for start, end in zip(points, points[1:]):
            drawing.add(ShapeLine(start[0], start[1], end[0], end[1], strokeColor=color, strokeWidth=1.6))
        drawing.add(String(5, bottom + chart_h - 4, str(max_value), fontSize=7, fillColor=colors.HexColor("#4b5563")))
        return drawing

    def _bar_drawing(self, labels: list[str], values: list[int], palette: list) -> Drawing:
        width, height = 450, 155
        left, bottom = 38, 28
        chart_w, chart_h = 380, 95
        drawing = Drawing(width, height)
        drawing.add(ShapeLine(left, bottom, left + chart_w, bottom, strokeColor=colors.HexColor("#9ca3af")))
        max_value = max(values) if values else 1
        max_value = max_value or 1
        bar_count = max(len(values), 1)
        slot = chart_w / bar_count
        for index, value in enumerate(values):
            bar_h = chart_h * value / max_value
            x = left + index * slot + slot * 0.18
            bar_w = slot * 0.64
            fill = palette[index % len(palette)]
            drawing.add(Rect(x, bottom, bar_w, bar_h, fillColor=fill, strokeColor=fill))
            label = labels[index][:16]
            drawing.add(String(x, 10, label, fontSize=6, fillColor=colors.HexColor("#4b5563")))
            drawing.add(String(x, bottom + bar_h + 4, str(value), fontSize=7, fillColor=colors.HexColor("#111827")))
        return drawing

    def _pdf_footer(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawString(1.5 * cm, 1 * cm, "NeoIASecurity / Neotel - relatório executivo demonstrativo")
        canvas.drawRightString(19.5 * cm, 1 * cm, f"Página {doc.page}")
        canvas.restoreState()
