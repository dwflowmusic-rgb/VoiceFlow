# ADR-004: SQLite para Persistência de Histórico

## Status

Aceito

## Contexto

O VoiceFlow precisava de uma forma segura de armazenar transcrições para evitar perda de dados em caso de falha no clipboard e para permitir consultas futuras pelo usuário.

## Decisão

Uso de **SQLite 3** como motor de banco de dados.

## Consequências

- **Zero Config:** Não requer instalação de servidor pelo usuário.
- **Portabilidade:** Todo o histórico reside em um único arquivo `.db`.
- **Integridade:** Suporte nativo a transações ACID, garantindo que a transcrição seja salva mesmo se a aplicação travar logo em seguida.

## Alternativas Rejeitadas

- **Arquivos JSON/Markdown:** Difíceis de pesquisar em escala e propensos a corrupção em escritas simultâneas.
- **Cloud Databases:** Introduziriam latência, custo e preocupações de privacidade desnecessárias para o escopo atual.
