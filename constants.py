"""
Constantes compartilhadas da aplicação.
Centraliza domínios e parâmetros padrão para evitar duplicações (DRY).
"""

DEFAULT_POSITIVE_DOMAINS: list[str] = [
    "conjur.com.br",
    "migalhas.com.br",
    "jota.info",
    "jusbrasil.com.br",
    "gov.br/anpd",
    "oab.org.br",
    "tjsp.jus.br",
    "tst.jus.br",
    "stf.jus.br",
    "stj.jus.br",
    "cnj.jus.br",
    "itsrio.org.br",
    "idp.edu.br",
    "law.com",
    "reuters.com",
    "csail.mit.edu",
    "cmu.edu",
    "harvard.edu",
    "ox.ac.uk",
    "cam.ac.uk",
    "turing.ac.uk",
    "nature.com",
    "ieee.org",
    "arxiv.org",
    "openai.com",
    "deepmind.google",
    "anthropic.com",
    "huggingface.co",
    "technologyreview.com",
    "techcrunch.com",
    "wired.com",
    "theverge.com",
    "arstechnica.com",
]

DEFAULT_IGNORED_DOMAINS: list[str] = [
    "panrotas.com.br",
    "uol.com.br",
    "economia.uol.com.br",
    "tilt.uol.com.br",
    "viagenspromo.com",
    "passagens",
    "melhoresdestinos.com.br",
    "voegol.com.br",
    "latamairlines.com",
    "voeazul.com.br",
    "aeroin.net",
    "mercadoeeventos.com.br",
    "decolar.com",
]

SCHEDULE_TASK_NAME: str = "BoletimIANews"
