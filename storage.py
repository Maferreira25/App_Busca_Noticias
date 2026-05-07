import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def save_summary_locally(content: str) -> str:
    """
    Salva o conteúdo gerado em um arquivo Markdown (.md) na pasta history.
    O nome do arquivo contém a data atual.
    """
    history_dir = "history"
    os.makedirs(history_dir, exist_ok=True)
    
    date_str = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = f"boletim_ia_{date_str}.md"
    filepath = os.path.join(history_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    logger.info(f"Boletim salvo com sucesso em: {filepath}")
    return filepath
