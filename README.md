# NeoIA Security Monorepo

Monorepo com tres frentes:

- `apps/web`: frontend React/Vite
- `apps/api`: API Python para Bedrock, tickets e governanca
- `apps/streamlit`: MVP original em Streamlit mantido como fallback

## Docker

Para subir o stack principal de desenvolvimento:

```powershell
docker compose up --build
```

Depois abra:

- `http://localhost:5173`
- `http://localhost:8000/health`

O compose sobe somente `apps/web` e `apps/api`. O `apps/streamlit` fica fora do stack principal.

## Execucao local no WSL/Linux

```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
python apps/api/main.py
```

Em outro terminal:

```bash
npm install --prefix apps/web
npm --prefix apps/web run dev
```

O frontend fica em `http://localhost:5173` e usa o proxy do Vite para
`http://127.0.0.1:8000`. Mantenha `VITE_API_BASE_URL` vazio. No Compose, o alvo do
proxy e `http://api:8000`, conforme `docker-compose.yml`.

## Diagnostico do chatbot

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/debug/rag?question=O%20que%20%C3%A9%20STA"
python apps/api/scripts/test_chat_quality.py
```

Uma resposta com `mode="fallback"` e `fallback_reason` indica uso da resposta local.
O frontend mostra isso apenas em **Detalhes tecnicos**. Para habilitar o Bedrock,
defina `BEDROCK_ENABLED=true`, `BEDROCK_MODEL_ID=amazon.nova-pro-v1:0` e as
credenciais AWS usuais (ou `AWS_BEARER_TOKEN_BEDROCK`) em `apps/api/.env`.

Se uma conversa antiga permanecer no navegador, use **Limpar conversa** ou execute
no console do navegador:

```javascript
localStorage.clear()
sessionStorage.clear()
```

Em falhas de conexao, confirme que a API responde ao `/health`, que o frontend usa
`/api/chat` e que o alvo do proxy corresponde ao modo local ou Docker descrito acima.

## Governança IA e exportação PDF

O dashboard **Governança IA** usa uma simulação local de logs do SafeNet Trusted
Access para demonstrar correlação executiva de eventos. Para gerar o relatório:

1. Abra **Governança IA** no frontend.
2. Clique em **Exportar**.
3. Selecione **STA** e o período desejado: 7, 15, 30 dias ou customizado.
4. Clique em **Gerar relatório PDF**.
5. Após a mensagem de sucesso, clique em **Baixar PDF**.

Endpoints relacionados:

```bash
curl "http://localhost:8000/api/governance/sta/summary?days=7"
curl -X POST "http://localhost:8000/api/governance/reports" \
  -H "Content-Type: application/json" \
  -d '{"solution":"STA","days":7}'
curl "http://localhost:8000/api/governance/debug/sta?days=7"
```

Os logs STA fake são gerados de forma determinística em runtime pelo backend, como
se fossem retornados por uma API de auditoria do STA. A fonte local fica documentada
em `apps/api/data/sta_logs/`. Os dados são fictícios e incluem autenticações bem
sucedidas, falhas de Push OTP, acessos negados, falhas repetidas, administradores
com MFA fraco, localização incomum e acessos SAML/OIDC a aplicações como ServiceNow,
Jira, Zoom e Office 365.

Privacidade do relatório:

- Apenas métricas agregadas e amostras sanitizadas são usadas.
- Usuários são pseudonimizados e IPs são mascarados.
- Identificadores como tenant, account e session não são incluídos no payload final.
- Nenhum log bruto de cliente é enviado para IA.

Os PDFs gerados ficam fora do git em `apps/api/generated_reports/`. No Docker Compose,
o diretório é montado em `/app/generated_reports`.

Solução de problemas:

- Relatório não baixa: confirme se o backend está no ar e teste o `download_url`
  retornado por `/api/governance/reports`.
- Permissão em `generated_reports`: crie o diretório local e garanta escrita pelo
  usuário/container que executa a API.
- `ReportLab` ou `matplotlib` ausente: rode `pip install -r apps/api/requirements.txt`
  e confirme `python -c "import reportlab, matplotlib"`.
- Volume Docker: confirme `./apps/api/generated_reports:/app/generated_reports` em
  `docker-compose.yml` e recrie o container com `docker compose up --build`.

## Integração com Zammad

O Zammad deve estar em execução em `http://localhost:8080`. Crie um token para um
usuário com permissão `ticket.agent` ou `admin` e salve-o somente em
`apps/api/.env`; não exponha esse valor no frontend, em logs ou na documentação.
Configure ao menos:

```dotenv
TICKET_API_MODE=zammad
ZAMMAD_BASE_URL=http://localhost:8080
ZAMMAD_API_TOKEN=
ZAMMAD_GROUP=Suporte
ZAMMAD_CUSTOMER_EMAIL=cliente@empresa.com.br
```

