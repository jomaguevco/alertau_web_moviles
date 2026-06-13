import os

from flask import Flask


app = Flask(__name__)

# Registrar blueprints


@app.route('/')
def home():
    return 'MedicalApp - API RESTful Running'


if __name__ == '__main__':
    # Railway (y la mayoria de plataformas) inyectan el puerto en la variable PORT.
    # En local cae al 3007 por defecto.
    port = int(os.environ.get('PORT', 3007))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(port=port, debug=debug, host='0.0.0.0')
