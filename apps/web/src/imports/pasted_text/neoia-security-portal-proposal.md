Proposta de Projeto de IA - NeoIA Security Portal
Documento preliminar para discussão interna - Neotel
NeoIA Security Portal
Proposta de MVP para plataforma de IA aplicada a suporte técnico, análise de logs e
governança em cibersegurança
Preparado para discussão interna de projeto de IA na Neotel
Data: 24/05/2026
Resumo da proposta
Criar uma interface única com duas alas: uma ala técnica, com chatbot baseado em conhecimento interno e
geração assistida de chamados; e uma ala de governança, com análise de logs de ferramentas como STA e
DLP para geração de relatórios executivos e técnicos. O MVP pode aproveitar a infraestrutura ESXi/DL360 ou
DL380 já disponível, com opção de IA local via Ollama ou IA em nuvem via Amazon Bedrock, OpenAI API ou
Azure OpenAI.
Proposta de Projeto de IA - NeoIA Security Portal
Documento preliminar para discussão interna - Neotel
Sumário Executivo
Este documento consolida a proposta discutida para criação de uma plataforma interna de IA voltada à realidade
da Neotel, considerando cibersegurança, operação técnica, suporte, governança e integração com ferramentas
já disponíveis, como Octadesk e logs do STA.
A proposta é viável tecnicamente e pode ser construída em fases. O MVP recomendado utiliza uma VM Linux no
ESXi existente, com processamento controlado, integração inicial com logs do STA, geração de relatório e
criação assistida de chamados no Octadesk. A IA pode operar localmente via Ollama ou em nuvem via Amazon
Bedrock/OpenAI/Azure OpenAI, conforme o nível de privacidade, custo e desempenho desejado.
Critério Avaliação
Viabilidade técnica Alta, desde que o escopo inicial seja reduzido e
progressivo.
Complexidade de desenvolvimento Média. A maior complexidade está em organizar a
base de conhecimento, criar parsers e desenhar bons
fluxos.
Complexidade de infraestrutura Baixa a média para MVP; média/alta apenas se exigir
appliance dedicado com GPU.
Custo inicial Baixo se aproveitar ESXi existente; variável se usar
nuvem ou appliance dedicado.
Principal risco Impacto em host ESXi compartilhado, governança de
dados sensíveis e qualidade dos relatórios.
Recomendação Começar com MVP local controlado + opção cloud
para comparação de qualidade e custo.
1. Conceito do Projeto
O NeoIA Security Portal seria uma plataforma única de IA com dois módulos principais: uma ala técnica e uma
ala de governança. O objetivo é apoiar tanto o time operacional quanto a geração de valor executivo para
clientes e gestores.
Módulo Objetivo Principais entregas
Ala Técnica Apoiar analistas, consultores e
suporte técnico na resolução de
dúvidas sobre ferramentas e
procedimentos.
Chatbot técnico, busca em
documentação, geração de passos
de troubleshooting, sugestão de
evidências e geração assistida de
chamados.
Ala Governança Transformar logs e eventos
técnicos em relatórios executivos,
técnicos e recomendações de
segurança.
Relatórios para STA, DLP/Safetica
e futuras ferramentas,
classificação de risco,
recomendações e criação de
insumos para governança.
Mensagem de valor
A proposta não é substituir analistas, SIEM ou ferramentas de segurança existentes. A IA atuaria como uma
camada consultiva, capaz de resumir eventos, explicar contexto, recomendar ações e padronizar
comunicações técnicas e executivas.
Proposta de Projeto de IA - NeoIA Security Portal
Documento preliminar para discussão interna - Neotel
2. Ala Técnica - Chatbot e Chamados
A ala técnica funcionaria como um copiloto para analistas e consultores. O usuário faria perguntas sobre
ferramentas, erros, integrações, procedimentos e boas práticas. A IA responderia com base em uma base de
conhecimento interna e, quando necessário, poderia gerar um rascunho de chamado para o Octadesk.
Função Descrição
Chatbot técnico Responde perguntas sobre STA, CTE, DDC,
DLP/Safetica, SIEM, IAM, PAM e outros temas
definidos.
RAG/base de conhecimento Busca documentos internos, playbooks,
procedimentos, templates, FAQs e documentação de
fabricantes antes de responder.
Geração de chamado A IA monta título, descrição, impacto, evidências
necessárias, produto afetado e severidade sugerida.
Integração Octadesk No MVP, recomenda-se gerar o texto e permitir
revisão humana antes da criação via API.
Ponto de controle recomendado
Para o MVP, a criação de chamado deve ser assistida, não totalmente automática: a IA gera o conteúdo, o
usuário revisa e somente depois clica em "Criar chamado no Octadesk".
3. Ala Governança - Relatórios Executivos
A ala de governança seria responsável por analisar logs ou exportações de ferramentas pré-estabelecidas, como
STA e DLP/Safetica, e gerar relatórios claros para gestores, clientes e áreas de governança.
Entrada Processamento Saída
Logs do STA via endpoint/API Parser, normalização,
mascaramento, regras de risco e
IA generativa.
Relatório executivo, relatório
técnico, recomendações e possível
chamado.
Exportações de DLP/Safetica Agrupamento por usuário,
operação, aplicação, política,
bloqueios e tendências.
Resumo de operações, riscos,
ações recomendadas e evidência
para auditoria.
Alertas de SIEM ou CSV manual Classificação de eventos, volume,
severidade, eventos recorrentes e
correlação básica.
Resumo para governança,
possíveis incidentes e
recomendações de resposta.
O MVP deve começar com poucas fontes. A recomendação é iniciar por STA, devido à disponibilidade do
endpoint de logs, e eventualmente adicionar DLP/Safetica em uma segunda etapa.
4. Onde a IA Entra no Processo
A IA não deve receber logs brutos gigantes nem tomar decisões sozinha. O desenho recomendado combina
regras determinísticas, processamento em Python, busca em base de conhecimento e geração de linguagem
natural.
Camada Papel
Parser/normalização Lê logs brutos, extrai campos importantes e
transforma em estrutura padronizada.
Proposta de Projeto de IA - NeoIA Security Portal
Documento preliminar para discussão interna - Neotel
Mascaramento Remove ou substitui dados sensíveis antes de enviar
ao modelo, especialmente em modo nuvem.
Motor de regras Identifica padrões como falhas excessivas, MFA
negado, acesso fora do horário e usuários com risco
elevado.
IA generativa Transforma os dados estruturados em análise,
resumo, recomendação, relatório e texto de chamado.
RAG Permite que o chatbot responda com base em
documentos internos e playbooks.
5. Infraestrutura Atual Observada
A evidência enviada mostra um host ESXi com recursos relevantes para um MVP, mas também com grande
número de máquinas virtuais e uso de storage considerável. Os números abaixo foram extraídos visualmente do
print disponibilizado.
Item Valor observado
Host imperial-shuttle.neotel.com.br
Fabricante/modelo HPE ProLiant DL380 Gen10 Plus
ESXi 8.0
CPU 48 CPUs / capacidade aproximada de 100,6 GHz /
uso baixo no momento do print
Memória 383,45 GB de RAM / cerca de 206,45 GB em uso /
177 GB livres
Storage 3,58 TB de capacidade / cerca de 2,93 TB usado /
668,86 GB livres
Máquinas virtuais 53 VMs listadas no host
Evidência visual da infraestrutura analisada:
Proposta de Projeto de IA - NeoIA Security Portal
Documento preliminar para discussão interna - Neotel
Conclusão: é possível hospedar o MVP em uma VM nesse host, mas o Ollama deve ser limitado e usado em
processamento assíncrono, preferencialmente fora do horário comercial, para evitar impacto nas demais VMs.
6. Opções de Infraestrutura
Opção Descrição Viabilidade para MVP
Local com Ollama no ESXi VM Ubuntu no ESXi, Docker,
Ollama, modelo 7B/8B quantizado,
processamento em lote.
Alta, desde que limitada a 4-8
vCPU e 16-32 GB RAM.
Híbrido com Bedrock Portal local faz
parser/mascaramento e envia
resumo estruturado para Amazon
Bedrock.
Alta, com melhor desempenho e
qualidade, mas exige política de
envio de dados para nuvem.
OpenAI/Azure OpenAI Similar ao Bedrock, com modelos
via API e custo por token.
Alta para MVP, principalmente se
dados forem mascarados.
Appliance dedicado com GPU Servidor ou workstation com GPU
para IA local performática.
Boa para produto futuro, mas não
necessária no MVP.
7. Arquitetura Recomendada para o MVP
A recomendação é começar com um MVP local controlado, aproveitando o ESXi existente e integrando Octadesk
e logs do STA. A arquitetura deve ser modular para permitir trocar o motor de IA entre Ollama e nuvem sem
reescrever todo o sistema.
Componente Recomendação para MVP
Sistema operacional Ubuntu Server 22.04/24.04
Virtualização VM no ESXi existente
Recursos iniciais 4 vCPU, 16 GB RAM, 80-100 GB de disco
Recursos recomendados 8 vCPU, 32 GB RAM, 150-200 GB de disco
IA local Ollama com modelo 7B/8B quantizado
Aplicação Streamlit para protótipo; FastAPI + frontend em
evolução
Banco SQLite no protótipo; PostgreSQL em MVP interno
Base vetorial ChromaDB ou Qdrant para RAG
Processamento Batch/agendado; relatórios diários ou semanais
Integrações iniciais STA Logs API e Octadesk API
8. Fluxo Funcional Proposto
Usuário acessa o Portal NeoIA
|
+-- Ala Técnica
| |
| +-- Chatbot técnico
| +-- Busca em base de conhecimento
| +-- Geração de troubleshooting
| +-- Geração assistida de chamado no Octadesk
|
+-- Ala Governança
|
Proposta de Projeto de IA - NeoIA Security Portal
Documento preliminar para discussão interna - Neotel
+-- Coleta ou upload de logs
+-- Parser e normalização
+-- Mascaramento de dados
+-- Motor de regras
+-- IA local ou nuvem
+-- Relatório executivo/técnico
+-- Sugestão de chamado ou ação
9. Estimativa de Custos
Os valores abaixo são estimativas de ordem de grandeza para discussão. Custos finais dependem de cotação,
modelo escolhido, região cloud, volume de uso, política comercial dos provedores e capacidade disponível no
ambiente.
Cenário Custo de infraestrutura Custo recorrente Observações
ESXi existente + Ollama Baixo, caso haja
capacidade disponível no
host atual.
Baixo.
Energia/manutenção já
existentes; sem custo por
token.
Mais lento sem GPU,
mas aceitável para
relatórios assíncronos.
Bedrock/OpenAI/Azure Baixo localmente. Por token. Pode ser
muito baixo se o sistema
enviar apenas resumos
estruturados.
Melhor qualidade e
velocidade, mas exige
governança sobre dados
enviados.
Appliance simples com
GPU
Estimativa: R$ 15 mil a
R$ 35 mil.
Baixo/médio. Workstation ou servidor
simples com GPU de 16-
24 GB. Bom para
laboratório ou produto
inicial.
Appliance profissional Estimativa: R$ 50 mil a
R$ 120 mil+.
Médio. Servidor com suporte,
mais RAM, storage e
GPU profissional.
Appliance enterprise Estimativa: R$ 120 mil a
R$ 300 mil+.
Médio/alto. Cenário para oferta
comercial robusta,
suporte e hardware
homologado.
9.1 Fórmula de custo para IA em nuvem
Em modelos cobrados por tokens, o custo aproximado por relatório pode ser estimado assim:
Custo = (tokens de entrada / 1.000.000 x preço de entrada) + (tokens de saída / 1.000.000 x
preço de saída)
Exemplo de dimensionamento para relatório já pré-processado: 20.000 tokens de entrada e 3.000 tokens de
saída. O custo real deve ser recalculado de acordo com o preço vigente do modelo escolhido no Amazon
Bedrock, OpenAI API ou Azure OpenAI.
10. Riscos e Controles
Risco Impacto Controle recomendado
Impacto no ESXi compartilhado Pode afetar outras VMs se o
Ollama consumir CPU/RAM em
excesso.
Limitar vCPU/RAM, agendar jobs
fora do horário comercial,
monitorar host e começar com
cargas pequenas.
Proposta de Projeto de IA - NeoIA Security Portal
Documento preliminar para discussão interna - Neotel
Dados sensíveis em logs Risco de exposição de usuários,
IPs, hostnames e eventos de
segurança.
Mascaramento, criptografia em
repouso, controle de acesso e
política clara para modo nuvem.
Alucinação da IA Relatórios podem conter
interpretação incorreta.
Usar dados estruturados, regras
determinísticas, revisão humana e
evidências anexas.
Base de conhecimento
desorganizada
Chatbot pode responder mal ou de
forma genérica.
Curadoria inicial de documentos,
versionamento e validação por
especialistas.
Abertura automática de chamados Pode gerar ruído operacional. Manter etapa de revisão humana
antes da criação via Octadesk.
11. Plano de Implementação por Fases
Fase Objetivo Entregas
Fase 1 - Prova de conceito Validar fluxo básico em ambiente
controlado.
VM Ubuntu, Ollama, upload de log,
parser simples, relatório em tela e
geração de texto de chamado.
Fase 2 - MVP integrado Integrar fontes reais e Octadesk. Coleta de logs STA, criação
assistida de chamado via API,
histórico básico e relatórios
exportáveis.
Fase 3 - Ala técnica com RAG Adicionar chatbot com base de
conhecimento.
Upload de documentos, indexação,
perguntas técnicas e respostas
baseadas em documentação.
Fase 4 - Comparativo local x
nuvem
Testar qualidade e custo com
Bedrock/OpenAI/Azure.
Alternância de provider,
mascaramento, comparação de
relatórios e métricas.
Fase 5 - Produto interno/comercial Evoluir para uso recorrente e multi-
ferramenta.
RBAC, auditoria, PostgreSQL,
Qdrant, integrações adicionais,
dashboards e relatórios
agendados.
12. Métricas de Sucesso
 Redução do tempo para criar relatórios executivos a partir de logs.
 Redução do tempo para montar chamados técnicos com evidências e contexto.
 Aumento da padronização de respostas técnicas e relatórios para clientes.
 Capacidade de gerar relatório com dados mascarados e revisão humana.
 Baixo impacto no host ESXi durante testes controlados.
 Aceitação do time técnico e de governança sobre a utilidade das recomendações.
