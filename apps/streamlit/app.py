import os
import copy
import hashlib
import ipaddress
import json
import random
import re
import uuid
from collections import Counter
from datetime import datetime, time, timedelta, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape

import boto3
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


load_dotenv()


def env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_FALLBACK_MODEL_ID = os.getenv("BEDROCK_FALLBACK_MODEL_ID", "amazon.nova-pro-v1:0")

AWS_CA_BUNDLE = os.getenv("AWS_CA_BUNDLE", "").strip()
REQUESTS_CA_BUNDLE = os.getenv("REQUESTS_CA_BUNDLE", "").strip()
if AWS_CA_BUNDLE:
    os.environ["AWS_CA_BUNDLE"] = AWS_CA_BUNDLE
if REQUESTS_CA_BUNDLE:
    os.environ["REQUESTS_CA_BUNDLE"] = REQUESTS_CA_BUNDLE

TICKET_API_MODE = os.getenv("TICKET_API_MODE", "generic").strip().lower()
TICKET_API_URL = os.getenv("TICKET_API_URL", "").strip()
TICKET_API_METHOD = os.getenv("TICKET_API_METHOD", "POST").strip().upper()
TICKET_API_AUTH_TYPE = os.getenv("TICKET_API_AUTH_TYPE", "bearer").strip().lower()
TICKET_API_TOKEN = os.getenv("TICKET_API_TOKEN", "").strip()
TICKET_API_EXTRA_HEADER_NAME = os.getenv("TICKET_API_EXTRA_HEADER_NAME", "").strip()
TICKET_API_EXTRA_HEADER_VALUE = os.getenv("TICKET_API_EXTRA_HEADER_VALUE", "").strip()
EMAIL_ENABLED = env_bool("EMAIL_ENABLED", False)

OCTADESK_API_URL = os.getenv("OCTADESK_API_URL", "https://api.octadesk.services").rstrip("/")
OCTADESK_ACCESS_TOKEN = os.getenv("OCTADESK_ACCESS_TOKEN", "")
OCTADESK_AGENT_EMAIL = os.getenv("OCTADESK_AGENT_EMAIL", "")
OCTADESK_REQUESTER_EMAIL = os.getenv("OCTADESK_REQUESTER_EMAIL", "")

LOCAL_RAG_ENABLED = env_bool("LOCAL_RAG_ENABLED", True)
LOCAL_RAG_DOC_PATH = os.getenv("LOCAL_RAG_DOC_PATH", "docs/sta.md")
LOCAL_RAG_MAX_CHUNKS = env_int("LOCAL_RAG_MAX_CHUNKS", 5)
LOCAL_RAG_CHUNK_SIZE = env_int("LOCAL_RAG_CHUNK_SIZE", 2500)

PUBLIC_DOC_LOOKUP_ENABLED = env_bool("PUBLIC_DOC_LOOKUP_ENABLED", True)
PUBLIC_DOC_MAX_URLS = env_int("PUBLIC_DOC_MAX_URLS", 6)
COMBINED_CONTEXT_MAX_CHARS = env_int("COMBINED_CONTEXT_MAX_CHARS", 18000)
GOVERNANCE_LOG_DIR = os.getenv("GOVERNANCE_LOG_DIR", "data/sta_logs_fake")
GOVERNANCE_REPORT_DIR = os.getenv("GOVERNANCE_REPORT_DIR", "reports")
GOVERNANCE_DEFAULT_DAYS = env_int("GOVERNANCE_DEFAULT_DAYS", 7)
GOVERNANCE_DEFAULT_LOG_COUNT = env_int("GOVERNANCE_DEFAULT_LOG_COUNT", 500)
GOVERNANCE_USE_FAKE_STA_API = env_bool("GOVERNANCE_USE_FAKE_STA_API", True)
GOVERNANCE_PRIVACY_MODE = env_bool("GOVERNANCE_PRIVACY_MODE", True)
GOVERNANCE_HASH_SALT = os.getenv("GOVERNANCE_HASH_SALT", "CHANGE_ME_DEMO_SALT")
GOVERNANCE_SEND_RAW_LOGS_TO_AI = env_bool("GOVERNANCE_SEND_RAW_LOGS_TO_AI", False)
GOVERNANCE_MAX_SANITIZED_SAMPLES = env_int("GOVERNANCE_MAX_SANITIZED_SAMPLES", 20)
GOVERNANCE_MASK_IP_MODE = os.getenv("GOVERNANCE_MASK_IP_MODE", "partial").strip().lower()
GOVERNANCE_REMOVE_SESSION_IDENTIFIERS = env_bool("GOVERNANCE_REMOVE_SESSION_IDENTIFIERS", True)

INSUFFICIENT_CONTEXT_ANSWER = (
    "Não encontrei informação suficiente na documentação local ou pública "
    "carregada neste MVP para responder com segurança."
)

SYSTEM_CONTEXT = """
Você é um chatbot técnico de cibersegurança da Neotel.

Responda sempre em português do Brasil.

Objetivo:
Ajudar clientes e analistas com dúvidas técnicas sobre soluções de cibersegurança, atendimento, triagem inicial e orientação de suporte.

Fontes de conhecimento disponíveis neste MVP:
1. Documentação local em Markdown, quando carregada pela aplicação.
2. Documentação pública allowlistada, quando carregada pela aplicação.
3. Contexto mínimo explícito no prompt.

Limitações:
- Você não navega livremente na internet.
- Você só pode usar documentação pública quando o texto dela for fornecido pela aplicação no prompt.
- Você só pode usar documentação local quando o texto dela for fornecido pela aplicação no prompt.
- Não diga que consultou documentação pública se nenhuma fonte pública foi fornecida.
- Não diga que consultou documentação local se nenhum contexto local foi fornecido.

Regras anti-alucinação:
- Não invente produtos, módulos, versões, endpoints, comandos, links ou procedimentos.
- Não afirme que uma empresa possui determinada solução se isso não estiver explicitamente no contexto.
- Se não houver informação suficiente, diga:
"Não encontrei informação suficiente na documentação local ou pública carregada neste MVP para responder com segurança."
- Para perguntas sobre listas de produtos, integrações, APIs, versões ou procedimentos específicos, só responda se isso aparecer no contexto fornecido.

Contexto mínimo conhecido:
- STA significa SafeNet Trusted Access.
- SafeNet Trusted Access é uma solução da Thales voltada para controle de acesso, autenticação multifator e Single Sign-On.
- O STA ajuda empresas a controlar o acesso de usuários a aplicações corporativas, SaaS e web.
- O STA pode integrar aplicações por padrões como SAML e OIDC, dependendo da aplicação.
- O STA permite aplicar políticas de acesso e métodos de autenticação, como MFA.
- Em termos simples, o STA ajuda a garantir que o usuário correto acesse a aplicação correta, com o nível adequado de autenticação.

Regras de resposta:
- Para perguntas conceituais, responda de forma direta e didática.
- Para troubleshooting, organize a resposta em:
  1. Possíveis causas
  2. Validações iniciais
  3. Evidências/logs que devem ser coletados
  4. Próximos passos recomendados
  5. Quando abrir chamado
- No final, pergunte se a orientação resolveu o problema.
"""


def load_local_markdown(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as markdown_file:
            return markdown_file.read()
    except (FileNotFoundError, OSError):
        return ""


def chunk_text(text: str, chunk_size: int) -> list[str]:
    if not text.strip():
        return []

    sections = re.split(r"(?=^#{1,3}\s+)", text, flags=re.MULTILINE)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= chunk_size:
            chunks.append(section)
            continue
        chunks.extend(
            section[index : index + chunk_size].strip()
            for index in range(0, len(section), chunk_size)
            if section[index : index + chunk_size].strip()
        )
    return chunks


def score_chunk(question: str, chunk: str) -> int:
    terms = {term for term in re.findall(r"\w+", question.lower()) if len(term) >= 3}
    lowered_chunk = chunk.lower()
    score = sum(lowered_chunk.count(term) for term in terms)
    headings = "\n".join(
        line.lower() for line in chunk.splitlines() if re.match(r"^#{1,3}\s+", line)
    )
    score += sum(3 for term in terms if term in headings)
    return score


def retrieve_local_context(question: str) -> tuple[str, list[str]]:
    if not LOCAL_RAG_ENABLED:
        return "", []

    markdown_text = load_local_markdown(LOCAL_RAG_DOC_PATH)
    scored_chunks = [
        (score_chunk(question, chunk), chunk)
        for chunk in chunk_text(markdown_text, LOCAL_RAG_CHUNK_SIZE)
    ]
    selected = [
        chunk
        for score, chunk in sorted(scored_chunks, key=lambda item: item[0], reverse=True)
        if score > 0
    ][:LOCAL_RAG_MAX_CHUNKS]
    context = "\n\n".join(selected)[:10000]
    return (context, [LOCAL_RAG_DOC_PATH]) if context else ("", [])


def load_public_doc_urls() -> list[str]:
    return [
        url.strip()
        for url in os.getenv("PUBLIC_DOC_URLS", "").split(",")
        if url.strip()
    ]


def is_allowed_url(url: str, allowed_urls: list[str]) -> bool:
    requested_host = (urlparse(url).hostname or "").lower()
    allowed_hosts = {(urlparse(item).hostname or "").lower() for item in allowed_urls}
    return bool(requested_host) and requested_host in allowed_hosts


def fetch_public_doc_text(url: str) -> str:
    allowed_urls = load_public_doc_urls()
    if not is_allowed_url(url, allowed_urls):
        return ""

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Neotel-chatbot-MVP/1.0"},
        )
    except requests.RequestException:
        return ""
    if response.status_code != 200:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    return text[:8000]


