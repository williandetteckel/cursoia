# data-zip-analyzer/services/logger_config.py

import logging
import os
from logging.handlers import RotatingFileHandler # Para rotacionar logs

def setup_logging():
    """
    Configura o sistema de logging para o projeto.
    Os logs serão gravados em './tmp/agent_activity.log' com rotação.
    """
    log_file = './tmp/agent_activity.log'
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True) # Garante que o diretório ./tmp exista

    # Cria o logger principal
    logger = logging.getLogger("agent_poc_logger")
    logger.setLevel(logging.INFO) # Define o nível mínimo para INFO (ou DEBUG para mais detalhes)

    # Impede que handlers sejam adicionados múltiplas vezes ao recarregar módulos (Streamlit)
    if not logger.handlers:
        # Handler para arquivo - Rotaciona o arquivo a cada 5MB, mantendo 5 backups
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        # Handler para console (opcional, útil para depuração imediata no terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    return logger

# Inicializa o logger uma vez ao importar
app_logger = setup_logging()