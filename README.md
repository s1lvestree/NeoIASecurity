# chatbot

## Visão geral

Este projeto é um MVP de chatbot técnico de cibersegurança da Neotel construído
com Streamlit. Ele consulta documentação local em Markdown e páginas públicas
allowlistadas antes de enviar o contexto recuperado ao Amazon Bedrock.

O único modelo configurado por padrão é o Amazon Nova Pro:
`amazon.nova-pro-v1:0`.

O MVP não navega livremente na internet, não usa banco de dados, embeddings,
Docker ou Bedrock Knowledge Bases. Quando a documentação carregada não contém
informação suficiente, a resposta deve ser conservadora. A interface também
permite abrir um chamado fixo de teste por API quando a orientação não resolve o
problema.

## Criar o ambiente virtual no PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Instalar dependências

```powershell
pip install -r requirements.txt
```

## Configurar o arquivo `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha a chave de API do Bedrock e, para testar a abertura de chamado, escolha
o modo genérico ou o modo de compatibilidade Octadesk. Não compartilhe tokens do
arquivo `.env`.

Os campos `AWS_CA_BUNDLE` e `REQUESTS_CA_BUNDLE` podem apontar para um arquivo
de certificados corporativos quando necessário.

## Configurar a API de chamados

### Exemplo com Webhook.site

```dotenv
TICKET_API_MODE=generic
TICKET_API_URL=https://webhook.site/SEU_ENDPOINT
TICKET_API_AUTH_TYPE=none
TICKET_API_TOKEN=
```

O Webhook.site serve somente para demonstrar o envio HTTP da API. Ele não é uma
plataforma real de chamados.

O modo genérico envia um payload JSON simples para `TICKET_API_URL`. O método
padrão é `POST`. Tokens bearer e um cabeçalho HTTP adicional são opcionais.

### Exemplo com Octadesk

```dotenv
TICKET_API_MODE=octadesk
OCTADESK_API_URL=https://api.octadesk.services
OCTADESK_ACCESS_TOKEN=...
OCTADESK_AGENT_EMAIL=...
OCTADESK_REQUESTER_EMAIL=...
```

Esse modo preserva o payload e o endpoint compatíveis com Octadesk.

## Colocar documentação local

O projeto já inclui um arquivo `docs/sta.md` inicial com contexto conceitual
mínimo. Para usar uma documentação STA mais completa e validada:

```powershell
mkdir docs
Copy-Item C:\caminho\para\sta.md docs\sta.md
```

## Rodar a aplicação

```powershell
streamlit run app.py
```

## Interface

Na barra lateral, somente o seletor `Área da aplicação` fica visível por padrão,
com as opções `Ala Técnica` e `Ala de Governança`. Diagnósticos e informações
técnicas permanecem disponíveis em seções expansíveis fechadas:

- `Diagnóstico Bedrock`
- `Fontes de conhecimento`
- `Governança e privacidade`
- `Integração de chamados`

As URLs de documentação pública e os status de configuração ficam ocultos até
que o usuário expanda manualmente a seção correspondente. Tokens, senhas e
chaves de API nunca são exibidos.

## Diagnosticar o Bedrock

```powershell
python diagnose_bedrock.py
```

O script exibe região, IDs dos modelos e se a chave Bedrock está configurada,
sem imprimir segredos. Ele lista modelos Amazon e Anthropic quando a permissão
da conta permitir, testa primeiro `amazon.nova-pro-v1:0` e também testa
`BEDROCK_MODEL_ID` quando ele for diferente.

## Perguntas para teste

- O que é STA?
- Quais métodos de autenticação o STA suporta?
- Como funciona o Push OTP no MobilePASS+?
- Como revogar um token MobilePASS+?
- Quais validações fazer quando uma aplicação SAML integrada ao STA falha?
- Quais são as soluções da GuardianKey?

## Comportamento esperado

Para perguntas sobre STA, a aplicação usa `docs/sta.md` e/ou documentação
pública da Thales configurada em `PUBLIC_DOC_URLS`.

Se não houver documentação GuardianKey no contexto local ou público recuperado,
o chatbot não deve inventar produtos ou soluções. A resposta esperada é:

> Não encontrei informação suficiente na documentação local ou pública carregada neste MVP para responder com segurança.

As fontes efetivamente recuperadas são exibidas após cada resposta.

## Ala de Governança — Relatório Executivo STA

A Ala de Governança simula uma integração com a API de Logs do SafeNet Trusted
Access sem usar dados reais de clientes. O fluxo analisa eventos localmente com
Python, calcula indicadores, identifica padrões suspeitos e propõe políticas de
acesso baseadas em cenários contextuais do STA.

Ao solicitar o relatório executivo, a aplicação envia ao Amazon Bedrock somente
o resumo da análise, as recomendações e até 20 amostras relevantes. O relatório
continua sendo gerado com Amazon Nova Pro.

O relatório combina:

- Logs STA simulados armazenados localmente.
- Indicadores e achados calculados em Python.
- Recomendações de políticas de acesso.
- Amazon Bedrock com Amazon Nova Pro.
- Conceitos de políticas STA baseados em documentação pública.

Os dados desta área são simulados. Eles não devem ser tratados como dados reais
de clientes ou como evidência de incidentes reais.

### Fluxo da Ala de Governança

O usuário não gera logs manualmente pela interface. A experiência simula uma
busca real na STA Logs API:

1. Selecione a solução `SafeNet Trusted Access (STA)`.
2. Selecione o período de análise entre 1 e 30 dias.
3. Clique em `Buscar logs`.
4. Revise a prévia concisa da correlação.
5. Clique em `Gerar relatório executivo`.
6. Baixe o PDF executivo.

O Markdown permanece disponível como exportação secundária.

