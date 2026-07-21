LABORATÓRIO VIDAPET V3.6.2 — CORREÇÃO DE BANCO E EXCLUSÃO

Correções:
- Corrige o erro "column lab_results.method does not exist".
- Ao iniciar, o sistema verifica e adiciona colunas ausentes sem apagar dados.
- Atualiza instalações antigas com lab_results.method, lab_requests.created_at e lab_reports.created_at.
- Preenche data/hora em registros antigos que estavam sem essa informação.
- Exclusão de requisições remove resultados e laudos vinculados em uma transação segura.
- Remove o paciente somente quando ele não possui outra requisição.
- Remove arquivos PDF vinculados, quando existirem.

Atualização:
1. Pare o servidor.
2. Faça backup do banco e da pasta do sistema.
3. Copie os arquivos desta versão sobre a instalação atual, preservando .env e venv.
4. Execute:
   venv\Scripts\activate.bat
   pip install -r requirements.txt
   python run.py

A atualização do banco ocorre automaticamente na primeira inicialização.
