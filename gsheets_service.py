from flask import flash
from googleapiclient.discovery import build
from google.oauth2 import service_account

import os
import google.generativeai as genai
from google_auth_oauthlib.flow import InstalledAppFlow

# Google Sheets setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
ID_PLANILHA_GSHEETS = os.getenv("ID_PLANILHA_GSHEETS")
TIPO_ENTRADA_GSHEETS = "USER_ENTERED"
TIPO_DADO_GSHEETS = "INSERT_ROWS"
GSHEETS_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

def obter_sheets_service():
    modo = os.getenv("AUTH_MODE", "installed").lower()
    caminho_credencial = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if modo == "service":
        try:
            credentials = service_account.Credentials.from_service_account_file(
                caminho_credencial, scopes=SCOPES
            )
            return build("sheets", "v4", credentials=credentials)
        except Exception as e:
            flash(f"❌ Erro com conta de serviço: {e}")
            raise

    elif modo == "installed":
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                caminho_credencial, SCOPES
            )
            creds = flow.run_local_server(port=0)
            return build("sheets", "v4", credentials=creds)
        except Exception as e:
            flash(f"❌ Erro com conta instalada (OAuth): {e}")
            raise

    else:
        raise ValueError("⚠️ AUTH_MODE inválido: use 'installed' ou 'service'")

def obter_barreiras(valores):
    barreiras = []
    for linha in valores[1:]:
        if len(linha) >= 9:
            barreiras.append({
                "Descrição da Barreira": linha[0],
                "Deficiência Impactada": linha[1],
                "Tipo de Deficiência Impactada": linha[2],
                "Severidade": linha[3],
                "Sugestão de Correção": linha[4],
                "Fonte da Norma": linha[5],
                "Regra Avaliada": linha[6],
                "Status": linha[7],
                "ID Ticket Jira": linha[8]
            })
    return barreiras

def pesquisar_barreira(sheets_service, descricao):
    barreira = sheets_service.spreadsheets().values().get(
        spreadsheetId=ID_PLANILHA_GSHEETS,
        range=f"Barreiras!A2:A",
    ).execute()

    values = barreira.get('values', [])

    for i, row in enumerate(values, start=2):
        if len(row) > 0 and descricao.strip() == row[0].strip():
            return i
    return None
        