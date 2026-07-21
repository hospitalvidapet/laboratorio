LABORATÓRIO VIDAPET — V3.6.5

CORREÇÃO DE MIGRAÇÃO PARA POSTGRESQL/RENDER

Corrige o erro:

    column "active" is of type integer but expression is of type boolean

Bancos criados por versões antigas podem armazenar campos active como INTEGER
(0/1), enquanto a versão atual utiliza BOOLEAN (false/true). Antes de preencher
valores ausentes, a migração agora converte com segurança esses campos no
PostgreSQL usando:

- 0 = FALSE
- qualquer valor diferente de 0 = TRUE
- NULL permanece NULL até o preenchimento padrão

Campos verificados:
- users.active
- clinics.active
- species.active
- exams.active
- exam_profiles.active
- sample_types.active

A migração continua idempotente e preserva os registros existentes.

PUBLICAÇÃO
1. Substitua os arquivos do repositório pelos desta versão.
2. Não envie .env ao GitHub.
3. Faça commit e push.
4. Mantenha no Render:

   gunicorn run:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120

5. Use Manual Deploy > Deploy latest commit.
