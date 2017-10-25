"""Main Script"""

import os
from polyIntersect import app

# This is only used when running locally. When running live, Gunicorn runs
# the application.
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', '8000')),
        debug=os.getenv('DEBUG') == 'True',
        threaded=True
    )
