import math
from flask import Flask, render_template ,request ,redirect ,url_for, session ,flash ,jsonify ,make_response
from flask_mysqldb import MySQL
from flask_mysqldb import MySQL
import MySQLdb.cursors
import json ,re
import mysql.connector
from decimal import Decimal
import hashlib ,secrets
import requests, os
import stripe ,uuid
import time ,random ,string
from flask_mail import Mail, Message
from datetime import date
from flask_htmlmin import HTMLMIN
from datetime import datetime
from flask_login import login_required
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()           
drive = GoogleDrive(gauth)  


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

app.config['HIDE_ELEMENTS'] = False

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Aadi@9011'
app.config['MYSQL_DB'] = 'ecart'

mysql = MySQL(app)


app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'team.personelexpensetracker@gmail.com'
app.config['MAIL_PASSWORD'] = 'uabvnvzwyngutqit'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)



stripe.api_key = 'sk_test_51MecXQSDtBJBmoILDf81I4a1WOUDvL4uZARTjE5HDBoejn0mhWr00VBSgDpVfwqAVqXRUQHzTDWlWWPtI6oiAADo00nYf3isY7'


@app.route('/some-protected-page')
@login_required
def some_protected_page():
    # Code for the protected page goes here
    return render_template('index.html')


@app.errorhandler(404)
def page_not_found(e):
    # Render the 404.html template with the error message
    return render_template('404.html'), 404

@app.route('/offline')
def offline():
    return render_template('404.html')


@app.route('/')
def index():
    name =session.get('username')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT favorites.user, products.esin, products.pprice, products.ptitle, products.pimage, products.prating FROM products JOIN favorites ON products.esin = favorites.product_id WHERE favorites.user = %s',(name,))
    fav = cursor.fetchall()

    cursor1 = mysql.connection.cursor()
    cursor1.execute("SELECT products.esin,products.pimage,products.prating,products.pprice, products.ptitle, COUNT(search_history.id) AS num_searches  FROM products JOIN search_history ON products.ptitle LIKE CONCAT('%', search_history.search_term, '%') OR products.pdescription LIKE CONCAT('%', search_history.search_term, '%') GROUP BY products.esin ORDER BY num_searches DESC limit 10;")
    trend = cursor1.fetchall()

    if fav:
        # for item in fav:
        #     price = item[2]
        #     newprice = updated_price(price)
        #     item[2] = newprice

        return render_template('index.html',data = fav,trenddata = trend)
    
    else:
    
     return render_template('index.html',trenddata = trend)




@app.route('/reset',methods = ['GET','POST'])
def reset():
    cursor = mysql.connection.cursor()
    email = session.get('emailver')
    # print(email)

    cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
    account = cursor.fetchone()
    if account:
        val = account[7]
        if request.method == 'POST':
             password = request.form['newpass']
             hashpass = hashlib.sha256(password.encode()).hexdigest()
             confirm_password = request.form['conpass']
             hashconpass = hashlib.sha256(confirm_password.encode()).hexdigest()
             if password == confirm_password:
                    cursor.execute('UPDATE users SET password =%s, conformpassword =%s, otp=NULL WHERE email=%s', (hashpass, hashconpass, email))
                    mysql.connection.commit()
                    msg = 'Password Reset successfully'
                    return render_template('LogReg.html',msg = msg)
             else:
                    flash('Passwords do not match')
                    return render_template('reset.html', val=val)
        else:
                flash('Invalid OTP')
                return render_template('reset.html', val=val)
    else:
        val = None
    return render_template('reset.html', val=val)

    

@app.route('/generateotp', methods = ['GET','POST'] )
def generateotp():
    return render_template('otp.html')

@app.route('/email-verification', methods = ['GET','POST'] )
def emailverification():
    if request.method == 'POST' and 'mail' in request.form:
        email = request.form['mail']

        cursor = mysql.connection.cursor()

        cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
        account = cursor.fetchone()
        name = account[1]

        if account:
            session['emailver'] = email
            
            if 'otp' not in session:  # Check if OTP has been generated yet
                otp = random.randint(100000, 999999)
                # print(otp)
                cursor.execute('UPDATE users SET otp=%s WHERE email=%s', (otp, email))
                mysql.connection.commit()
                session['otp'] = otp
                html = render_template('email.html', name=name , otp=otp)
                msg = Message('Subject of the email', sender='team.personelexpensetracker@gmail.com', recipients=[email])
                msg.html = html

                # Send the email message
                mail.send(msg)
            return redirect(url_for('reset'))
        else:
            flash('Email does not exist')
            return redirect(url_for('generateotp'))

    return render_template('otp.html')




    



