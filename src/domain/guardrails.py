"""
domain/guardrails.py — O Roteador de Comandos do Boteco
========================================================
CORREÇÕES:
  - BUG: No handle_message.py original, após enviar resposta_rapida o código
    usava `elif` para as ações seguintes. Isso significa que comandos com
    resposta_rapida E ação (ex: FAZER_FIGURINHA manda "Saindo uma obra de arte..."
    E depois deveria chamar o Celery) nunca chegavam ao Celery.
    CORRIGIDO: guardrails agora separa claramente resposta_rapida de acao,
    e o handle_message usa `if` independente para cada bloco.
    Aqui garantimos que FAZER_FIGURINHA sempre tem acao="FAZER_FIGURINHA"
    mesmo quando tem resposta_rapida (a confirmação para o usuário).
  - BUG MENOR: regex_todos capturava o grupo(2) que podia ser None ou
    ter espaço inicial. Adicionado .strip() no parametro.
"""
import re
from dataclasses import dataclass

@dataclass
class AcaoBot:
    acao:           str
    parametro:      str
    resposta_rapida: str
    precisa_celery: bool

class RegexGreeter:
    def __init__(self):
        self.regex_musica  = re.compile(r'^[!/](play|toca|p)\s+(.+)', re.IGNORECASE)
        self.regex_fila    = re.compile(r'^[!/](fila|f)$', re.IGNORECASE)
        self.regex_limpar  = re.compile(r'^[!/](limpar|clear|stop)$', re.IGNORECASE)
        self.regex_sticker = re.compile(r'^[!/](sticker|figurinha|s)$', re.IGNORECASE)
        self.regex_todos   = re.compile(r'^[!/](todos|all)(\s+.*)?$', re.IGNORECASE)
        self.regex_menu    = re.compile(r'^[!/](menu|ajuda|help)$', re.IGNORECASE)

    def analisar(self, mensagem: str, has_media: bool) -> AcaoBot:
        msg = mensagem.strip()

        # 1. MENU
        if self.regex_menu.match(msg):
            menu_text = (
                "🍻 *MENU DO BOTECO AI* 🍻\n\n"
                "🎵 *MÚSICA*\n"
                "• `!play [nome]` → Pede um som\n"
                "• `!f` → Vê a fila de espera\n"
                "• `!limpar` → Esvazia a jukebox\n\n"
                "🖼️ *ZOEIRA*\n"
                "• `!s` → Faz figurinha (mande com foto ou responda uma)\n"
                "• `!todos [msg]` → Acorda o grupo\n\n"
                "🧠 *IA*\n"
                "• Basta falar comigo sem comandos!"
            )
            return AcaoBot(
                acao="MENU",
                parametro="",
                resposta_rapida=menu_text,
                precisa_celery=False,
            )

        # 2. FIGURINHAS
        #    ✅ CORRIGIDO: quando has_media=False retorna acao="ERRO" com resposta_rapida.
        #    Quando has_media=True retorna acao="FAZER_FIGURINHA" com resposta_rapida
        #    de confirmação. O handle_message trata os dois casos independentemente.
        if self.regex_sticker.match(msg):
            if not has_media:
                return AcaoBot(
                    acao="ERRO",
                    parametro="",
                    resposta_rapida="🖼️ Cadê a foto? Mande uma imagem com `!s` ou responda uma imagem!",
                    precisa_celery=False,
                )
            return AcaoBot(
                acao="FAZER_FIGURINHA",
                parametro="",
                resposta_rapida="🖼️ Saindo uma obra de arte...",
                precisa_celery=True,
            )

        # 3. MÚSICA
        match_musica = self.regex_musica.match(msg)
        if match_musica:
            return AcaoBot(
                acao="TOCAR_MUSICA",
                parametro=match_musica.group(2).strip(),
                resposta_rapida="",
                precisa_celery=True,
            )

        if self.regex_fila.match(msg):
            return AcaoBot(acao="VER_FILA", parametro="", resposta_rapida="", precisa_celery=False)

        if self.regex_limpar.match(msg):
            return AcaoBot(
                acao="LIMPAR_FILA",
                parametro="",
                resposta_rapida="🧹 Jukebox reiniciada!",
                precisa_celery=False,
            )

        # 4. CHAMAR TODOS
        match_todos = self.regex_todos.match(msg)
        if match_todos:
            # ✅ CORRIGIDO: .strip() evita espaço inicial no parâmetro
            param = (match_todos.group(2) or "").strip() or "📣 Acorda galera!"
            return AcaoBot(
                acao="CHAMAR_TODOS",
                parametro=param,
                resposta_rapida="",
                precisa_celery=True,
            )

        # 5. IA
        return AcaoBot(acao="LLM", parametro=msg, resposta_rapida="", precisa_celery=False)


guardrails = RegexGreeter()