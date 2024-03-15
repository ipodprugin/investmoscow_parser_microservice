import logging


logging.basicConfig(
    filename='./app/app.log',
    format='%(asctime)s - %(process)s - %(name)s:%(lineno)d - %(levelname)s -'
    ' %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

