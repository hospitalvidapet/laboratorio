Correção: PostgreSQL via DATABASE_URL + seed inicial único. Acesso: admin@vidapet.com.br / admin123


CORREÇÃO SEED/REDEPLOY
- Corrigido erro UNIQUE constraint failed: users.email.
- Se o banco já tiver usuários, o sistema não recria o admin no redeploy.
- Se aparecer sqlite3 no log, significa que a variável DATABASE_URL não foi configurada no Render ou não foi lida pelo serviço.

IMPORTANTE:
No Render > Web Service > Environment, adicione:
DATABASE_URL = Internal Database URL do PostgreSQL

Depois faça:
Manual Deploy > Clear build cache & deploy


CORREÇÃO RENDER / POSTGRESQL / PYTHON
- Removido psycopg2-binary.
- Adicionado psycopg[binary]==3.2.3.
- runtime.txt definido como python-3.12.4.
- URLs PostgreSQL agora usam driver SQLAlchemy: postgresql+psycopg://
- Seed inicial protegido contra duplicação de usuários.

PASSOS NO RENDER
1. Substitua todos os arquivos no GitHub por esta versão.
2. Confirme que runtime.txt está na raiz do projeto com:
   python-3.12.4
3. No Render > Web Service > Environment:
   DATABASE_URL = Internal Database URL do PostgreSQL
4. Se existir PYTHON_VERSION, defina:
   3.12.4
5. Manual Deploy > Clear build cache & deploy

LIS V1:
- Lançamento de resultados por requisição.
- Campos: exame, parâmetro, resultado, unidade, referência, flag, método e observações.
- Geração de laudo PDF automático.
- Status muda para Resultado liberado após gerar PDF.
- PDF fica disponível dentro da requisição.
