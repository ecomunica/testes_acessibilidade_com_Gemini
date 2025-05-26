from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask import send_from_directory

import os
import ast
import google.generativeai as genai
import logging
import io

from gsheets_service import obter_sheets_service, obter_barreiras, pesquisar_barreira, ID_PLANILHA_GSHEETS, TIPO_ENTRADA_GSHEETS, TIPO_DADO_GSHEETS
from jira_service import campoNorma, campoSeveridade, campoDescricao, campoDeficiencia, campoFonte, campoStatus, campoSugestaoCorrecao, obter_jira_service
from prompt_service import construir_prompt, construir_prompt_correcao

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
                            "Status": "Aberta"
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
                    "Status": "Bruto"
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
                "Status": "Erro"
            }]

        # Jira + Google Sheets
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
                    campoDescricao: barreira['Descrição da Barreira'],
                    campoDeficiencia: barreira['Deficiência Impactada'],
                    campoSeveridade: barreira['Severidade'],
                    campoNorma: barreira['Regra Avaliada'],
                    campoFonte: barreira['Fonte da Norma'],
                    campoStatus: barreira['Status'],
                    campoSugestaoCorrecao: barreira['Sugestão de Correção'],
                }

                try:
                    ticketJira = jira.create_issue(fields=barreira_dict)
                    flash(f"✅ Ticket criado no Jira: {ticketJira} - {barreira['Descrição da Barreira']}")
                    # Adiciona o ID do ticket à barreira para salvar futuros feedbacks
                    barreira['ID Ticket Jira'] = ticketJira.id 
                except Exception as e:
                    flash(f"❌ Erro ao criar ticket no Jira: {e.args}")

                barreiras_gsheets.append([
                    barreira['Descrição da Barreira'],
                    barreira['Deficiência Impactada'],
                    barreira['Tipo de Deficiência Impactada'],
                    barreira['Severidade'],
                    barreira['Sugestão de Correção'],
                    barreira['Fonte da Norma'],
                    barreira['Regra Avaliada'],
                    barreira['Status'],
                    barreira['ID Ticket Jira']
                ])
            # Enviar dados para o Google Sheets
            try:
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=ID_PLANILHA_GSHEETS,
                    range="Barreiras!A1",
                    valueInputOption=TIPO_ENTRADA_GSHEETS,
                    insertDataOption=TIPO_DADO_GSHEETS,
                    body={"values": barreiras_gsheets}
                ).execute()
                flash("✅ Barreiras registradas no Google Sheets.")
            except Exception as e:
                flash(f"❌ Erro ao registrar barreiras no Google Sheets: {e.args}")
        except Exception as e:
            flash(f"❌ Erro ao registrar em planilhas ou Jira: {e}")
        filename = os.path.basename(filepath)
        return render_template('resultado.html', barreiras=barreiras,filepath=filepath,filename=filename)

    except Exception as e:
        flash(f"Erro com a IA: {e}")
        return redirect(url_for('index'))
    
@app.route('/corrigir', methods=['POST'])
def corrigir():
    nome_arquivo = request.form.get('filename')

    if not nome_arquivo:
        flash("Nome do arquivo não enviado.")
        return redirect(url_for('index'))

    caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)

    if not os.path.exists(caminho_arquivo):
        flash("Arquivo original não encontrado.")
        return redirect(url_for('index'))
    
    # Só realiza a correção se for um arquivo HTML ou TXT
    extensao = nome_arquivo.rsplit('.', 1)[1].lower()
    if extensao not in {'html', 'txt'}:
        flash("Arquivo não suportado para correção. Apenas HTML e TXT são permitidos.")
        return redirect(url_for('index'))
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo_html = f.read()
    except UnicodeDecodeError:
        flash("Erro ao ler o arquivo de texto. Codificação inválida.")
        return redirect(url_for('index'))

    prompt = construir_prompt_correcao(conteudo_html)
        
    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content([prompt])
        codigo_corrigido = response.text.strip()

        if codigo_corrigido.startswith("```html"):
            codigo_corrigido = codigo_corrigido.replace("```html", "").replace("```", "").strip()

        nome_corrigido = f"corrigido_{os.path.basename(caminho_arquivo)}"
        caminho_corrigido = os.path.join(app.config['UPLOAD_FOLDER'], nome_corrigido)

        with open(caminho_corrigido, 'w', encoding='utf-8') as f:
            f.write(codigo_corrigido)

        return redirect(url_for('download', filename=nome_corrigido))

    except Exception as e:
        flash(f"Erro ao corrigir HTML com IA: {e}")
        return redirect(url_for('index'))
    
