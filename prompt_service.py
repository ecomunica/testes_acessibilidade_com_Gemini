
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

def construir_prompt_correcao(content):
    return f"""
    Você é um especialista em acessibilidade digital. Corrija o seguinte código HTML com base nas diretrizes WCAG 2.1 (níveis A e AA) e eMAG 3.1.

Seu objetivo é:
- Corrigir todas as barreiras de acessibilidade.
- Comentar no código o que foi alterado (com <!-- Comentário -->).
- Manter a estrutura geral do HTML.
- Não incluir explicações fora do código. Retorne apenas o código HTML corrigido.

Código original:
{content}
"""