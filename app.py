import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime



UPLOAD_FOLDER = 'static/comprobantes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///turnos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'clave_super_secreta'

db = SQLAlchemy(app)

class Turno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    fecha = db.Column(db.String(10), nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    motivo = db.Column(db.Text, nullable=True)
    comprobante = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    turnos = Turno.query.with_entities(Turno.fecha, Turno.hora).all()
    turnos_ocupados = [{'fecha': t.fecha, 'hora': t.hora} for t in turnos]
    return render_template('index.html', turnos_ocupados = turnos_ocupados)

@app.route('/turno', methods=['POST'])
def recibir_turno():
    nombre = request.form['nombre']
    email = request.form['email']
    telefono = request.form['telefono']
    
    # Validar y formatear fecha y hora correctamente
    fecha_raw = request.form['fecha']
    hora = request.form['hora']
    
    try:
        fecha = datetime.strptime(fecha_raw, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return "<h3>Fecha inválida</h3><a href='/'>Volver</a>"

    motivo = request.form.get('motivo', '')

    # Verificar si ya hay un turno con la misma fecha y hora
    existente = Turno.query.filter_by(fecha=fecha, hora=hora).first()
    if existente:
        return f"""
        <h3>Ya hay un turno registrado para {fecha} a las {hora}.</h3>
        <a href="/">Elegir otro horario</a>
        """

    # Manejo del comprobante (imagen)
    archivo = request.files.get('comprobante')
    ruta_comprobante = None
    if archivo and archivo.filename != '':
        filename = secure_filename(archivo.filename)
        ruta = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        archivo.save(ruta)
        ruta_comprobante = ruta

    # Crear y guardar el nuevo turno
    nuevo_turno = Turno(
        nombre=nombre,
        email=email,
        telefono=telefono,
        fecha=fecha,
        hora=hora,
        motivo=motivo,
        comprobante=ruta_comprobante
    )
    db.session.add(nuevo_turno)
    db.session.commit()

    # Confirmación
    return f'''
    <h1>Turno recibido</h1>
    <p><strong>Nombre:</strong> {nombre}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Teléfono:</strong> {telefono}</p>
    <p><strong>Fecha:</strong> {fecha}</p>
    <p><strong>Hora:</strong> {hora}</p>
    <p><strong>Motivo:</strong> {motivo}</p>
    <p><strong>Comprobante:</strong> {ruta_comprobante or 'No se adjuntó imagen'}</p>
    <a href="/">Volver</a>
    '''

@app.route('/admin')
def ver_turnos():
    if not session.get('Entraste'):
        return redirect(url_for('login'))
    
    turnos = Turno.query.all()
    return render_template('admin.html', turnos=turnos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        if usuario == 'admin' and contraseña == '1234':
            session['Entraste'] = True
            return redirect(url_for('ver_turnos'))
        else:
            return '<h3>Credenciales incorrectas</h3><a href="/login">Intentar otra vez</a>'
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('Entraste', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
