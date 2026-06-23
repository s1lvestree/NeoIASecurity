# Logs STA simulados

Este diretório documenta a fonte local de logs STA usada pela demo de Governança IA.

Na implementação atual, os eventos completos são gerados de forma determinística em runtime pelo backend a partir do período selecionado. Os arquivos `sta_logs_7d.json`, `sta_logs_15d.json` e `sta_logs_30d.json` são amostras sanitizadas da fonte local usada pela demo. Os eventos simulam uma chamada de API ao SafeNet Trusted Access e já saem minimizados/pseudonimizados para uso no dashboard e nos relatórios executivos.

Não armazene logs reais de clientes neste diretório.
