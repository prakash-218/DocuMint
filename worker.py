"""
Background jobs: email sync.

    python worker.py --once     one pass (Railway cron service, every 5 minutes)
    python worker.py            keep running, a pass every EMAIL_SYNC_INTERVAL seconds (default 300)
"""

import logging
import os
import sys
import time

import observability

observability.configure_logging()
logger = logging.getLogger('worker')


def run_once():
    import emailsync
    if not emailsync.accounts_from_env():
        logger.info('No mailboxes configured (EMAIL_ACCOUNTS); nothing to do')
        return 0
    started = time.perf_counter()
    results = emailsync.sync_all()
    stored = sum(r.get('stored') or 0 for r in results)
    failed = [r for r in results if r.get('error')]
    logger.log(logging.ERROR if failed else logging.INFO, f'email sync: {stored} new, {len(failed)} failed', extra={
        'event': 'email_sync_done', 'stored': stored, 'failed': len(failed),
        'durationMs': round((time.perf_counter() - started) * 1000)})
    return 1 if failed and len(failed) == len(results) else 0


if __name__ == '__main__':
    if '--once' in sys.argv:
        sys.exit(run_once())
    interval = int(os.getenv('EMAIL_SYNC_INTERVAL', '300'))
    while True:
        try:
            run_once()
        except Exception:                   # keep the worker alive; the next pass may work
            logger.exception('Email sync pass failed')
        time.sleep(interval)
