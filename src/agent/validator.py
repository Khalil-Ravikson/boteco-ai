"""
agent/validator.py — O Segurança do Boteco (Sanitização Universal) 🛡️
=====================================================================
Limpa o output de qualquer IA (Groq, DeepSeek, Llama) para garantir 
que o tom de "boteco" não seja quebrado por papo de robô.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass
class ValidationResult:
    valido:  bool
    output:  str       # Texto limpo e pronto para o WhatsApp
    motivo:  str = ""  

# Frases proibidas (Papo de robô que o barman nunca diria)
PAPO_CORPORATIVO = [
    "como um modelo de linguagem",
    "como uma inteligência artificial",
    "fui desenvolvido pela",
    "não tenho sentimentos",
    "não posso ajudar com",
    "sinto muito, mas",
    "diretrizes de segurança",
    "assistant:", # Às vezes o Llama repete o próprio nome
    "user:",
]

def validar_resposta_ia(output: str) -> ValidationResult:
    """
    Limpa o output da IA e garante que tem o tom certo para o grupo.
    """
    if not output or not output.strip():
        return ValidationResult(False, "Foi mal, fiquei sem palavras! Pede um chopp aí. 🍻", "output vazio")

    # 1. Limpar tags de pensamento (DeepSeek R1 usa <think>, o Groq pode usar no futuro)
    output_limpo = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL).strip()
    
    # 2. Limpar preâmbulos comuns do Llama/Groq (ex: "Aqui está a sua resposta:")
    # Se a IA começar com frases de "mordomo", nós cortamos.
    preambulos = [
        r"^(claro|com certeza|aqui está|com certeza posso ajudar).*?[:!]\s*",
        r"^(entendido|perfeito|olá).*?[:!]\s*"
    ]
    for pattern in preambulos:
        output_limpo = re.sub(pattern, '', output_limpo, flags=re.IGNORECASE).strip()

    output_lower = output_limpo.lower()

    # 3. Intercetar papo corporativo/mordomo
    for chato in PAPO_CORPORATIVO:
        if chato in output_lower:
            resposta_zoeira = "Ih, não me meto nessa! Sou só o boteco-ai. 🍻 Pede uma música ou manda figurinha!"
            return ValidationResult(True, resposta_zoeira, "bloqueou papo corporativo")

    # 4. Output demasiado curto
    if len(output_limpo) < 2:
        return ValidationResult(False, "Manda de novo que não entendi nada! 🍺", "output muito curto")

    # Retorna o texto limpinho e pronto para o grupo
    return ValidationResult(True, output_limpo)