# LABORATÓRIO VIDAPET V3.1 FUNCIONAL

Esta versão inclui:
- Administração
- Usuários
- Clínicas
- Catálogo de exames
- Perfis e amostras
- Nova requisição
- Resultados
- PDF
- Status com cores

Para substituir mantendo o mesmo banco:
1. Faça backup da pasta atual.
2. Copie os arquivos desta versão por cima da pasta atual.
3. Preserve o arquivo `.env`.
4. Ative o venv.
5. Execute `pip install -r requirements.txt`.
6. Execute `python -m scripts.seed`.
7. Execute `python run.py`.

## V3.6.3 — Sincronização automática
Consulte `README_V3_6_3.txt` para configurar `ONLINE_DATABASE_URL` e o intervalo de sincronização.
