"""
Módulo de gerenciamento de infraestrutura local do Docker e Evolution API.
Responsável por verificar, iniciar e validar a prontidão dos serviços em background.
"""

import logging
import os
import subprocess
import time
import requests

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_docker_desktop_path() -> str | None:
    """Busca o executável do Docker Desktop em locais padrões."""
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidate_paths = [
        os.path.join(program_files, "Docker", "Docker", "Docker Desktop.exe"),
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        r"D:\Program Files\Docker\Docker\Docker Desktop.exe",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return None


def is_docker_running() -> bool:
    """Verifica se o daemon do Docker está ativo e responsivo."""
    try:
        subprocess.run(["docker", "ps"], check=True, capture_output=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def start_docker_desktop() -> bool:
    """Inicia o Docker Desktop caso esteja fechado e aguarda a inicialização do daemon."""
    docker_path = get_docker_desktop_path()
    if not docker_path:
        logger.error("Executável do Docker Desktop não localizado nas pastas padrões.")
        return False

    logger.info("Iniciando Docker Desktop automaticamente...")
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    subprocess.Popen([docker_path], shell=False, creationflags=creation_flags)

    # Aguarda até 2 minutos (24 tentativas x 5s)
    for i in range(1, 25):
        logger.info(f"Aguardando Docker daemon iniciar... ({i * 5}s)")
        time.sleep(5)
        if is_docker_running():
            logger.info("Docker daemon iniciado e pronto.")
            return True

    logger.error("Tempo limite excedido aguardando inicialização do Docker.")
    return False


def ensure_environment() -> bool:
    """
    Garante que o Docker daemon e o container da Evolution API estejam operacionais.
    Retorna True se a API estiver respondendo, False caso contrário.
    """
    logger.info("Verificando ambiente (Docker e Evolution API)...")

    if not is_docker_running():
        logger.warning("Docker daemon não detectado.")
        if not start_docker_desktop():
            return False

    # Subir os containers do docker-compose
    logger.info("Subindo containers da Evolution API via docker-compose...")
    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True,
            capture_output=True,
            cwd=BASE_DIR,
            text=True
        )
    except Exception as e:
        logger.error(f"Erro ao executar docker-compose up: {e}")
        return False

    # Aguardar a Evolution API responder na URL configurada
    api_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
    for attempt in range(1, 11):
        try:
            res = requests.get(api_url, timeout=2)
            if res.status_code in [200, 404]:  # Resposta HTTP válida do Express
                logger.info("Evolution API está online e respondendo!")
                return True
        except requests.RequestException:
            logger.info(f"Aguardando Evolution API ficar online (tentativa {attempt}/10)...")
            time.sleep(3)

    logger.warning("A Evolution API não respondeu no tempo esperado.")
    return False
