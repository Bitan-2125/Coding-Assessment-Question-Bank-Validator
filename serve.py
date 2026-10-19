"""Single-process production WSGI entry point. Configure through environment."""
import os
from waitress import serve
from web.app import app
from validation import load_bank


if __name__ == '__main__':
    load_bank()  # Fail startup on a broken question-bank contract.
    serve(app, host='127.0.0.1', port=int(os.environ.get('PORT', '8080')),
          threads=4, max_request_body_size=16 * 1024, channel_timeout=180)
