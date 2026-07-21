LABORATÓRIO VIDAPET — V3.6.6

Correção da migração PostgreSQL para colunas booleanas antigas.

A migração agora executa, nesta ordem:
1. DROP DEFAULT do valor inteiro antigo;
2. conversão INTEGER (0/1) para BOOLEAN (FALSE/TRUE);
3. SET DEFAULT TRUE em tipo booleano.

A rotina é idempotente: depois da conversão, novos deploys reconhecem que a
coluna já é BOOLEAN e não repetem o ALTER TYPE. Nenhum registro é apagado.
