# New Conversation Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer cada clique em “Nova conversa” limpar o rascunho e focar o editor sem persistir uma conversa vazia.

**Architecture:** O hook de chat emitirá um contador monotônico de reset, independente do identificador da conversa. A página repassará esse sinal ao editor, que reagirá limpando seu estado local e focando a área de texto; a persistência continuará restrita ao primeiro envio.

**Tech Stack:** React 18, TypeScript, Vitest, Testing Library, Vite.

---

## File map

- `apps/web/src/app/hooks/useTechnicalCopilotChat.ts`: mantém e expõe o sinal de reset.
- `apps/web/src/app/hooks/useTechnicalCopilotChat.test.ts`: prova que cliques consecutivos em nova conversa geram resets distintos.
- `apps/web/src/app/components/TechnicalCopilot.tsx`: limpa e foca o editor quando recebe um novo sinal.
- `apps/web/src/app/components/TechnicalCopilot.test.tsx`: prova limpeza e foco sem mudança de `conversationId`.
- `apps/web/src/app/pages/TechnicalCopilotPage.tsx`: conecta o sinal do hook ao editor.

### Task 1: Emitir um reset em cada solicitação de nova conversa

**Files:**
- Modify: `apps/web/src/app/hooks/useTechnicalCopilotChat.ts`
- Test: `apps/web/src/app/hooks/useTechnicalCopilotChat.test.ts`

- [ ] **Step 1: Write the failing hook test**

Adicionar ao `describe('useTechnicalCopilotChat', ...)`:

```ts
it('emite um novo reset a cada solicitacao de nova conversa', () => {
  const repository = new MemoryConversationRepository();
  const chatService: ChatService = { sendMessage: vi.fn() };
  const { result } = renderHook(() =>
    useTechnicalCopilotChat({ repository, chatService, healthService }),
  );

  expect(result.current.editorResetKey).toBe(0);

  act(() => result.current.startNewConversation());
  expect(result.current.editorResetKey).toBe(1);

  act(() => result.current.startNewConversation());
  expect(result.current.editorResetKey).toBe(2);
  expect(repository.conversations).toEqual([]);
});
```

- [ ] **Step 2: Run the hook test and verify RED**

Run:

```powershell
npm --prefix apps/web test -- --run src/app/hooks/useTechnicalCopilotChat.test.ts
```

Expected: FAIL porque `editorResetKey` ainda não existe.

- [ ] **Step 3: Add the minimal reset state**

Em `useTechnicalCopilotChat`, adicionar o estado:

```ts
const [editorResetKey, setEditorResetKey] = useState(0);
```

Atualizar o callback:

```ts
const startNewConversation = useCallback(() => {
  setActiveConversationId(null);
  setError(null);
  setEditorResetKey((current) => current + 1);
}, []);
```

Expor `editorResetKey` no objeto retornado pelo hook.

- [ ] **Step 4: Run the hook test and verify GREEN**

Run:

```powershell
npm --prefix apps/web test -- --run src/app/hooks/useTechnicalCopilotChat.test.ts
```

Expected: todos os testes do arquivo passam.

- [ ] **Step 5: Commit the hook change**

```powershell
git add apps/web/src/app/hooks/useTechnicalCopilotChat.ts apps/web/src/app/hooks/useTechnicalCopilotChat.test.ts
git commit -m "fix: emit new conversation editor reset"
```

### Task 2: Limpar e focar o editor ao receber o reset

**Files:**
- Modify: `apps/web/src/app/components/TechnicalCopilot.tsx`
- Test: `apps/web/src/app/components/TechnicalCopilot.test.tsx`
- Modify: `apps/web/src/app/pages/TechnicalCopilotPage.tsx`

- [ ] **Step 1: Write the failing component test**

No teste do `TechnicalCopilot`, importar `render`, `screen` e `waitFor` de Testing Library e `userEvent`. Adicionar:

```tsx
it('limpa e foca o rascunho quando uma nova conversa e solicitada', async () => {
  const user = userEvent.setup();
  const { rerender } = render(
    <TechnicalCopilot {...defaultProps} conversationId={null} editorResetKey={0} />,
  );
  const editor = screen.getByRole('textbox', { name: 'Mensagem para o Copiloto' });

  await user.type(editor, 'rascunho ainda nao enviado');
  expect(editor).toHaveValue('rascunho ainda nao enviado');

  rerender(<TechnicalCopilot {...defaultProps} conversationId={null} editorResetKey={1} />);

  await waitFor(() => expect(editor).toHaveValue(''));
  expect(editor).toHaveFocus();
});
```

Atualizar as renderizações existentes no arquivo para fornecer `editorResetKey={0}`.

- [ ] **Step 2: Run the component test and verify RED**

Run:

```powershell
npm --prefix apps/web test -- --run src/app/components/TechnicalCopilot.test.tsx
```

Expected: FAIL de TypeScript/execução porque `editorResetKey` ainda não pertence às props.

- [ ] **Step 3: Implement reset and focus in the editor**

Adicionar à interface:

```ts
editorResetKey: number;
```

Receber `editorResetKey` nas props, criar a referência:

```ts
const editorRef = useRef<HTMLTextAreaElement | null>(null);
```

Substituir o efeito atual de limpeza por:

```ts
useEffect(() => {
  setDraft('');
  editorRef.current?.focus();
}, [conversationId, editorResetKey]);
```

Associar a referência à área de texto:

```tsx
<textarea
  ref={editorRef}
  // propriedades existentes
/>
```

Na página, repassar o valor:

```tsx
<TechnicalCopilot
  conversationId={copilot.activeConversationId}
  editorResetKey={copilot.editorResetKey}
  // propriedades existentes
/>
```

- [ ] **Step 4: Run the component test and verify GREEN**

Run:

```powershell
npm --prefix apps/web test -- --run src/app/components/TechnicalCopilot.test.tsx
```

Expected: todos os testes do arquivo passam, incluindo limpeza e foco.

- [ ] **Step 5: Run the complete frontend verification**

Run:

```powershell
npm --prefix apps/web test -- --run
npm run build:web
```

Expected: suíte sem falhas e build Vite concluído com exit code 0.

- [ ] **Step 6: Commit the UI change**

```powershell
git add apps/web/src/app/components/TechnicalCopilot.tsx apps/web/src/app/components/TechnicalCopilot.test.tsx apps/web/src/app/pages/TechnicalCopilotPage.tsx
git commit -m "fix: reset and focus new conversation editor"
```

### Task 3: Verify the running application

**Files:**
- No file changes.

- [ ] **Step 1: Ensure the development server is running**

Run:

```powershell
npm run dev:web
```

Expected: Vite atende `http://localhost:5173`.

- [ ] **Step 2: Verify the original scenario manually**

No Copiloto Técnico, digitar um rascunho sem enviar, clicar em **Nova conversa** e verificar que o texto desaparece e o cursor permanece no editor. Repetir o clique e confirmar que nenhuma conversa vazia aparece no histórico.
