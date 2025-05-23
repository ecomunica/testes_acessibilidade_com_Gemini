from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import os
import ast
import google.generativeai as genai
import logging

from gsheets_service import obter_sheets_service, ID_PLANILHA_GSHEETS, TIPO_ENTRADA_GSHEETS, TIPO_DADO_GSHEETS
from jira_service import campoNorma, campoSeveridade, campoDescricao, campoDeficiencia, campoFonte, campoStatus, campoSugestaoCorrecao, obter_jira_service

load_dotenv()

app = Flask(__name__)
app.secret_key = 'segredo_para_flash'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'html', 'txt', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')

    if not file or not allowed_file(file.filename):
        flash("Envie um arquivo válido (.html, .txt, .png ou .jpg)")
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    extensao = filename.rsplit('.', 1)[1].lower()

    if extensao in {'html', 'txt'}:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conteudo_html = f.read()
        except UnicodeDecodeError:
            flash("Erro ao ler o arquivo de texto. Codificação inválida.")
            return redirect(url_for('index'))
    elif extensao in {'png', 'jpg', 'jpeg'}:
        conteudo_html = f"Imagem enviada: {filename}. Analise os aspectos visuais e semânticos baseando-se em possíveis barreiras visuais, contraste, ausência de descrição, foco, semântica ou legibilidade da interface."
    else:
        flash("Tipo de arquivo não suportado.")
        return redirect(url_for('index'))

    prompt = construir_prompt(conteudo_html)

    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content([prompt])
        text = response.text.strip()

        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()

        if not text:
            flash("Resposta da IA vazia. Tente novamente.")
            return redirect(url_for('index'))

        try:
            text = text.replace("Resposta Livre da IA", "").strip()
            barreiras = []

            try:
                lista_original = ast.literal_eval(text)
                if isinstance(lista_original, list):
                    for b in lista_original:
                        nova = {
                            "Regra Avaliada": b.get("Regra Avaliada", ""),
                            "Descrição da Barreira": b.get("Descrição da Barreira", ""),
                            "Deficiência Impactada": b.get("Deficiência Impactada", ""),
                            "Tipo de Deficiência Impactada": b.get("Tipo de Deficiência Impactada", ""),
                            "Severidade": b.get("Severidade", ""),
                            "Sugestão de Correção": b.get("Sugestão de Correção", ""),
                            "Fonte da Norma": b.get("Fonte da Norma", ""),
                            "status": "Aberta"
                        }
                        barreiras.append(nova)
                else:
                    raise ValueError("Retorno da IA não é uma lista.")
            except Exception as e:
                logging.error(f"❌ Conteúdo inesperado da IA: {text}\nErro: {e}")
                barreiras = [{
                    "Regra Avaliada": "Formato livre",
                    "Descrição da Barreira": text,
                    "Deficiência Impactada": "—",
                    "Tipo de Deficiência Impactada": "—",
                    "Severidade": "Média",
                    "Sugestão de Correção": "—",
                    "Fonte da Norma": "IA",
                    "status": "Bruto"
                }]

        except Exception as e:
            logging.error(f"❌ Erro não tratado ao processar IA: {text}\nErro: {e}")
            flash("Erro ao processar resposta da IA.")
            barreiras = [{
                "Regra Avaliada": "—",
                "Descrição da Barreira": "A IA não retornou uma lista JSON válida.",
                "Deficiência Impactada": "—",
                "Tipo de Deficiência Impactada": "—",
                "Severidade": "Média",
                "Sugestão de Correção": "—",
                "Fonte da Norma": "IA",
                "status": "Erro"
            }]

        #Jira + Google Sheets
        try:
            jira = obter_jira_service()
        
            sheets_service = obter_sheets_service()
            barreiras_gsheets = []

            for barreira in barreiras:
                resumo = f"Acessibilidade: {barreira['Regra Avaliada']}"
                descricao = f"""
**Descrição da Barreira**: {barreira['Descrição da Barreira']}
**Deficiência Impactada**: {barreira['Deficiência Impactada']}
**Tipo de Deficiência Impactada**: {barreira['Tipo de Deficiência Impactada']}
**Severidade**: {barreira['Severidade']}
**Sugestão de Correção**: {barreira['Sugestão de Correção']}
**Fonte da Norma**: {barreira['Fonte da Norma']}
"""

                barreira_dict = {
                    'project': {'key': os.getenv("JIRA_PROJECT")},
                    'summary': resumo,
                    'description': descricao,
                    'issuetype': {'name': 'Task'},
                    #campoNorma: barreira['Regra Avaliada'],
                    #campoDescricao: barreira['Descrição da Barreira'],
                    #campoDeficiencia: barreira['Deficiência Impactada'],
                    #campoSeveridade: barreira['Severidade'],
                    #campoFonte: barreira['Fonte da Norma'],
                    #campoStatus: barreira['status'],
                    #campoSugestaoCorrecao: barreira['Sugestão de Correção'],
                }

                barreiras_gsheets.append([
                    barreira['Descrição da Barreira'],
                    barreira['Deficiência Impactada'],
                    barreira['Tipo de Deficiência Impactada'],
                    barreira['Severidade'],
                    barreira['Sugestão de Correção'],
                    barreira['Fonte da Norma'],
                    barreira['Regra Avaliada'],
                    barreira['status']
                ])

                try:
                    jira.create_issue(fields=barreira_dict)
                    flash(f"✅ Ticket criado no Jira: {barreira['Descrição da Barreira']}")
                except Exception as e:
                    flash(f"❌ Erro ao criar ticket no Jira: {e.args}")

            # Enviar dados para o Google Sheets
            sheets_service.spreadsheets().values().append(
                spreadsheetId=ID_PLANILHA_GSHEETS,
                range="Barreiras!A1",
                valueInputOption=TIPO_ENTRADA_GSHEETS,
                insertDataOption=TIPO_DADO_GSHEETS,
                body={"values": barreiras_gsheets}
            ).execute()
            flash("✅ Barreiras registradas no Google Sheets.")
        except Exception as e:
            flash(f"❌ Erro ao registrar em planilhas ou Jira: {e}")

        return render_template('resultado.html', barreiras=barreiras)

    except Exception as e:
        flash(f"Erro com a IA: {e}")
        return redirect(url_for('index'))