@app.route('/login', methods=['GET','POST'])
def LogReg():
    msg = ''
    name = ''
    if 'register' in request.form:
        if request.method == 'POST' and 'Name' in request.form and 'Pass' in request.form and 'Email' in request.form and 'Mobile' in request.form and 'Conpass' in request.form :
            username = request.form['Name']
            email = request.form['Email']
            mobile = request.form['Mobile']
            password = request.form['Pass']
            conpassword = request.form['Conpass']
            address = request.form['Address']

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            hashed_conpassword = hashlib.sha256(conpassword.encode()).hexdigest()
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = % s', (username, ))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address !'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers !'
            elif not username or not password or not email:
                msg = 'Please fill out the form !'
            else:
                if (password == conpassword):
                    cursor.execute('INSERT INTO users VALUES (NULL, % s, % s, % s, % s, % s, % s, NULL)', (username, email, mobile, hashed_password, hashed_conpassword, address,  ))
                    mysql.connection.commit()
                    msg = 'You have successfully registered !'
                else:
                    msg = 'Passwords does not match.Reenter password'
        elif request.method == 'POST':
            msg = 'Please fill out the form !'
        return render_template('LogReg.html', msg = msg)
    else:
        if request.method == 'POST' and 'uname' in request.form and 'upass' in request.form:
            username = request.form['uname']
            password = request.form['upass']
            hashpass = hashlib.sha256(password.encode()).hexdigest()
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE password = % s', (hashpass, ))
            
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['username'] = username
                msg = "Login successfull"
                # resp = make_response(render_template('index.html',msg = msg))
                # resp.set_cookie('username', username)
                # return resp
                return redirect(url_for('index'))
                
            else:
                msg = "Invalid Credentials"
    return render_template('LogReg.html',msg = msg)


# @app.route('/filter-products', methods=['GET','POST'])
# def filter_products():
#     filter_values = request.json
#     price = filter_values.get('price')
    
#     # Build SQL query based on filter values
#     sql_query = 'SELECT * FROM bags WHERE newprice <= %f'
#     cursor = mysql.connection.cursor()
#     cursor.execute(sql_query, (price,))
#     data = cursor.fetchall()
#     print(data)
    
#     # commit changes and close cursor
#     mysql.connection.commit()
#     cursor.close()
    
#     return jsonify(data)







ROWS_PER_PAGE = 5


# @app.route('/products')
# def products(): 
#     category = request.args.get('category')
#     print(category)
#     filters = {}
#     filters['category'] = request.args.get('sort-rating', '')
#     filters['price'] = request.args.get('price', '')
#     cur = mysql.connection.cursor()
#     # cur1 = mysql.connection.cursor()
#     # query1 = "SELECT min(newprice),max(newprice) from bags"
#     # cur1.execute(query1)
#     # res = cur1.fetchone()
#     # min = res[0] * 83
#     # max = res[1] * 83
#     # cur.execute("SELECT * FROM ac")
#     # all_products = cur.fetchall()
#     page = request.args.get('page', default=1, type=int)

#     # calculate the offset based on the current page number
#     offset = (page - 1) * 10

#     # create a cursor object

#     # execute a SELECT query with LIMIT and OFFSET
#     query = "SELECT * FROM {} LIMIT 10 OFFSET %s".format(category)
#     if filters['category']:
#             query += " WHERE starrating = 3"
#     cur.execute(query, (offset,))

#     # fetch the results
#     results = cur.fetchall()

#     # calculate the total number of pages
   

#     column_names = [desc[0] for desc in cur.description]
    

#     products = []
#     for row in results:
#         product_dict = {}
#         for i in range(len(column_names)):
#             product_dict[column_names[i]] = row[i]
        
        
#         price = product_dict['price']
#         product_dict['price'] = updated_price(price)
#         products.append(product_dict)
     
#     query = "SELECT COUNT(*) FROM {}".format(category)
#     cur.execute(query)
#     total_count = cur.fetchone()[0]
#     total_pages = (total_count + 9) // 10

#     tdata_json = json.dumps(products)
    
#     return render_template('productdis.html', tdata = products,tdata_json = tdata_json, page=page, total_pages=total_pages )


