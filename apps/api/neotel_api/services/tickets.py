from __future__ import annotations

import re
import smtplib
from email.message import EmailMessage

import requests

from ..config import Settings, clean_env_value, get_settings
from ..schemas import TicketTestResponse


def _clean(value: str | None, fallback: str = "Não informado") -> str:
    normalized = (value or "").strip()
    return normalized or fallback


def _short_question(question: str | None, limit: int = 80) -> str:
    normalized = " ".join((question or "").split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."


def _sanitize_response(response: requests.Response, token: str) -> str:
    text = response.text[:2000]
    if token:
        text = text.replace(token, "[REDACTED]")
    return text


class ZammadIntegrationError(RuntimeError):
    """Expected Zammad failure safe to expose through the API."""

    def __init__(self, message: str, *, http_status: int = 502, **diagnostics: object) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.detail = {"message": message, **diagnostics}


def _zammad_config(settings: Settings) -> dict[str, str]:
    return {
        "base_url": clean_env_value(settings.zammad_base_url).rstrip("/"),
        "token": clean_env_value(settings.zammad_api_token),
        "group": clean_env_value(settings.zammad_group),
        "customer_email": _normalize_email(settings.zammad_customer_email),
        "customer_name": clean_env_value(settings.zammad_customer_name),
        "state": clean_env_value(settings.zammad_ticket_state),
        "priority": clean_env_value(settings.zammad_ticket_priority),
    }


def _normalize_email(value: str | None) -> str:
    cleaned = clean_env_value(value)
    markdown = re.fullmatch(r"\[([^\]]+)\]\(mailto:([^\)]+)\)", cleaned, re.IGNORECASE)
    if markdown:
        cleaned = markdown.group(2)
    return cleaned.strip().lower()


def zammad_headers(settings: Settings) -> dict[str, str]:
    token = clean_env_value(settings.zammad_api_token)
    return {"Authorization": f"Token token={token}", "Content-Type": "application/json"}


def zammad_get(
    settings: Settings, path: str, params: dict | None = None
) -> requests.Response:
    config = _zammad_config(settings)
    return requests.get(
        f"{config['base_url']}/{path.lstrip('/')}",
        headers=zammad_headers(settings),
        params=params,
        timeout=30,
    )


def zammad_post(settings: Settings, path: str, payload: dict) -> requests.Response:
    config = _zammad_config(settings)
    return requests.post(
        f"{config['base_url']}/{path.lstrip('/')}",
        headers=zammad_headers(settings),
        json=payload,
        timeout=30,
    )


def _response_items(response: requests.Response, *keys: str) -> list[dict]:
    try:
        data = response.json()
    except ValueError:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in keys:
            items = data.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def _zammad_error(
    settings: Settings, response: requests.Response, message: str, *, hint: str | None = None
) -> ZammadIntegrationError:
    diagnostics: dict[str, object] = {
        "status_code": response.status_code,
        "zammad_error": _sanitize_response(response, clean_env_value(settings.zammad_api_token)),
    }
    if hint:
        diagnostics["hint"] = hint
    return ZammadIntegrationError(message, **diagnostics)


def validate_zammad_auth(settings: Settings) -> dict:
    response = zammad_get(settings, "/api/v1/users/me")
    if response.status_code != 200:
        message = (
            "Falha de autorização no Zammad. Verifique token, permissões e papel do usuário."
            if response.status_code in (401, 403)
            else "Falha de autenticação com o Zammad. Verifique token e permissões."
        )
        raise _zammad_error(settings, response, message)
    try:
        user = response.json()
    except ValueError as exc:
        raise ZammadIntegrationError("Zammad retornou dados de autenticação inválidos.") from exc
    return user if isinstance(user, dict) else {}


def validate_zammad_group(settings: Settings, group_name: str) -> dict:
    response = zammad_get(settings, "/api/v1/groups")
    if response.status_code != 200:
        raise _zammad_error(settings, response, "Não foi possível validar os grupos do Zammad.")
    groups = _response_items(response, "groups", "result")
    group = next((item for item in groups if str(item.get("name", "")) == group_name), None)
    if group is None:
        available = sorted(
            str(item["name"]) for item in groups if item.get("name") is not None
        )
        raise ZammadIntegrationError(
            f"Grupo do Zammad não encontrado: {group_name}",
            available_groups=available,
        )
    return group


def find_zammad_user_by_email(settings: Settings, email: str) -> dict | None:
    normalized_email = _normalize_email(email)
    response = zammad_get(settings, "/api/v1/users/search", params={"query": normalized_email})
    if response.status_code != 200:
        return None
    users = _response_items(response, "users", "result")
    return next(
        (
            user
            for user in users
            if _normalize_email(str(user.get("email", ""))) == normalized_email
        ),
        None,
    )


def _customer_name_parts(name: str) -> tuple[str, str]:
    parts = clean_env_value(name).split(maxsplit=1)
    if not parts:
        return "Cliente", "Demonstração"
    return parts[0], parts[1] if len(parts) > 1 else "Demonstração"


def ensure_zammad_customer(settings: Settings, email: str, name: str) -> dict:
    normalized_email = _normalize_email(email)
    normalized_name = clean_env_value(name)
    existing = find_zammad_user_by_email(settings, normalized_email)
    if existing is not None:
        return {**existing, "_neoia_created": False}

    firstname, lastname = _customer_name_parts(normalized_name)
    payload = {
        "firstname": firstname,
        "lastname": lastname,
        "email": normalized_email,
        "roles": ["Customer"],
        "active": True,
    }
    response = zammad_post(settings, "/api/v1/users", payload)
    if response.status_code not in (200, 201):
        roles_response = zammad_get(settings, "/api/v1/roles")
        roles = (
            _response_items(roles_response, "roles", "result")
            if roles_response.status_code == 200
            else []
        )
        customer_role = next(
            (role for role in roles if str(role.get("name", "")).casefold() == "customer"), None
        )
        if customer_role and customer_role.get("id") is not None:
            fallback_payload = {key: value for key, value in payload.items() if key != "roles"}
            fallback_payload["role_ids"] = [customer_role["id"]]
            response = zammad_post(settings, "/api/v1/users", fallback_payload)
    if response.status_code not in (200, 201):
        # Some Zammad setups persist the user but return an error while assigning
        # roles. Recover the now-existing customer instead of creating duplicates.
        recovered = find_zammad_user_by_email(settings, normalized_email)
        if recovered is not None:
            return {**recovered, "_neoia_created": True}
        raise _zammad_error(
            settings,
            response,
            f"Falha ao criar o cliente no Zammad: {normalized_email}",
            hint="Verifique as permissões de administração de usuários do token.",
        )
    try:
        customer = response.json()
    except ValueError as exc:
        raise ZammadIntegrationError("Zammad criou o cliente sem retornar JSON válido.") from exc
    if not isinstance(customer, dict) or customer.get("id") is None:
        raise ZammadIntegrationError("Zammad criou o cliente sem retornar seu ID.")
    return {**customer, "email": customer.get("email") or normalized_email, "_neoia_created": True}


def _zammad_payload(settings: Settings, question: str | None, answer: str | None) -> dict:
    config = _zammad_config(settings)
    title = "Chamado gerado pelo NeoIASecurity"
    short_question = _short_question(question)
    if short_question:
        title = f"{title} - {short_question}"
    body = "\n".join(
        (
            f"Solicitante: {_clean(config['customer_name'])} "
            f"<{_clean(config['customer_email'])}>",
            f"Pergunta original: {_clean(question)}",
            f"Resposta do chatbot: {_clean(answer)}",
            "Motivo: usuário informou que a resposta não resolveu",
            "Origem: NeoIASecurity Chatbot",
        )
    )
    return {
        "title": title,
        "group": config["group"],
        "customer": config["customer_email"],
        "state": config["state"],
        "priority": config["priority"],
        "article": {
            "subject": title,
            "body": body,
            "type": "note",
            "internal": False,
        },
    }


def _create_zammad_ticket(
    settings: Settings, question: str | None = None, answer: str | None = None
) -> dict:
    config = _zammad_config(settings)
    if not config["base_url"]:
        raise RuntimeError("ZAMMAD_BASE_URL não configurado.")
    if not config["token"]:
        raise RuntimeError("ZAMMAD_API_TOKEN não configurado.")
    if not config["group"]:
        raise RuntimeError("ZAMMAD_GROUP não configurado.")
    if not config["customer_email"]:
        raise RuntimeError("ZAMMAD_CUSTOMER_EMAIL não configurado.")

    validate_zammad_auth(settings)
    validate_zammad_group(settings, config["group"])
    customer = ensure_zammad_customer(
        settings, config["customer_email"], config["customer_name"]
    )
    payload = _zammad_payload(settings, question, answer)
    response = zammad_post(settings, "/api/v1/tickets", payload)
    if response.status_code == 422 and customer.get("id") is not None:
        retry_payload = {key: value for key, value in payload.items() if key != "customer"}
        retry_payload["customer_id"] = customer["id"]
        response = zammad_post(settings, "/api/v1/tickets", retry_payload)
    if response.status_code not in (200, 201):
        if response.status_code in (401, 403):
            raise _zammad_error(
                settings,
                response,
                "Falha de autorização no Zammad. Verifique token, permissões e papel do usuário.",
            )
        if response.status_code == 422:
            raise _zammad_error(
                settings,
                response,
                "Zammad recusou o payload do chamado.",
                hint="Verifique cliente, grupo, estado e prioridade configurados.",
            )
        raise _zammad_error(settings, response, "Falha ao criar o chamado no Zammad.")
    try:
        response_json = response.json()
    except ValueError as exc:
        raise RuntimeError("Zammad retornou uma resposta de sucesso sem JSON válido.") from exc

    ticket_id = response_json.get("id")
    if ticket_id is None:
        raise RuntimeError("Zammad retornou sucesso sem o ID do chamado.")
    return {
        "success": True,
        "mode": "zammad",
        "status_code": response.status_code,
        "ticket_id": ticket_id,
        "ticket_number": response_json.get("number"),
        "ticket_title": payload["title"],
        "ticket_url": f"{config['base_url']}/#ticket/zoom/{ticket_id}",
        "customer_email": config["customer_email"],
        "customer_id": customer.get("id"),
        "created_customer": bool(customer.get("_neoia_created")),
    }


def create_zammad_ticket(question: str | None = None, answer: str | None = None) -> dict:
    """Create a Zammad ticket using settings loaded from apps/api/.env."""
    return _create_zammad_ticket(get_settings(), question, answer)


def _create_generic_ticket(settings: Settings, question: str | None, answer: str | None) -> dict:
    if not settings.ticket_api_url:
        raise RuntimeError("TICKET_API_URL não configurado.")
    payload = {
        "title": "Chamado gerado pelo NeoIASecurity",
        "question": question,
        "answer": answer,
        "reason": "Usuário informou que a resposta não resolveu",
        "source": "NeoIASecurity Chatbot",
    }
    headers = {"Content-Type": "application/json"}
    if settings.ticket_api_auth_type == "bearer" and settings.ticket_api_token:
        headers["Authorization"] = f"Bearer {settings.ticket_api_token}"
    if settings.ticket_api_extra_header_name and settings.ticket_api_extra_header_value:
        headers[settings.ticket_api_extra_header_name] = settings.ticket_api_extra_header_value
    response = requests.request(
        settings.ticket_api_method,
        settings.ticket_api_url,
        headers=headers,
        json=payload,
        timeout=30,
    )
    if not response.ok:
        detail = _sanitize_response(response, settings.ticket_api_token)
        raise RuntimeError(f"API de tickets respondeu com status {response.status_code}: {detail}")
    try:
        response_json: dict | str = response.json()
    except ValueError:
        response_json = response.text
    result = response_json if isinstance(response_json, dict) else {}
    return {
        "success": True,
        "mode": "generic",
        "status_code": response.status_code,
        "ticket_id": result.get("id") or result.get("ticket_id"),
        "ticket_number": result.get("number") or result.get("ticket_number"),
        "ticket_url": result.get("url") or result.get("ticket_url"),
        "response_json": response_json,
    }


def create_generic_ticket(question: str | None, answer: str | None) -> dict:
    return _create_generic_ticket(get_settings(), question, answer)


def create_ticket(question: str | None, answer: str | None) -> dict:
    mode = get_settings().ticket_api_mode.lower().strip()
    if mode == "zammad":
        return create_zammad_ticket(question, answer)
    if mode == "generic":
        return create_generic_ticket(question, answer)
    raise RuntimeError(f"TICKET_API_MODE inválido: {mode}")


def _send_email(settings: Settings, recipient: str, subject: str, body: str) -> None:
    sender = settings.smtp_from or settings.smtp_username
    if not settings.smtp_host or not sender or not recipient:
        raise RuntimeError("Configuração SMTP ou destinatário incompleto.")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def _notify(settings: Settings, ticket: dict, question: str | None, answer: str | None) -> dict:
    status: dict = {"enabled": settings.email_enabled, "warning": False}
    if not settings.email_enabled:
        return status
    number = ticket.get("ticket_number") or ticket.get("ticket_id") or "sem número"
    body = (
        f"Chamado #{number} criado pelo NeoIASecurity.\n"
        f"Pergunta: {_clean(question)}\nResposta: {_clean(answer)}\n"
        f"Link: {ticket.get('ticket_url') or 'não disponível'}"
    )
    recipients = (
        ("requester", settings.notify_requester, settings.requester_email,
         f"{settings.smtp_subject_prefix} Chamado criado - #{number}"),
        ("technician", settings.notify_technician, settings.technician_email,
         f"{settings.smtp_subject_prefix} Novo chamado para análise - #{number}"),
    )
    for label, enabled, recipient, subject in recipients:
        if not enabled:
            status[label] = {"requested": False, "sent": False}
            continue
        try:
            _send_email(settings, recipient, subject, body)
            status[label] = {"requested": True, "sent": True}
        except Exception:
            status[label] = {"requested": True, "sent": False}
            status["warning"] = True
    return status


class TicketService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_ticket(self, question: str | None, answer: str | None) -> dict:
        mode = self.settings.ticket_api_mode.lower().strip()
        if mode == "zammad":
            result = _create_zammad_ticket(self.settings, question, answer)
        elif mode == "generic":
            result = _create_generic_ticket(self.settings, question, answer)
        else:
            raise RuntimeError(f"TICKET_API_MODE inválido: {mode}")
        result["email_notification"] = _notify(self.settings, result, question, answer)
        return result

    def create_test_ticket(self, dry_run: bool = True) -> TicketTestResponse:
        payload = {
            "title": "teste",
            "summary": "teste",
            "description": "Chamado de teste criado pela API NeoIA.",
            "source": "neoia-api",
            "tags": ["chatbot", "mvp", "teste"],
        }
        mode = self.settings.ticket_api_mode.lower().strip()
        endpoint = (
            f"{self.settings.zammad_base_url}/api/v1/tickets"
            if mode == "zammad" and self.settings.zammad_base_url
            else self.settings.ticket_api_url or None
        )
        if dry_run:
            return TicketTestResponse(
                ok=True,
                dry_run=True,
                mode=mode,
                payload=payload,
                endpoint=endpoint,
                response={"message": "Dry run: nenhuma chamada externa foi realizada."},
            )
        result = self.create_ticket("Chamado de teste", payload["description"])
        return TicketTestResponse(
            ok=True,
            dry_run=False,
            mode=mode,
            payload=payload,
            endpoint=endpoint,
            response=result,
        )
