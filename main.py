from ui.sci_fi_ui import launch_ui
import logging
from config import LOG_LEVEL, LOG_FILE

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()),
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(LOG_FILE),
                        logging.StreamHandler()
                    ])

if __name__ == "__main__":
    logging.info("Starting AI Crypto Simulator (Pure Simulation Mode).")
    launch_ui()
    logging.info("AI Crypto Simulator finished.")