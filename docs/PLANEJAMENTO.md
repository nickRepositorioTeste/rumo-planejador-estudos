# Planejamento — Rumo: Planejador de Estudos

**Estado:** planejamento reduzido aprovado pela estudante em conversa; desenvolvimento autorizado. **Autora:** Nicolly Cristina Gonçalves da Silva. **Tema:** proposta da estudante; aprovação docente não verificada.

## Inspeção inicial
- Ambiente de trabalho disponível nesta sessão: Python 3.13.5 e pip 25.1.1. A estudante informa Python 3.14.10 no Windows; compatibilidade da hospedagem ainda não verificada.
- Não há repositório Git ou código-fonte do projeto acessível nesta sessão. `git status` executado no diretório inicial retornou “not a git repository”. Apenas o enunciado/prompt foi recebido. Não houve instalação, execução de aplicativo, testes ou publicação.
- Os documentos aqui são uma proposta independente; antes de implementar no repositório real será necessário inspecioná-lo e preservar seus arquivos.

## Problema e objetivo
Candidatos precisam organizar disciplinas e horários até a prova e registrar resultados de simulados sem perder histórico. Criar aplicação web responsiva com CRUD, validação no servidor, persistência SQLite e publicação verificável.

## Escopo recomendado para entrega acadêmica (MVP)
1. Cadastro/login simples; senha com hash, sessão e isolamento de registros por usuário.
2. CRUD de concursos e disciplinas com pesos, quantidades, penalidade, mínimos e metas.
3. CRUD de disponibilidade semanal (um intervalo por dia) e datas bloqueadas.
4. Gerar cronograma básico até a véspera da prova, listar, concluir, editar e excluir sessões; regeneração substitui apenas sessões futuras não concluídas após confirmação.
5. Registrar e consultar/editar/excluir simulados por concurso, com acertos/erros/brancos por disciplina, pontuação e histórico imutável das regras utilizadas.
6. Dashboard enxuto: dias restantes, próximas sessões, tempo planejado/concluído, último simulado e metas/mínimos.

**Cortes propostos para caber no prazo:** adiar sessões automáticas específicas de questões e frequência automática de simulados, otimização por desempenho, gráficos avançados, múltiplos intervalos por dia e agrupamentos de disciplinas. Simulados podem ser registrados manualmente; sessões de questões podem ser criadas/rotuladas manualmente. O restante é priorizado, mas se o prazo apertar, simplificar primeiro o dashboard, nunca o CRUD, a segurança ou a persistência.

## Telas
Login/cadastro; Visão geral; Concursos (lista, formulário, detalhes com disciplinas); Disponibilidade; Cronograma (lista por dia, geração e edição); Simulados (formulário e histórico). Interface Jinja/HTML/CSS responsiva, branco/off-white, grafite, verde profundo, sem página de marketing.

## Entidades e relações
- **Usuario** (id, email único, hash_senha): proprietário de concursos.
- **Concurso** (id, usuario_id, nome, cargo, data_prova, minimo_geral, meta_geral): pertence a usuário, tem disciplinas, sessões e simulados.
- **Disciplina** (id, concurso_id, nome, total_questoes, pontos_acerto, penalidade_erro, minimo_pontos, meta_percentual, nao_zerar): pertence a concurso.
- **Disponibilidade** (id, usuario_id, dia_semana, inicio, fim): pertence a usuário, um intervalo por dia.
- **DataIndisponivel** (id, usuario_id, data): pertence a usuário.
- **Sessao** (id, concurso_id, disciplina_id, inicio, fim, tipo, status, minutos_reais, observacao): pertence a concurso e, quando aplicável, disciplina.
- **Simulado** (id, concurso_id, data, nota_total, regras_snapshot): pertence a concurso, tem resultados por disciplina.
- **ResultadoDisciplina** (id, simulado_id, disciplina_nome_snapshot, acertos, erros, brancos, total_questoes_snapshot, pontos_acerto_snapshot, penalidade_snapshot, minimo_snapshot, nao_zerar_snapshot, nota): pertence a simulado. Snapshots preservam pontuação histórica após alterações.

## Regras e algoritmo inicial
- O usuário informa regras; não há importação automática de editais.
- Nota da disciplina = acertos × pontos_por_acerto − erros × penalidade_por_erro; branco = zero. Nota geral = soma das notas; notas negativas são mantidas. Usar Decimal em cálculos monetários/pontuação decimal e arredondar apenas na exibição a duas casas.
- Verificar separadamente mínimo geral, mínimo por disciplina, regra de não zerar e metas pessoais. Exibir “atingiu os mínimos configurados”, nunca “aprovado”. Pontos e percentuais identificados explicitamente.
- Cronograma: enumerar dias entre a data atual e a véspera da prova; remover datas bloqueadas e dias sem intervalo; dividir o tempo em blocos de 50 minutos de estudo com pausa de 10 minutos entre blocos quando couber, sem exceder disponibilidade. Se houver janela menor que 50 minutos, admitir bloco final de no mínimo 25 minutos; caso contrário avisar indisponibilidade.
- Distribuição das disciplinas por rodízio ponderado: peso relativo = total_questoes × pontos_acerto, com pesos não positivos tratados como peso mínimo 1 somente para alocação (não para nota). Alocar os próximos blocos à disciplina com menor razão blocos_atribuidos/peso, desempate por ordem de cadastro. É uma heurística explicável, não otimização perfeita nem adaptação automática ao desempenho.
- Persistir cronograma em transação. Para regeração, confirmar exclusão apenas de sessões futuras não concluídas e recriá-las em uma transação; proteger contra duplicatas por constraints/controle transacional. Preservar concluídas e históricos.

## Segurança e implementação
Flask, SQLite, Jinja, CSS/JS e pytest; sem frameworks de frontend. Banco fora de diretório público e fora do Git. Senhas com Werkzeug, SECRET_KEY por ambiente, CSRF em POST, cookies de sessão seguros conforme ambiente, consultas parametrizadas/ORM e filtro de proprietário em cada rota. Validar todos os campos no servidor, usar escape do Jinja, debug desativado na produção. Não usar dados compartilhados entre visitantes. Hospedagem somente após verificar compatibilidade Flask e persistência real do SQLite.

## Critérios de aceite verificáveis
- Usuário A não acessa nem altera registros de B; senhas não ficam em texto puro.
- CRUD completo para concursos e disciplinas, com dados mantidos após reinício.
- Datas de prova passadas, intervalos inválidos e contagens de questões incompatíveis são rejeitados sem gravação parcial.
- Quarta-feira editada para 11h não recebe sessões após 11h; datas bloqueadas e dia da prova não recebem sessões.
- Cronograma sem disponibilidade informa motivo; regeneração não duplica sessões e preserva concluídas.
- Cálculo de penalidade correto, mínimos e metas separados; simulado antigo mantém nota após mudança das regras.
- Testes pytest com banco temporário real e isolado, cobrindo rotas e autorização; resultados registrados somente após execução.
- UI verificada em desktop e celular; repositório GitHub e URL pública testados antes de constarem como entregues.
- Auditorias na ordem 4 → 1 → 3 → 2, respeitando as aprovações exigidas em cada fase.

## Limitações e riscos
Cronograma não considera dificuldade subjetiva, feriados não bloqueados nem desempenho histórico automaticamente. Um intervalo diário e uma área de pontuação por disciplina. Sem garantia de classificação. SQLite exige hospedagem com disco persistente; deploy ainda pendente. Repositório real indisponível nesta sessão, logo não foi inspecionado. Auditorias, testes, prints e publicação ainda não realizados.