13. Recomendação Final
A recomendação é avançar com um MVP em escopo reduzido, aproveitando o ESXi existente e priorizando o
fluxo com logs do STA e criação assistida de chamados no Octadesk. O processamento deve ser assíncrono e
controlado, com IA local via Ollama em uma primeira validação. Em paralelo, recomenda-se criar uma opção de
provider em nuvem, como Amazon Bedrock, para comparação de qualidade, velocidade e custo.
Frase de apresentação sugerida
Proposta de Projeto de IA - NeoIA Security Portal
Documento preliminar para discussão interna - Neotel
O NeoIA Security Portal propõe uma plataforma única de IA para apoiar a operação técnica e a governança
em cibersegurança. Na ala técnica, atua como copiloto para troubleshooting e geração assistida de chamados.
Na ala de governança, transforma logs de ferramentas como STA e DLP em relatórios executivos e técnicos. A
primeira versão pode rodar em uma VM no ESXi existente usando Ollama, com possibilidade de evolução para
Bedrock, OpenAI/Azure ou appliance dedicado com GPU.
14. Referências Consultadas
 Amazon Bedrock - Pricing: https://aws.amazon.com/bedrock/pricing/
 Amazon Bedrock - Visão geral: https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-
bedrock.html
 Ollama API - Documentação: https://docs.ollama.com/api/introduction
 Ollama API - Autenticação local: https://docs.ollama.com/api/authentication
 OpenAI API Platform: https://openai.com/pt-BR/api/
 VMware/Broadcom - VMDirectPath I/O:
https://knowledge.broadcom.com/external/article/309986/configuring-vmdirectpath-io-passthrough.html
Observação: preços de nuvem e hardware mudam com frequência. Antes de decisão de compra ou contratação,
recomenda-se validar valores diretamente nas páginas oficiais e/ou com fornecedores homologados.
15. Observações de Segurança e Governança
Como o projeto lida com logs de segurança, recomenda-se adotar desde o MVP práticas de minimização de
dados, mascaramento, revisão humana, controle de acesso e trilha de auditoria. A solução deve ser posicionada
como suporte à decisão, não como mecanismo automático de resposta a incidentes ou substituição do analista.