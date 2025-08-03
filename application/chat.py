import logging
import sys
import info

model_name = "Claude 3.7 Sonnet"
model_type = "claude"
models = info.get_model_info(model_name)
model_id = models[0]["model_id"]

logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("chat")

debug_mode = False
def update(modelName, debugMode):
    global model_name, models, model_type, model_id, debug_mode

    if modelName is not model_name:
        model_name = modelName
        logger.info(f"modelName: {modelName}")

        models = info.get_model_info(model_name)
        model_type = models[0]["model_type"]
        model_id = models[0]["model_id"]
        logger.info(f"model_id: {model_id}")
        logger.info(f"model_type: {model_type}")

    if debugMode is not debug_mode:
        debug_mode = debugMode
        logger.info(f"debug_mode: {debug_mode}")
