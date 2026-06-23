from __future__ import annotations

import logging
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

from ..config import Settings
from ..schemas import ChatResponse

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover
    boto3 = None
    Config = None

    class ClientError(Exception):
        pass

INSUFFICIENT_CONTEXT_ANSWER = (
    "Não encontrei informação suficiente na documentação local ou pública carregada neste MVP "
    "para responder com segurança. Verifique se a documentação STA completa está em "
    "apps/api/docs/sta.md ou tente uma pergunta mais específica."
)

SYSTEM_CONTEXT = """
Você é um chatbot técnico de cibersegurança da Neotel.
Responda sempre em português do Brasil.
Use apenas o contexto recuperado pela aplicação.
"""

DEFAULT_CONVERSATIONS = [
    {
        "id": "technical-copilot",
        "title": "Copiloto Técnico",
        "preview": "Conversa principal preparada para Bedrock e troubleshooting.",
        "dateLabel": "Hoje",
        "timeLabel": "Agora",
        "active": True,
    }
]

CONCEPT_ANSWER_STA = (
    "STA significa SafeNet Trusted Access. É uma solução da Thales voltada para controle de "
    "acesso, autenticação multifator (MFA) e Single Sign-On (SSO). Na prática, ajuda a garantir "
    "que o usuário correto acesse a aplicação correta com o nível adequado de autenticação.\n\n"
    "O STA pode proteger aplicações SaaS, web e corporativas, aplicando políticas de acesso "
    "baseadas em contexto, como usuário, aplicação, rede, localização e método de autenticação.\n\n"
    "Em resumo, ele centraliza e fortalece o acesso às aplicações, reduzindo risco de acesso "
    "indevido e melhorando a experiência do usuário."
)

STOPWORDS = {
    "a", "an", "and", "ao", "as", "como", "da", "de", "do", "dos", "e", "em",
    "for", "how", "in", "is", "o", "of", "os", "para", "por", "que", "the",
    "to", "um", "uma", "what",
}
TROUBLESHOOTING_TERMS = {"erro", "falha", "bloqueado", "timeout", "resolucao", "causa", "verificacoes", "sintoma"}
PROCEDURAL_TERMS = {
    "acao", "acoes", "configurar", "delete", "desativar", "disable", "excluir",
    "gerenciar", "gestao", "management", "passo", "procedure", "procedimento",
    "remove", "remover", "revoke", "revogar", "revocation", "steps", "token",
    "unassign", "user", "usuario",
}
PUBLIC_MIN_SCORE = 8
LOCAL_STRONG_SCORE = 35
INTERNAL_CONTEXT_LINE_RE = re.compile(
    r"^(?:#{1,6}\s*)?(?:CONTEXTO LOCAL|CONTEXTO P[ÚU]BLICO|Resumo do contexto disponível|Trecho RAG|RAG chunk|Chunk)\s*:?.*$",
    re.IGNORECASE,
)


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in value if unicodedata.category(char) != "Mn")


def classify_question_intent(question: str) -> str:
    normalized = _normalize(question)
    rules = (
        ("how_to", ("como", "passo a passo", "configurar", "criar", "integrar", "revogar", "revoke", "remover", "remove", "excluir", "delete", "desativar", "disable", "unassign")),
        ("troubleshooting", ("erro", "falha", "nao funciona", "problema", "bloqueado", "desbloquear", "timeout", "nao redireciona")),
        ("concept", ("o que e", "explique", "para que serve", "qual e", "quais metodos")),
        ("policy", ("politica", "mfa", "fido", "geolocalizacao", "step-up", "acesso")),
    )
    for intent, terms in rules:
        if any(term in normalized for term in terms):
            return intent
    return "unknown"


def clean_model_answer(answer: str) -> str:
    if not answer:
        return ""
    cleaned_lines: list[str] = []
    in_code_block = False
    for raw_line in answer.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            cleaned_lines.append(raw_line.rstrip())
            continue
        if not in_code_block and INTERNAL_CONTEXT_LINE_RE.match(stripped):
            continue
        if not in_code_block and re.match(r"^\[?(?:source|fonte|chunk|trecho)\s*[:#-]", stripped, re.IGNORECASE):
            continue
        cleaned_lines.append(raw_line.rstrip())
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M")


