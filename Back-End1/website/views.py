from flask import Blueprint, render_template, flash, redirect, request, jsonify
from .models import Product, Cart, Order
from flask_login import login_required, current_user
from . import db

# views.py - Contains all thre routes for different parts of the website


views = Blueprint('views', __name__)


# Home page route
@views.route('/')
def home():
 # Fetching products with flash sale enabled
    items = Product.query.filter_by(flash_sale=True)
    return render_template('home.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

# Route for adding an item to the cart
@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    # Fetching the item to be added to the cart
    item_to_add = Product.query.get(item_id)
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()

     # If item already exists in the cart, increase its quantity by one
    if item_exists:
        try:
            item_exists.quantity = item_exists.quantity + 1
            db.session.commit()
            flash(f' Quantity of { item_exists.product.product_name } has been updated')
            return redirect(request.referrer)
        except Exception as e:
            print('Quantity not Updated', e)
            flash(f'Quantity of { item_exists.product.product_name } not updated')
            return redirect(request.referrer)

 # If item does not exist, create a new cart item
    new_cart_item = Cart()
    new_cart_item.quantity = 1
    new_cart_item.product_link = item_to_add.id
    new_cart_item.customer_link = current_user.id

    try:
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f'{new_cart_item.product.product_name} added to cart')
    except Exception as e:
        print('Item not added to cart', e)
        flash(f'{new_cart_item.product.product_name} has not been added to cart')
    return redirect(request.referrer)

# Route for displaying the cart
@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.product.current_price * item.quantity
    return render_template('cart.html', cart=cart, amount=amount, total=amount+10)

# Route for increasing the quantity of an item in the cart
@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity + 1
        db.session.commit()
        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 10
        }

        return jsonify(data)
    
# Route for decreasing the quantity of an item in the cart
@views.route('/minuscart')
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity - 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 10
        }

        return jsonify(data)
    

# Route for removing an item from the cart
@views.route('removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 10
        }

        return jsonify(data)
    
 # Route for placing an order   
@views.route('/place-order')
@login_required
def place_order():
    customer_cart = Cart.query.filter_by(customer_link=current_user.id).all()
    if customer_cart:
        try:
            for item in customer_cart:
                # Create a new order for each item in the cart
                new_order = Order()
                new_order.quantity = item.quantity
                new_order.price = item.product.current_price
                new_order.status = 'Pending'  # Set a default status value
                new_order.payment_id = 'Placeholder'  # Set a default or placeholder value for payment_id

                new_order.product_link = item.product_link
                new_order.customer_link = item.customer_link

                db.session.add(new_order)

                # Update product stock
                product = Product.query.get(item.product_link)
                product.in_stock -= item.quantity

                # Remove item from cart
                db.session.delete(item)

            db.session.commit()

            flash('Order Placed Successfully')

            return redirect('/orders')
        except Exception as e:
            print(e)
            flash('Order not placed. An error occurred')
            return redirect('/')
    else:
        flash('Your cart is Empty')
        return redirect('/')

# Route for displaying orders
@views.route('/orders')
@login_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('orders.html', orders=orders)

# Route for searching products
@views.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search')
        items = Product.query.filter(Product.product_name.ilike(f'%{search_query}%')).all()
        return render_template('search.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

    return render_template('search.html')


# Route for the contact us page
@views.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')


# Route for the about us page
@views.route('/about_us')
def about_us():
    return render_template('about_us.html')

# Routes for different product categories:

@views.route('/computers_laptops')
def computers_laptops():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"PC"}%')) |
        (Product.product_name.ilike(f'%{"Laptop"}%'))
    ).all()

    return render_template('computers_laptops.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])
                           

@views.route('/phones_tablets')
def phones_tablets():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"Phone"}%')) |
        (Product.product_name.ilike(f'%{"Tablet"}%'))
    ).all()

    return render_template('phones_tablets.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])


@views.route('/cameras')
def cameras():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"Camera"}%'))
    ).all()

    return render_template('cameras.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])



@views.route('/audio')
def audio():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"Audio"}%')) |
        (Product.product_name.ilike(f'%{"Headphones"}%'))|
        (Product.product_name.ilike(f'%{"Earphones"}%'))
    ).all()

    return render_template('audio.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])



@views.route('/tvs_home')
def tv_home():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"TV"}%')) 
    ).all()

    return render_template('tvs_home.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])





@views.route('/gaming')
def gaming():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"Gaming"}%')) 
    ).all()

    return render_template('gaming.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])



@views.route('/networking')
def networking():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"Networking"}%')) 
    ).all()

    return render_template('networking.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])





@views.route('/components')
def components():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"Component"}%')) 
    ).all()

    return render_template('components.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])




@views.route('/wearable_tech')
def wearable_tech():
    
    items = Product.query.filter(
        (Product.product_name.ilike(f'%{"Wearable"}%')) 
    ).all()

    return render_template('wearable_tech.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                      if current_user.is_authenticated else [])
