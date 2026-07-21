LABORATÓRIO VIDAPET — V4.0 STABLE

Principais melhorias
- Migrador PostgreSQL reescrito e idempotente.
- Criação automática de colunas ausentes sem apagar registros.
- Conversão segura de campos active antigos (INTEGER 0/1) para BOOLEAN.
- Remoção do DEFAULT incompatível antes da conversão.
- Estratégia alternativa por coluna temporária caso o ALTER TYPE falhe.
- Restauração de defaults no banco após a migração.
- Preservação do acesso admin@vidapet.com.br.
- Compatibilidade mantida com SQLite para desenvolvimento local.

Render
Build command: pip install -r requirements.txt
Start command: gunicorn run:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120

Segurança
O projeto não contém senhas ou URLs privadas. Configure DATABASE_URL e demais
variáveis somente no painel Environment do Render.