# @app.route('/products')
# def products():

    
#     category = request.args.get('category')
#     print(category)

 
#     cur = mysql.connection.cursor()
#     # cur1 = mysql.connection.cursor()
#     # query1 = "SELECT min(newprice),max(newprice) from bags"
#     # cur1.execute(query1)
#     # res = cur1.fetchone()
#     # min = res[0] * 83
#     # max = res[1] * 83
#     # cur.execute("SELECT * FROM ac")
#     # all_products = cur.fetchall()
#     page = request.args.get('page', default=1, type=int)

#     # calculate the offset based on the current page number
#     offset = (page - 1) * 10

#     # create a cursor object
   

#     # execute a SELECT query with LIMIT and OFFSET
#     query = "SELECT * FROM {} LIMIT 10 OFFSET %s".format(category)
#     cur.execute(query, (offset,))

#     # fetch the results
#     results = cur.fetchall()

#     # calculate the total number of pages
   

#     column_names = [desc[0] for desc in cur.description]
    

#     products = []
#     for row in results:
#         product_dict = {}
#         for i in range(len(column_names)):
#             product_dict[column_names[i]] = row[i]
        
        
#         price = product_dict['price']
#         product_dict['price'] = updated_price(price)
#         products.append(product_dict)
     
#     query = "SELECT COUNT(*) FROM {}".format(category)
#     cur.execute(query)
#     total_count = cur.fetchone()[0]
#     total_pages = (total_count + 9) // 10

#     tdata_json = json.dumps(products)
    
#     return render_template('productdis.html', tdata = products,tdata_json = tdata_json, page=page, total_pages=total_pages )

@app.route('/products')
def products():
    category = request.args.get('category')
    cat = request.form.get('cat')
    subcategory = None
    priceval = request.args.get('price')
    page = request.args.get('page', default=1, type=int)
    sort = request.args.get('sort')
    # offset = (page - 1) * 10
    minp =0
    maxp = 0
    cur1 = mysql.connection.cursor()
    query1 = "SELECT pprice from products Where pcategory = '{}' ".format(category)
    params = ()
    cur1.execute(query1)
    res = cur1.fetchall()
    numeric_prices = []
    for price in res:
        numeric_prices.append(updated_price(price[0]))




    minp = min(numeric_prices)
    maxp = max(numeric_prices)  
    
    cursor = mysql.connection.cursor()

    query = "select * from products Where pcategory = '{}' ".format(category)
    if sort:
        query += " ORDER BY title %s"
        params += (sort,)
    

    if priceval:
        query += " ORDER BY starrating %s"
        params += (sort,)
        
    cursor.execute(query,params)
    results = cursor.fetchall()

    column_names = [desc[0] for desc in cursor.description]
    
    products = []
    for row in results:
        product_dict = {}
        for i in range(len(column_names)):
            product_dict[column_names[i]] = row[i]
        price = product_dict['pprice']
        product_dict['price'] = updated_price(price)
        products.append(product_dict)
    
        # print(products)
     

    # cursor.execute("SELECT COUNT(*) FROM products Where pcategory = '{}'".format(category))
    # total_count = cursor.fetchone()[0]
    # total_pages = math.ceil(total_count / 10)


    cursor.execute("Select distinct psubcategory from products where pcategory = '{}'".format(category))
    subcategory = cursor.fetchall()

    cursor.execute("Select distinct pbrand from products where pcategory = '{}'".format(category))
    brand = cursor.fetchall()
    
    
    return render_template('productdis.html', tdata=products, category=category,min =minp,max = maxp,subcat = subcategory,brand = brand)



def adddollaar(val):
    if val.strip():  # Check if val is not empty or whitespace
      value = int(val)
    else:
       value = 0
     
    dollar_value = "{:,.2f}".format(value/83)
    return dollar_value

