# SafeNet Trusted Access (STA) — Documentação Técnica

## Visão Geral

SafeNet Trusted Access (STA) é a solução de autenticação multifator (MFA) e Single Sign-On (SSO) da Thales utilizada pela Neotel para controle de acesso seguro a aplicações corporativas e em nuvem.

O STA gerencia políticas de autenticação, tokens OTP, aplicações SAML/OIDC e logs de acesso dos usuários.

---

## Principais Componentes

### Token OTP
- **SafeNet MobilePASS+**: aplicativo mobile que gera senhas de uso único (TOTP)
- **SafeNet eToken**: token físico USB para autenticação de hardware
- **OTP por SMS/e-mail**: código temporário enviado por canal alternativo

### Aplicações e Federação
- Suporte a **SAML 2.0** e **OIDC** para SSO com aplicações em nuvem
- Integração com Active Directory (AD) e LDAP para sincronização de usuários
- Console de administração web acessível em `https://sta.safenetid.com`

### Políticas de Acesso
- Políticas de autenticação baseadas em: grupo de usuário, aplicação, faixa de IP, horário
- Suporte a autenticação adaptativa (risco baseado em contexto)
- Bloqueio automático após tentativas inválidas configurável

---

## Troubleshooting Comum

### Usuário não consegue se autenticar

**Sintomas**: Token rejeitado, acesso negado, loop de autenticação.

**Verificações**:
1. Confirmar que o token do usuário está **ativo** no console STA
2. Verificar sincronização de hora do dispositivo (TOTP é sensível a drift de tempo maior que 30s)
3. Checar se a política de acesso permite o IP/horário do usuário
4. Revisar logs em Relatórios - Log de Autenticação filtrando pelo usuário e período

**Ações corretivas**:
- Ressincronizar o token via console: Usuários, selecionar usuário, Ações, Ressincronizar Token
- Emitir novo token temporário (OTP por e-mail) enquanto investiga
- Verificar se o usuário está no grupo correto vinculado à política

---

### Token bloqueado

**Causa**: Excesso de tentativas inválidas (padrão: 10 tentativas).

**Resolução**:
1. Acesse o console STA
2. Usuários, buscar usuário, Tokens
3. Clique em Desbloquear Token
4. Oriente o usuário a aguardar 2 minutos antes de tentar novamente

---

### Usuário sem token cadastrado

**Sintoma**: Usuário existe no AD mas não tem token no STA.

**Passos**:
1. Verificar se a sincronização AD para STA está ativa e atualizada
2. Atribuir token manualmente: Usuários, selecionar, Atribuir Token
3. Enviar e-mail de ativação do MobilePASS+ para o usuário

---

### Aplicação SAML não redireciona corretamente

**Sintoma**: Após autenticação no STA, usuário é redirecionado para página de erro na aplicação.

**Verificações**:
1. Conferir Entity ID e ACS URL cadastrados no STA e na aplicação — devem ser idênticos
2. Validar certificado SAML: Aplicações, selecionar app, Metadados SAML
3. Checar atributos SAML enviados (ex: email, grupos) — comparar com o que a aplicação espera
4. Testar com ferramenta SAML Tracer no navegador para capturar o assertion

---

## Logs e Relatórios

### Acessar logs de autenticação
- Console STA, Relatórios, Log de Autenticação
- Filtros disponíveis: usuário, aplicação, status (sucesso/falha), período, IP de origem
- Export disponível em CSV

### Eventos importantes para monitorar

| Evento | Significado |
|--------|-------------|
| AUTH_FAILED | Tentativa de autenticação inválida |
| TOKEN_LOCKED | Token bloqueado por excesso de falhas |
| POLICY_DENIED | Acesso negado por política (IP, horário, grupo) |
| SSO_SUCCESS | SSO concluído com sucesso |
| TOKEN_SYNC | Ressincronização de token realizada |

---

## Integrações Comuns na Neotel

- **VPN Cisco**: autenticação via RADIUS + STA OTP
- **Microsoft 365**: SSO via SAML com STA como IdP
- **Aplicações internas**: OIDC com STA como provedor de identidade
- **Octadesk**: abertura de chamados para suporte de acesso

---

## DLP — Data Loss Prevention

O módulo DLP monitora e controla a transferência de dados sensíveis nos endpoints e na rede.

### Eventos DLP comuns
- **Bloqueio de USB**: cópia para dispositivo removível bloqueada por política
- **Upload bloqueado**: tentativa de upload de arquivo classificado para serviço não autorizado
- **Print Screen**: captura de tela de aplicação sensível bloqueada

### Troubleshooting DLP
1. Verificar se o agente DLP está ativo no endpoint
2. Conferir a política aplicada ao usuário/grupo
3. Checar logs de incidente filtrando por usuário ou hash do arquivo

---

## IAM/PAM — Gestão de Identidade e Acesso Privilegiado

### Conceitos
- **IAM**: gerencia identidades de todos os usuários (criação, provisionamento, desativação)
- **PAM**: controla acesso privilegiado de administradores a sistemas críticos

### Troubleshooting PAM
- Usuário sem acesso a servidor via PAM: verificar se a conta está no grupo de acesso correto
- Sessão gravada não disponível: checar configuração de storage de gravação
- Credencial rotacionada automaticamente: usar o cofre PAM para obter a senha atual

---

## SIEM — Security Information and Event Management

O SIEM agrega logs do STA, DLP, firewall e endpoints para correlação de eventos de segurança.

### Consultas comuns
- Falhas de autenticação repetidas do mesmo IP: possível ataque de força bruta
- Acesso fora do horário comercial: revisar logs de autenticação STA + VPN
- Volume alto de eventos DLP: investigar possível exfiltração de dados

### Escalação
Em caso de alerta crítico do SIEM, abrir chamado no Octadesk com categoria Segurança - Incidente e prioridade Alta.
