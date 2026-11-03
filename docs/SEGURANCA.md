# Prompt 1 — Auditoria de segurança e plano (sem aplicar correções)

**Status:** auditoria inicial preservada abaixo; **correção 1 aprovada e aplicada**. Demais correções continuam dependendo de autorização. Não houve teste de intrusão ou deploy.

| Achado | Risco | Arquivo/linha | Correção proposta |
|---|---|---|---|
| `SECRET_KEY` não é obrigatória, causando chave efêmera entre reinícios | Médio | `app.py:30` | Exigir chave via ambiente quando em produção, instruir geração no README |
| Não há bloqueio de tentativas repetidas de senha | Médio | `app.py:163–178` | Limitar tentativas por origem/conta de maneira compatível com hospedagem; não instalar serviço pesado sem necessidade |
| Intervalos podem se sobrepor, afetando integridade do cronograma | Alto (integridade) | `app.py:22,368–410` | Validar não sobreposição em escrita e regeneração, adicionar teste de concorrência |
| Mudanças de disponibilidade podem deixar cronograma antigo incompatível | Médio (integridade) | `app.py:277–317,323–379` | Avisar usuário e exigir regeneração ou recálculo controlado |
| Consultas SQL parametrizadas e autorização por dono implementadas | Baixo residual, não testado | `app.py:53–83` e rotas | Testar permissão em CRUD de A versus B com banco real temporário |
| POST utiliza token CSRF de sessão, HTML usa autoescape Jinja | Baixo residual, não testado | `app.py:118–124`, templates | Testar CSRF ausente, XSS em nomes/observações, logout por POST |
| Sessões HTTP-only/SameSite; Secure depende do ambiente | Médio se produção HTTPS não definir variável | `app.py:30` | Configurar COOKIE_SECURE=1 no servidor HTTPS e revisar configurações reais |
| SQLite fora de `/static`, `.env` e banco ignorados no Git | Baixo residual | `.gitignore`, `app.py:29–32` | Conferir conteúdo enviado ao Git e permissões da hospedagem |
| Supabase, RLS, service_role, APIs externas, webhooks/pagamento | Não se aplica | — | Nenhuma mudança |

**Não encontrado na inspeção:** senha/token real hardcoded, consultas SQL montadas por concatenação de input, saída com `|safe` em conteúdo do usuário. **Não verificado:** histórico Git remoto (inexistente aqui), backup público, HTTPS e filesystem da hospedagem, autorização real sob requisições, testes simultâneos.

## Sequência proposta — uma correção por aprovação

1. Garantir que cronograma e edição de sessões não permitam intervalos sobrepostos; preservar sessões concluídas e validar operação atômica.
2. Exigir SECRET_KEY estável na produção; verificar configuração segura do cookie.
3. Deixar claro que mudanças de disponibilidade exigem regenerar agenda.
4. Criar/verificar testes de autorização e CSRF; avaliar limitação de tentativas de login sem complexidade excessiva.

**Ponto de aprovação:** aguardar OK explícito para o item 1 antes de alterar código. A aprovação da implementação inicial não equivale à aprovação dessas correções.


## Acompanhamento — correção 1, aprovada em conversa em 02/11/2026

**Autorização expressa:** impedir sessões sobrepostas, preservar sessões concluídas e documentar correção e verificação. Não houve aprovação para aplicar os itens 2 a 4.

**Alterações efetivamente realizadas** em `app.py`:

- Função `overlapping_session`: detecta qualquer interseção de intervalos entre sessões de **todos os concursos do usuário autenticado**, inclusive sessões concluídas e pendentes; sessões de usuários diferentes não conflitam. Intervalos contíguos (fim = início) são permitidos.
- `regenerate`: mantém transação SQLite iniciada por `BEGIN IMMEDIATE`; elimina apenas sessões futuras pendentes do concurso escolhido, preservando as concluídas e o histórico. Antes de inserir, verifica cada intervalo contra o banco após a exclusão e contra os blocos recém-inseridos. Pula blocos com conflito e informa quantos foram gerados/ignorados. Substituiu `INSERT OR IGNORE` por `INSERT` depois da checagem, evitando ocultar falhas. Se não houver sequer um novo bloco livre, a transação é revertida, inclusive as exclusões.
- `session_detail`: valida os horários após normalizar a minutos e rejeita períodos com sobreposição; consulta conflitos e altera a sessão **na mesma transação imediata**, excluindo a própria sessão da checagem. Horários com fuso explícito são recusados para manter comparação local consistente.
- Não houve mudança de schema ou migração, instalação de dependências, alteração da auditoria inicial ou alteração de dados reais.

**Verificação executada:** `python docs/evidencias/verificar_correcao_01.py` → **7 verificações isoladas passaram**, usando banco SQLite temporário e funções reais extraídas do código com substitutos para entrada HTTP/flash. Inclui concorrência com duas conexões independentes, edição com conflito, bordas contíguas, isolamento por usuário, regeneração repetida, preservação de concluída e rollback completo quando sem vagas. Saída em `docs/evidencias/correcao_01_verificacao.txt`.

**Limites:** NÃO constitui execução de Flask, suíte `pytest` de integração HTTP, teste de navegador ou teste em produção. A validação real via Flask e os cenários do Prompt 3 seguem pendentes de autorização; os resultados acima não permitem afirmar ausência de toda condição de corrida em todos os endpoints. Sessões antigas que já estejam sobrepostas **não são corrigidas automaticamente**; as rotas de geração/edição impedem novos conflitos.

**Próximo ponto de aprovação:** correção 2 (exigir `SECRET_KEY` estável na produção). Não executada.


## Correção 2 — chave de sessão estável em produção e cookies

**Aprovação expressa da estudante:** exigir `SECRET_KEY` estável em produção e configurar cookies de sessão com segurança. Alteração limitada a esse item; correções 3 e 4 **não autorizadas**.

**Mudança em `app.py:28–49`:** a variável `RUMO_ENV=production` identifica o ambiente de produção. Nessa condição, se `SECRET_KEY` estiver ausente ou contiver apenas espaços, `create_app` interrompe a inicialização com erro claro, **antes de criar/abrir o banco**. Quando há chave, ela permanece a mesma entre reinícios desde que a hospedagem mantenha a variável. `SESSION_COOKIE_SECURE` é habilitado automaticamente em produção e também pode ser habilitado opcionalmente via `COOKIE_SECURE=1`. `SESSION_COOKIE_HTTPONLY=True` e `SESSION_COOKIE_SAMESITE='Lax'` são mantidos. Ambiente local HTTP permanece utilizável com segredo de desenvolvimento efêmero, sem o atributo Secure por padrão. `.env.example` e `README.md` atualizados sem inserir segredo real.

**Evidência:** `python -m compileall -q app.py tests` concluiu sem erros de sintaxe. O caso real `test_producao_exige_secret_key_e_cookie_seguro` foi escrito no módulo `tests/test_auth_security.py`, mas **não executado**: a coleta do pytest foi bloqueada pela ausência de Flask no ambiente desta conversa. Isso não equivale a aprovação automática do caso. Fluxo local Flask e screenshots confirmados pela estudante no Windows antes desta alteração; a nova configuração ainda precisa ser testada lá.

**Observações:** configurar `RUMO_ENV=production` é indispensável na hospedagem; sem ele, o modo de desenvolvimento continua intencionalmente permissivo para a chave. Em produção HTTPS, o cookie Secure impede que a sessão seja enviada por HTTP, mas não substitui TLS válido, proteção de conta, controle de propriedade ou rate limiting. Não foi feita alteração de schema nem do banco; nenhum segredo foi incluído no código.
