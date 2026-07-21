LABORATÓRIO VIDAPET V3.6.3 — SINCRONIZAÇÃO AUTOMÁTICA

Novidades:
- Sincronização direta com o banco PostgreSQL online.
- Importa e atualiza espécies, grupos, exames, perfis e tipos de amostra.
- Correspondência por nome, sem duplicar registros.
- Não apaga dados locais nem históricos.
- Botões administrativos para testar conexão e sincronizar agora.
- Histórico das sincronizações e registro de erros.
- Sincronização automática opcional ao iniciar e em intervalos configuráveis.

Variáveis de ambiente:
ONLINE_DATABASE_URL=<URL externa do banco online>
AUTO_SYNC_ENABLED=true
AUTO_SYNC_ON_STARTUP=true
AUTO_SYNC_INTERVAL_MINUTES=30

Importante:
- Não grave a senha no código nem no GitHub.
- No Render, cadastre as variáveis em Environment.
- Para uso local, coloque as variáveis no arquivo .env, que já está no .gitignore.