### Fidelidade dos logs simulados do STA

Os logs fake foram modelados com base na documentação pública do STA. A Logs API
retorna objetos JSON e o campo `details.type` identifica o tipo de evento. Este
MVP gera pares relacionados:

- `ACCESS_REQUEST`: representa a solicitação de acesso e inclui aplicação,
  política, cenário, estado, motivo e credenciais.
- `AUTHENTICATION`: representa a tentativa de autenticação e inclui resultado,
  mensagem, agente e tipo de credencial.

Os eventos relacionados compartilham `context.globalAccessId`, além de
identificadores de sessão, tenant, usuário e endereço de origem. Assim, 500
tentativas simuladas geram aproximadamente 1000 entradas de log.

O MVP usa somente dados simulados. Em produção, a fonte local seria substituída
pela STA Logs API ou pelo SafeNet Logging Agent.

### Como a simulação funciona

Os logs são salvos em `data/sta_logs_fake/`, separados por dia:

```text
data/sta_logs_fake/sta_logs_YYYY-MM-DD.json
```

Cada arquivo contém um array JSON de objetos STA-style. Ao clicar em
`Buscar logs`, a aplicação lê esses arquivos locais e se comporta como uma busca
simulada da Logs API. Se faltarem arquivos para o período selecionado, o app
prepara silenciosamente uma massa local de demonstração somente para os dias
ausentes. Nenhuma ação manual é necessária e nenhum dado real de cliente é usado.

Em produção, esse mecanismo pode ser substituído pela STA Logs API real ou por
integração com SafeNet Logging Agent, SIEM ou data lake.

### Relatório PDF

O relatório executivo pode ser baixado em Markdown e PDF. O PDF é gerado
localmente com `reportlab` e inclui capa, indicadores, gráficos, principais
achados, recomendações de políticas e narrativa executiva. A aplicação monta o
layout diretamente com ReportLab para evitar problemas de conversão bruta de
Markdown. O Markdown permanece disponível como exportação secundária.

### Soberania dos Dados no MVP

Os logs brutos permanecem locais. Antes de chamar a IA, a aplicação aplica
minimização e pseudonimização. O Amazon Nova Pro recebe somente:

- Métricas agregadas.
- Resumos de correlação.
- Achados de risco.
- Recomendações de políticas geradas localmente.
- Um número limitado de amostras sanitizadas.

Identificadores de usuários são convertidos em hashes estáveis e IPs são
mascarados. Campos como `tenantId`, `tenantCode`, `accountName`, `sessionId`,
`globalAccessId` e outros IDs sensíveis são removidos ou pseudonimizados antes
do envio. O PDF também não inclui identificadores diretos.

As configurações ficam no `.env`. O padrão recomendado mantém
`GOVERNANCE_PRIVACY_MODE=true` e `GOVERNANCE_SEND_RAW_LOGS_TO_AI=false`.

### Como validar o pacote enviado à IA

Na Ala de Governança, busque os logs e abra:

`Ver prévia do pacote sanitizado enviado para a IA`

Confirme que nenhum usuário bruto, IP completo, `tenantId`, `sessionId`,
`tenantCode` ou `accountName` aparece. A interface executa essa validação
automaticamente e bloqueia a geração do relatório se detectar vazamento.

### Limitações

Este MVP aplica pseudonimização e minimização. Isso não equivale a anonimização
matematicamente irreversível em todos os contextos. Uma implantação produtiva
deve definir gestão do salt, retenção, controle de acesso e política de
auditoria. Em produção, armazene o salt em um gerenciador de segredos, nunca em
texto puro no `.env`.

### Evolução futura

- Substituir a busca local simulada pela STA Logs API real.
- Adicionar agendamento de relatórios semanais e mensais.
- Adicionar seleção de cliente ou tenant.
- Adicionar identidade visual do cliente com logo no PDF.
- Adicionar score de risco ao longo do tempo.
- Adicionar comparação entre períodos.

## Troubleshooting

### `AWS_BEARER_TOKEN_BEDROCK` ausente

Configure `AWS_BEARER_TOKEN_BEDROCK` no arquivo `.env`. O diagnóstico informa
somente se o valor existe.

### Erros de modelo Bedrock

Execute `python diagnose_bedrock.py`. Confirme a região, o acesso ao Amazon Nova
Pro e o ID `amazon.nova-pro-v1:0`. O fallback padrão também aponta para Amazon
Nova Pro.

### `SSL: self-signed certificate in certificate chain`

Configure `AWS_CA_BUNDLE` e/ou `REQUESTS_CA_BUNDLE` no `.env` com o caminho do
arquivo PEM da autoridade certificadora corporativa.

### Octadesk/API retorna `401` ou `403`

Confirme `OCTADESK_ACCESS_TOKEN`, `OCTADESK_AGENT_EMAIL`,
`OCTADESK_REQUESTER_EMAIL` e a permissão do token para criar tickets. O MVP faz
`POST` em `{OCTADESK_API_URL}/tickets`.

### API genérica não recebe o chamado de teste

Confirme `TICKET_API_MODE=generic`, `TICKET_API_URL`, `TICKET_API_METHOD` e,
quando usados, `TICKET_API_AUTH_TYPE`, `TICKET_API_TOKEN` e os campos
`TICKET_API_EXTRA_HEADER_*`.

### Documentação pública não carrega

Confirme conectividade, certificados corporativos e as URLs em
`PUBLIC_DOC_URLS`. O MVP consulta somente hosts allowlistados e ignora páginas
que não retornam HTTP `200`.

### `docs/sta.md` ausente

Crie o arquivo ou ajuste `LOCAL_RAG_DOC_PATH`. Sem o arquivo, a aplicação
continua executando, mas não usa contexto local.