@app.route('/fetchrecords', methods=['POST'])
def fetchrecords():
    cur = mysql.connection.cursor()
    query = request.form['sort']
    # query1 = request.form['sortbrand']
    category = request.form['cat']
    minval = request.form['minval']
    rangeval = request.form['rangeval']
    srangeval = request.form['starrangeval']
    minstarval = 1

    minv = adddollaar(minval)
    rangevalv = adddollaar(rangeval) 
    print(srangeval)
    print(minstarval)

    products = []

    if query == 'All' and rangevalv > minv:
        cur.execute("SELECT * FROM products WHERE pcategory = %s and compprice >= %s and compprice <= %s" , (category,minv,rangevalv))
        print("i am excecuted")

    elif query == 'All' and srangeval:
        cur.execute("SELECT * FROM products WHERE pcategory = %s and prating >= %s and prating <= %s" , (category,minstarval,srangeval))
        print("i am excecuted")    
    
    elif query:
        cur.execute("SELECT * FROM products WHERE psubcategory = %s" , (query,))

    else:
        cur.execute('SELECT * FROM products WHERE pcategory=%s', (category,))

    productlist = cur.fetchall()

    column_names = [desc[0] for desc in cur.description]
    
    for row in productlist:
        product_dict = {}
        for i in range(len(column_names)):
            product_dict[column_names[i]] = row[i]
        price = product_dict['pprice']
        product_dict['price'] = updated_price(price)
        products.append(product_dict)

    print(products)

    htmlresponse = render_template('productcard.html', productlist=products)
    return jsonify({'htmlresponse': htmlresponse})







def updated_price(price):
       
        price_without_currency = price.replace('$', '')
        prsc = price_without_currency.replace(',','')
        pri1 = float(prsc)
        pri = float(pri1)
        p = int(pri)
        updated_price = p * 83   
        return updated_price


def updated_price(price1):
       
        price_without_currency1 = price1.replace('$', '')
        prsc = price_without_currency1.replace(',','')
        pri1 = float(prsc)
        p1 = int(pri1)
        updated_price1 = p1 * 83   
        return updated_price1




       
def updated_price2(price2):
       
        price_without_currency1 = price2.replace('$', '')
        pri1 = float(price_without_currency1)
        p1 = int(pri1)
        updated_price1 = p1 * 83   
        return updated_price1



@app.route('/productdesc/<string:item_id>')   #/<string:cat>
def productdesc(item_id):
    id = item_id
    val =0
    name = session.get('username')
    cartprod = session.get('newcart',{})
    # print(cartprod)
   
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products Where esin = %s ',(id, ))
    product = cur.fetchone()

    cur1 = mysql.connection.cursor()
    cur1.execute('SELECT * FROM favorites Where product_id = %s and user = %s ',(id,name ))
    fav = cur1.fetchone()
    # print(fav)
    if fav:
        val = "true"
    
    productdesc = []
    if product:
        # Get column headings
        headings = [desc[0] for desc in cur.description]

        # Create a dictionary with headings and values
        product_dict = {}
        for i in range(len(headings)):
            product_dict[headings[i]] = product[i]
        

        price = product_dict['pprice']
        product_dict['price'] = updated_price(price)
        price1 = product_dict['porgprice']
        product_dict['originalprice'] = updated_price(price1)
        
        productdesc.append(product_dict)

        
    


    return render_template('productdesc.html',pdata = productdesc ,check = val,uname = name )  #category=cat



@app.route('/favorite', methods=['POST'])
def add_favorite():
    # Get the product ID from the request body
    product_id = request.json.get('id')
    # print(product_id)
    
    # Get the current user's username
    username = session.get('username')
    # print(username)

    # Insert the favorite product into the favorites table
    favorite_query = "INSERT INTO favorites (user, product_id) VALUES (%s, %s)"
    favorite_data = (username, product_id)
    
    try:
        cursor = mysql.connection.cursor()
        cursor.execute(favorite_query, favorite_data)
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/remove-favorite/<string:item_id>', methods=['GET','POST'])
def remove_favorite(item_id):
    # Execute DELETE query
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM favorites WHERE product_id = %s", (item_id,))
    mysql.connection.commit()

    return 'Product removed from favorites'

@app.route('/add_to_cart',  methods=['GET', 'POST'])
def add_to_cart():
    category = request.args.get('category')
    username = session.get('username')
    if username is None:
        msg = 'Please Login yto add Things to cart.. :)'
        return redirect(url_for('LogReg', msg=msg))
    if request.method == 'POST':
        # Get the product ID and quantity from the form data
            product_id = request.form.get('itemid')
            image = request.form.get('itemimage')
            desc = request.form.get('itemdesc')
            quanitem = int(request.form.get('quant'))
            price = int(request.form.get('price'))
            orprice = int(request.form.get('itempr'))
            title = str(request.form.get('itemtit'))
            user_id = session.get('username')
            cart = session.get('cart', {})
            pr = price*quanitem
            cur = mysql.connection.cursor()
            if user_id is not None :

                query = "INSERT INTO cart (id, price, items, user, title, originalprice, image, description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                data = (product_id, pr, quanitem, user_id, title, orprice, image, desc)
                cur.execute(query, data)
                mysql.connection.commit()
            
            else:
                flash(f"Please Sign in or Signup to add items to cart. <a href='{url_for('LogReg')}'>SignIn /SignUp</a>")
                return render_template('productdesc.html')
        

        # update the cart with the new product information
            cart = {
                'userid': user_id,
                'productid':product_id,
                'quantity': quanitem,
                'price':quanitem*price
            }

            # save the cart to the session
            session['cart'] = cart
            
            
            
    return redirect(url_for('index'))


