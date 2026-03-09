"""
domain/guardrails.py — O Roteador do Boteco 🚦
================================================
Interceta comandos rapidamente com Regex. Custo zero de tokens.
"""
import re
from dataclasses import dataclass

@dataclass
class AcaoBot:
    acao: str              # Ex: "TOCAR_MUSICA", "LLM", "VER_FILA"
    parametro: str         # O nome da música ou o texto para o LLM
    resposta_rapida: str   # Resposta síncrona imediata
    precisa_celery: bool   # Se True, a ação pesada vai para background

class RegexGreeter:
    def __init__(self):
        # ── Regex para Músicas ──
        self.regex_musica = re.compile(r'^[!/](play|toca|p)\s+(.+)', re.IGNORECASE)
        self.regex_fila   = re.compile(r'^[!/](fila|queue|f)', re.IGNORECASE)
        self.regex_limpar = re.compile(r'^[!/](limpar|clear|stop)', re.IGNORECASE)
        
        # ── Regex para Utilidades ──
        self.regex_sticker = re.compile(r'^[!/](sticker|figurinha|s)', re.IGNORECASE)
        self.regex_todos   = re.compile(r'^[!/](todos|all)\s*(.*)', re.IGNORECASE)
        self.regex_menu    = re.compile(r'^[!/](menu|ajuda|help)', re.IGNORECASE)

    def analisar(self, mensagem: str, has_media: bool) -> AcaoBot:
        msg = mensagem.strip()

        # 1. MÚSICA
        match_musica = self.regex_musica.match(msg)
        if match_musica:
            return AcaoBot(acao="TOCAR_MUSICA", parametro=match_musica.group(2), resposta_rapida="", precisa_celery=True)

        if self.regex_fila.match(msg):
            return AcaoBot(acao="VER_FILA", parametro="", resposta_rapida="", precisa_celery=False)

        if self.regex_limpar.match(msg):
            return AcaoBot(acao="LIMPAR_FILA", parametro="", resposta_rapida="🧹 A Jukebox foi reiniciada! Fila limpa.", precisa_celery=False)

        # 2. FIGURINHAS
        if self.regex_sticker.match(msg):
            if not has_media:
                return AcaoBot(acao="ERRO", parametro="", resposta_rapida="🖼️ Cadê a foto, chefe? Tens de enviar uma IMAGEM junto com o comando!", precisa_celery=False)
            return AcaoBot(acao="FAZER_FIGURINHA", parametro="", resposta_rapida="🖼️ Saindo uma obra de arte...", precisa_celery=True)

        # 3. CHAMAR TODOS
        match_todos = self.regex_todos.match(msg)
        if match_todos:
            texto_aviso = match_todos.group(2) or "Acorda grupo!"
            return AcaoBot(acao="CHAMAR_TODOS", parametro=texto_aviso, resposta_rapida="", precisa_celery=True)

        # 4. MENU
        if self.regex_menu.match(msg):
            menu = (
                "🍻 *MENU DO BOTECO AI* 🍻\n\n"
                "🎵 *Música:*\n"
                " `!play [nome]` - Pede um som\n"
                " `!fila` - Vê o que vai tocar\n"
                " `!limpar` - Cancela a fila toda\n\n"
                "🛠️ *Zoeira:*\n"
                " `!figurinha` - Manda com uma foto\n"
                " `!todos [msg]` - Acorda o grupo\n\n"
                "🧠 *Ou só fala comigo normalmente (sem !)*"
            )
            return AcaoBot(acao="MENU", parametro="", resposta_rapida=menu, precisa_celery=False)

        # Se não tiver comando nenhum, manda para o DeepSeek conversar
        return AcaoBot(acao="LLM", parametro=msg, resposta_rapida="", precisa_celery=False)

guardrails = RegexGreeter()