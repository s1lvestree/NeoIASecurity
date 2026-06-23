from __future__ import annotations

import hashlib
import ipaddress
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from ..config import Settings
from ..schemas import GovernancePreviewResponse, GovernancePreviewRow, GovernanceReportResponse

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

_RISK_SCENARIOS = {
    "geo_anomaly": "Acesso de localização incomum",
    "off_hours": "Acesso fora do horário comercial",
    "repeated_failure": "Múltiplas falhas consecutivas",
    "push_timeout": "Timeout de push MFA",
    "admin_weak": "Admin com autenticação fraca",
    "ok": "OK",
}


class GovernanceService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_preview(self, days: int, events_per_day: int) -> GovernancePreviewResponse:
        logs = self._generate_fake_logs(days=days, events_per_day=events_per_day)
        analysis = self._analyze_logs(logs)
        recommendations = self._build_recommendations(analysis)
        privacy_issues = self._validate_privacy(logs)
        preview_rows = [
            GovernancePreviewRow(
                timestamp=log["timestamp"],
                principalId=log["principal_id"],
                applicationName=log["application_name"],
                accessState=log["access_state"],
                authResult=log["auth_result"],
                riskSignal=log["risk_signal"],
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

    def _generate_fake_logs(self, days: int, events_per_day: int) -> list[dict]:
        logs: list[dict] = []
        now = datetime.now(timezone.utc)

        for day in range(days):
            base_dt = now - timedelta(days=day)
            for index in range(events_per_day):
                principal_id = random.choice(_USERS)
                application_name = random.choice(_APPLICATIONS)

                # Realistic outcome distribution
                outcome = random.choices(
                    ["accepted", "failed", "denied", "timeout"],
                    weights=[75, 12, 8, 5],
                    k=1,
                )[0]

                if outcome == "accepted":
                    access_state = "Accepted"
                    auth_result = "Success"
                elif outcome == "failed":
                    access_state = "Failed"
                    auth_result = "Failed"
                elif outcome == "denied":
                    access_state = "Denied"
                    auth_result = "Denied"
                else:
                    access_state = "Failed"
                    auth_result = "PushTimeout"

                # Risk signal
                hour = random.randint(0, 23)
                risk_signal = "OK"
                if principal_id.startswith("admin") and outcome != "accepted":
                    risk_signal = _RISK_SCENARIOS["admin_weak"]
                elif outcome == "denied" and random.random() < 0.4:
                    risk_signal = _RISK_SCENARIOS["repeated_failure"]
                elif hour < 6 or hour > 22:
                    risk_signal = _RISK_SCENARIOS["off_hours"]
                elif outcome == "timeout":
                    risk_signal = _RISK_SCENARIOS["push_timeout"]
                elif random.random() < 0.05:
                    risk_signal = _RISK_SCENARIOS["geo_anomaly"]

                event_dt = base_dt.replace(
                    hour=hour,
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )
                logs.append(
                    {
                        "timestamp": event_dt.isoformat(),
                        "principal_id": self._stable_hash(principal_id),
                        "application_name": application_name,
                        "access_state": access_state,
                        "auth_result": auth_result,
                        "risk_signal": risk_signal,
                        "source_ip": self._mask_ip(f"10.{random.randint(0,5)}.{random.randint(1,254)}.{random.randint(1,254)}"),
                    }
                )

        logs.sort(key=lambda item: item["timestamp"], reverse=True)
        return logs

    def _analyze_logs(self, logs: list[dict]) -> dict:
        total = len(logs)
        denied = sum(1 for log in logs if log["access_state"] == "Denied")
        failed = sum(1 for log in logs if log["auth_result"] in ("Failed", "PushTimeout"))
        successes = sum(1 for log in logs if log["access_state"] == "Accepted")
        admin_failures = sum(
            1 for log in logs if log["risk_signal"] == _RISK_SCENARIOS["admin_weak"]
        )
        off_hours = sum(
            1 for log in logs if log["risk_signal"] == _RISK_SCENARIOS["off_hours"]
        )
        geo_anomalies = sum(
            1 for log in logs if log["risk_signal"] == _RISK_SCENARIOS["geo_anomaly"]
        )

        unique_users = len({log["principal_id"] for log in logs})
        unique_apps = len({log["application_name"] for log in logs})

        denial_rate = denied / total if total else 0.0
        failure_rate = failed / total if total else 0.0

        # risk_score 0-100: denial_rate and failure_rate each weighted
        risk_score = int(min(100, denial_rate * 60 + failure_rate * 20 + min(admin_failures * 3, 20)))

        top_failed_users = Counter(
            log["principal_id"] for log in logs if log["access_state"] in ("Denied", "Failed")
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
            "off_hours_events": off_hours,
            "geo_anomaly_events": geo_anomalies,
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
            if "." in log["principal_id"] and not log["principal_id"].startswith("user-"):
                issues.append("Usuário não pseudonimizado detectado.")
            if log["source_ip"].count(".") == 3 and "x" not in log["source_ip"]:
                issues.append("IP não mascarado detectado.")
                break
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