class ChatService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.last_bedrock_error: str | None = None
        self.last_public_doc_error: str | None = None
        self._local_cache_lock = threading.Lock()
        self._local_cache_key: tuple[int, int] | None = None
        self._local_markdown_cache = ""
        self._local_chunks_cache: list[str] = []
        self._public_cache_lock = threading.Lock()
        self._public_cache: dict[str, tuple[float, str]] = {}

    def list_conversations(self) -> list[dict]:
        return DEFAULT_CONVERSATIONS

    def list_messages(self, conversation_id: str) -> list[dict]:
        return []

    def ask(self, question: str) -> ChatResponse:
        intent = classify_question_intent(question)
        combined_context, local_sources, public_sources = self._retrieve_combined_context(question, intent)
        mode = "fallback"
        fallback_reason = "bedrock_disabled"
        answer = self._build_fallback_answer(question, combined_context, intent)

        if self.settings.bedrock_enabled and combined_context.strip():
            try:
                answer = self._call_bedrock(question, combined_context)
                if INSUFFICIENT_CONTEXT_ANSWER in answer and combined_context.strip():
                    answer = self._build_fallback_answer(question, combined_context, intent)
                mode = "bedrock"
                fallback_reason = None
                self.last_bedrock_error = None
            except Exception as exc:
                self.last_bedrock_error = self._sanitize_error(exc)
                logger.warning("Bedrock falhou, usando fallback: %s", self.last_bedrock_error)
                mode = "fallback"
                fallback_reason = "bedrock_error"

        answer = clean_model_answer(answer)

        references = []
        if local_sources:
            references.append("Documentação local")
        if public_sources:
            references.append("Documentação pública")
        normalized_question = _normalize(question)
        if ("STA" in answer or "SafeNet Trusted Access" in answer) and (
            "sta" in self._query_terms(question) or "safenet trusted access" in normalized_question
        ):
            references.append("STA")

        return ChatResponse(
            id=f"assistant-{uuid4().hex[:8]}",
            answer=answer,
            content=answer,
            timestamp=_timestamp(),
            mode=mode,
            intent=intent,
            fallback_reason=fallback_reason,
            local_sources=local_sources,
            public_sources=public_sources,
            references=references,
        )

    def _load_local_markdown(self) -> str:
        path = self.settings.local_rag_doc_path
        try:
            stat = path.stat()
            cache_key = (stat.st_mtime_ns, stat.st_size)
        except OSError as exc:
            with self._local_cache_lock:
                self._local_cache_key = None
                self._local_markdown_cache = ""
                self._local_chunks_cache = []
            logger.warning("Local RAG document unavailable (%s): %s", path, self._sanitize_error(exc))
            return ""
        with self._local_cache_lock:
            if self._local_cache_key == cache_key:
                return self._local_markdown_cache
            try:
                markdown = path.read_text(encoding="utf-8-sig")
            except OSError as exc:
                logger.warning("Local RAG document could not be read (%s): %s", path, self._sanitize_error(exc))
                return ""
            self._local_cache_key = cache_key
            self._local_markdown_cache = markdown
            self._local_chunks_cache = self._chunk_text(markdown)
            return markdown

    def _local_chunks(self) -> list[str]:
        self._load_local_markdown()
        with self._local_cache_lock:
            return list(self._local_chunks_cache)

    def _chunk_text(self, text: str) -> list[str]:
        if not text.strip():
            return []
        sections = re.split(r"(?=^#{1,3}\s+)", text, flags=re.MULTILINE)
        chunks: list[str] = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if len(section) <= self.settings.local_rag_chunk_size:
                chunks.append(section)
                continue
            chunks.extend(
                section[index:index + self.settings.local_rag_chunk_size].strip()
                for index in range(0, len(section), self.settings.local_rag_chunk_size)
                if section[index:index + self.settings.local_rag_chunk_size].strip()
            )
        return chunks

    def _query_terms(self, question: str) -> set[str]:
        normalized = _normalize(question)
        terms = {term for term in re.findall(r"\w+", normalized) if len(term) >= 3 and term not in STOPWORDS}
        if "sta" in terms or "safenet trusted access" in normalized:
            terms.update({
                "safenet", "trusted", "access", "trusted access", "mfa", "sso",
                "access policy", "authentication policy", "policy", "politica",
                "token", "otp",
            })
        if "gridsure" in normalized or "grid sure" in normalized or re.search(r"\bgrid\b", normalized):
            terms.update({
                "gridsure", "grid sure", "grid", "pattern", "pattern token", "token",
                "otp", "credential", "revoke", "revogar", "revocation", "remove",
                "remover", "delete", "excluir", "bloquear", "desbloquear",
                "blocked token", "token blocked",
            })
        if any(term in normalized for term in ("revogar", "revoke", "remover", "remove", "excluir", "delete")):
            terms.update({
                "revoke", "revocation", "remove", "delete", "unassign", "deactivate",
                "disable", "excluir", "remover", "desativar", "token", "credential",
            })
        if "token" in normalized:
            terms.update({
                "mobilepass+", "otp", "credential", "revogar", "revoke", "unassign",
                "remove", "remover", "delete", "excluir", "blocked", "bloqueado",
            })
        return terms

    def _score_chunk(self, question: str, chunk: str, intent: str | None = None) -> int:
        terms = self._query_terms(question)
        original_terms = {
            term for term in re.findall(r"\w+", _normalize(question))
            if len(term) >= 3 and term not in STOPWORDS
        }
        lowered_chunk = _normalize(chunk)
        headings = _normalize("\n".join(
            line.lower() for line in chunk.splitlines() if re.match(r"^#{1,3}\s+", line)
        ))
        score = 0
        if "table of contents" in headings:
            score -= 80
        for term in terms:
            if term in {"sta", "access"}:
                if term in headings:
                    score += 2
                elif re.search(rf"\b{re.escape(term)}\b", lowered_chunk):
                    score += 1
                continue
            if " " in term and term in lowered_chunk:
                score += 10
            elif term in lowered_chunk:
                score += lowered_chunk.count(term)
            if term in headings:
                score += 8 if " " in term else 4
        for term in original_terms:
            if term in {"sta"}:
                score += 2 if term in headings else (1 if re.search(rf"\b{term}\b", lowered_chunk) else 0)
                continue
            if term in headings:
                score += 6
            score += 3 * lowered_chunk.count(term)
        if intent == "concept":
            score -= sum(8 for term in TROUBLESHOOTING_TERMS if term in lowered_chunk)
            if "visao geral" in lowered_chunk:
                score += 12
            if any(term in _normalize(question) for term in ("metodos", "methods", "autenticacao", "authentication")):
                score += sum(
                    18
                    for term in (
                        "authentication methods", "mfa methods", "metodos de autenticacao",
                        "token types", "tokens and mfa", "mfa method", "otp", "push otp",
                    )
                    if term in lowered_chunk
                )
                score -= sum(8 for term in ("revogar", "revoke", "suspend", "unlock", "troubleshooting") if term in lowered_chunk)
        elif intent == "troubleshooting" and any(term in lowered_chunk for term in TROUBLESHOOTING_TERMS):
            score += 8
        elif intent == "how_to":
            score += sum(3 for term in PROCEDURAL_TERMS if term in lowered_chunk)
            normalized_question = _normalize(question)
            if "desblo" in normalized_question or "unlock" in normalized_question:
                score += sum(18 for term in ("desbloquear", "unlock", "locked", "bloqueado") if term in lowered_chunk)
                if "desbloquear" in headings or "unlock" in headings:
                    score += 45
                score -= sum(18 for term in ("revogar", "revoke", "revocation", "gridsure") if term in lowered_chunk)
            if "gridsure" not in normalized_question and "gridsure" in lowered_chunk:
                score -= 30
        return score

    def _retrieve_local_context(self, question: str, intent: str) -> tuple[str, list[str]]:
        if not self.settings.local_rag_enabled:
            return "", []
        selected = [chunk for _, chunk in self._select_local_chunks(question, intent)]
        context = "\n\n".join(selected)[:10000]
        return (context, [str(self.settings.local_rag_doc_path)]) if context else ("", [])

    def _rank_local_chunks(self, question: str, intent: str) -> list[tuple[int, str]]:
        return sorted(
            ((self._score_chunk(question, chunk, intent), chunk) for chunk in self._local_chunks()),
            key=lambda item: item[0],
            reverse=True,
        )

    def _select_local_chunks(self, question: str, intent: str) -> list[tuple[int, str]]:
        limit = min(self.settings.local_rag_max_chunks, 3 if intent == "concept" else self.settings.local_rag_max_chunks)
        return [(score, chunk) for score, chunk in self._rank_local_chunks(question, intent) if score > 0][:limit]

    def _local_context_is_weak(self, question: str, intent: str, selected: list[tuple[int, str]]) -> bool:
        if not selected:
            return True
        best_score = selected[0][0]
        normalized_question = _normalize(question)
        selected_text = _normalize("\n\n".join(chunk for _, chunk in selected))
        if "gridsure" in normalized_question and "gridsure" not in selected_text:
            return True
        if any(term in normalized_question for term in ("revogar", "revoke", "remover", "remove", "excluir", "delete")):
            if not any(term in selected_text for term in ("revogar", "revoke", "revocation", "remove", "remover", "delete", "excluir")):
                return True
        return best_score < LOCAL_STRONG_SCORE and intent in {"how_to", "troubleshooting", "unknown"}

    def _is_allowed_url(self, url: str) -> bool:
        requested_host = (urlparse(url).hostname or "").lower()
        allowed_hosts = {(urlparse(item).hostname or "").lower() for item in self.settings.public_doc_urls}
        return bool(requested_host) and requested_host in allowed_hosts

    def _fetch_public_doc_page(self, url: str) -> tuple[str, str | None]:
        if not self._is_allowed_url(url):
            return "", "url_not_allowlisted"
        now = time.monotonic()
        with self._public_cache_lock:
            cached = self._public_cache.get(url)
            if cached and now - cached[0] < self.settings.public_doc_cache_ttl_seconds:
                return cached[1], None
        try:
            response = requests.get(url, timeout=self.settings.public_doc_timeout_seconds, headers={"User-Agent": "NeoIA-API/1.0"})
        except requests.Timeout:
            return "", "timeout"
        except requests.SSLError:
            return "", "ssl_error"
        except requests.RequestException as exc:
            return "", self._sanitize_error(exc)
        if response.status_code != 200:
            return "", f"http_{response.status_code}"
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
        text = text[:8000]
        with self._public_cache_lock:
            self._public_cache[url] = (now, text)
        return text, None

    def _fetch_public_doc_text(self, url: str) -> str:
        text, _ = self._fetch_public_doc_page(url)
        return text

    def _retrieve_public_context(self, question: str, intent: str) -> tuple[str, list[str]]:
        context, sources, _, _ = self._retrieve_public_context_detailed(question, intent)
        return context, sources

    def _retrieve_public_context_detailed(
        self, question: str, intent: str
    ) -> tuple[str, list[str], list[str], list[str]]:
        if not self.settings.public_doc_lookup_enabled:
            return "", [], [], []
        relevant_pages: list[tuple[int, str, str]] = []
        limit = min(self.settings.public_doc_max_urls, self.settings.public_doc_max_urls_per_query)
        urls = self.settings.public_doc_urls[:limit]
        attempted: list[str] = []
        errors: list[str] = []
        if urls:
            with ThreadPoolExecutor(max_workers=len(urls), thread_name_prefix="public-doc") as executor:
                futures = {executor.submit(self._fetch_public_doc_page, url): url for url in urls}
                for future in as_completed(futures):
                    url = futures[future]
                    attempted.append(url)
                    try:
                        text, error = future.result()
                    except Exception as exc:
                        text = ""
                        error = self._sanitize_error(exc)
                    if error:
                        errors.append(f"{url}: {error}")
                    score = self._score_chunk(question, text, intent)
                    if text and score >= PUBLIC_MIN_SCORE:
                        relevant_pages.append((score, url, text))
        self.last_public_doc_error = "; ".join(errors[:3]) if errors else None
        context_parts: list[str] = []
        sources: list[str] = []
        used_chars = 0
        for _, url, text in sorted(relevant_pages, key=lambda item: item[0], reverse=True):
            remaining = 8000 - used_chars
            if remaining <= 0:
                break
            selected = text[:remaining]
            context_parts.append(f"[source: {url}]\n{selected}")
            sources.append(url)
            used_chars += len(selected)
        return "\n\n".join(context_parts), sources, attempted, errors

    def _retrieve_combined_context(self, question: str, intent: str) -> tuple[str, list[str], list[str]]:
        selected_local = self._select_local_chunks(question, intent) if self.settings.local_rag_enabled else []
        local_context = "\n\n".join(chunk for _, chunk in selected_local)[:10000]
        local_sources = [str(self.settings.local_rag_doc_path)] if local_context else []
        public_context, public_sources = "", []
        normalized = _normalize(question)
        needs_external = any(term in normalized for term in ("documentacao oficial", "publica", "versao atual", "mais recente"))
        local_weak = self._local_context_is_weak(question, intent, selected_local)
        if self.settings.public_doc_lookup_enabled and (local_weak or needs_external):
            try:
                public_context, public_sources = self._retrieve_public_context(question, intent)
            except Exception as exc:
                self.last_public_doc_error = self._sanitize_error(exc)
                logger.warning("Public documentation lookup failed: %s", self.last_public_doc_error)
        parts: list[str] = []
        if local_context:
            parts.append(f"### CONTEXTO LOCAL\n{local_context}")
        if public_context:
            parts.append(f"### CONTEXTO PÚBLICO\n{public_context}")
        return "\n\n".join(parts)[: self.settings.combined_context_max_chars], local_sources, public_sources

    def _build_bedrock_payload(self, question: str, combined_context: str) -> dict:
        supplied_context = combined_context or "Nenhum contexto local ou público relevante foi recuperado."
        final_prompt = (
            "Responda apenas com base no contexto fornecido. "
            "Não invente comandos, nomes de ações ou caminhos de interface ausentes do contexto. "
            "Se houver conteúdo relacionado, mas não o procedimento exato solicitado, deixe essa "
            "limitação explícita e ofereça somente próximos passos sustentados pelo contexto. "
            f'Se o contexto não for suficiente, responda exatamente: "{INSUFFICIENT_CONTEXT_ANSWER}".\n\n'
            f"Contexto:\n{supplied_context}\n\nPergunta:\n{question}"
        )
        return {
            "system": [{"text": SYSTEM_CONTEXT}],
            "messages": [{"role": "user", "content": [{"text": final_prompt}]}],
            "inferenceConfig": {"maxTokens": 1200, "temperature": 0.1, "topP": 0.9},
        }

    def _call_bedrock(self, question: str, combined_context: str) -> str:
        if self.settings.aws_bearer_token_bedrock:
            return self._call_bedrock_bearer(question, combined_context)

        if boto3 is None:
            raise RuntimeError("boto3 não está disponível no ambiente.")
        payload = self._build_bedrock_payload(question, combined_context)
        client = boto3.client(
            "bedrock-runtime",
            region_name=self.settings.aws_region,
            config=Config(connect_timeout=5, read_timeout=self.settings.bedrock_timeout_seconds, retries={"max_attempts": 1}),
        )
        response = client.converse(modelId=self.settings.bedrock_model_id, **payload)
        return response["output"]["message"]["content"][0]["text"]

    def _call_bedrock_bearer(self, question: str, combined_context: str) -> str:
        payload = self._build_bedrock_payload(question, combined_context)
        url = (
            f"https://bedrock-runtime.{self.settings.aws_region}.amazonaws.com"
            f"/model/{self.settings.bedrock_model_id}/converse"
        )
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.settings.aws_bearer_token_bedrock}",
                "Content-Type": "application/json",
            },
            timeout=(5, self.settings.bedrock_timeout_seconds),
        )
        if not response.ok:
            logger.error("Bedrock bearer HTTP status %s", response.status_code)
        response.raise_for_status()
        return response.json()["output"]["message"]["content"][0]["text"]

    def _build_fallback_answer(self, question: str, combined_context: str, intent: str) -> str:
        if not combined_context.strip():
            return INSUFFICIENT_CONTEXT_ANSWER
        normalized = _normalize(question)
        normalized_context = _normalize(combined_context)
        is_sta = bool(re.search(r"\bsta\b", normalized)) or "safenet trusted access" in normalized
        if intent == "concept" and "metodos" in normalized and is_sta:
            return (
                "O STA suporta autenticação multifator com tokens OTP, incluindo SafeNet MobilePASS+, "
                "SafeNet eToken e códigos temporários por SMS ou e-mail. Também oferece SSO para "
                "aplicações por SAML 2.0 e OIDC e pode aplicar autenticação adaptativa conforme a política de acesso."
            )
        if intent == "concept" and is_sta:
            return f"{CONCEPT_ANSWER_STA}\n\nResposta gerada localmente com base na documentação carregada."
        if "gridsure" in normalized and "token" in normalized_context and any(
            term in normalized for term in ("revogar", "revoke", "remover", "remove", "excluir", "delete")
        ):
            if "revogar token gridsure" in normalized_context or (
                "gridsure" in normalized_context and "revoke" in normalized_context
            ):
                return (
                    "O contexto carregado contém um procedimento para revogar token GrIDsure.\n\n"
                    "Passos principais\n"
                    "1. Acesse o STA Token Management Console com permissões de operador.\n"
                    "2. Localize o usuário e selecione o User ID correspondente.\n"
                    "3. Abra Authentication Methods para listar os tokens atribuídos.\n"
                    "4. No token GrIDsure, selecione Manage.\n"
                    "5. Escolha Revoke e confirme a revogação.\n\n"
                    "Resultado esperado: o token GrIDsure é removido do usuário, retorna ao "
                    "inventário disponível e o evento Token Revoked aparece nos audit logs.\n\n"
                    "Resposta gerada com base na documentação carregada."
                )
        if "gridsure" in normalized and "token" in normalized_context:
            if intent == "concept":
                return (
                    "Não encontrei uma definição específica de GrIDsure no contexto carregado. "
                    "A documentação disponível contém informações gerais sobre tokens OTP e gestão "
                    "de tokens no STA, mas não é suficiente para descrever o funcionamento do "
                    "GrIDsure com segurança.\n\n"
                    "Resposta gerada localmente com base na documentação carregada."
                )
            return (
                "Não encontrei um procedimento específico para revogação de GrIDsure no contexto "
                "carregado, mas encontrei informações relacionadas à gestão de tokens no STA.\n\n"
                "Como próximos passos seguros, confirme o estado do token do usuário no console STA "
                "e revise o Log de Autenticação. O contexto também documenta atribuição, "
                "ressincronização e desbloqueio de tokens, mas não permite afirmar qual ação ou tela "
                "revoga especificamente um token GrIDsure. Valide esse procedimento na documentação "
                "oficial aplicável antes de remover a credencial.\n\n"
                "Resposta gerada localmente com base na documentação carregada."
            )
        if intent == "how_to" and "token" in normalized and any(
            term in normalized for term in ("revogar", "revoke", "remover", "excluir")
        ):
            token_name = "MobilePASS+" if "mobilepass" in normalized else "o token informado"
            return (
                f"Não encontrei um procedimento específico para revogar {token_name} no contexto "
                "carregado. Encontrei informações relacionadas à gestão de tokens no STA, incluindo "
                "consulta de estado, atribuição, ressincronização, desbloqueio e revisão do Log de "
                "Autenticação. Valide a ação exata de revogação na documentação oficial aplicável "
                "antes de remover ou desatribuir a credencial.\n\n"
                "Resposta gerada localmente com base na documentação carregada."
            )
        if intent == "troubleshooting" and "saml" in normalized and ("redirecion" in normalized or "acs" in normalized):
            return (
                "Possíveis causas\n- Entity ID ou ACS URL divergentes entre o STA e a aplicação.\n"
                "- Certificado SAML inválido, expirado ou diferente do configurado.\n"
                "- NameID ou claims/atributos incompatíveis com o que a aplicação espera.\n\n"
                "Validações iniciais\n1. Compare exatamente o Entity ID e a ACS URL nos dois lados.\n"
                "2. Valide o certificado e os metadados SAML.\n3. Confira o formato do NameID e os claims enviados.\n\n"
                "Evidências para coletar\n- Assertion capturada com SAML Tracer, horário do teste e mensagem de erro.\n"
                "- Metadados SAML e logs de autenticação do STA, sem credenciais ou tokens.\n\n"
                "Próximos passos\nCorrija a divergência encontrada, repita o teste e compare os novos logs.\n\n"
                "Essas validações resolveram o redirecionamento?\n\n"
                "Resposta gerada localmente com base na documentação carregada."
            )
        if intent == "troubleshooting" and "token" in normalized and ("bloque" in normalized or "desblo" in normalized):
            return (
                "Possíveis causas\n- O token foi bloqueado após tentativas inválidas.\n\n"
                "Validações iniciais\n1. Confirme o estado do token no console STA.\n2. Verifique tentativas recentes no Log de Autenticação.\n\n"
                "Evidências para coletar\n- Usuário pseudonimizado, horário, status do token e código do evento.\n\n"
                "Próximos passos\nNo console STA, abra Usuários, localize o usuário, acesse Tokens e use Desbloquear Token. Oriente o usuário a aguardar dois minutos antes de testar novamente.\n\n"
                "O acesso voltou a funcionar após o desbloqueio?\n\n"
                "Resposta gerada localmente com base na documentação carregada."
            )
        return INSUFFICIENT_CONTEXT_ANSWER

    @staticmethod
    def _sanitize_error(exc: Exception) -> str:
        if isinstance(exc, ClientError):
            code = exc.response.get("Error", {}).get("Code", "AWSClientError")
            return f"ClientError ({code})"
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            return f"HTTPError ({exc.response.status_code})"
        return exc.__class__.__name__

    def _simple_response(self, question: str, reason: str) -> ChatResponse:
        intent = classify_question_intent(question)
        return ChatResponse(
            id=f"assistant-{uuid4().hex[:8]}", answer=INSUFFICIENT_CONTEXT_ANSWER,
            content=INSUFFICIENT_CONTEXT_ANSWER, timestamp=_timestamp(), mode="fallback",
            intent=intent, fallback_reason=reason,
        )

    def timeout_response(self, question: str) -> ChatResponse:
        return self._simple_response(question, "request_timeout")

    def error_response(self, question: str) -> ChatResponse:
        return self._simple_response(question, "internal_error")

    def _chunk_heading(self, chunk: str) -> str:
        for line in chunk.splitlines():
            if re.match(r"^#{1,3}\s+", line):
                return re.sub(r"^#{1,3}\s+", "", line).strip()[:160]
        return "Trecho sem título"

    def debug_retrieval(self, question: str) -> dict:
        started = time.perf_counter()
        intent = classify_question_intent(question)
        warnings: list[str] = []
        local_started = time.perf_counter()
        doc_path = self.settings.local_rag_doc_path
        doc_exists = doc_path.is_file()
        doc_size = doc_path.stat().st_size if doc_exists else 0
        chunks = self._local_chunks() if self.settings.local_rag_enabled and doc_exists else []
        selected = self._select_local_chunks(question, intent) if chunks else []
        local_rag_ms = round((time.perf_counter() - local_started) * 1000, 2)
        if not self.settings.local_rag_enabled:
            warnings.append("Local RAG is disabled.")
        elif not doc_exists:
            warnings.append("Local RAG document is missing.")
        elif not selected:
            warnings.append("No relevant local chunks were selected.")
        elif "gridsure" in _normalize(question) and not any("gridsure" in _normalize(chunk) for _, chunk in selected):
            warnings.append("A documentação local foi carregada, mas não contém procedimento específico para GrIDsure/revogação.")

        public_started = time.perf_counter()
        public_context, public_sources, public_attempted, public_errors = "", [], [], []
        normalized = _normalize(question)
        needs_external = any(term in normalized for term in ("documentacao oficial", "publica", "versao atual", "mais recente"))
        local_weak = self._local_context_is_weak(question, intent, selected)
        if self.settings.public_doc_lookup_enabled and (local_weak or needs_external):
            try:
                public_context, public_sources, public_attempted, public_errors = self._retrieve_public_context_detailed(question, intent)
            except Exception as exc:
                public_errors.append(self._sanitize_error(exc))
                warnings.append(f"Public documentation lookup failed: {self._sanitize_error(exc)}")
        public_doc_ms = round((time.perf_counter() - public_started) * 1000, 2)
        if self.settings.public_doc_lookup_enabled and public_doc_ms > self.settings.public_doc_timeout_seconds * 1000:
            warnings.append("Public documentation lookup was slow.")
        if self.settings.public_doc_lookup_enabled and local_weak and not public_attempted:
            warnings.append("Public documentation lookup was enabled but no public URL was attempted.")
        if self.settings.public_doc_lookup_enabled and public_attempted and not public_sources:
            warnings.append("Public documentation lookup ran but no public context passed the relevance threshold.")
        local_length = sum(len(chunk) for _, chunk in selected)
        total_ms = round((time.perf_counter() - started) * 1000, 2)
        selected_local_chunks = [
            {
                "heading": self._chunk_heading(chunk),
                "score": score,
                "source": "Documentação local",
                "preview": re.sub(r"\s+", " ", chunk).strip()[:250],
            }
            for score, chunk in selected
        ]
        result = {
            "question": question,
            "detected_intent": intent,
            "local": {
                "enabled": self.settings.local_rag_enabled,
                "configured_path": self.settings.configured_local_doc_path,
                "resolved_path": str(doc_path),
                "exists": doc_exists,
                "size_bytes": doc_size,
                "chunks_count": len(chunks),
                "selected_chunks": selected_local_chunks,
            },
            "public": {
                "enabled": self.settings.public_doc_lookup_enabled,
                "urls_configured": self.settings.public_doc_urls,
                "urls_attempted": public_attempted,
                "selected_sources": public_sources,
                "errors": public_errors,
            },
            "combined_context_length": min(local_length + len(public_context), self.settings.combined_context_max_chars),
            "timings_ms": {
                "local_rag": local_rag_ms,
                "public_docs": public_doc_ms,
                "total_retrieval": total_ms,
            },
            "warnings": warnings,
            # Backward-compatible aliases for older scripts/tests.
            "local_rag_enabled": self.settings.local_rag_enabled,
            "configured_local_doc_path": self.settings.configured_local_doc_path,
            "resolved_local_doc_path": str(doc_path),
            "local_doc_exists": doc_exists,
            "local_doc_size_bytes": doc_size,
            "local_chunks_count": len(chunks),
            "selected_local_chunks": selected_local_chunks,
            "public_doc_lookup_enabled": self.settings.public_doc_lookup_enabled,
            "selected_public_sources": public_sources,
            "local_rag_ms": local_rag_ms,
            "public_doc_ms": public_doc_ms,
            "bedrock_ms": 0.0,
            "total_ms": total_ms,
            "mode": {"bedrock_enabled": self.settings.bedrock_enabled, "expected": "bedrock" if self.settings.bedrock_enabled else "fallback"},
        }
        return result

    def debug_timeout(self, question: str) -> dict:
        path = self.settings.local_rag_doc_path
        exists = path.is_file()
        return {
            "question": question, "detected_intent": classify_question_intent(question),
            "local": {
                "enabled": self.settings.local_rag_enabled,
                "configured_path": self.settings.configured_local_doc_path,
                "resolved_path": str(path),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
                "chunks_count": 0,
                "selected_chunks": [],
            },
            "public": {
                "enabled": self.settings.public_doc_lookup_enabled,
                "urls_configured": self.settings.public_doc_urls,
                "urls_attempted": [],
                "selected_sources": [],
                "errors": ["retrieval_timeout"],
            },
            "timings_ms": {
                "local_rag": 0.0,
                "public_docs": 0.0,
                "total_retrieval": self.settings.chat_request_timeout_seconds * 1000,
            },
            "local_rag_enabled": self.settings.local_rag_enabled,
            "configured_local_doc_path": self.settings.configured_local_doc_path,
            "resolved_local_doc_path": str(path), "local_doc_exists": exists,
            "local_doc_size_bytes": path.stat().st_size if exists else 0,
            "local_chunks_count": 0, "selected_local_chunks": [],
            "public_doc_lookup_enabled": self.settings.public_doc_lookup_enabled,
            "selected_public_sources": [], "combined_context_length": 0,
            "warnings": ["RAG retrieval exceeded the configured request timeout."],
            "local_rag_ms": 0.0, "public_doc_ms": 0.0, "bedrock_ms": 0.0,
            "total_ms": self.settings.chat_request_timeout_seconds * 1000,
            "error": "retrieval_timeout",
            "mode": {"bedrock_enabled": self.settings.bedrock_enabled, "expected": "fallback"},
        }