@app.route('/cart')
def cart():
    name = session.get('username')
    products = []
    total_price= 0
    particular_items = 0
    cartnum = 0
    pit = 0
    conprice =0
    val=0
    
    if name is not None:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM cart WHERE user = %s', (name,))
        cart_items = cur.fetchall()
        
        

        if cart_items:
            for item in cart_items:
                particular_items += item[2]
                total_price += item[1]
                pit = item[2]

        # print(particular_items)
        cur.execute('SELECT SUM(items) FROM cart WHERE user = %s', (name,))
        cartnu = cur.fetchone()[0]
        if cartnu is not None:
            cartnum = int(cartnu)
        else:
            cartnum = None

        
        for item in cart_items:
            cur.execute('SELECT * FROM products WHERE esin = %s', (item[0],))
            product = cur.fetchone()

            if product:
                # Get column headings
                headings = [desc[0] for desc in cur.description]

                # Create a dictionary with headings and values
                product_dict = {}
                for i in range(len(headings)):
                    product_dict[headings[i]] = product[i]


                conprice = product_dict['pprice']
                product_dict['price'] = updated_price(conprice)

                product_dict['quantity'] = item[2]
                products.append(product_dict)
                
    
                # Add the product to the cart
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT favorites.user, products.esin, products.pprice, products.ptitle, products.pimage, products.prating FROM products JOIN favorites ON products.esin = favorites.product_id WHERE favorites.user = %s',(name,))
    fav = cursor.fetchall()
              

                


    return render_template('cart.html', totprice=total_price, particularitem=pit, cartval=cartnum, products=products, username = name ,data = fav)





@app.context_processor
def inject_data():
    # logic to retrieve data
    name =session.get('username')
    
    data = session.get('cart')
    cartnum = 0
    tot_price = 0
    userid =0
    if name is not None:
         cur = mysql.connection.cursor()
         cur1 = mysql.connection.cursor()
         cur.execute('SELECT SUM(items) FROM cart WHERE user = %s',(name,))
         cur1.execute('SELECT SUM(price) FROM cart WHERE user = %s',(name,))
         cartnu = cur.fetchone()[0]
         totpri = cur1.fetchone()[0]
         cur.execute('SELECT * FROM users WHERE username = %s',(name,))
         userid = cur.fetchone()[0]
         
         if cartnu and totpri is not None:
             cartnum = int(cartnu)
             tot_price = int(totpri)
            
         else:
            cartnum = 0
            tot_price = 0
         
            
    # else:
    #         if data is not None:
    #             cartnum = data['quantity']
    return dict(uname=name, cartvalue = cartnum ,totalcart = tot_price, uid = userid)

@app.route('/pay',methods = ['GET','POST'])
def pay ():


      return render_template('checkout.html')

YOUR_DOMAIN = 'http://localhost:5000'
def price(pr):
      
      tot_price=pr*100
      originalpr = tot_price
      return originalpr


@app.route('/create-checkout-session1', methods=['GET','POST'])
def create_checkout_session1():
    
    user_data = inject_data()
    username = user_data.get('uname')

    if username is None:
        return render_template('LogReg.html',msg = 'please sign in ...')
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM cart WHERE user = %s', (username,))
    cart_items = cur.fetchall()
    line_items = []
    for product in cart_items:
        line_items.append({
            "price_data": {
                "currency": "inr",
                "product_data": {
                    "name": product[4], 
                },
                "unit_amount": price(product[5]),
            },
            "quantity": product[2]
        })

        session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url = url_for('thanks', _external=True, paymentmethod='paid'),
        cancel_url=url_for('errorpay', _external=True)
    )
    return redirect(session.url, code=303)





