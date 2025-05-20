
# VertexVision – Versão de Testes

Este repositório contém a **versão de testes** do projeto **VertexVision**, desenvolvido para o **1º Hackathon Unicesumar** em parceria com o **Google Cloud**.

## 📌 Visão Geral

O objetivo deste projeto é promover **inclusão digital e acessibilidade** por meio da análise automatizada de interfaces web (HTML, imagens), utilizando **IA generativa (Vertex AI - Gemini)** e recursos em nuvem.

A solução permite:

- 📂 Enviar arquivos HTML, PNG ou JPG com a interface a ser analisada;
- ♿ Avaliar automaticamente a acessibilidade com base nas normas **WCAG 2.1** e **eMAG 3.1**;
- ✅ Gerar um relatório com barreiras detectadas e sugestões de correção;
- 🧠 Utilizar IA do Google para interpretar código e contexto visual;
- 📊 Registrar as barreiras em **Google Sheets**;
- 🧾 Criar tickets no **Jira** para acompanhamento de correções.

## 🚀 Tecnologias Utilizadas

- Python + Flask
- Vertex AI (Gemini)
- Google Sheets API
- Jira API
- Bootstrap 5

## 🛠 Como executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure as variáveis de ambiente no arquivo `.env` (exemplo fornecido no projeto):
   - `GOOGLE_API_KEY`
   - `GOOGLE_APPLICATION_CREDENTIALS`
   - `ID_PLANILHA_GSHEETS`
   - `JIRA_SERVER`, `JIRA_EMAIL`, `JIRA_TOKEN`, `JIRA_PROJECT`

3. Execute a aplicação:
   ```bash
   python run.py
   ```

4. Acesse em `http://localhost:5000` para utilizar a interface web.

## 🎯 Contexto do Hackathon

O projeto foi desenvolvido como proposta para o desafio do **Tema 01: Responsabilidade Social e Acessibilidade Digital**, com base no edital do Hackathon promovido pela Unicesumar. A proposta visa aplicar IA e computação em nuvem para detectar barreiras digitais e ampliar o acesso equitativo a serviços essenciais online.

---

> 
