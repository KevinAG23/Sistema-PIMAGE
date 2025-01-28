from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from image_security_analyzer import ImageSecurityAnalyzer

# Configuración básica de Flask y PostgreSQL
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:4321@localhost:5432/imagen_bd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

# Modelo de base de datos para imágenes
class ImageModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    approved = db.Column(db.Boolean, default=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400

    file = request.files['file']
    alias = request.form.get('alias')

    if not alias:
        return jsonify({'error': 'Alias es obligatorio'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Guardar temporalmente la imagen
        file.save(filepath)

        # Crear instancia del analizador
        analyzer = ImageSecurityAnalyzer()
        
        # Analizar la imagen
        is_safe, message = analyzer.analyze_image(filepath)
        
        if not is_safe:
            os.remove(filepath)  # Eliminar la imagen si no es segura
            return jsonify({'error': message}), 400

        # Si pasa todas las verificaciones, guardar en la base de datos como no aprobado
        new_image = ImageModel(alias=alias, filename=filename, approved=False)
        db.session.add(new_image)
        db.session.commit()

        return jsonify({'message': 'Imagen subida exitosamente, pendiente de aprobación'}), 201
    else:
        return jsonify({'error': 'Archivo no permitido'}), 400

@app.route('/admin')
def admin():
    # Obtener imágenes que no están aprobadas
    pending_images = ImageModel.query.filter_by(approved=False).all()
    return render_template('admin.html', images=pending_images)

@app.route('/gallery', endpoint='gallery_page')
def gallery():
    # Obtener imágenes aprobadas
    approved_images = ImageModel.query.filter_by(approved=True).all()
    return render_template('gallery.html', images=approved_images)

@app.route('/approve/<int:image_id>', methods=['POST'])
def approve_image(image_id):
    image = ImageModel.query.get_or_404(image_id)
    image.approved = True
    db.session.commit()
    flash('Imagen aprobada con éxito.')
    return redirect('/admin')

@app.route('/reject/<int:image_id>', methods=['POST'])
def reject_image(image_id):
    image = ImageModel.query.get_or_404(image_id)
    # Eliminar el archivo del servidor
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
    # Eliminar la entrada de la base de datos
    db.session.delete(image)
    db.session.commit()
    flash('Imagen rechazada y eliminada.')
    return redirect('/admin')

@app.route('/interface', methods=['GET'])
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)
