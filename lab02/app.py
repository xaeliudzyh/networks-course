import os
from flask import Flask, jsonify, request, abort, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # допустимые форматы
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

products = {}
next_id = 1

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 1. GET /products — получить список всех продуктов (без файлов, только метаданные)
@app.route('/products', methods=['GET'])
def get_all_products():
    # Возвращаем все поля, кроме закодированной иконки; вместо иконки отдаём URL, если есть
    result = []
    for prod in products.values():
        info = {
            "id": prod["id"],
            "name": prod["name"],
            "description": prod["description"],
            "icon_url": f"/products/{prod['id']}/icon" if prod.get("icon_filename") else None
        }
        result.append(info)
    return jsonify(result), 200

# 2. GET /products/<id> — получить продукт по id (с URL иконки)
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    prod = products.get(product_id)
    if not prod:
        abort(404, description="Product not found")
    info = {
        "id": prod["id"],
        "name": prod["name"],
        "description": prod["description"],
        "icon_url": f"/products/{prod['id']}/icon" if prod.get("icon_filename") else None
    }
    return jsonify(info), 200

# 2.1 GET /products/<id>/icon — вернуть файл иконки (если есть)
@app.route('/products/<int:product_id>/icon', methods=['GET'])
def get_product_icon(product_id):
    prod = products.get(product_id)
    if not prod:
        abort(404, description="Product not found")
    filename = prod.get("icon_filename")
    if not filename:
        abort(404, description="Icon not found")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 3. POST /products — создать новый продукт (multipart/form-data)
@app.route('/products', methods=['POST'])
def create_product():
    global next_id
    if 'name' not in request.form or 'description' not in request.form:
        abort(400, description="Missing 'name' or 'description' in form data")
    name = request.form['name']
    description = request.form['description']
    icon_file = request.files.get('icon')
    icon_filename = None
    if icon_file:
        if icon_file.filename == '':
            abort(400, description="Empty filename")
        if not allowed_file(icon_file.filename):
            abort(400, description="File type not allowed")
        filename = secure_filename(icon_file.filename)
        filename = f"{next_id}_{filename}"
        icon_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        icon_filename = filename
    prod = {
        "id": next_id,
        "name": name,
        "description": description,
        "icon_filename": icon_filename
    }
    products[next_id] = prod
    next_id += 1
    response = {
        "id": prod["id"],
        "name": prod["name"],
        "description": prod["description"],
        "icon_url": f"/products/{prod['id']}/icon" if icon_filename else None
    }
    return jsonify(response), 201

# 4. PUT /products/<id> — обновить продукт (multipart/form-data)
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    if product_id not in products:
        abort(404, description="Product not found")
    if 'name' not in request.form or 'description' not in request.form:
        abort(400, description="Missing 'name' or 'description' in form data")
    prod = products[product_id]
    prod['name'] = request.form['name']
    prod['description'] = request.form['description']
    icon_file = request.files.get('icon')
    if icon_file:
        if icon_file.filename == '':
            abort(400, description="Empty filename")
        if not allowed_file(icon_file.filename):
            abort(400, description="File type not allowed")
        filename = secure_filename(icon_file.filename)
        filename = f"{product_id}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        icon_file.save(save_path)
        old_fn = prod.get("icon_filename")
        if old_fn:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_fn))
            except OSError:
                pass
        prod["icon_filename"] = filename
    response = {
        "id": prod["id"],
        "name": prod["name"],
        "description": prod["description"],
        "icon_url": f"/products/{prod['id']}/icon" if prod.get("icon_filename") else None
    }
    return jsonify(response), 200

# 5. DELETE /products/<id> — удалить продукт и файл-иконку, если есть
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    prod = products.get(product_id)
    if not prod:
        abort(404, description="Product not found")
    # Удаляем файл-иконку, если он есть
    fn = prod.get("icon_filename")
    if fn:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], fn))
        except OSError:
            pass
    del products[product_id]
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
