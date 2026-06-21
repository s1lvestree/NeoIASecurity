from __future__ import annotations

import logging
import re
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
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover
    boto3 = None

    class ClientError(Exception):
        pass

INSUFFICIENT_CONTEXT_ANSWER = (
    "Não encontrei informação suficiente na documentação local ou pública carregada neste MVP "
    "para responder com segurança."
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


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M")


class ChatService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_conversations(self) -> list[dict]:
        return DEFAULT_CONVERSATIONS

    def list_messages(self, conversation_id: str) -> list[dict]:
        return []

    def ask(self, question: str) -> ChatResponse:
        combined_context, local_sources, public_sources = self._retrieve_combined_context(question)
        mode = "fallback"
        answer = self._build_fallback_answer(question, combined_context)

        if self.settings.bedrock_enabled:
            try:
                answer = self._call_bedrock(question, combined_context)
                mode = "bedrock"
            except Exception as exc:
                logger.warning("Bedrock falhou, usando fallback: %s", exc)
                mode = "fallback"

        references = []
        if local_sources:
            references.append("Documentação local")
        if public_sources:
            references.append("Documentação pública")
        if "STA" in answer or "SafeNet Trusted Access" in answer:
            references.append("STA")

        return ChatResponse(
            id=f"assistant-{uuid4().hex[:8]}",
            answer=answer,
            content=answer,
            timestamp=_timestamp(),
            mode=mode,
            local_sources=local_sources,
            public_sources=public_sources,
            references=references,
        )

    def _load_local_markdown(self) -> str:
        try:
            return self.settings.local_rag_doc_path.read_text(encoding="utf-8")
        except OSError:
            return ""

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

    def _score_chunk(self, question: str, chunk: str) -> int:
        terms = {term for term in re.findall(r"\w+", question.lower()) if len(term) >= 3}
        lowered_chunk = chunk.lower()
        score = sum(lowered_chunk.count(term) for term in terms)
        headings = "\n".join(
            line.lower() for line in chunk.splitlines() if re.match(r"^#{1,3}\s+", line)
        )
        score += sum(3 for term in terms if term in headings)
        return score

    def _retrieve_local_context(self, question: str) -> tuple[str, list[str]]:
        if not self.settings.local_rag_enabled:
            return "", []
        markdown_text = self._load_local_markdown()
        scored = [
            (self._score_chunk(question, chunk), chunk)
            for chunk in self._chunk_text(markdown_text)
        ]
        selected = [
            chunk
            for score, chunk in sorted(scored, key=lambda item: item[0], reverse=True)
            if score > 0
        ][: self.settings.local_rag_max_chunks]
        context = "\n\n".join(selected)[:10000]
        return (context, [str(self.settings.local_rag_doc_path)]) if context else ("", [])

    def _is_allowed_url(self, url: str) -> bool:
        requested_host = (urlparse(url).hostname or "").lower()
        allowed_hosts = {(urlparse(item).hostname or "").lower() for item in self.settings.public_doc_urls}
        return bool(requested_host) and requested_host in allowed_hosts

    def _fetch_public_doc_text(self, url: str) -> str:
        if not self._is_allowed_url(url):
            return ""
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "NeoIA-API/1.0"})
        except requests.RequestException:
            return ""
        if response.status_code != 200:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
        return text[:8000]

    def _retrieve_public_context(self, question: str) -> tuple[str, list[str]]:
        if not self.settings.public_doc_lookup_enabled:
            return "", []
        relevant_pages: list[tuple[int, str, str]] = []
        for url in self.settings.public_doc_urls[: self.settings.public_doc_max_urls]:
            text = self._fetch_public_doc_text(url)
            score = self._score_chunk(question, text)
            if text and score > 0:
                relevant_pages.append((score, url, text))
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
        return "\n\n".join(context_parts), sources

    def _retrieve_combined_context(self, question: str) -> tuple[str, list[str], list[str]]:
        local_context, local_sources = self._retrieve_local_context(question)
        public_context, public_sources = self._retrieve_public_context(question)
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
        client = boto3.client("bedrock-runtime", region_name=self.settings.aws_region)
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
            timeout=30,
        )
        if not response.ok:
            logger.error("Bedrock bearer HTTP %s: %s", response.status_code, response.text[:500])
        response.raise_for_status()
        return response.json()["output"]["message"]["content"][0]["text"]

    def _build_fallback_answer(self, question: str, combined_context: str) -> str:
        if not combined_context.strip():
            return INSUFFICIENT_CONTEXT_ANSWER
        compact_context = re.sub(r"\s+", " ", combined_context)
        snippet = compact_context[:600]
        if "safenet trusted access" in question.lower() or "sta" in question.lower():
            return (
                "Com base no contexto carregado, SafeNet Trusted Access (STA) é a solução usada "
                "para controle de acesso, autenticação multifator e SSO. "
                f"Resumo do contexto disponível: {snippet}"
            )
        return f"Resposta de fallback baseada no contexto recuperado: {snippet}"