@app.route('/feedback', methods=['POST'])
def feedback():
    id_barreira = request.form.get('id_barreira')
    status = request.form.get('status')
    descricao = request.form.get('descricao')
    try:
        barreira_dict = {
            campoStatus: status
        }

        # Atualiza a barreira no Jira e Google Sheets
        try:
            jira = obter_jira_service()
            jira.issue(id_barreira).update(fields=barreira_dict)
            flash(f"✅ Avaliação registrada no Jira para o ticket {descricao}")
        except Exception as e:
            flash(f"❌ Erro ao atualizar ticket {descricao} no Jira: {e.args}")   
        
        try:
            sheets_service = obter_sheets_service()
            linha = pesquisar_barreira(sheets_service, descricao)

            body = {
                "values": [[status]]
            }
            sheets_service.spreadsheets().values().update(
                spreadsheetId=ID_PLANILHA_GSHEETS,
                range=f"Barreiras!H{linha}",
                valueInputOption='RAW',
                body=body
            ).execute()

            flash("✅ Barreira atualizada no Google Sheets.")
        except Exception as e:
            flash(f"❌ Erro ao atualizar barreira {descricao} no Google Sheets: {e.args}") 
    except Exception as e:
        flash(f"❌ Erro ao registrar avaliação em planilhas ou Jira: {e}")

    flash(f"Feedback enviado para barreira {id_barreira} - {descricao}: {status}")
    return '', 204 # Para evitar redirecionamento

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/metricas', methods=['POST'])
def metricas():
    try:
        sheets_service = obter_sheets_service()
        resultado = sheets_service.spreadsheets().values().get(
            spreadsheetId=ID_PLANILHA_GSHEETS,
            range="Barreiras!A1:I"
        ).execute()

        valores = resultado.get('values', [])
        if not valores:
            flash("Nenhum dado encontrado.")
            return redirect(url_for('index'))

        metricas = []
        metricas = obter_barreiras(valores)

        return render_template('metricas.html', metricas=metricas)
    except Exception as e:
        flash(f"Erro ao buscar métricas: {e}")
        return redirect(url_for('index'))

@app.route('/avaliacoes', methods=['POST', 'GET'])
def avaliacoes():
    sheets_service = obter_sheets_service()

    if request.method == 'POST':
        id_barreira = request.form.get('id_barreira')
        status = request.form.get('status')
        descricao = request.form.get('descricao')

        barreira_dict = {
            campoStatus: status
        }

        # Atualiza a barreira no Jira e Google Sheets
        try:
            jira = obter_jira_service()
            jira.issue(id_barreira).update(fields=barreira_dict)
            flash(f"✅ Avaliação registrada no Jira para o ticket {id_barreira} - {descricao}")
        except Exception as e:
            flash(f"❌ Erro ao atualizar ticket {id_barreira} - {descricao} no Jira: {e.args}")
            
        linha = pesquisar_barreira(sheets_service, request.form['descricao'])
        try:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=ID_PLANILHA_GSHEETS,
                range=f"Barreiras!H{linha}",
                valueInputOption='RAW',
                body={"values": [[request.form['status']]]}
            ).execute()
            flash("✅ Avaliação atualizada com sucesso no Google Sheets.")
        except Exception as e:
            flash(f"❌ Erro ao atualizar barreira {request.form['descricao']} no Google Sheets: {e.args}")
        return redirect(request.referrer)
    else:
        try:
            resultado = sheets_service.spreadsheets().values().get(
                spreadsheetId=ID_PLANILHA_GSHEETS,
                range="Barreiras!A1:I"
            ).execute()

            valores = resultado.get('values', [])
            barreiras = []
            barreiras = obter_barreiras(valores)
            return render_template('avaliacoes.html', barreiras=barreiras)
        except Exception as e:
            flash(f"Erro ao buscar avaliações: {e}")
        return render_template('index.html')
