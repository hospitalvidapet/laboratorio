LABORATÓRIO VIDAPET V3.4

Novidades:
- Prioridade visual clara para Rotina, Urgente e Emergência.
- Urgência recebe destaque laranja.
- Emergência recebe destaque vermelho pulsante.
- Administrador pode editar e excluir requisições.
- Painel possui cartões clicáveis: Pendentes, Em análise e Liberados.
- Cada cartão filtra e exibe somente as requisições correspondentes.
- Banco atual preservado; não há alteração de estrutura.

Atualização:
1. Pare o servidor.
2. Faça backup da pasta.
3. Copie os arquivos sobre a pasta atual.
4. Preserve .env e venv.
5. Execute:
   venv\Scripts\activate.bat
   pip install -r requirements.txt
   python -m scripts.seed
   python run.py
