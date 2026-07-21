LABORATÓRIO VIDAPET — V3.6.4

CORREÇÃO DE PRODUÇÃO

Esta versão corrige o erro de login no Render:

    column users.role does not exist

A rotina app/database_upgrade.py agora atualiza automaticamente bancos antigos,
criando de forma idempotente as colunas ausentes usadas pelas versões V3.
Nenhum paciente, usuário, exame, perfil, requisição, resultado ou laudo é apagado.

DESTAQUES
- Cria users.role quando ausente.
- Mantém admin@vidapet.com.br com perfil admin.
- Cria e preenche users.active quando necessário.
- Verifica outras colunas incrementais do catálogo, requisições e resultados.
- Pode ser executada novamente sem duplicar colunas.
- Continua compatível com PostgreSQL do Render e SQLite local.

PUBLICAÇÃO
1. Substitua os arquivos do repositório pelos desta versão.
2. Não envie o arquivo .env ao GitHub.
3. Faça commit e push.
4. No Render, mantenha o Start Command:

   gunicorn run:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120

5. Faça Deploy latest commit.
6. Nos logs, procure por "Database upgraded:".
7. Teste o login.

Não é necessário executar SQL manual no PostgreSQL.