@app.route('/create-checkout-session/<string:item_id>/<int:quantity>', methods=['GET','POST'])
def create_checkout_session(item_id,quantity):
    productid = item_id
    user_data = inject_data()
    username = user_data.get('uname')
    line_items = []
    if username is None:
        return render_template('LogReg.html',msg = 'please sign in ...')
    
    if productid and quantity is not None:
        cur1 = mysql.connection.cursor()
        cur1.execute('SELECT * FROM products WHERE esin = %s', (productid,))
        buy_items = cur1.fetchall()

        if buy_items:
            for product in buy_items:
                line_items.append({
                    "price_data": {
                        "currency": "inr",
                        "product_data": {
                            "name": product[14],
                        },
                        "unit_amount": price(updated_price(product[7])),
                    },
                    "quantity": quantity
                })
                orderid = product[1]
        else:
            return render_template('error.html',msg = 'Product not found...')
    
    # Create the Checkout Session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url = url_for('thanks1', _external=True, paymentmethod='paid', total=quantity*updated_price(product[7]),qty = quantity,orderid =orderid ),
        cancel_url=url_for('errorpay', _external=True)
    )

    return redirect(session.url, code=303)

          


@app.route('/success')
def thanks():
    user_data = inject_data()
    username = user_data.get('uname')
    
    payment_method = request.args.get('paymentmethod')
    paytotal = request.args.get('total')
    total_cart_value = paytotal if paytotal else user_data.get('totalcart', 0)
  
        

    # print(payment_method)
    # Generate a unique order ID
    order_id = generate_id()

    # Get user data including username and total cart value

    if payment_method == "paid":
      paymentstatus = "paid"
    else:
        paymentstatus = "COD"
    
    order_date = date.today()
    
    # print(total_cart_value)
    # send_email(username,total_cart_value,order_date,order_id)

    # Get the current date
    

    # Insert order details into the orderdetails table
    order_details_query = "INSERT INTO orderdetails (orderid, orderdate, username, paymentstatus, total, orderstatus) VALUES (%s, %s, %s, %s, %s, 'pending')"
    order_details_data = (order_id, order_date, username,paymentstatus, total_cart_value)
    execute_query(order_details_query, order_details_data)

    # Insert each cart item as an order item into the orders table
    cart_items_query = "SELECT * FROM cart WHERE user = %s"
    cart_items_data = (username,)
    cart_items = execute_query(cart_items_query, cart_items_data)

    for cart_item in cart_items:
        order_item_query = "INSERT INTO orders (orderid, username, orderdate, ordertotal, orderstatus, orderproductid, orderoftotparitem) VALUES (%s, %s, %s, %s, 'pending', %s, %s)"
        order_item_data = (order_id, username, order_date, cart_item[1], cart_item[0], cart_item[2])
        execute_query(order_item_query, order_item_data)


    q = "Update products SET quantitysold = %s Where esin = %s"
    d = (cart_item[2],cart_item[0])
    execute_query(q,d)

    # Clear the cart for the current user
    clear_cart_query = "DELETE FROM cart WHERE user = %s"
    clear_cart_data = (username,)
    execute_query(clear_cart_query, clear_cart_data)
    

    # Render the success.html template
    return render_template('success.html')

@app.route('/success1')
def thanks1():

    
    payment_method = request.args.get('paymentmethod')
    paytotal = request.args.get('total')
    quantity = request.args.get('qty')
    orderid = request.args.get('orderid')
    total_cart_value = paytotal if paytotal else user_data.get('totalcart', 0)
  
        

    # print(payment_method)
    # Generate a unique order ID
    order_id = generate_id()

    # Get user data including username and total cart value
    user_data = inject_data()
    username = user_data.get('uname')
    if payment_method == "paid":
      paymentstatus = "paid"
    else:
        paymentstatus = "COD"
    
    order_date = date.today()
    
    # print(total_cart_value)
    

    # Get the current date
    

    # Insert order details into the orderdetails table
    order_details_query = "INSERT INTO orderdetails (orderid, orderdate, username, paymentstatus, total, orderstatus) VALUES (%s, %s, %s, %s, %s, 'pending')"
    order_details_data = (order_id, order_date, username,paymentstatus, total_cart_value)
    execute_query(order_details_query, order_details_data)

    # Insert each cart item as an order item into the orders table


    order_item_query = "INSERT INTO orders (orderid, username, orderdate, ordertotal, orderstatus, orderproductid, orderoftotparitem) VALUES (%s, %s, %s, %s, 'pending', %s, %s)"
    order_item_data = (order_id, username, order_date, total_cart_value, orderid, quantity)
    execute_query(order_item_query, order_item_data)

    q = "Update products SET quantitysold = %s Where esin = %s"
    d = (quantity,orderid)
    execute_query(q,d)

    

    # Render the success.html template
    return render_template('success.html')

