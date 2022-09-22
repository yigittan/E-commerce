from flask import Flask, request, jsonify , session
from flask_pymongo import PyMongo
from products.products_service import ProductService
from products.products_storage import ProductMongoStorage
from baskets.baskets_service import BasketService
from baskets.baskets_storage import BasketMongoStorage
from users.users_service import UserService
from users.users_storage import UsersMongoStorage
from orders.orders_service import OrderService
from orders.orders_storage import OrdersMongoStorage
from users.User import User
from products.Product import Product
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

client = PyMongo(app, uri="mongodb://localhost:27017/Commerce")

p_storage = ProductMongoStorage(client)
products_service = ProductService(p_storage)
b_storage = BasketMongoStorage(client)
baskets_service = BasketService(b_storage)
u_storage = UsersMongoStorage(client)
users_service = UserService(u_storage)
o_storage = OrdersMongoStorage(client)
orders_service = OrderService(o_storage)

def loginUser(email):
    user = users_service.getUser_by_email(email)
    session['logged_in'] = True
    session['email'] = email
    session['id'] = user['id']

@app.route('/')
def index():
    return {'messages': "You Are At Index Page :)"}

# KULLANICI KAYDI REGİSTER

@app.route('/register', methods=['POST'])
def register():
    body = request.get_json()
    name = body['name']
    surname = body['surname']
    username = body['username']
    email = body['email']
    password = body['password']
    city = body['city']
    zip_code = body['zip_code']
    street = body['street']
    building = body['building']
    user = User(name, surname, username, email, password,
                city, zip_code, street, building)
    res = users_service.create(user)
    baskets_service.create(res)
    return res

# KULLANICI GİRİŞİ LOG İN

@app.route('/login',methods=['POST'])
def login():
    body = request.get_json()
    email = body['email']
    candidatePassword = body['password']
    user = users_service.getUser_by_email(email)
    if (user):
        if (users_service.check_password(email,candidatePassword)):
            loginUser(email)
            return jsonify({'messages':'Log in is success'})
        else:
            return jsonify({'messages':"log in is failed"})

#  ÜRÜNLERİ LİSTELEMEK VE ÜRÜN EKLEMEK İÇİN

@app.route('/products' , methods=['GET','POST'])
def products():
    if request.method == 'GET':
        products = products_service.get_all_products()
        if products is None:
            return {'message':'Products not found'}
        return jsonify(products)
    if request.method == 'POST':
        body = request.get_json()
        name = body['name']
        price = body['price']
        brand = body['brand']
        description = body['description']
        category = body['category']
        created_at = datetime.now()
        discount = body['discount']
        size = body['size']
        color = body['color']
        product = Product(name,price,brand,description,category,created_at,discount,size,color)
        res = products_service.create(product)
        return jsonify(res)

@app.route('/products/filter')
def params():
    arg = request.args
    brand = arg.get('brand')
    name = arg.get('name')
    color = arg.get('color')
    filter_query =  {}
    if brand is not None:
        filter_query.update({'brand':brand})
    if color is not None:
        filter_query.update({'color':color})
    if name is not None:
        filter_query.update({'name':name})
    products = products_service.filter(filter_query)
    return jsonify(products)


@app.route('/products/<string:product_id>' , methods=['GET','PUT','DELETE'])
def productss(product_id):
    if request.method == 'GET':
        product = products_service.get_by_id(product_id)
        return jsonify(product)
    
    if request.method == 'PUT':
        body = request.get_json()
        name = body['name']
        price = body['price']
        brand= body['brand']
        description = body['description']
        category = body['category']
        created_at = datetime.now()
        discount = body['discount']
        size = body['size']
        color = body['color']
        product = Product(name,price,brand,description,category,created_at,discount,size,color)
        res = products_service.update(product,product_id)
        return jsonify(res)

    if request.method == 'DELETE':
        return product_id

@app.route('/users/<string:user_id>' , methods=['GET','DELETE','PUT'])
def users(user_id):
    if request.method == 'GET':
        user = users_service.get_by_id(user_id)
        return jsonify(user)

    if request.method == 'PUT':
        body = request.get_json()
        name = body['name']
        surname = body['surname']
        username = body['username']
        email = body['email']
        password = body['password']
        city = body['city']
        zip_code = body['zip_code']
        street = body['street']
        building = body['building']
        user = User(name, surname, username, email, password,
                    city, zip_code, street, building)
        res = users_service.update(user,user_id)
        return jsonify(res)

    if request.method == 'DELETE':
        return users_service.remove(user_id)
        
@app.route('/baskets/<string:basket_id>' , methods=['GET'])
def basket(basket_id):
    if request.method == 'GET':
        basket = baskets_service.get_by_id(basket_id)
        return jsonify(basket['products'])

@app.route('/baskets/<string:basket_id>/products/<string:product_id>' , methods=['POST','DELETE'])
def basket_cd(basket_id,product_id):
    if request.method == 'POST':
        product = products_service.get_by_id(product_id)
        basket= baskets_service.get_by_id(basket_id)
        price = product['price'] + basket['price']
        basket = baskets_service.add(basket_id,product_id,price)
        return jsonify(basket['price'])

    if request.method == 'DELETE':
        basket = baskets_service.remove(basket_id,product_id)
        return jsonify(basket['products'])

@app.route('/baskets/<string:basket_id>/clear' , methods=['DELETE'])
def basket_clear(basket_id):
    basket  = baskets_service.clear(basket_id)
    basket['price'] = 0
    return jsonify(basket['products'])   # basket bırakırsak 'products' = [......] array halinde geliyor

@app.route('/orders/<string:basket_id>' , methods=['GET','POST'])
def order(basket_id):
    if request.method == 'POST':
        user_id = session['id']
        basket = baskets_service.get_by_id(basket_id)
        price = basket['price']
        products_id = [product_id for product_id in basket['products']]
        res = orders_service.create(products_id,user_id,price)
        return res
    
    if request.method =='GET':
        user_id = session['id']
        order = orders_service.get(user_id)
        return jsonify(order['products'])


    



if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.run(debug=True, host="127.0.0.1", port=3000)
