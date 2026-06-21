from __future__ import annotations

import hashlib
import ipaddress
import random
from collections import Counter
from datetime import datetime, timedelta, timezone

from ..config import Settings
from ..schemas import GovernancePreviewResponse, GovernancePreviewRow, GovernanceReportResponse


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
            )
            for log in logs[:12]
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
        )

    def build_report(self, days: int, events_per_day: int) -> GovernanceReportResponse:
        preview = self.build_preview(days=days, events_per_day=events_per_day)
        top_users = ", ".join(
            f"{user} ({count})" for user, count in preview.analysis["top_failed_users"][:3]
        ) or "sem concentração relevante"
        report_markdown = (
            "# Relatório Executivo de Governança\n\n"
            f"- Período analisado: {preview.metadata['days']} dias\n"
            f"- Eventos simulados: {preview.analysis['total_log_entries']}\n"
            f"- Taxa de sucesso: {preview.analysis['success_rate']:.2f}%\n"
            f"- Usuários com mais falhas: {top_users}\n\n"
            "## Recomendações\n"
            + "\n".join(
                f"- **{item['priority']}**: {item['policy_name']} — {item['recommended_decision']}"
                for item in preview.recommendations
            )
        )
        return GovernanceReportResponse(
            metadata=preview.metadata,
            analysis=preview.analysis,
            report_markdown=report_markdown,
            recommendations=preview.recommendations,
            privacy_issues=preview.privacy_issues,
            mode="fallback",
        )

    def _generate_fake_logs(self, days: int, events_per_day: int) -> list[dict]:
        users = [
            "joao.silva",
            "maria.souza",
            "ana.lima",
            "admin.ti",
            "admin.seguranca",
            "suporte.terceiro",
        ]
        applications = ["Office 365", "VPN Corporativa", "Portal Interno", "AWS Console"]
        logs: list[dict] = []
        now = datetime.now(timezone.utc)
        for day in range(days):
            for index in range(events_per_day):
                principal_id = random.choice(users)
                application_name = random.choice(applications)
                risk_signal = "OK"
                access_state = random.choices(["Accepted", "Denied"], weights=[80, 20], k=1)[0]
                auth_result = "Success" if access_state == "Accepted" else "Failed"
                if principal_id.startswith("admin") and access_state == "Denied":
                    risk_signal = "Admin com autenticação fraca"
                elif access_state == "Denied":
                    risk_signal = "Falha recorrente"
                timestamp = (now - timedelta(days=day, minutes=index * 7)).isoformat()
                logs.append(
                    {
                        "timestamp": timestamp,
                        "principal_id": self._stable_hash(principal_id),
                        "application_name": application_name,
                        "access_state": access_state,
                        "auth_result": auth_result,
                        "risk_signal": risk_signal,
                        "source_ip": self._mask_ip(f"10.20.{day}.{index % 240 + 10}"),
                    }
                )
        logs.sort(key=lambda item: item["timestamp"], reverse=True)
        return logs

    def _analyze_logs(self, logs: list[dict]) -> dict:
        total = len(logs)
        denied = sum(1 for log in logs if log["access_state"] == "Denied")
        successes = total - denied
        top_failed_users = Counter(
            log["principal_id"] for log in logs if log["access_state"] == "Denied"
        ).most_common(5)
        return {
            "total_log_entries": total,
            "total_access_requests": total,
            "total_authentications": total,
            "denied_access_count": denied,
            "auth_failure_count": denied,
            "success_rate": (successes / total * 100) if total else 0.0,
            "top_failed_users": top_failed_users,
            "admin_weak_auth_events": sum(
                1 for log in logs if log["risk_signal"] == "Admin com autenticação fraca"
            ),
        }

    def _build_recommendations(self, analysis: dict) -> list[dict]:
        return [
            {
                "priority": "Alta",
                "policy_name": "Step-up para administradores",
                "scenario_or_condition": "Admin com falhas recorrentes",
                "recommended_decision": "Exigir MFA forte e revisão humana",
                "target": "Perfis administrativos",
            },
            {
                "priority": "Média",
                "policy_name": "Bloqueio progressivo",
                "scenario_or_condition": "Taxa de falha elevada",
                "recommended_decision": "Aplicar política de bloqueio temporário",
                "target": "Usuários com repetição de falhas",
            },
        ]

    def _validate_privacy(self, logs: list[dict]) -> list[str]:
        issues: list[str] = []
        for log in logs[:20]:
            if "." in log["principal_id"] and not log["principal_id"].startswith("user-"):
                issues.append("Usuário não pseudonimizado detectado.")
            if log["source_ip"].count(".") > 3:
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