def retrieve_public_context(question: str) -> tuple[str, list[str]]:
    if not PUBLIC_DOC_LOOKUP_ENABLED:
        return "", []

    relevant_pages: list[tuple[int, str, str]] = []
    for url in load_public_doc_urls()[:PUBLIC_DOC_MAX_URLS]:
        text = fetch_public_doc_text(url)
        score = score_chunk(question, text)
        if text and score > 0:
            relevant_pages.append((score, url, text))

    context_parts: list[str] = []
    sources: list[str] = []
    used_chars = 0
    for _, url, text in sorted(relevant_pages, key=lambda item: item[0], reverse=True):
        remaining = 8000 - used_chars
        if remaining <= 0:
            break
        selected_text = text[:remaining]
        context_parts.append(f"[source: {url}]\n{selected_text}")
        sources.append(url)
        used_chars += len(selected_text)
    return "\n\n".join(context_parts), sources


def retrieve_combined_context(question: str) -> tuple[str, list[str], list[str]]:
    local_context, local_sources = retrieve_local_context(question)
    public_context, public_sources = retrieve_public_context(question)

    parts: list[str] = []
    if local_context:
        parts.append(f"### CONTEXTO LOCAL\n[source: {LOCAL_RAG_DOC_PATH}]\n{local_context}")
    if public_context:
        parts.append(f"### CONTEXTO PÚBLICO\n{public_context}")
    return "\n\n".join(parts)[:COMBINED_CONTEXT_MAX_CHARS], local_sources, public_sources


def call_bedrock(question: str, model_id: str, combined_context: str) -> str:
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    supplied_context = combined_context or "Nenhum contexto local ou público relevante foi recuperado."
    final_prompt = f"""
Responda à pergunta abaixo somente com base no contexto fornecido e no contexto mínimo explícito do sistema.
Não use conhecimento externo. Não invente informações. Se o contexto não for suficiente, responda exatamente:
"{INSUFFICIENT_CONTEXT_ANSWER}"

Contexto recuperado pela aplicação:
{supplied_context}

Pergunta:
{question}
"""
    response = client.converse(
        modelId=model_id,
        system=[{"text": SYSTEM_CONTEXT}],
        messages=[{"role": "user", "content": [{"text": final_prompt}]}],
        inferenceConfig={"maxTokens": 1800, "temperature": 0.1, "topP": 0.9},
    )
    return response["output"]["message"]["content"][0]["text"]


def ask_bedrock(question: str) -> tuple[str, list[str], list[str]]:
    combined_context, local_sources, public_sources = retrieve_combined_context(question)
    try:
        answer = call_bedrock(question, BEDROCK_MODEL_ID, combined_context)
    except ClientError:
        if BEDROCK_FALLBACK_MODEL_ID == BEDROCK_MODEL_ID:
            raise
        answer = call_bedrock(question, BEDROCK_FALLBACK_MODEL_ID, combined_context)
    return answer, local_sources, public_sources


