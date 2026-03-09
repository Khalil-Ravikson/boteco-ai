"""
agent/validator.py — O Segurança do Boteco (Sanitização)
=========================================================
Limpa o output do DeepSeek para garantir que ele não fala como um robô.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass
class ValidationResult:
    valido:  bool
    output:  str       # texto limpo e pronto para o WhatsApp
    motivo:  str = ""  

# Frases proibidas (Papo de robô)
PAPO_CORPORATIVO = [
    "como um modelo de linguagem",
    "como uma inteligência artificial",
    "fui desenvolvido pela",
    "não tenho sentimentos",
    "não posso ajudar com",
    "sinto muito, mas",
]

def validar_deepseek(output: str) -> ValidationResult:
    """
    Limpa o output do DeepSeek e garante que tem o tom certo para o grupo.
    """
    if not output:
        return ValidationResult(False, "Foi mal, fiquei sem palavras! Pede um chopp aí. 🍻", "output vazio")

    # 1. Limpar a tag <think> (Caso uses o modelo deepseek-reasoner R1 no futuro)
    output_limpo = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL).strip()

    output_lower = output_limpo.lower()

    # 2. Intercetar papo corporativo
    for chato in PAPO_CORPORATIVO:
        if chato in output_lower:
            resposta_zoeira = "Ih, não me meto nessa! Sou só o boteco-ai. 🍻 Pede uma música ou manda figurinha!"
            return ValidationResult(True, resposta_zoeira, "bloqueou papo corporativo")

    # 3. Output demasiado curto
    if len(output_limpo) < 2:
        return ValidationResult(False, "Manda de novo que não entendi nada! 🍺", "output muito curto")

    # Retorna o texto limpinho
    return ValidationResult(True, output_limpo)