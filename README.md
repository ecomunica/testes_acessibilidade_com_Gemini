
# VertexVision – MVP de Acessibilidade Digital com Google Cloud

Este repositório contém o MVP funcional da equipe VertexVision do projeto QA Acessível, desenvolvido para o 1º Hackathon Unicesumar em parceria com o Google Cloud.

## Visão Geral

O projeto tem como objetivo automatizar a identificação de barreiras de acessibilidade digital em páginas HTML e imagens. 
A solução utiliza Inteligência Artificial generativa (Gemini, via Vertex AI) e integra recursos da Google Cloud, seguindo as diretrizes das normas WCAG 2.1 e eMAG 3.1.

## Objetivos do MVP

- Detectar barreiras de acessibilidade em interfaces digitais;
- Registrar tecnicamente cada barreira com informações completas;
- Permitir revisão humana de cada item analisado;
- Gerar relatórios organizados em planilhas Google e no Jira;
- Disponibilizar um painel com métricas e filtros de acessibilidade.

## Componentes Principais

- **Backend**: Python + Flask
- **Frontend**: HTML + Bootstrap 5
- **IA**: Gemini via Vertex AI
- **Banco de Dados**: Firestore (planejado), Google Sheets (implementado)
- **Gerenciamento de Incidentes**: Jira
- **Painel e Métricas**: Interface em HTML

## Como Executar Localmente

1. Instale os pacotes necessários:
   ```
   pip install -r requirements.txt
   ```

2. Configure as variáveis no arquivo `.env`:
   - GOOGLE_API_KEY
   - GOOGLE_APPLICATION_CREDENTIALS
   - ID_PLANILHA_GSHEETS
   - JIRA_SERVER, JIRA_EMAIL, JIRA_TOKEN, JIRA_PROJECT

3. Execute a aplicação:
   ```
   python run.py
   ```

4. Acesse `http://localhost:5000` no navegador.

## Estrutura de Diretórios

- `app_gemini.py`: Código principal da aplicação
- `templates/`: Contém as páginas HTML (upload, resultado, avaliações, métricas)
- `uploads/`: Armazenamento local de arquivos enviados (ambiente de testes)
- `static/`: Imagens utilizadas na interface
- `gsheets_service.py`: Integração com Google Sheets
- `jira_service.py`: Integração com Jira
- `run.py`: Arquivo de inicialização da aplicação

## Funcionalidades Implementadas

- Exportação de HTML:
  Após a análise, o usuário pode baixar um arquivo `.html` contendo o código com as sugestões aplicadas pela IA. 
  Essa funcionalidade permite reaproveitamento direto do conteúdo com correções embutidas.

- Envio de arquivos `.html`, `.jpg`, `.png`
- Análise de acessibilidade com IA generativa
- Registro das barreiras em planilha Google
- Criação automática de tickets no Jira
- Interface de revisão manual por analistas
- Exportação do código HTML com sugestões aplicadas
- Painel com filtros por severidade, tipo de deficiência e status

## Observações Técnicas

- A aplicação roda localmente em ambiente Flask;
- O uso do Vertex AI está implementado por meio de chave de API;
- O Firestore será utilizado na versão final, quando a infraestrutura estiver provisionada;
- O módulo de notificações via Google Chat não foi implementado, pois requer domínio com Workspace ativo.

## Alinhamento com o Hackathon

- Tema atendido: Responsabilidade Social e Acessibilidade Digital
- ODS: Educação de Qualidade, Inovação, Cidades Sustentáveis
- MVP funcional entregue com tela, análise, feedback e métrica
- Estrutura preparada para migração à nuvem com Cloud Run e Firestore