def send_email(name,tot,date,id):
 username = name


 if username is not None:
    cur = mysql.connection.cursor()
    cur1 = mysql.connection.cursor()
    cur.execute('SELECT * FROM cart WHERE user = %s', (username,))
    
    
    cart_items = cur.fetchall()

    cur1.execute('SELECT * FROM users WHERE username=%s', (username,))
    account = cur1.fetchone()
    email = account[2]
    address = account[6]

    




        


    msg = Message('Order Confirmation', sender='team.personelexpensetracker@gmail.com',recipients=[email])
    msg.html = render_template('orderinvoice.html',  order = cart_items,  name =username ,total=tot, address =address,date=date,id=id)
    

    mail.send(msg)


# def send_email1(name,tot,date,id):
#  username = name

# #  if username is not None:
#     cur = mysql.connection.cursor()
#     cur1 = mysql.connection.cursor()
#     cur.execute('SELECT * FROM cart WHERE user = %s', (username,))
    
    
#     cart_items = cur.fetchall()

#     cur1.execute('SELECT * FROM users WHERE username=%s', (username,))
#     account = cur1.fetchone()
#     email = account[2]
#     address = account[6]

    




        


#     msg = Message('Order Confirmation', sender='team.personelexpensetracker@gmail.com',recipients=[email])
#     msg.html = render_template('orderinvoice.html',  order = cart_items,  name =username ,total=tot, address =address,date=date,id=id)
    

#     mail.send(msg)



def execute_query(query, data):
    # Execute the given query with the given data and return the results
    cur = mysql.connection.cursor()
    cur.execute(query, data)
    mysql.connection.commit()
    results = cur.fetchall()
    cur.close()
    return results


@app.route('/cancel')
def errorpay():
    return render_template('cancel.html')

@app.route('/orders')
def orders():
    # Get the username from the session
    user_data = inject_data()
    username = user_data.get('uname')
    if username is None:
        # If the user is not logged in, redirect them to the login page
        return redirect(url_for('LogReg'))

    # Get the user's orders from the database
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM orderdetails WHERE username = %s ORDER BY orderdate DESC' , (username,))
    orders = cur.fetchall()

    # id = orders[0]
    # # Get the total price of all the user's orders
    # cur.execute('SELECT SUM(ordertotal) FROM orders WHERE orderid = %s', (id,))
    # row = cur.fetchone()
    # total_price = row[0] if row[0] is not None else 0
    total_price = user_data.get('totalcart')

    # Render the orders template with the user's orders and the total price
    return render_template('orders.html', orders=orders, total_price=total_price)


@app.route('/item/<string:item_id>', methods=['GET'])
def get_item_details(item_id):


    
    cur = mysql.connection.cursor()
    cur.execute('SELECT products.ptitle, orders.ordertotal, orders.orderoftotparitem FROM products JOIN orders ON products.esin = orders.orderproductid where orderid = %s',(item_id,))
    item = cur.fetchall()

    if item:
         products = []
         for result in item:
            product = {
                'id': item_id,
                'name': result[0],
                'price':result[1],
                'quantity': result[2],
            }
            products.append(product)
         return jsonify(products)
   
    


@app.route('/cart/delete/<string:product_id>', methods=['DELETE', 'GET', 'POST'])
def delete_product_from_cart(product_id):
    pid =product_id
    cur = mysql.connection.cursor()
    query = "DELETE FROM cart WHERE id = %s"
    cur.execute(query, (pid,))
    mysql.connection.commit()
    return redirect(url_for('cart'))

            

def generate_id():
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choices(characters, k=6))
    return random_string
    

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    resp = make_response(render_template('LogReg.html'))
    resp.delete_cookie('username')
    return resp

    return redirect(url_for('LogReg'))