Quando o NeoIASecurity é executado sem Docker, use
`ZAMMAD_BASE_URL=http://localhost:8080`. Dentro do Docker, use
`ZAMMAD_BASE_URL=http://host.docker.internal:8080`. O serviço `api` no
`docker-compose.yml` inclui o mapeamento necessário:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Integração com Zammad em Docker

Se a API do NeoIASecurity roda diretamente no WSL/Python, configure:

```dotenv
ZAMMAD_BASE_URL=http://localhost:8080
```

Se a API roda dentro do Docker Compose, `localhost` aponta para o próprio container.
Nesse caso, configure em `apps/api/.env`:

```dotenv
ZAMMAD_BASE_URL=http://host.docker.internal:8080
```

O serviço `api` precisa manter este mapeamento em `docker-compose.yml`:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Teste a conectividade a partir do container da API:

```bash
docker compose exec api python - <<'PY'
import requests
r = requests.get("http://host.docker.internal:8080", timeout=10)
print(r.status_code)
PY
```

Valide credenciais e criação de chamado antes de testar o botão do chatbot:

```bash
python apps/api/scripts/test_zammad_integration.py
```

O modo Webhook genérico continua disponível com `TICKET_API_MODE=generic` e as
variáveis `TICKET_API_URL`, `TICKET_API_METHOD` e `TICKET_API_TOKEN`.

Solução de problemas:

- `403 Not authorized`: confira o token, as permissões e o papel do usuário.
- `422`: confira grupo, cliente e payload configurados.
- `Connection refused`: confira a URL do Zammad e o estado dos containers.
- Chamado criado, mas e-mail falhou: confira `EMAIL_ENABLED` e a configuração SMTP.

### Erro 422: No lookup value found for customer

Esse erro indica que o cliente definido em `ZAMMAD_CUSTOMER_EMAIL` não existe no
Zammad ou não pôde ser resolvido. O backend normaliza a configuração, procura o
usuário e tenta criá-lo automaticamente antes de abrir o chamado. Se a criação ainda
falhar, crie o cliente manualmente no Zammad e confira as permissões da API.

O token deve pertencer a um usuário Admin/Agent e ter permissões `admin` e
`ticket.agent`. Confirme também que o grupo `Suporte` (ou o valor configurado em
`ZAMMAD_GROUP`) existe. Execute o diagnóstico completo, que não imprime o token:

```bash
python apps/api/scripts/test_zammad_integration.py
```

## RAG e documentação local

O backend usa `apps/api/docs/sta.md` como caminho canônico da documentação STA.
Configure `LOCAL_RAG_DOC_PATH=apps/api/docs/sta.md` em `apps/api/.env`. Caminhos
relativos são procurados a partir da raiz do repositório, de `apps/api` e do diretório
de execução; o mesmo valor funciona na execução local e no container.

O arquivo deve conter somente documentação autorizada para uso pelo chatbot. Se a
documentação oficial não estiver disponível, mantenha um arquivo Markdown explicando
onde ela deve ser colocada; não preencha procedimentos oficiais por suposição.

Diagnóstico:

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/debug/rag?question=Como%20revogar%20um%20token%20GrIDsure%3F"
python apps/api/scripts/check_rag_setup.py
```

O `/health` e o endpoint de debug mostram o caminho configurado, o caminho resolvido,
existência e tamanho do documento sem retornar o documento completo. O `.env` pode ser
inspecionado localmente para diagnóstico, mas nunca deve ser commitado nem ter tokens,
senhas ou credenciais copiados para logs, interface ou README.

### Quando a IA não encontra resposta na documentação

Use esta sequência para diagnosticar respostas como "não encontrei informação
suficiente":

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/debug/rag?question=Como%20revogar%20um%20token%20GrIDsure%3F"
python apps/api/scripts/check_rag_setup.py
```

No Docker, valide o caminho visto pelo container:

```bash
docker compose exec api python scripts/check_runtime_paths.py
```

Se o container estiver executando a partir da raiz do repositório em vez de `/app`,
use:

```bash
docker compose exec api python apps/api/scripts/check_runtime_paths.py
```

Verifique:

- `LOCAL_RAG_DOC_PATH=apps/api/docs/sta.md`.
- O arquivo `apps/api/docs/sta.md` existe e tem tamanho compatível com a documentação completa.
- `/health` mostra `local_doc_exists=true`.
- `/api/debug/rag` mostra chunks locais selecionados, URLs públicas tentadas quando o contexto local é fraco e warnings claros quando falta conteúdo específico.
- `PUBLIC_DOC_LOOKUP_ENABLED=true`.
- `PUBLIC_DOC_URLS` contém apenas URLs públicas permitidas.

Diferença de paths: localmente o arquivo vive em `apps/api/docs/sta.md`; dentro do
container da API, `COPY apps/api/ .` e o bind mount `./apps/api:/app` fazem o mesmo
arquivo aparecer como `/app/docs/sta.md`. O resolver aceita ambos.

## Streamlit legado

```powershell
pip install -r apps/streamlit/requirements.txt
streamlit run apps/streamlit/app.py
```
