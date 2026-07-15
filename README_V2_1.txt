LABORATÓRIO VIDAPET — VERSÃO 2.1 CORRIGIDA

Correções sem apagar histórico:
- Migração segura adiciona selected_profiles_json na tabela requests.
- Requisições antigas continuam no banco.
- Ao solicitar por perfil, o nome do perfil passa a ser gravado.
- Laboratório vê perfil solicitado + exames do perfil.
- Tela da requisição mostra todos os dados do paciente, tutor, clínica, amostras e dados clínicos.
- Requisições têm cor conforme status.

Após subir no GitHub:
Manual Deploy > Clear build cache & deploy

Não apague o banco PostgreSQL atual.
