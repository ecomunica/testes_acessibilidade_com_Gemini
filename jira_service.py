from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from jira import JIRA
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

import os
import ast
import json
import google.generativeai as genai
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

campoNorma = os.getenv("CAMPO_JIRA_NORMA")
campoSeveridade = os.getenv("CAMPO_JIRA_SEVERIDADE")
campoDescricao = os.getenv("CAMPO_JIRA_DESCRICAO")
campoDeficiencia = os.getenv("CAMPO_JIRA_DEFICIENCIA")
campoFonte = os.getenv("CAMPO_JIRA_FONTE")
campoStatus = os.getenv("CAMPO_JIRA_STATUS")
campoSugestaoCorrecao = os.getenv("CAMPO_JIRA_SUGESTAO_CORRECAO")

def obter_jira_service():
    jiraServer = {'server': os.getenv("JIRA_SERVER")}
    jira = JIRA(jiraServer, basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))
    return jira