@app.route('/search')
def search():
    query = request.args.get('q')

    user_data = inject_data()
    user_id = user_data.get('uid')
    now = datetime.now()
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO search_history (user_id, search_term, search_time) VALUES (%s, %s, %s)", (user_id, query, now))
    mysql.connection.commit()
    
    # Perform search query using query and category parameters
    # Return search results as a list of dictionaries
    cursor1 = mysql.connection.cursor()
    cursor1.execute("SELECT * FROM products WHERE pdescription LIKE %s", ('%' + query + '%',))
    results = cursor1.fetchall()


    


   

    column_names = [desc[0] for desc in cursor1.description]
    

    products = []
    for row in results:
        product_dict = {}
        for i in range(len(column_names)):
            product_dict[column_names[i]] = row[i]
        
        
        price = product_dict['pprice']
        product_dict['price'] = updated_price(price)
        products.append(product_dict)
        

    return jsonify(products)


@app.route('/trending')
def trending():
    cursor1 = mysql.connection.cursor()
    cursor1.execute("SELECT products.esin,products.pdescription, products.ptitle, COUNT(search_history.id) AS num_searches  FROM products JOIN search_history ON search_history.search_term = products.ptitle GROUP BY products.esin ORDER BY num_searches DESC limit 10;")
    results = cursor1.fetchall()

    column_names = [desc[0] for desc in cursor1.description]

    products = []
    for row in results:
        product_dict = {}
        for i in range(len(column_names)):
            product_dict[column_names[i]] = row[i]
        products.append(product_dict)

    return jsonify(products)



@app.route('/ordersearch/<int:order_id>')
def get_order_data(order_id):
    # fetch the data for the requested order
    
    user_data = inject_data()
    user_id = user_data.get('uname')
    cursor1 = mysql.connection.cursor()
    cursor1.execute("SELECT * FROM orders WHERE orderid = %s and username = %s", (order_id,user_id,))
    order_data =cursor1.fetchall()

    # return the data as a JSON response
    return jsonify(order_data)

@app.route('/bulkorder')
def bulkorder():
    cursor = mysql.connection.cursor()
    cursor.execute("select distinct psubcategory from products")
    subcat = cursor.fetchall()
    return render_template('bulkorder.html',subcat = subcat)


@app.route('/subcategory', methods=['GET'])
def subcat():
    # Get the subcategory ID from the query parameters


    # Look up the products for the given subcategory ID
    cursor = mysql.connection.cursor()
    cursor.execute("select distinct psubcategory from products ")   
    products = cursor.fetchall()
    print(products)

    # Return the products as JSON
    return jsonify(products), 200, {'Content-Type': 'application/json'}


@app.route('/productbulk', methods=['POST'])
def get_products():
    # Get the subcategory ID from the POST data
    subcat_id = request.form['subcat']

    # Look up the products for the given subcategory ID
    cursor = mysql.connection.cursor()
    cursor.execute("select distinct ptitle,esin from products where psubcategory = %s",(subcat_id,))   
    products = cursor.fetchall()

    product_options = ''
    for product in products:
        product_options += '<option value="' + product[1] + '">' + product[0] + '</option>'
    

    # Return the products as JSON
    return jsonify({'product_options': product_options})


@app.route('/price', methods=['POST'])
def get_price():
    # Get the product ID from the form data
    prod_id = request.form['esin']

    # Look up the price for the given product ID
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT pprice FROM products WHERE esin = %s", (prod_id,))   
    p = cursor.fetchall()

    # If the price is not found, return an error
    if len(p) == 0:
        return jsonify({'error': 'Price not found.'}), 404

    # Otherwise, return the price as JSON
    price = updated_price(p[0][0])
    return jsonify({'price': price})


@app.route('/add-to-table', methods=['POST'])
def add_to_table():
    data = request.get_json()
    username = session.get('username')

    print(data)
    cursor = mysql.connection.cursor()
    for row in data:
        # Get product details from the database based on the product name
        cursor.execute("SELECT pimage, porgprice,esin,pdescription FROM products WHERE esin = %s", (row['prod'],))
        product_data = cursor.fetchone()
        print(product_data)
        pimage = product_data[0]
        porg = product_data[1]
        porgprice = updated_price(porg)
        pid = product_data[2]
        pdesc = product_data[3]



        # Insert data into the mytable
        # cursor.execute("INSERT INTO cart (subcat, prod, qty, price, pimage, porgprice) VALUES (%s, %s, %s, %s, %s, %s)", (row['subcat'], row['prod'], row['qty'], row['price'], pimage, porgprice))
        cursor.execute("INSERT INTO cart (id,price,items,user,title,originalprice,image,description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (pid, row['price'], row['qty'],username,row['prod'], porgprice, pimage,pdesc ))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'success': True})



if __name__ == '__main__':
    app.run(debug=True)
