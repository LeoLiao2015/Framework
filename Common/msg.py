import json
import logging
import traceback

# if __name__ == "__main__":
#     # 由于scrapy 冲突
#     logging.basicConfig(level=logging.INFO,
#                         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_msg(q, src, dst, mtype, params=None):
    if q:
        q.put({
            "SRC": src,
            "DST": dst,
            "TYPE": mtype,
            "PARAMS": params
        })
    else:
        logger.info('{}->{}:{} {}'.format(src, dst, mtype, params))
