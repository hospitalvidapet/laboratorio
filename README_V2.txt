LABORATÓRIO VIDAPET — VERSÃO 2.0

Esta versão foi criada para ser testada em ambiente separado de homologação, sem alterar a versão atual em produção.

NOME SUGERIDO NO RENDER:
laboratorio-vidapet-homolog

BANCO SUGERIDO:
laboratorio-vidapet-homolog-db

PRINCIPAIS MÓDULOS DA VERSÃO 2.0:
1. Requisições laboratoriais
2. Cadastro de exames
3. Grupos e ordem de exibição
4. Perfis de exames
5. Tipos de amostra
6. Lançamento de resultados
7. Geração de laudo PDF
8. Administração de usuários
9. Auditoria
10. Relatórios básicos

RECURSOS NOVOS DA V2:
- Estrutura para uso como LIS.
- Resultado laboratorial lançado diretamente no sistema.
- PDF gerado pelo sistema.
- Status automático como Resultado liberado após emissão do laudo.
- Ambiente preparado para PostgreSQL no Render.
- Seed inicial protegido para não recriar perfis excluídos.
- Driver PostgreSQL atualizado para psycopg v3.
- Preparado para homologação sem afetar produção.

CONFIGURAÇÃO NO RENDER:
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app --bind 0.0.0.0:$PORT

Environment Variables:
DATABASE_URL = Internal Database URL do PostgreSQL de homologação
PYTHON_VERSION = 3.12.4
SECRET_KEY = uma-chave-secreta-forte

IMPORTANTE:
Use um Web Service novo e um banco PostgreSQL novo para testar.
Não conecte esta versão ao banco de produção enquanto estiver em validação.

ACESSO INICIAL:
admin@vidapet.com.br
admin123

Após o primeiro acesso, altere a senha do administrador.
