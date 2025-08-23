from app import app

#ssl_context=('cert.pem', 'key.pem') da aggiungere sotto per accedere in https
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