@app.route('/feedback', methods=['POST'])
def feedback():
    id_barreira = request.form.get('id')
    status = request.form.get('status')
    flash(f"Feedback enviado para barreira {id_barreira}: {status}")
    return redirect(url_for('index'))

@app.route('/metricas', methods=['POST'])
def metricas():
    try:
        sheets_service = obter_sheets_service()
        resultado = sheets_service.spreadsheets().values().get(
            spreadsheetId=ID_PLANILHA_GSHEETS,
            range="Barreiras!A1:H"
        ).execute()

        valores = resultado.get('values', [])
        if not valores:
            flash("Nenhum dado encontrado.")
            return redirect(url_for('index'))

        metricas = []
        for linha in valores[1:]:
            if len(linha) >= 8:
                metricas.append({
                    "Descrição da Barreira": linha[0],
                    "Deficiência Impactada": linha[1],
                    "Tipo de Deficiência Impactada": linha[2],
                    "Severidade": linha[3],
                    "Sugestão de Correção": linha[4],
                    "Fonte da Norma": linha[5],
                    "Regra Avaliada": linha[6],
                    "Status": linha[7],
                })

        return render_template('metricas.html', metricas=metricas)
    except Exception as e:
        flash(f"Erro ao buscar métricas: {e}")
        return redirect(url_for('index'))

def construir_prompt(content):
    return f"""Você é um auditor especialista em acessibilidade digital com conhecimento técnico aprofundado nas diretrizes:

    WCAG 2.1 (níveis A e AA)

    eMAG 3.1 (modelo de acessibilidade brasileiro para serviços públicos)

Sua tarefa é analisar criticamente o conteúdo abaixo
— que pode ser código HTML ou uma descrição textual de interface
— e identificar todas as barreiras de acessibilidade presentes.
— simular uma auditoria completa, analisando o conteúdo a seguir (HTML ou descrição textual de interface) com base em cada um dos critérios de sucesso da WCAG 2.1 níveis A e AA e as principais recomendações do eMAG 3.1, incluindo:

• Imagens com texto alternativo  
• Contraste de cor e legibilidade  
• Navegação por teclado  
• Semântica e uso correto de marcação  
• Títulos e cabeçalhos claros  
• Tamanho do foco visível  
• Uso de linguagem clara  
• Suporte a tecnologias assistivas  
• Compatibilidade com leitores de tela  
• Flexibilidade para adaptação visual  
• Responsividade e escalabilidade  
• Acessibilidade de formulários e controles  
• Acessibilidade de vídeos e áudios  
• Erros de entrada e sugestões  
• Evitar conteúdo que pisque ou distraia  
• Evitar dependência exclusiva de mouse ou gestos

Para cada item analisado, forneça a seguinte estrutura:

    Regra Avaliada
    Descrição da Barreira
    Deficiência Impactada
    Tipo de Deficiência Impactada
    Severidade
    Sugestão de Correção
    Fonte da Norma

Se um critério não for possível de avaliar com base no conteúdo recebido, informe explicitamente: “Não aplicável neste contexto”.
Além disso, não ultrapasse 250 caracteres para cada descrição de barreira e utilize uma linguagem clara e objetiva.

A resposta final deve ser uma lista JSON pura com objetos, cada um contendo os seguintes campos:
- "Regra Avaliada"
- "Descrição da Barreira"
- "Deficiência Impactada"
- "Tipo de Deficiência Impactada"
- "Severidade"
- "Sugestão de Correção"
- "Fonte da Norma"

Conteúdo a ser analisado:
{content}
"""
