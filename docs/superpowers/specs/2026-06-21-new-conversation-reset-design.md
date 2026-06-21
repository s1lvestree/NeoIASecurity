# Reset de nova conversa

## Problema

O botão **Nova conversa** apenas define `activeConversationId` como `null`. Quando nenhuma conversa está ativa, clicar no botão repete `null -> null`; o React não produz uma alteração observável, o rascunho permanece preenchido e o campo não recebe foco.

## Comportamento esperado

- Cada clique em **Nova conversa** limpa o rascunho, inclusive quando nenhuma conversa está ativa.
- O campo de mensagem recebe foco após o reset.
- Mensagens e erros da conversa selecionada deixam de ser exibidos.
- Uma conversa vazia não aparece no histórico nem é persistida.
- A conversa continua sendo criada e salva somente após o primeiro envio válido.

## Design

O hook `useTechnicalCopilotChat` manterá um contador de reset do editor. `startNewConversation` continuará removendo a seleção ativa e limpando o erro, mas também incrementará esse contador em cada chamada. O contador será exposto ao `TechnicalCopilotPage` e repassado ao componente `TechnicalCopilot`.

O `TechnicalCopilot` observará o contador junto do identificador da conversa. Quando um deles mudar, limpará o rascunho e focará a área de texto por meio de uma referência local. O contador permite distinguir cliques consecutivos quando `conversationId` permanece `null`, sem remontar o componente inteiro e sem expor uma API imperativa ao componente pai.

## Estado e persistência

O reset é exclusivamente estado de interface. Ele não cria `ChatConversation`, não chama o repositório e não altera o histórico salvo. O fluxo existente de `submitMessage` permanece responsável por criar e persistir a conversa no primeiro envio.

## Erros e concorrência

O reset continuará limpando erros visíveis. Esta correção não altera o comportamento de requisições já em andamento; o botão não cancela chamadas HTTP. Nenhuma nova falha de persistência é possível, pois o reset não acessa o repositório.

## Testes

- Teste do hook: chamadas consecutivas a `startNewConversation` incrementam o contador mesmo com `activeConversationId = null`.
- Teste do componente: a mudança do contador limpa um rascunho e foca a área de texto sem exigir mudança do identificador.
- Regressão: os testes existentes devem confirmar que uma conversa só é persistida após o primeiro envio.

## Fora de escopo

- Criar ou salvar conversas vazias.
- Cancelar uma resposta em andamento.
- Alterar layout, textos ou histórico.
