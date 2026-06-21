from __future__ import annotations

import requests

from ..config import Settings
from ..schemas import TicketTestResponse


class TicketService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_test_ticket(self, dry_run: bool = True) -> TicketTestResponse:
        payload = self._build_payload()
        if self.settings.ticket_api_mode == "octadesk":
            endpoint = f"{self.settings.octadesk_api_url}/tickets"
        else:
            endpoint = self.settings.ticket_api_url or None
        if dry_run:
            return TicketTestResponse(
                ok=True,
                dry_run=True,
                mode=self.settings.ticket_api_mode,
                payload=payload,
                endpoint=endpoint,
                response={"message": "Dry run: nenhuma chamada externa foi realizada."},
            )

        if self.settings.ticket_api_mode == "octadesk":
            result = self._create_octadesk_ticket(payload)
        else:
            result = self._create_generic_ticket(payload)

        return TicketTestResponse(
            ok=True,
            dry_run=False,
            mode=self.settings.ticket_api_mode,
            payload=payload,
            endpoint=endpoint,
            response=result,
        )

    def _build_payload(self) -> dict:
        return {
            "title": "teste",
            "summary": "teste",
            "description": "Chamado de teste criado pela API NeoIA.",
            "source": "neoia-api",
            "tags": ["chatbot", "mvp", "teste"],
        }

    def _create_generic_ticket(self, payload: dict) -> dict | str:
        if not self.settings.ticket_api_url:
            raise RuntimeError("TICKET_API_URL não configurado.")
        headers = {"Content-Type": "application/json"}
        if self.settings.ticket_api_auth_type == "bearer" and self.settings.ticket_api_token:
            headers["Authorization"] = f"Bearer {self.settings.ticket_api_token}"
        if self.settings.ticket_api_extra_header_name and self.settings.ticket_api_extra_header_value:
            headers[self.settings.ticket_api_extra_header_name] = self.settings.ticket_api_extra_header_value
        response = requests.request(
            self.settings.ticket_api_method,
            self.settings.ticket_api_url,
            headers=headers,
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return response.text

    def _create_octadesk_ticket(self, payload: dict) -> dict | str:
        if not self.settings.octadesk_access_token:
            raise RuntimeError("OCTADESK_ACCESS_TOKEN não configurado.")
        headers = {
            "Authorization": f"Bearer {self.settings.octadesk_access_token}",
            "Content-Type": "application/json",
        }
        if self.settings.octadesk_agent_email:
            headers["octa-agent-email"] = self.settings.octadesk_agent_email
        octadesk_payload = {
            "requester": {"email": self.settings.octadesk_requester_email},
            "summary": payload["summary"],
            "description": payload["description"],
            "comments": {"public": {"content": payload["description"]}},
            "tags": payload["tags"],
        }
        response = requests.post(
            f"{self.settings.octadesk_api_url}/tickets",
            headers=headers,
            json=octadesk_payload,
            timeout=15,
        )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return response.text