def create_octadesk_test_ticket() -> dict | str:
    if not OCTADESK_ACCESS_TOKEN:
        raise RuntimeError("OCTADESK_ACCESS_TOKEN não configurado.")
    if not OCTADESK_REQUESTER_EMAIL:
        raise RuntimeError("OCTADESK_REQUESTER_EMAIL não configurado.")

    headers = {
        "Authorization": f"Bearer {OCTADESK_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    if OCTADESK_AGENT_EMAIL:
        headers["octa-agent-email"] = OCTADESK_AGENT_EMAIL

    description = "Chamado de teste criado pelo MVP chatbot via API."
    payload = {
        "requester": {"email": OCTADESK_REQUESTER_EMAIL},
        "summary": "teste",
        "description": description,
        "comments": {"public": {"content": description}},
        "tags": ["chatbot", "mvp", "teste"],
    }
    response = requests.post(
        f"{OCTADESK_API_URL}/tickets",
        headers=headers,
        json=payload,
        timeout=15,
    )
    if response.status_code not in {200, 201}:
        raise RuntimeError(f"Erro da API ({response.status_code}): {response.text}")
    try:
        return response.json()
    except ValueError:
        return response.text


def create_generic_test_ticket() -> dict | str:
    if not TICKET_API_URL:
        raise RuntimeError("TICKET_API_URL não configurado.")

    headers = {"Content-Type": "application/json"}
    if TICKET_API_AUTH_TYPE == "bearer" and TICKET_API_TOKEN:
        headers["Authorization"] = f"Bearer {TICKET_API_TOKEN}"
    if TICKET_API_EXTRA_HEADER_NAME and TICKET_API_EXTRA_HEADER_VALUE:
        headers[TICKET_API_EXTRA_HEADER_NAME] = TICKET_API_EXTRA_HEADER_VALUE

    payload = {
        "title": "teste",
        "summary": "teste",
        "description": "Chamado de teste criado pelo MVP chatbot via API genérica.",
        "source": "chatbot",
        "tags": ["chatbot", "mvp", "teste"],
    }
    response = requests.request(
        TICKET_API_METHOD,
        TICKET_API_URL,
        headers=headers,
        json=payload,
        timeout=15,
    )
    if not 200 <= response.status_code < 300:
        raise RuntimeError(f"Erro da API ({response.status_code}): {response.text}")
    try:
        return response.json()
    except ValueError:
        return response.text


def create_test_ticket() -> dict | str:
    if TICKET_API_MODE == "octadesk":
        return create_octadesk_test_ticket()
    if TICKET_API_MODE == "generic":
        return create_generic_test_ticket()
    raise RuntimeError("TICKET_API_MODE deve ser 'generic' ou 'octadesk'.")


def ensure_governance_directories() -> None:
    Path(GOVERNANCE_LOG_DIR).mkdir(parents=True, exist_ok=True)
    Path(GOVERNANCE_REPORT_DIR).mkdir(parents=True, exist_ok=True)


def save_fake_sta_logs_by_day(logs: list[dict], output_dir: str) -> list[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logs_by_day: dict[str, list[dict]] = {}
    for log in logs:
        day = log.get("timeStamp", "")[:10]
        if day:
            logs_by_day.setdefault(day, []).append(log)

    created_files: list[str] = []
    for day, day_logs in sorted(logs_by_day.items()):
        output_path = Path(output_dir) / f"sta_logs_{day}.json"
        output_path.write_text(
            json.dumps(day_logs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        created_files.append(str(output_path))
    return created_files


def load_sta_logs_from_local_folder(
    days: int = 7, log_dir: str = GOVERNANCE_LOG_DIR
) -> list[dict]:
    logs: list[dict] = []
    log_path = Path(log_dir)
    today = datetime.now(timezone.utc).date()
    for day_offset in range(max(days, 1)):
        day = today - timedelta(days=day_offset)
        input_path = log_path / f"sta_logs_{day.isoformat()}.json"
        if not input_path.exists():
            continue
        try:
            content = json.loads(input_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(content, list):
            logs.extend(item for item in content if isinstance(item, dict))
    return sorted(logs, key=lambda item: item.get("timeStamp", ""), reverse=True)


def simulate_sta_logs_api_fetch(days: int = 7) -> tuple[list[dict], dict]:
    logs = load_sta_logs_from_local_folder(days, GOVERNANCE_LOG_DIR)
    today = datetime.now(timezone.utc).date()
    files_read = [
        str(Path(GOVERNANCE_LOG_DIR) / f"sta_logs_{(today - timedelta(days=offset)).isoformat()}.json")
        for offset in range(max(days, 1))
        if (Path(GOVERNANCE_LOG_DIR) / f"sta_logs_{(today - timedelta(days=offset)).isoformat()}.json").exists()
    ]
    metadata = {
        "source": "local_simulated_sta_logs_api",
        "solution": "SafeNet Trusted Access (STA)",
        "days": days,
        "log_dir": GOVERNANCE_LOG_DIR,
        "files_read": files_read,
        "total_logs": len(logs),
        "collected_at": datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S"),
        "note": "Simulação local de chamada ao STA Logs API para fins de MVP.",
    }
    return logs, metadata


def generate_fake_sta_logs(num_access_events: int = 500, days: int = 7) -> list[dict]:
    users = [
        "joao.silva", "maria.souza", "ana.lima", "carlos.rocha", "fernanda.alves",
        "rafael.costa", "suporte.terceiro", "admin.ti", "admin.seguranca",
    ]
    applications = {
        "Office 365": "SAML", "Salesforce": "SAML", "ServiceNow": "SAML",
        "AWS Console": "SAML", "Portal Interno": "OIDC", "Aplicação Web Interna": "OIDC",
        "VPN Corporativa": "NPS", "Outlook Web": "Outlook Web Access",
        "Windows Logon": "Windows Logon", "ADFS Federation": "ADFS",
    }
    policies = [
        "Global Policy for STA", "MFA Required - External Access", "Office 365 Standard Policy",
        "VPN MFA Policy", "Block High Risk Countries", "Require FIDO2 for Admins",
        "Step-up Authentication for Admins", "Deny Legacy Authentication",
    ]
    scenarios = [
        "Corporate Network", "External Access", "High Risk Country", "Admin Access",
        "Windows only", "Default Requirements", "",
    ]
    locations = [
        ("BR", "São Paulo"), ("BR", "Rio de Janeiro"), ("BR", "Brasília"),
        ("US", "Ashburn"), ("NL", "Amsterdam"), ("RU", "Moscow"), ("CN", "Beijing"),
    ]
    regular_ips = [f"10.20.{subnet}.{host}" for subnet in range(1, 5) for host in range(10, 20)]
    suspicious_ips = ["185.220.101.24", "45.148.10.91"]
    clustered_users = ["suporte.terceiro", "joao.silva"]
    credential_mapping = {
        "MobilePASS+": "push", "Password": "password", "SMS OTP": "otp",
        "Email OTP": "otp", "FIDO2": "fido", "GrIDsure": "grid", "Certificate": "certificate",
    }
    tenant_code = "BWUD0CN4AD"
    tenant_id = "tenant-neotel-demo"
    logs: list[dict] = []
    now = datetime.now(timezone.utc)

    for event_index in range(num_access_events):
        outcome_bucket = event_index % 100
        if outcome_bucket < 75:
            outcome = "accepted"
        elif outcome_bucket < 87:
            outcome = "failed"
        elif outcome_bucket < 92:
            outcome = "denied"
        elif outcome_bucket < 96:
            outcome = "push_timeout"
        elif outcome_bucket < 98:
            outcome = "saml_rejected"
        else:
            outcome = "locked_or_certificate"

        principal_id = random.choice(users)
        application_name = random.choice(list(applications))
        originating_address = random.choice(regular_ips)
        country, city = random.choices(locations, weights=[45, 20, 15, 6, 5, 5, 4], k=1)[0]
        if outcome != "accepted" and random.random() < 0.65:
            principal_id = random.choice(clustered_users)
            originating_address = random.choice(suspicious_ips)
        if outcome == "denied":
            country, city = random.choice(locations[3:])
        if outcome == "saml_rejected":
            application_name = random.choice(["Office 365", "Salesforce"])

        is_admin = principal_id.startswith("admin.")
        if random.random() < 0.12:
            principal_id = random.choice(["admin.ti", "admin.seguranca"])
            application_name = random.choice(["AWS Console", "Office 365", "Portal Interno"])
            is_admin = True
        if event_index < 4:
            principal_id = random.choice(["admin.ti", "admin.seguranca"])
            application_name = random.choice(["AWS Console", "Office 365", "Portal Interno"])
            is_admin = True
        elif 75 <= outcome_bucket < 81:
            principal_id = clustered_users[event_index % len(clustered_users)]
            originating_address = suspicious_ips[event_index % len(suspicious_ips)]

        policy_name = random.choice(policies)
        scenario_name = random.choice(scenarios)
        if is_admin:
            policy_name = random.choice(["Step-up Authentication for Admins", "Require FIDO2 for Admins"])
            scenario_name = "Admin Access"

        credential_type = random.choice(list(credential_mapping))
        if is_admin:
            credential_type = random.choices(
                ["FIDO2", "Certificate", "MobilePASS+", "SMS OTP", "Password"],
                weights=[45, 25, 20, 5, 5],
                k=1,
            )[0]
        if event_index < 4:
            credential_type = random.choice(["SMS OTP", "Password"])

        state, reason, auth_result, result_text = "Accepted", "", "0", "AUTH_SUCCESS"
        message = f"Authentication successful. Login from {application_name}."
        credential_state = "Verified"
        if outcome == "failed":
            reason = random.choice(["SASIDP_INVALID_CREDENTIALS", "SASIDP_INVALID_OTP"])
            message = (
                f"Invalid OTP. Login from {application_name}."
                if reason == "SASIDP_INVALID_OTP"
                else f"Invalid password. Login from {application_name}."
            )
            state, auth_result, result_text, credential_state = "Failed", "1", "AUTH_FAILURE", "Failed"
        elif outcome == "denied":
            state, reason, auth_result, result_text, credential_state = (
                "Denied", "SASIDP_POLICY_DENIED", "1", "AUTH_FAILURE", "Denied"
            )
            message = f"Access denied by policy. Login from {application_name}."
        elif outcome == "push_timeout":
            state, reason, auth_result, result_text, credential_state = (
                "Failed", "SASIDP_PUSH_TIMEOUT", "1", "AUTH_FAILURE", "Timed out"
            )
            credential_type = "MobilePASS+"
            message = f"Push authentication timed out. Login from {application_name}."
        elif outcome == "saml_rejected":
            state, reason, auth_result, result_text, credential_state = (
                "Failed", "SASIDP_SAML_ASSERTION_REJECTED", "1", "AUTH_FAILURE", "Failed"
            )
            message = f"SAML assertion rejected. Login from {application_name}."
        elif outcome == "locked_or_certificate":
            reason = random.choice(["SASIDP_USER_LOCKED", "SASIDP_CERTIFICATE_EXPIRED"])
            state, auth_result, result_text, credential_state = "Failed", "1", "AUTH_FAILURE", "Failed"
            credential_type = "Certificate" if reason == "SASIDP_CERTIFICATE_EXPIRED" else credential_type
            message = (
                f"Access denied by policy. Login from {application_name}."
                if reason == "SASIDP_USER_LOCKED"
                else f"Authentication failed. Login from {application_name}."
            )

        global_access_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        day_offset = random.randint(0, max(days, 1) - 1)
        seconds_limit = int((now - datetime.combine(now.date(), time.min, tzinfo=timezone.utc)).total_seconds())
        random_seconds = random.randint(0, seconds_limit if day_offset == 0 else 86399)
        timestamp = datetime.combine(
            now.date() - timedelta(days=day_offset), time.min, tzinfo=timezone.utc
        ) + timedelta(seconds=random_seconds)
        common_context = {
            "tenantId": tenant_id, "originatingAddress": originating_address,
            "principalId": principal_id, "globalAccessId": global_access_id, "sessionId": session_id,
        }
        access_context = {
            **common_context, "applicationName": application_name,
            "applicationType": applications[application_name], "policyName": policy_name,
            "scenarioName": scenario_name, "geo": {"country": country, "city": city},
        }
        auth_context = {**common_context, "geo": {"country": country, "city": city}}
        common_log = {
            "logVersion": "1.0", "category": "AUDIT",
            "timeStamp": timestamp.isoformat().replace("+00:00", "Z"),
            "accountName": "Cliente Demonstração", "tenantCode": tenant_code,
        }
        logs.append({
            **common_log, "id": str(uuid.uuid4()), "context": access_context,
            "details": {
                "type": "ACCESS_REQUEST", "state": state, "reason": reason, "action": "auth",
                "credentials": [{"type": credential_mapping[credential_type], "state": credential_state}],
            },
        })
        logs.append({
            **common_log, "id": str(uuid.uuid4()), "context": auth_context,
            "details": {
                "type": "AUTHENTICATION", "serial": random.choice(["0", uuid.uuid4().hex[:12].upper()]),
                "action": "0", "actionText": "AUTH_ATTEMPT", "result": auth_result,
                "resultText": result_text, "agentId": random.choice(["14", "18", "22", "31"]),
                "message": message, "usedName": principal_id, "credentialType": credential_type,
            },
        })
    return sorted(logs, key=lambda item: item["timeStamp"], reverse=True)


def prepare_local_sta_demo_dataset(days: int = 7, events_per_day: int = 100) -> list[str]:
    """
    Silently prepares local simulated STA logs if there are no local files.
    This function is not exposed as a main UI action.
    It generates STA-style logs and saves them by day under data/sta_logs_fake/.
    Returns file paths created.
    """
    ensure_governance_directories()
    created_files: list[str] = []
    today = datetime.now(timezone.utc).date()
    random_state = random.getstate()
    try:
        for day_offset in range(max(days, 1)):
            day = today - timedelta(days=day_offset)
            output_path = Path(GOVERNANCE_LOG_DIR) / f"sta_logs_{day.isoformat()}.json"
            if output_path.exists():
                continue
            random.seed(int(day.strftime("%Y%m%d")) + 42)
            day_logs = generate_fake_sta_logs(events_per_day, days=1)
            for log in day_logs:
                timestamp = datetime.fromisoformat(log["timeStamp"].replace("Z", "+00:00"))
                log["timeStamp"] = timestamp.replace(
                    year=day.year, month=day.month, day=day.day
                ).isoformat().replace("+00:00", "Z")
            output_path.write_text(
                json.dumps(day_logs, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            created_files.append(str(output_path))
    finally:
        random.setstate(random_state)
    return created_files


def correlate_sta_logs(logs: list[dict]) -> dict:
    correlated: dict = {}
    for log in logs:
        global_access_id = log.get("context", {}).get("globalAccessId")
        if not global_access_id:
            continue
        group = correlated.setdefault(global_access_id, {"access": None, "authentications": []})
        if log.get("details", {}).get("type") == "ACCESS_REQUEST":
            group["access"] = log
        elif log.get("details", {}).get("type") == "AUTHENTICATION":
            group["authentications"].append(log)
    return correlated


def analyze_sta_logs(logs: list[dict]) -> dict:
    correlated = correlate_sta_logs(logs)
    access_logs = [group["access"] for group in correlated.values() if group["access"]]
    auth_logs = [auth for group in correlated.values() for auth in group["authentications"]]
    failed_auth_logs = [log for log in auth_logs if log["details"]["result"] == "1"]
    failed_access_logs = [log for log in access_logs if log["details"]["state"] != "Accepted"]
    failed_ids = {log["context"]["globalAccessId"] for log in failed_auth_logs}
    failed_related_access = [log for log in failed_access_logs if log["context"]["globalAccessId"] in failed_ids]

    failed_users = Counter(log["context"]["principalId"] for log in failed_auth_logs)
    failed_ips = Counter(log["context"]["originatingAddress"] for log in failed_auth_logs)
    failed_apps = Counter(log["context"]["applicationName"] for log in failed_related_access)
    credential_types = Counter(log["details"]["credentialType"] for log in auth_logs)
    application_types = Counter(log["context"]["applicationType"] for log in access_logs)
    policies = Counter(log["context"]["policyName"] for log in access_logs)
    scenarios = Counter(log["context"]["scenarioName"] for log in access_logs)
    high_risk_countries = Counter(
        log["context"]["geo"]["country"] for log in failed_access_logs
        if log["context"]["geo"]["country"] in {"US", "NL", "RU", "CN"}
    )
    admin_auth_logs = [log for log in auth_logs if log["context"]["principalId"].startswith("admin.")]
    admin_weak_auth_logs = [
        log for log in admin_auth_logs if log["details"]["credentialType"] in {"SMS OTP", "Password"}
    ]
    suspicious_patterns = [
        f"Usuário {user} registrou {count} falhas de autenticação."
        for user, count in failed_users.items() if count > 5
    ]
    suspicious_patterns.extend(
        f"IP {ip} registrou {count} falhas de autenticação."
        for ip, count in failed_ips.items() if count > 10
    )
    if admin_weak_auth_logs:
        suspicious_patterns.append(
            f"Foram observados {len(admin_weak_auth_logs)} acessos administrativos com Password ou SMS OTP."
        )
    account_locked_count = sum(log["details"]["reason"] == "SASIDP_USER_LOCKED" for log in access_logs)
    saml_rejected_count = sum(
        log["details"]["reason"] == "SASIDP_SAML_ASSERTION_REJECTED" for log in access_logs
    )
    push_timeout_count = sum(log["details"]["reason"] == "SASIDP_PUSH_TIMEOUT" for log in access_logs)
    if account_locked_count:
        suspicious_patterns.append(f"Foram observados {account_locked_count} bloqueios de conta.")
    if high_risk_countries:
        suspicious_patterns.append(
            f"Eventos malsucedidos por país de maior risco: {dict(high_risk_countries)}."
        )
    if saml_rejected_count:
        suspicious_patterns.append(f"Foram observadas {saml_rejected_count} rejeições de assertion SAML.")
    if push_timeout_count:
        suspicious_patterns.append(f"Foram observados {push_timeout_count} timeouts de push.")

    auth_success_count = sum(log["details"]["result"] == "0" for log in auth_logs)
    auth_failure_count = len(failed_auth_logs)
    auth_total = len(auth_logs)
    strong_credentials = {"FIDO2", "Certificate", "MobilePASS+"}
    weak_credentials = {"Password", "SMS OTP", "Email OTP"}
    auth_by_access_id = {
        access_id: group["authentications"]
        for access_id, group in correlated.items()
    }
    applications_without_strong_mfa_signal = sorted({
        access["context"]["applicationName"]
        for access in access_logs
        if not any(
            auth["details"].get("credentialType") in strong_credentials
            for auth in auth_by_access_id.get(access["context"]["globalAccessId"], [])
        )
    })
    admin_access_without_fido_or_certificate = sum(
        log["details"]["credentialType"] not in {"FIDO2", "Certificate"} for log in admin_auth_logs
    )
    password_only_or_weak_auth_events = sum(
        log["details"]["credentialType"] in weak_credentials for log in auth_logs
    )
    repeated_failures_by_scenario = Counter(
        log["context"]["scenarioName"] or "(sem cenário)" for log in failed_related_access
    )
    repeated_denies_by_policy = Counter(
        log["context"]["policyName"] for log in access_logs if log["details"]["state"] == "Denied"
    )
    external_access_failure_count = sum(
        log["context"]["scenarioName"] == "External Access" for log in failed_related_access
    )
    high_risk_country_denied_count = sum(
        log["details"]["state"] == "Denied" and log["context"]["geo"]["country"] in {"US", "NL", "RU", "CN"}
        for log in access_logs
    )
    policy_totals = Counter(log["context"]["policyName"] for log in access_logs)
    policy_failures = Counter(log["context"]["policyName"] for log in failed_access_logs)
    policies_with_high_failure_rate = [
        {"policy": policy, "failure_rate": round(policy_failures[policy] / total * 100, 2)}
        for policy, total in policy_totals.items()
        if total and policy_failures[policy] / total >= 0.20
    ]
    applications_with_saml_errors = sorted({
        log["context"]["applicationName"]
        for log in access_logs
        if log["details"]["reason"] == "SASIDP_SAML_ASSERTION_REJECTED"
    })
    users_recommended_for_review = [user for user, count in failed_users.items() if count > 5]
    source_ips_recommended_for_block_or_review = [ip for ip, count in failed_ips.items() if count > 10]
    return {
        "total_log_entries": len(logs),
        "total_access_requests": len(access_logs),
        "total_authentications": auth_total,
        "accepted_access_count": sum(log["details"]["state"] == "Accepted" for log in access_logs),
        "failed_access_count": sum(log["details"]["state"] == "Failed" for log in access_logs),
        "denied_access_count": sum(log["details"]["state"] == "Denied" for log in access_logs),
        "auth_success_count": auth_success_count,
        "auth_failure_count": auth_failure_count,
        "success_rate": round((auth_success_count / auth_total * 100) if auth_total else 0, 2),
        "failure_rate": round((auth_failure_count / auth_total * 100) if auth_total else 0, 2),
        "top_failed_users": failed_users.most_common(5),
        "top_failed_source_ips": failed_ips.most_common(5),
        "top_failed_applications": failed_apps.most_common(5),
        "credential_type_distribution": dict(credential_types),
        "application_type_distribution": dict(application_types),
        "policy_distribution": dict(policies),
        "scenario_distribution": dict(scenarios),
        "high_risk_country_events": dict(high_risk_countries),
        "admin_events": len(admin_auth_logs),
        "admin_weak_auth_events": len(admin_weak_auth_logs),
        "saml_assertion_rejected_count": saml_rejected_count,
        "push_timeout_count": push_timeout_count,
        "account_locked_count": account_locked_count,
        "applications_without_strong_mfa_signal": applications_without_strong_mfa_signal,
        "admin_access_without_fido_or_certificate": admin_access_without_fido_or_certificate,
        "password_only_or_weak_auth_events": password_only_or_weak_auth_events,
        "repeated_failures_by_scenario": dict(repeated_failures_by_scenario),
        "repeated_denies_by_policy": dict(repeated_denies_by_policy),
        "external_access_failure_count": external_access_failure_count,
        "high_risk_country_denied_count": high_risk_country_denied_count,
        "policies_with_high_failure_rate": policies_with_high_failure_rate,
        "applications_with_saml_errors": applications_with_saml_errors,
        "users_recommended_for_review": users_recommended_for_review,
        "source_ips_recommended_for_block_or_review": source_ips_recommended_for_block_or_review,
        "suspicious_patterns": suspicious_patterns,
    }


def stable_hash(value: str, salt: str, prefix: str = "hash") -> str:
    """Return a stable pseudonymous identifier."""
    if not value:
        return ""
    digest = hashlib.sha256((salt + value).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:8]}"


def mask_ip(ip: str, mode: str = "partial") -> str:
    """Mask IPv4 and IPv6 addresses before data leaves the application."""
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return "invalid_or_unknown_ip"
    if mode == "hash":
        return stable_hash(str(address), GOVERNANCE_HASH_SALT, prefix="ip")
    if mode == "full":
        return "x.x.x.x" if address.version == 4 else "x:x:x:x:x:x:x:x"
    if address.version == 4:
        octets = str(address).split(".")
        return f"{octets[0]}.{octets[1]}.x.x"
    hextets = address.exploded.split(":")
    return ":".join([hextets[0], hextets[1], "x", "x", "x", "x", "x", "x"])


def sanitize_log_message(message: str, salt: str) -> str:
    """Mask common direct identifiers embedded in free-text log messages."""
    if not message:
        return ""
    sanitized = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "user_redacted", message)
    sanitized = re.sub(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        lambda match: mask_ip(match.group(0), GOVERNANCE_MASK_IP_MODE),
        sanitized,
    )
    return sanitized


def sanitize_sta_log_sample(log: dict, salt: str) -> dict:
    """Return a minimized and pseudonymized copy of one STA log entry."""
    sanitized = copy.deepcopy(log)
    for key in ("id", "tenantCode", "accountName"):
        sanitized.pop(key, None)
    context = sanitized.get("context", {})
    context.pop("tenantId", None)
    context.pop("sessionId", None)
    global_access_id = context.pop("globalAccessId", "")
    if global_access_id and not GOVERNANCE_REMOVE_SESSION_IDENTIFIERS:
        context["globalAccessId"] = stable_hash(global_access_id, salt, prefix="gaid")
    for key in ("principalId", "usedName"):
        if context.get(key):
            context[key] = stable_hash(context[key], salt, prefix="user")
    if context.get("originatingAddress"):
        context["originatingAddress"] = mask_ip(context["originatingAddress"], GOVERNANCE_MASK_IP_MODE)
    details = sanitized.get("details", {})
    details.pop("serial", None)
    details.pop("agentId", None)
    if details.get("usedName"):
        details["usedName"] = stable_hash(details["usedName"], salt, prefix="user")
    if details.get("message"):
        details["message"] = sanitize_log_message(details["message"], salt)
    return sanitized


def sanitize_sta_logs_for_ai(logs: list[dict], max_samples: int, salt: str) -> list[dict]:
    """Select a small risk-oriented sample and sanitize every selected entry."""
    def is_relevant(log: dict) -> bool:
        details = log.get("details", {})
        reason = details.get("reason", "")
        return (
            details.get("state") in {"Failed", "Denied"}
            or details.get("resultText") == "AUTH_FAILURE"
            or any(token in reason for token in ("SAML", "LOCKED", "DENIED", "INVALID", "TIMEOUT"))
        )

    relevant_logs = [log for log in logs if is_relevant(log)]
    fallback_logs = [log for log in logs if not is_relevant(log)]
    selected_logs = (relevant_logs + fallback_logs)[:max(max_samples, 0)]
    return [sanitize_sta_log_sample(log, salt) for log in selected_logs]


def build_local_traceability_map(logs: list[dict], salt: str) -> dict:
    """Build a local-only pseudonym map. Never send this map to Bedrock or PDF."""
    traceability_map: dict = {"users": {}, "ips": {}}
    for log in logs:
        context = log.get("context", {})
        user = context.get("principalId", "")
        if user:
            traceability_map["users"][stable_hash(user, salt, prefix="user")] = user
        source_ip = context.get("originatingAddress", "")
        if source_ip:
            masked_ip = mask_ip(source_ip, GOVERNANCE_MASK_IP_MODE)
            traceability_map["ips"].setdefault(masked_ip, [])
            if source_ip not in traceability_map["ips"][masked_ip]:
                traceability_map["ips"][masked_ip].append(source_ip)
    return traceability_map


def build_local_risk_findings(analysis: dict) -> list[dict]:
    """Create short identifier-free findings for the AI payload and PDF narrative."""
    return [
        {"finding": "Falhas recorrentes de autenticação", "evidence": analysis["auth_failure_count"], "priority": "Alta"},
        {"finding": "Eventos administrativos com autenticação fraca", "evidence": analysis["admin_weak_auth_events"], "priority": "Alta"},
        {"finding": "Acessos negados por política", "evidence": analysis["denied_access_count"], "priority": "Média"},
        {"finding": "Rejeições de assertion SAML", "evidence": analysis["saml_assertion_rejected_count"], "priority": "Média"},
        {"finding": "Timeouts de Push", "evidence": analysis["push_timeout_count"], "priority": "Média"},
    ]


def build_minimized_governance_payload_for_ai(
    analysis: dict,
    recommendations: list[dict],
    logs: list[dict],
    fetch_metadata: dict | None = None,
) -> dict:
    """Build the only governance payload allowed to be sent to Bedrock."""
    metadata = fetch_metadata or {}
    metric_keys = [
        "total_log_entries", "total_access_requests", "total_authentications",
        "accepted_access_count", "failed_access_count", "denied_access_count",
        "auth_success_count", "auth_failure_count", "success_rate", "failure_rate",
        "high_risk_country_events", "admin_events", "admin_weak_auth_events",
        "saml_assertion_rejected_count", "push_timeout_count", "account_locked_count",
        "password_only_or_weak_auth_events",
    ]
    return {
        "privacy_notice": {
            "privacy_mode": GOVERNANCE_PRIVACY_MODE,
            "raw_logs_sent_to_ai": False,
            "data_minimization": True,
            "pseudonymization": True,
            "description": "A IA recebe somente métricas agregadas, achados, recomendações e amostras mascaradas.",
        },
        "collection_context": {
            "solution": "SafeNet Trusted Access (STA)",
            "period_days": metadata.get("days", analysis.get("analysis_period_days", GOVERNANCE_DEFAULT_DAYS)),
            "source": "Simulação local da API de Logs do STA",
            "total_logs_collected": metadata.get("total_logs", analysis.get("total_log_entries", 0)),
        },
        "aggregated_metrics": {key: analysis.get(key) for key in metric_keys},
        "correlation_summary": {
            "top_failed_users": [
                [stable_hash(user, GOVERNANCE_HASH_SALT, prefix="user"), count]
                for user, count in analysis.get("top_failed_users", [])
            ],
            "top_failed_source_ips": [
                [mask_ip(source_ip, GOVERNANCE_MASK_IP_MODE), count]
                for source_ip, count in analysis.get("top_failed_source_ips", [])
            ],
            "top_failed_applications": analysis.get("top_failed_applications", []),
            "policies_with_high_failure_rate": analysis.get("policies_with_high_failure_rate", []),
            "applications_with_saml_errors": analysis.get("applications_with_saml_errors", []),
            "users_recommended_for_review": [
                stable_hash(user, GOVERNANCE_HASH_SALT, prefix="user")
                for user in analysis.get("users_recommended_for_review", [])
            ],
            "source_ips_recommended_for_block_or_review": [
                mask_ip(source_ip, GOVERNANCE_MASK_IP_MODE)
                for source_ip in analysis.get("source_ips_recommended_for_block_or_review", [])
            ],
            "policy_distribution": analysis.get("policy_distribution", {}),
            "scenario_distribution": analysis.get("scenario_distribution", {}),
        },
        "risk_findings": build_local_risk_findings(analysis),
        "policy_recommendations": recommendations,
        "sanitized_log_samples": sanitize_sta_logs_for_ai(
            logs, GOVERNANCE_MAX_SANITIZED_SAMPLES, GOVERNANCE_HASH_SALT
        ),
    }


def validate_minimized_payload(payload: dict) -> list[str]:
    """Return privacy issues found in the serialized AI payload."""
    serialized = json.dumps(payload, ensure_ascii=False)
    issues: list[str] = []
    if re.search(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", serialized):
        issues.append("Foi encontrado um endereço de e-mail.")
    if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", serialized):
        issues.append("Foi encontrado um endereço IPv4 completo.")
    for forbidden_key in ("tenantId", "tenantCode", "sessionId", "accountName"):
        if f'"{forbidden_key}"' in serialized:
            issues.append(f"Foi encontrada a chave sensível {forbidden_key}.")
    if GOVERNANCE_REMOVE_SESSION_IDENTIFIERS and '"globalAccessId"' in serialized:
        issues.append("Foi encontrada a chave globalAccessId.")
    for match in re.finditer(r'"principalId"\s*:\s*"([^"]*)"', serialized):
        if match.group(1) and not match.group(1).startswith("user_"):
            issues.append("Foi encontrado principalId sem pseudonimização.")
            break
    return issues


def build_policy_recommendations(analysis: dict) -> list[dict]:
    recommendations: list[dict] = []

    def add(
        policy_name: str,
        priority: str,
        finding: str,
        scenario_or_condition: str,
        recommended_decision: str,
        target: str,
        expected_risk_reduction: str,
        implementation_hint: str,
    ) -> None:
        recommendations.append({
            "policy_name": policy_name,
            "priority": priority,
            "finding": finding,
            "scenario_or_condition": scenario_or_condition,
            "recommended_decision": recommended_decision,
            "target": target,
            "expected_risk_reduction": expected_risk_reduction,
            "implementation_hint": implementation_hint,
        })

    if analysis["admin_weak_auth_events"]:
        add(
            "Require FIDO2 or Certificate for Admins", "Alta",
            f"{analysis['admin_weak_auth_events']} eventos administrativos foram identificados com autenticação fraca.",
            "Group Membership = Admins OR applicationName in ['AWS Console', 'Office 365', 'Portal Interno']",
            "Grant access only with FIDO2 or Certificate. Deny password-only access.",
            "Contas administrativas e aplicações críticas",
            "Reduz risco de comprometimento de contas privilegiadas.",
            "Criar cenário específico para grupo administrativo e aplicar método forte como FIDO2/certificado.",
        )
    if analysis["source_ips_recommended_for_block_or_review"]:
        masked_sources = [
            mask_ip(source_ip, GOVERNANCE_MASK_IP_MODE)
            for source_ip in analysis["source_ips_recommended_for_block_or_review"]
        ]
        add(
            "Restrict Repeated Failed Sources", "Média",
            f"IPs mascarados com falhas recorrentes: {', '.join(masked_sources)}.",
            "source IP with repeated authentication failures",
            "Deny or require stronger MFA after threshold.",
            "Aplicações com falhas recorrentes",
            "Reduz risco de brute force, password spraying e tentativas automatizadas.",
            "Criar cenário por origem de rede/IP e aplicar negação ou step-up após o limiar definido.",
        )
    if analysis["high_risk_country_denied_count"]:
        add(
            "Block High Risk Countries", "Alta",
            f"{analysis['high_risk_country_denied_count']} acessos de países de maior risco foram negados.",
            "geo.country in ['RU', 'CN'] OR IP reputation high risk",
            "Deny access or require step-up authentication.",
            "Todas as aplicações expostas externamente",
            "Reduz exposição a acessos originados fora do perfil esperado.",
            "Criar cenário de geolocalização/IP de maior risco e manter uma decisão padrão explícita para os demais acessos.",
        )
    if analysis["saml_assertion_rejected_count"]:
        add(
            "Review SAML Application Policy", "Média",
            f"{analysis['saml_assertion_rejected_count']} rejeições SAML em: {', '.join(analysis['applications_with_saml_errors'])}.",
            "applicationName with repeated SAML assertion rejected",
            "Review application configuration and keep MFA policy active.",
            "Aplicações SAML com falhas recorrentes",
            "Reduz falhas de acesso legítimo e indisponibilidade operacional.",
            "Validar ACS URL, Entity ID, certificado, NameID e mapeamento de atributos.",
        )
    if analysis["push_timeout_count"]:
        add(
            "MobilePASS+ Push Reliability and Fallback", "Média",
            f"{analysis['push_timeout_count']} timeouts de autenticação push foram observados.",
            "High push timeout rate",
            "Allow fallback OTP only after push timeout and monitor repeated failures.",
            "Usuários com Push OTP recorrente",
            "Melhora experiência do usuário sem reduzir controle de acesso.",
            "Revisar entrega push, conectividade e permitir fallback OTP somente após timeout.",
        )
    if analysis["password_only_or_weak_auth_events"]:
        add(
            "MFA Required for External Access", "Alta",
            f"{analysis['password_only_or_weak_auth_events']} eventos utilizaram Password, SMS OTP ou Email OTP.",
            "External access or non-corporate network",
            "Require Push OTP, FIDO2 or Certificate; avoid password-only access.",
            "Aplicações SaaS e acessos externos",
            "Reduz risco associado a credenciais comprometidas.",
            "Usar contexto de rede, Authentication Level e aplicação para exigir MFA ou step-up.",
        )
    if analysis["top_failed_applications"]:
        app, count = analysis["top_failed_applications"][0]
        add(
            "Application Risk-Based Step-up", "Baixa",
            f"A aplicação {app} concentrou {count} falhas relacionadas.",
            f"applicationName = '{app}' AND high-risk context",
            "Require step-up authentication when the scenario matches; otherwise apply the default policy decision.",
            app,
            "Melhora controle de acesso com impacto direcionado.",
            "Combinar contexto da aplicação com rede/IP, navegador/SO, localização e nível de autenticação.",
        )
    return recommendations


def build_local_recommendations(analysis: dict) -> list[dict]:
    return build_policy_recommendations(analysis)


def generate_governance_report_with_bedrock(
    logs: list[dict],
    analysis: dict,
    recommendations: list[dict],
    fetch_metadata: dict | None = None,
) -> str:
    minimized_payload = build_minimized_governance_payload_for_ai(
        analysis, recommendations, logs, fetch_metadata
    )
    privacy_issues = validate_minimized_payload(minimized_payload)
    if privacy_issues:
        raise RuntimeError(
            "Payload minimizado falhou na validação de privacidade: "
            + " ".join(privacy_issues)
        )
    prompt = f"""
Gere um relatório formal com o título:
"Relatório Executivo de Governança — SafeNet Trusted Access"

Use português do Brasil e tom profissional para diretores e governança.
Inclua obrigatoriamente estas afirmações perto do início:
- "A análise foi realizada com minimização e pseudonimização dos dados antes do envio à IA."
- "A IA não recebeu logs brutos, identificadores diretos de usuários, IPs completos, tenantId, sessionId ou tokens."
- "Os dados analisados neste MVP são simulados para fins de demonstração."

Você receberá um pacote de dados previamente minimizado e pseudonimizado. Não solicite nem presuma dados brutos.
Não tente reidentificar usuários, IPs ou sessões. Use apenas métricas agregadas, correlações, achados de risco,
recomendações locais e amostras sanitizadas.

Não invente fatos, métricas, ambientes ou dados reais de cliente. Use somente o pacote sanitizado fornecido.

Estruture o relatório com:
1. Sumário Executivo
2. Escopo da Análise
3. Indicadores Principais
4. Leitura de Risco
5. Principais Achados
6. Recomendações de Políticas
7. Priorização das Ações
8. Roadmap Sugerido
9. Conclusão Executiva

Use títulos simples, parágrafos executivos curtos e bullets somente quando forem úteis.
Não use tabelas Markdown, blocos de código, listas profundamente aninhadas, linhas longas ou excesso de marcadores em negrito.
O PDF final será montado pela aplicação, portanto mantenha o texto limpo e fácil de converter.

Considere explicitamente estes conceitos de política do STA:
- Políticas de acesso decidem se o acesso é concedido ou negado.
- Quando o acesso é concedido, a política pode definir o método de autenticação exigido.
- Cenários alteram o comportamento da política conforme condições de rede/IP, navegador/SO, localização,
  grupo, aplicação, nível de autenticação e risco.
- Quando um cenário corresponde à requisição, sua decisão é aplicada; caso contrário, vale a decisão padrão.
- Priorize hardening administrativo, restrições de geolocalização/IP, step-up e revisão SAML/OIDC quando aplicável.

Na seção "Recomendações de políticas", detalhe para cada ação:
- Nome sugerido da política
- Trigger/cenário
- Ação
- Público-alvo ou aplicação
- Redução de risco esperada

Pacote sanitizado e minimizado:
{json.dumps(minimized_payload, ensure_ascii=False, indent=2)}
"""
    try:
        return call_governance_bedrock(prompt, BEDROCK_MODEL_ID)
    except ClientError:
        if BEDROCK_FALLBACK_MODEL_ID == BEDROCK_MODEL_ID:
            raise
        return call_governance_bedrock(prompt, BEDROCK_FALLBACK_MODEL_ID)


def call_governance_bedrock(prompt: str, model_id: str) -> str:
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    response = client.converse(
        modelId=model_id,
        system=[
            {
                "text": (
                    "Você gera relatórios executivos de governança em português do Brasil. "
                    "Use somente os dados simulados fornecidos. Não invente informações."
                )
            }
        ],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 2500, "temperature": 0.1, "topP": 0.9},
    )
    return response["output"]["message"]["content"][0]["text"]


def generate_governance_pdf(
    report_text: str, analysis: dict, recommendations: list[dict], output_path: str | BytesIO
) -> str | BytesIO:
    pdf_bytes = generate_governance_pdf_bytes(report_text, analysis, recommendations)
    if isinstance(output_path, BytesIO):
        output_path.write(pdf_bytes)
    else:
        Path(output_path).write_bytes(pdf_bytes)
    return output_path


def prepare_pdf_download(report_text: str, analysis: dict, recommendations: list[dict]) -> bytes:
    return generate_governance_pdf_bytes(report_text, analysis, recommendations)


def _pdf_paragraph(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(value or "")).replace("\n", "<br/>"), style)


def _chart_image(
    labels: list[str], values: list[int], title: str, color: str = "#1F4E78"
) -> Image:
    figure, axis = plt.subplots(figsize=(7.2, 3.1))
    axis.bar(labels or ["Sem dados"], values or [0], color=color)
    axis.set_title(title, fontsize=11, fontweight="bold")
    axis.tick_params(axis="x", labelrotation=25, labelsize=8)
    axis.tick_params(axis="y", labelsize=8)
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    image_buffer = BytesIO()
    figure.savefig(image_buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(figure)
    image_buffer.seek(0)
    return Image(image_buffer, width=16.6 * cm, height=7.1 * cm)


def markdown_to_clean_pdf_flowables(report_text: str, styles) -> list:
    flowables: list = []
    for line in report_text.splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line == "---":
            flowables.append(Spacer(1, 0.12 * cm))
            continue
        if clean_line.startswith("###"):
            flowables.append(_pdf_paragraph(clean_line.lstrip("# ").strip(), styles["Heading3"]))
            continue
        if clean_line.startswith("#"):
            flowables.append(_pdf_paragraph(clean_line.lstrip("# ").strip(), styles["SectionTitle"]))
            continue
        if clean_line.startswith(("- ", "* ")):
            clean_line = f"• {clean_line[2:].strip()}"
        clean_line = re.sub(r"[*_`]+", "", clean_line)
        flowables.append(_pdf_paragraph(clean_line, styles["BodyText"]))
        flowables.append(Spacer(1, 0.06 * cm))
    return flowables


def generate_governance_pdf_bytes(
    report_text: str,
    analysis: dict,
    recommendations: list[dict],
    preview_df: pd.DataFrame | None = None,
) -> bytes:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CoverTitle", parent=styles["Title"], alignment=TA_CENTER,
        fontSize=25, leading=30, textColor=colors.HexColor("#17365D"),
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle", parent=styles["Heading2"], alignment=TA_CENTER,
        fontSize=15, leading=19, textColor=colors.HexColor("#1F4E78"),
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle", parent=styles["Heading2"], fontSize=15, leading=19,
        textColor=colors.HexColor("#17365D"), spaceBefore=10, spaceAfter=7,
    ))
    styles.add(ParagraphStyle(name="TableText", parent=styles["BodyText"], fontSize=7, leading=8.5))
    styles.add(ParagraphStyle(
        name="Disclaimer", parent=styles["BodyText"], alignment=TA_CENTER,
        fontSize=9, leading=13, textColor=colors.HexColor("#555555"),
    ))
    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer, pagesize=A4, rightMargin=1.35 * cm, leftMargin=1.35 * cm,
        topMargin=1.5 * cm, bottomMargin=1.45 * cm,
    )
    story = [
        Spacer(1, 3.2 * cm),
        Paragraph("Relatório Executivo de Governança", styles["CoverTitle"]),
        Spacer(1, 0.35 * cm),
        Paragraph("SafeNet Trusted Access (STA)", styles["CoverSubtitle"]),
        Spacer(1, 0.6 * cm),
        Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Disclaimer"]),
        Paragraph(f"Período analisado: últimos {analysis.get('analysis_period_days', 7)} dias", styles["Disclaimer"]),
        Spacer(1, 1.1 * cm),
        Paragraph("Dados simulados para fins de demonstração do MVP.", styles["Disclaimer"]),
        Spacer(1, 6.5 * cm),
        Paragraph("NeoIA Security Portal", styles["CoverSubtitle"]),
        PageBreak(),
        Paragraph("Proteção e Soberania dos Dados", styles["SectionTitle"]),
    ]
    privacy_data = [
        ["Controle", "Status"],
        ["Minimização de dados", "Ativa"],
        ["Pseudonimização", "Ativa"],
        ["Logs brutos enviados à IA", "Não"],
        ["Usuários", "Hash estável"],
        ["IPs", "Mascaramento parcial"],
        ["Identificadores de sessão", "Removidos/pseudonimizados"],
        ["Identificadores de tenant/conta", "Removidos"],
        ["Máximo de amostras sanitizadas", str(GOVERNANCE_MAX_SANITIZED_SAMPLES)],
    ]
    privacy_table = Table(privacy_data, colWidths=[9.5 * cm, 6.5 * cm])
    privacy_table.setStyle(_standard_pdf_table_style())
    story.extend([
        privacy_table,
        Spacer(1, 0.35 * cm),
        Paragraph(
            "Para este relatório, a IA recebeu apenas métricas agregadas, correlações, achados de risco, "
            "recomendações locais e amostras sanitizadas. Os logs brutos não foram enviados ao modelo.",
            styles["BodyText"],
        ),
        Spacer(1, 0.35 * cm),
        Paragraph("Indicadores Executivos", styles["SectionTitle"]),
    ])
    indicator_data = [
        ["Indicador", "Valor"],
        ["Total de eventos", str(analysis["total_log_entries"])],
        ["Requisições de acesso", str(analysis["total_access_requests"])],
        ["Autenticações", str(analysis["total_authentications"])],
        ["Taxa de sucesso", f"{analysis['success_rate']:.2f}%"],
        ["Taxa de falha", f"{analysis['failure_rate']:.2f}%"],
        ["Eventos negados", str(analysis["denied_access_count"])],
        ["Contas bloqueadas", str(analysis["account_locked_count"])],
        ["Eventos administrativos com autenticação fraca", str(analysis["admin_weak_auth_events"])],
    ]
    indicators_table = Table(indicator_data, colWidths=[11 * cm, 5 * cm])
    indicators_table.setStyle(_standard_pdf_table_style())
    story.extend([
        indicators_table,
        Spacer(1, 0.45 * cm),
        Paragraph("Visão Gráfica", styles["SectionTitle"]),
        _chart_image(["Sucesso", "Falha"], [analysis["auth_success_count"], analysis["auth_failure_count"]],
                     "Distribuição dos resultados de autenticação", "#2E75B6"),
        Spacer(1, 0.2 * cm),
        _chart_image(list(analysis["credential_type_distribution"]), list(analysis["credential_type_distribution"].values()),
                     "Distribuição por tipo de credencial", "#70AD47"),
        Spacer(1, 0.2 * cm),
        _chart_image([item[0] for item in analysis["top_failed_applications"]],
                     [item[1] for item in analysis["top_failed_applications"]],
                     "Top 5 aplicações por falhas", "#C55A11"),
        PageBreak(),
        Paragraph("Principais Achados de Risco", styles["SectionTitle"]),
    ])
    findings = [
        ("Autenticação administrativa fraca", analysis["admin_weak_auth_events"], "Comprometimento privilegiado", "Alta"),
        ("Falhas recorrentes de autenticação", analysis["auth_failure_count"], "Tentativas indevidas", "Alta"),
        ("Acessos negados por política", analysis["denied_access_count"], "Acesso fora da política", "Média"),
        ("Rejeições de assertion SAML", analysis["saml_assertion_rejected_count"], "Indisponibilidade federada", "Média"),
        ("Timeouts de Push", analysis["push_timeout_count"], "Atrito e fallback indevido", "Média"),
    ]
    findings_data = [["Achado", "Evidência", "Risco", "Prioridade"]]
    findings_data.extend([
        [_pdf_paragraph(value, styles["TableText"]) for value in row] for row in findings
    ])
    findings_table = Table(findings_data, colWidths=[5.3 * cm, 2.1 * cm, 5.7 * cm, 2.5 * cm], repeatRows=1)
    findings_table.setStyle(_standard_pdf_table_style())
    story.extend([findings_table, Spacer(1, 0.45 * cm), Paragraph("Recomendações de Políticas", styles["SectionTitle"])])
    recommendation_data = [["Prioridade", "Política sugerida", "Cenário/Condição", "Decisão recomendada", "Alvo"]]
    for item in recommendations:
        recommendation_data.append([
            _pdf_paragraph(item["priority"], styles["TableText"]),
            _pdf_paragraph(item["policy_name"], styles["TableText"]),
            _pdf_paragraph(item["scenario_or_condition"], styles["TableText"]),
            _pdf_paragraph(item["recommended_decision"], styles["TableText"]),
            _pdf_paragraph(item["target"], styles["TableText"]),
        ])
    recommendations_table = Table(
        recommendation_data, colWidths=[1.5 * cm, 3.2 * cm, 4.1 * cm, 4.1 * cm, 2.7 * cm], repeatRows=1
    )
    recommendations_table.setStyle(_standard_pdf_table_style())
    story.extend([
        recommendations_table,
        PageBreak(),
        Paragraph("Narrativa Executiva", styles["SectionTitle"]),
        *markdown_to_clean_pdf_flowables(report_text, styles),
    ])

    def add_page_footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(1.35 * cm, 0.75 * cm, "NeoIA Security Portal - MVP")
        canvas.drawRightString(A4[0] - 1.35 * cm, 0.75 * cm, f"Página {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=add_page_footer, onLaterPages=add_page_footer)
    return pdf_buffer.getvalue()


def _standard_pdf_table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


def flatten_sta_log(log: dict) -> dict:
    context = log.get("context", {})
    details = log.get("details", {})
    return {
        "timeStamp": log.get("timeStamp", ""),
        "details.type": details.get("type", ""),
        "context.principalId": context.get("principalId", ""),
        "context.applicationName": context.get("applicationName", ""),
        "context.applicationType": context.get("applicationType", ""),
        "context.originatingAddress": context.get("originatingAddress", ""),
        "context.policyName": context.get("policyName", ""),
        "context.scenarioName": context.get("scenarioName", ""),
        "details.state/resultText": details.get("state") or details.get("resultText", ""),
        "details.reason/message": details.get("reason") or details.get("message", ""),
        "details.credentialType": details.get("credentialType", ""),
    }


def build_governance_preview_dataframe(logs: list[dict]) -> pd.DataFrame:
    correlated = correlate_sta_logs(logs)
    failed_ips = Counter(
        auth["context"].get("originatingAddress", "")
        for group in correlated.values()
        for auth in group["authentications"]
        if auth.get("details", {}).get("result") == "1"
    )
    rows: list[dict] = []
    for group in correlated.values():
        access = group.get("access")
        if not access:
            continue
        auth = group["authentications"][0] if group["authentications"] else {}
        context = access.get("context", {})
        access_details = access.get("details", {})
        auth_details = auth.get("details", {})
        principal_id = context.get("principalId", "")
        source_ip = context.get("originatingAddress", "")
        country = context.get("geo", {}).get("country", "")
        credential_type = auth_details.get("credentialType", "")
        reason = access_details.get("reason", "")
        risk_signal = "OK"
        if principal_id.startswith("admin.") and credential_type in {"Password", "SMS OTP", "Email OTP"}:
            risk_signal = "Admin com autenticação fraca"
        elif reason == "SASIDP_SAML_ASSERTION_REJECTED":
            risk_signal = "Erro SAML"
        elif reason == "SASIDP_PUSH_TIMEOUT":
            risk_signal = "Timeout Push"
        elif country in {"RU", "CN"}:
            risk_signal = "País de risco"
        elif access_details.get("state") == "Denied":
            risk_signal = "Acesso negado"
        elif failed_ips[source_ip] > 5:
            risk_signal = "Falha recorrente"
        rows.append({
            "timeStamp": access.get("timeStamp", ""),
            "principalId": principal_id,
            "applicationName": context.get("applicationName", ""),
            "applicationType": context.get("applicationType", ""),
            "originatingAddress": source_ip,
            "policyName": context.get("policyName", ""),
            "scenarioName": context.get("scenarioName", ""),
            "accessState": access_details.get("state", ""),
            "authResult": auth_details.get("resultText", ""),
            "credentialType": credential_type,
            "riskSignal": risk_signal,
        })
    return pd.DataFrame(rows).sort_values("timeStamp", ascending=False)


def governance_insights(analysis: dict) -> list[str]:
    insights: list[str] = []
    if analysis["top_failed_users"]:
        user, count = analysis["top_failed_users"][0]
        insights.append(f"Usuário com mais falhas: {user} ({count}).")
    if analysis["top_failed_source_ips"]:
        source_ip, count = analysis["top_failed_source_ips"][0]
        insights.append(f"IP de origem com mais falhas: {source_ip} ({count}).")
    if analysis["top_failed_applications"]:
        application, count = analysis["top_failed_applications"][0]
        insights.append(f"Aplicação com mais falhas: {application} ({count}).")
    if analysis["repeated_denies_by_policy"]:
        policy, count = max(analysis["repeated_denies_by_policy"].items(), key=lambda item: item[1])
        insights.append(f"Política com mais negações: {policy} ({count}).")
    insights.append(
        f"Eventos administrativos com autenticação fraca: {analysis['admin_weak_auth_events']}."
    )
    return insights[:5]


def render_sidebar() -> None:
    with st.sidebar.expander("Diagnóstico Bedrock", expanded=False):
        st.write(f"AWS_REGION: `{AWS_REGION}`")
        st.write(f"BEDROCK_MODEL_ID: `{BEDROCK_MODEL_ID}`")
        st.write(f"BEDROCK_FALLBACK_MODEL_ID: `{BEDROCK_FALLBACK_MODEL_ID}`")
        token_status = "configurado" if os.getenv("AWS_BEARER_TOKEN_BEDROCK") else "não configurado"
        st.write(f"AWS_BEARER_TOKEN_BEDROCK: **{token_status}**")
        st.info("Modelo configurado para o MVP: Amazon Nova Pro")

    with st.sidebar.expander("Fontes de conhecimento", expanded=False):
        st.write(f"LOCAL_RAG_ENABLED: `{LOCAL_RAG_ENABLED}`")
        st.write(f"LOCAL_RAG_DOC_PATH: `{LOCAL_RAG_DOC_PATH}`")
        st.write(f"Arquivo local existe: `{os.path.exists(LOCAL_RAG_DOC_PATH)}`")
        st.write(f"PUBLIC_DOC_LOOKUP_ENABLED: `{PUBLIC_DOC_LOOKUP_ENABLED}`")
        st.write(f"PUBLIC_DOC_MAX_URLS: `{PUBLIC_DOC_MAX_URLS}`")
        st.write("PUBLIC_DOC_URLS:")
        for url in load_public_doc_urls():
            st.write(f"- {url}")
        st.write(f"COMBINED_CONTEXT_MAX_CHARS: `{COMBINED_CONTEXT_MAX_CHARS}`")

    with st.sidebar.expander("Governança e privacidade", expanded=False):
        st.write(f"GOVERNANCE_PRIVACY_MODE: `{GOVERNANCE_PRIVACY_MODE}`")
        st.write(f"GOVERNANCE_SEND_RAW_LOGS_TO_AI: `{GOVERNANCE_SEND_RAW_LOGS_TO_AI}`")
        st.write(f"GOVERNANCE_MAX_SANITIZED_SAMPLES: `{GOVERNANCE_MAX_SANITIZED_SAMPLES}`")
        st.write(f"GOVERNANCE_MASK_IP_MODE: `{GOVERNANCE_MASK_IP_MODE}`")
        st.write(
            "GOVERNANCE_REMOVE_SESSION_IDENTIFIERS: "
            f"`{GOVERNANCE_REMOVE_SESSION_IDENTIFIERS}`"
        )
        st.info("Logs brutos não são enviados para a IA por padrão.")
        st.write(f"GOVERNANCE_LOG_DIR: `{GOVERNANCE_LOG_DIR}`")
        st.write(f"GOVERNANCE_REPORT_DIR: `{GOVERNANCE_REPORT_DIR}`")
        st.write(f"GOVERNANCE_USE_FAKE_STA_API: `{GOVERNANCE_USE_FAKE_STA_API}`")

    with st.sidebar.expander("Integração de chamados", expanded=False):
        st.write(f"TICKET_API_MODE: `{TICKET_API_MODE}`")
        ticket_api_status = "configurado" if TICKET_API_URL else "não configurado"
        email_status = "configurado" if EMAIL_ENABLED else "não configurado"
        st.write(f"TICKET_API_URL: **{ticket_api_status}**")
        st.write(f"EMAIL_ENABLED: **{email_status}**")
        if TICKET_API_MODE == "generic":
            st.write(f"TICKET_API_METHOD: `{TICKET_API_METHOD}`")


def render_sources(local_sources: list[str], public_sources: list[str]) -> None:
    st.subheader("Fontes usadas")
    st.write("**Documentação local**")
    if local_sources:
        for source in local_sources:
            st.write(f"- `{source}`")
    else:
        st.write("- Nenhuma fonte local relevante recuperada.")

    st.write("**Documentação pública**")
    if public_sources:
        for source in public_sources:
            st.write(f"- {source}")
    else:
        st.write("- Nenhuma fonte pública relevante recuperada.")


def render_technical_area() -> None:
    st.title("chatbot")
    st.warning(
        "Este MVP usa documentação local e URLs públicas allowlistadas. "
        "Ele não navega livremente na internet."
    )

    question = st.text_area("Pergunta técnica")
    if st.button("Enviar pergunta"):
        if not question.strip():
            st.warning("Digite uma pergunta técnica.")
        else:
            with st.spinner("Consultando documentação e Amazon Bedrock..."):
                try:
                    answer, local_sources, public_sources = ask_bedrock(question.strip())
                    st.session_state["answer"] = answer
                    st.session_state["local_sources"] = local_sources
                    st.session_state["public_sources"] = public_sources
                except ClientError as error:
                    st.error(f"Erro ao consultar o Amazon Bedrock: {error}")
                except Exception as error:
                    st.error(f"Não foi possível responder: {error}")

    if "answer" in st.session_state:
        st.subheader("Resposta")
        st.write(st.session_state["answer"])
        render_sources(
            st.session_state.get("local_sources", []),
            st.session_state.get("public_sources", []),
        )
        st.write("A resposta resolveu o problema?")
        if st.button("Sim, resolveu"):
            st.success("Atendimento concluído.")
        if st.button("Não resolveu - abrir chamado de teste"):
            try:
                with st.spinner("Criando chamado de teste..."):
                    ticket_response = create_test_ticket()
                st.success("Chamado de teste criado.")
                if isinstance(ticket_response, dict):
                    st.json(ticket_response)
                else:
                    st.text(ticket_response or "Resposta vazia da API.")
            except Exception as error:
                st.error(f"Não foi possível criar o chamado de teste: {error}")


def render_governance_area() -> None:
    ensure_governance_directories()
    st.title("Ala de Governança")
    st.subheader("Relatório executivo a partir de logs do SafeNet Trusted Access")
    st.write(
        "Neste MVP, a busca de logs simula uma chamada à API de Logs do STA "
        "usando uma base local previamente preparada."
    )
    st.info("Dados simulados para fins de demonstração.")
    solution = st.selectbox("Solução", ["SafeNet Trusted Access (STA)"])
    days = st.slider(
        "Período de análise", min_value=1, max_value=30, value=GOVERNANCE_DEFAULT_DAYS,
        step=1, format="%d dias",
    )
    if st.button("Buscar logs", type="primary"):
        logs, metadata = simulate_sta_logs_api_fetch(int(days))
        if not logs or len(metadata["files_read"]) < int(days):
            prepare_local_sta_demo_dataset(days=max(int(days), 7), events_per_day=100)
            logs, metadata = simulate_sta_logs_api_fetch(int(days))
        analysis = analyze_sta_logs(logs)
        analysis["analysis_period_days"] = int(days)
        recommendations = build_policy_recommendations(analysis)
        st.session_state["governance_logs"] = logs
        st.session_state["governance_fetch_metadata"] = metadata
        st.session_state["governance_analysis"] = analysis
        st.session_state["governance_recommendations"] = recommendations
        st.session_state["governance_preview_df"] = build_governance_preview_dataframe(logs)
        st.session_state["local_traceability_map"] = build_local_traceability_map(
            logs, GOVERNANCE_HASH_SALT
        )
        st.session_state.pop("governance_report", None)
        st.session_state.pop("governance_pdf", None)

    logs = st.session_state.get("governance_logs", [])
    metadata = st.session_state.get("governance_fetch_metadata")
    if metadata:
        st.success("Logs carregados com sucesso a partir da simulação da API de Logs do STA.")
        st.subheader("Detalhes da coleta")
        metadata_columns = st.columns(3)
        metadata_columns[0].write(f"**Solução:** {solution}")
        metadata_columns[1].write(f"**Período:** últimos {metadata['days']} dias")
        metadata_columns[2].write(f"**Eventos coletados:** {metadata['total_logs']}")
        metadata_columns = st.columns(2)
        metadata_columns[0].write("**Fonte da coleta:** Simulação local da API de Logs do STA")
        metadata_columns[1].write(f"**Data/hora da coleta:** {metadata['collected_at']}")
        st.write(f"**Arquivos locais consultados:** {len(metadata['files_read'])}")
    if not logs:
        st.write("Busque os logs para visualizar a correlação e gerar o relatório executivo.")
        return

    analysis = st.session_state["governance_analysis"]
    recommendations = st.session_state["governance_recommendations"]
    preview_df = st.session_state["governance_preview_df"]
    st.subheader("Prévia da correlação")
    metric_columns = st.columns(3)
    metric_columns[0].metric("Total de eventos", analysis["total_log_entries"])
    metric_columns[1].metric("Requisições de acesso", analysis["total_access_requests"])
    metric_columns[2].metric("Autenticações", analysis["total_authentications"])
    metric_columns = st.columns(3)
    metric_columns[0].metric("Taxa de sucesso", f"{analysis['success_rate']:.2f}%")
    metric_columns[1].metric("Eventos negados", analysis["denied_access_count"])
    metric_columns[2].metric("Admin com autenticação fraca", analysis["admin_weak_auth_events"])
    st.dataframe(preview_df.head(10), width="stretch", hide_index=True)
    st.write("**Insights principais**")
    for insight in governance_insights(analysis):
        st.write(f"- {insight}")
    with st.expander("Ver amostra de logs brutos"):
        st.json(logs[:4])
    with st.expander("Ver dataframe completo"):
        st.dataframe(preview_df, width="stretch", hide_index=True)

    minimized_payload = build_minimized_governance_payload_for_ai(
        analysis, recommendations, logs, metadata
    )
    privacy_issues = validate_minimized_payload(minimized_payload)
    st.subheader("Proteção e Soberania dos Dados")
    if GOVERNANCE_SEND_RAW_LOGS_TO_AI:
        st.error("Atenção: envio de logs brutos para IA está habilitado. Não recomendado para produção.")
    privacy_columns = st.columns(2)
    privacy_columns[0].write("**Minimização de dados:** Ativa")
    privacy_columns[1].write("**Pseudonimização:** Ativa")
    privacy_columns[0].write("**Logs brutos enviados para IA:** Não")
    privacy_columns[1].write("**Usuários:** Hash estável")
    privacy_columns[0].write("**IPs:** Mascaramento parcial")
    privacy_columns[1].write("**IDs de sessão/globalAccessId:** Removidos ou pseudonimizados")
    privacy_columns[0].write("**Tenant/account identifiers:** Removidos")
    privacy_columns[1].write(
        f"**Máximo de amostras sanitizadas:** {GOVERNANCE_MAX_SANITIZED_SAMPLES}"
    )
    if privacy_issues:
        st.error("Payload minimizado falhou na validação de privacidade.")
        for issue in privacy_issues:
            st.write(f"- {issue}")
    else:
        st.success("Validação de privacidade: aprovada")
    with st.expander("Ver prévia do pacote sanitizado enviado para a IA"):
        st.caption(
            "Esta é a visão sanitizada enviada ao modelo. Os logs brutos permanecem apenas na aplicação."
        )
        st.json(minimized_payload)
    with st.expander("Mapa local de rastreabilidade — não enviado à IA"):
        st.warning(
            "Este mapa existe apenas localmente para auditoria e não é enviado ao modelo nem ao relatório."
        )
        st.json(st.session_state.get("local_traceability_map", {}))

    st.subheader("Relatório executivo")
    if st.button("Gerar relatório executivo", type="primary", disabled=bool(privacy_issues)):
        try:
            with st.spinner("Gerando relatório executivo com Amazon Nova Pro..."):
                report = generate_governance_report_with_bedrock(
                    logs, analysis, recommendations, metadata
                )
            st.session_state["governance_report"] = report
            try:
                st.session_state["governance_pdf"] = generate_governance_pdf_bytes(
                    report, analysis, recommendations, preview_df
                )
            except Exception as error:
                st.session_state.pop("governance_pdf", None)
                st.error(f"Não foi possível gerar o PDF: {error}")
        except ClientError as error:
            st.error(f"Erro ao consultar o Amazon Bedrock: {error}")
        except Exception as error:
            st.error(f"Não foi possível gerar o relatório: {error}")

    report = st.session_state.get("governance_report")
    if report:
        st.subheader("Relatório Executivo de Governança — SafeNet Trusted Access")
        st.markdown(report)
        download_columns = st.columns(2)
        if st.session_state.get("governance_pdf"):
            download_columns[0].download_button(
                "Baixar relatório executivo em PDF",
                data=st.session_state["governance_pdf"],
                file_name="relatorio_executivo_sta_mvp.pdf",
                mime="application/pdf",
                type="primary",
            )
        download_columns[1].download_button(
            "Baixar relatório em Markdown",
            data=report,
            file_name="relatorio_executivo_sta_mvp.md",
            mime="text/markdown",
        )


st.set_page_config(page_title="chatbot")
application_area = st.sidebar.radio(
    "Área da aplicação",
    ["Ala Técnica", "Ala de Governança"],
)
render_sidebar()
if application_area == "Ala Técnica":
    render_technical_area()
else:
    render_governance_area()
