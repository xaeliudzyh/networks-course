from flask import Flask, jsonify, request, abort

app = Flask(__name__)

products = {}
next_id = 1

# 1. GET /products — получить список всех продуктов
@app.route('/products', methods=['GET'])
def get_all_products():
    # возвращаем список значений словаря products
    return jsonify(list(products.values())), 200

# 2. GET /products/<int:product_id> — получить продукт по id
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    prod = products.get(product_id)
    if not prod:
        abort(404, description="Product not found")
    return jsonify(prod), 200

# 3. POST /products — добавить новый продукт
@app.route('/products', methods=['POST'])
def create_product():
    global next_id
    if not request.is_json:
        abort(400, description="Request body must be JSON")
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    if not name or not description:
        abort(400, description="Missing 'name' or 'description'")
    prod = {
        "id": next_id,
        "name": name,
        "description": description
    }
    products[next_id] = prod
    next_id += 1
    return jsonify(prod), 201

# 4. PUT /products/<int:product_id> — обновить существующий продукт
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    if product_id not in products:
        abort(404, description="Product not found")
    if not request.is_json:
        abort(400, description="Request body must be JSON")
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    if not name or not description:
        abort(400, description="Missing 'name' or 'description'")
    prod = products[product_id]
    prod['name'] = name
    prod['description'] = description
    return jsonify(prod), 200

# 5. DELETE /products/<int:product_id> — удалить продукт по id
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if product_id not in products:
        abort(404, description="Product not found")
    del products[product_id]
    return '', 204  # No Content

if __name__ == '__main__':
    app.run(debug=True)
