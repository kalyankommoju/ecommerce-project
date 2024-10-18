from flask import Flask,render_template,redirect,url_for,request,flash,abort,session
from flask_session import Session
import mysql.connector
from itsdangerous import URLSafeSerializer
from stoken import token
from key import salt,secret_key,salt2,salt3,salt4
from cmail import sendmail
from otp import genotp
import os
import re
import stripe
stripe.api_key='sk_test_51PZuDYRw90T9Io6obOhyTNCqCflnU6zbjoySyueUrUr2dm94tzICRWgQL2PXALOztaPTlD3bGaokZuf3bYt7BqJk00D35DKfuA'
mydb=mysql.connector.connect(host='localhost',user='root',password='kalyan',db='ecommy')
app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key=b'\xd8d8e7\x80\xd3c\xd7\xb3gz'


@app.route('/')
def index():
    return render_template('index.html')
@app.route('/home')
def home():
    fashion='fashion'
    home='home'
    electronics='electronics'
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(itemid),name,discription,qty,category,price,imgid from additems where category=%s',[fashion])
    fashion=cursor.fetchall()
    cursor.close()

    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(itemid),name,discription,qty,category,price,imgid from additems where category=%s',[home])
    home=cursor.fetchall()
    cursor.close()

    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(itemid),name,discription,qty,category,price,imgid from additems where category=%s',[electronics])
    electronics=cursor.fetchall()
    cursor.close()
    return render_template('home.html',fashion=fashion,home=home,electronics=electronics)
@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        user=request.form['username']
        mobile=request.form['number']
        email=request.form['email']
        address=request.form['address']
        password=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from signup where username=%s',[user])
            count=cursor.fetchone()[0]
            print(count)
            if count==1:
                raise Exception
        except Exception as e:
            flash('user already exsited')
            return redirect(url_for('signup'))
        else:
            data={'user':user,'mobile':mobile,'email':email,'address':address,'password':password}
            subject='The confirmation for Ecommerces website'
            body=f"click on the link to confirm {url_for('confirm',token=token(data,salt=salt),_external=True)}"
            sendmail(to=email,subject=subject,body=body)
            flash('verification link has sent to email')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        abort(404,'link expired')
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into signup (username,mobile,email,address,password) values (%s,%s,%s,%s,%s)',[data['user'],data['mobile'],data['email'],data['address'],data['password']])
        mydb.commit()
        cursor.close()
        flash('Your Details has registered successfully')
        return redirect(url_for('home'))
    
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from signup where username=%s and password=%s',[username,password])
            count=cursor.fetchone()[0]
            print(count)
            if count==0:
                raise Exception
        except Exception as e:
            flash('Username or password was incorrect')
            return redirect(url_for('login'))
        else:
            session['user']=username
            if not session.get(username):
                session[username]={}
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/ulogout')
def ulogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))

@app.route('/uforgot',methods=['GET','POST'])
def uforgot():
    if request.method=='POST':
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from signup where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        try:
            if count !=1:
                raise Exception
        except Exception as e:
            flash('Plss register the ecommerce accoutn')
            return redirect(url_for('signup'))
        else:
            subject="Ecommerce reset link has sent to your email"
            body=f"The link for ecommerce password reset is {url_for('uverify',token=token(email,salt=salt2),_external=True)}"
            sendmail(to=email,subject=subject,body=body)
            flash('The reset link has sent to email pls verify that')
            return redirect(url_for('uforgot'))
    return render_template('forgot.html')
@app.route('/uverify/<token>',methods=['GET','POST'])
def uverify(token):
    try:
        serializer=URLSafeSerializer(secret_key)
        data=serializer.loads(token,salt=salt2,max_age=180)
    except Exception as e:
        abort(404,'link expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update signup set password=%s where email=%s',[newpassword,data])
                mydb.commit()
                cursor.close()
                flash('Your password is change')
                return redirect(url_for('login'))
            else:
                flash('mismatched Password confirmation')
                return render_template('newpassword.html')
    return render_template('newpassword.html')

@app.route('/adminsignup',methods=['GET','POST'])
def adminsignup():
    if request.method=='POST':
        auser=request.form['username']
        amobile=request.form['mobile']
        aemail=request.form['email']
        apassword=request.form['password']
        otp=genotp()
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from adminsignup where email=%s',[aemail])
            count=cursor.fetchone()[0]
            print(count)
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from adminsignup where number=%s',[amobile])
            count2=cursor.fetchone()[0]
            print(count2)
            if count==1 and count==1:
                raise Exception
        except Exception as e:
            flash('user already exsited')
            return redirect(url_for('adminsignup'))
        else:
            details={'auser':auser,'amobile':amobile,'aemail':aemail,'apassword':apassword,'otp':otp}
            subject='The admin confirmation link for registerion'
            body=f"click on the link to confirm{otp}"
            sendmail(to=aemail,subject=subject,body=body)
            flash('OTP has sent to your email')
            return redirect(url_for('adminotp',token=token(details,salt=salt3),_external=True))
    return render_template('adminsignup.html')
@app.route('/adminotp<token>',methods=['GET','POST'])
def adminotp(token):
    if request.method=='POST':
        otp1=request.form['otp']
        serializer=URLSafeSerializer(secret_key)
        var1=serializer.loads(token,salt=salt3)
        if otp1==var1['otp']: 
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into adminsignup(name,number,email,password) values (%s,%s,%s,%s)',[var1['auser'],var1['amobile'],var1['aemail'],var1['apassword']])
            mydb.commit()
            cursor.close()
            flash('Your Admin details are registered success')
            return redirect(url_for('adminlogin'))
        else:
            flash('OTP was incorrect')
            return render_template('adminotp.html')
    return render_template('adminotp.html')

@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method=='POST':
        ademail=request.form['email']
        adpassword=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from adminsignup where email=%s and password=%s',[ademail,adpassword])
            var2=cursor.fetchone()[0]
            cursor.close()
            print(var2)
            if var2==0:
                raise Exception
        except Exception as e:
            flash('Check the Email or Password again')
            return redirect(url_for('adminlogin'))
        else:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select name from adminsignup where email=%s',[ademail])
            adname=cursor.fetchone()[0]
            cursor.close()
            session['adminuser']=adname
            return redirect(url_for('addashbord'))
    return render_template('adminlogin.html')

@app.route('/adminlogout',methods=['GET','POST'])
def adminlogout():
    if session.get('adminuser'):
        session.pop('adminuser')
        return redirect(url_for('adminlogin'))
    
@app.route('/adminforgot',methods=["GET","POST"])
def adminforgot():
    if request.method=='POST':
        adforgotemail=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from adminsignup where email=%s',[adforgotemail])
        count=cursor.fetchone()[0]
        cursor.close()
        try:
            if count !=1:
                raise Exception
        except Exception as e:
            flash('Plss register the ecommerce admin')
            return redirect(url_for('adminsignup'))
        else:
            subject="Ecommerce reset link has sent to your email"
            body=f"The link for ecommerce password reset is {url_for('adminpassword',token=token(adforgotemail,salt=salt4),_external=True)}"
            sendmail(to=adforgotemail,subject=subject,body=body)
            flash('The reset link has sent to email pls verify that')
            return redirect(url_for('adminforgot'))
    return render_template('adminforgot.html')
@app.route('/adminverify/<token>',methods=['GET','POST'])
def adminpassword(token):
    try:
        serializer=URLSafeSerializer(secret_key)
        var2=serializer.loads(token,salt=salt4,max_age=180)
    except Exception as e:
        abort(404,'link expired')
    else:
        if request.method=='POST':
            newpassword=request.form['newpassword']
            confirmpassword=request.form['confirmpassword']
            print( newpassword,confirmpassword)
            if newpassword==confirmpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update adminsignup set password=%s where email=%s',[newpassword,var2])
                mydb.commit()
                cursor.close()
                flash('Your password is change')
                return redirect(url_for('adminlogin'))
            else:
                flash('mismatched Password confirmation')
                return render_template('adminpassword.html')
    return render_template('adminpassword.html')
@app.route('/admindashbord')
def addashbord():
    return render_template('admindashbord.html')
@app.route('/additems',methods=['GET','POST'])
def additems():
    if session.get('adminuser'):
        if request.method=="POST":
            pname=request.form['itemname']
            pdec=request.form['discript']
            pqyt=request.form['quantity']
            catogery=request.form['category']
            print(catogery)
            price=request.form['price']
            addedby=session.get('adminuser')
            img=request.files['file']
            filename=genotp()+'.jpg'
            path=os.path.dirname(os.path.abspath(__file__))
            static_path=os.path.join(path,'static')
            img.save(os.path.join(static_path,filename))
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into additems(itemid,name,discription,qty,category,price,addedby,imgid) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s,%s)',[pname,pdec,pqyt,catogery,price,addedby,filename])
            mydb.commit()
            cursor.close()
            flash('Items are added  successfully')
            return redirect(url_for('addashbord'))
    else:
        return redirect(url_for('adminlogin'))
    return render_template('items.html')
@app.route('/productstatus')
def productstatus():
    if session.get('adminuser'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select bin_to_uuid(itemid),name,discription,qty,category,price from additems where addedby=%s',[session.get('adminuser')])
            items=cursor.fetchall()
            cursor.close()
        except Exception as e:
            abort(404,'Data not found')
        else:
            return render_template('productstatus.html',items=items)
    return render_template('productstatus.html')

@app.route('/updateproduct/<itemid>',methods=['GET','POST'])
def updateproduct(itemid):
    if session.get('adminuser'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select name,discription,qty,category,price from additems where itemid=uuid_to_bin(%s)',[itemid])
        data=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
            itemname=request.form['itemname']
            discript=request.form['discript']
            quantity=request.form['quantity']
            category=request.form['category']
            price=request.form['price']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update additems set name=%s,discription=%s,qty=%s,category=%s,price=%s where itemid=uuid_to_bin(%s)',[itemname,discript,quantity,category,price,itemid])
            mydb.commit()
            cursor.close()
            flash(f'{itemid} product details are updated')
            return redirect(url_for('productstatus'))
        return render_template('updateproduct.html',data=data)

@app.route('/deleteproduct/<itemid>')
def deleteproduct(itemid):
    if session.get('adminuser'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from additems where itemid=uuid_to_bin(%s)',[itemid])
        mydb.commit()
        cursor.close()
        flash(f'{itemid} Delete successfuly')
        return redirect(url_for('productstatus'))
    
@app.route('/dashbord/<category>')
def dashbord(category):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(itemid),name,discription,qty,category,price,imgid from additems where category=%s',[category])
    items=cursor.fetchall()
    cursor.close()
    return render_template('dashbord.html',items=items)

@app.route('/dic/<itemid>')
def discription(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(itemid),name,discription,qty,category,price,imgid from additems where itemid=uuid_to_bin(%s)',[itemid])
    items=cursor.fetchone()
    print(items)
    cursor.close()
    return render_template('discription.html',items=items)

@app.route('/allitems')
def allitems():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(itemid),name,discription,qty,category,price,imgid from additems')
    items=cursor.fetchall()
    print(items)
    cursor.close()
    return render_template('dashbord.html',items=items)

@app.route('/contactus',methods=['GET','POST'])
def contactus():
    if session.get('user'):
        if request.method=="POST":
            name=request.form['name']
            email=request.form['email']
            message=request.form['message']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into contactus (name,email,message) value (%s,%s,%s)',[name,email,message])
            mydb.commit()
            cursor.close()
            flash('Report as sent')
            return redirect(url_for('home'))
    return render_template('contactus.html')

@app.route('/customerqueries')
def queries():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from contactus')
    message=cursor.fetchall()
    cursor.close()
    return render_template('cqueries.html',message=message)

@app.route('/reviews/<itemid>',methods=['GET','POST'])
def addreview(itemid):
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            review=request.form['review']
            rating=request.form['rating']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into reviews (itemid,username,title,review,rating) values (uuid_to_bin(%s), %s, %s, %s, %s)',[itemid,session.get('user'), title, review, rating])
            mydb.commit()
            cursor.close()
            flash('Thankyou for your review')
            return redirect(url_for('discription',itemid=itemid))
    return render_template('review.html')

@app.route('/readreview/<itemid>',methods=['GET','POST'])
def readreview(itemid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,review,rating,username,date from reviews where itemid=uuid_to_bin(%s)',[itemid])
        review=cursor.fetchall()
        print(review)
        cursor.close()
        return render_template('readreview.html',review=review)

@app.route('/search',methods=['GET','POST'])
def search():
    if request.method=='POST':
        name=request.form['search']
        strg=['A-Za-z0-9']
        pattern=re.compile(f'^{strg}', re.IGNORECASE)
        if (pattern.match(name)):
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select bin_to_uuid(itemid),name,discription,qty,category,price,imgid from additems where name like %s',[name +'%'])
            data=cursor.fetchall()
            cursor.close()
            return render_template('dashbord.html', items=data)
        else:
            flash('result not found')
            return redirect(url_for('home'))
    return render_template('home.html')

@app.route('/cart/<itemid>/<name>/<discription>/<qty>/<category>/<price>/<imgid>')
def cart(itemid,name,discription,qty,category,price,imgid):
    if not session.get('user'):
        return redirect(url_for('login'))
    if itemid not in session[session.get('user')]:
        session[session.get('user')][itemid]=[name,discription,1,price,imgid]
        session.modified=True
        flash(f'{name} Added to Your Cart')
        return redirect(url_for('dashbord',category=category))
    session[session.get('user')][itemid][2]+=1
    flash(f'This {name} again added')
    return redirect(url_for('dashbord',category=category))

@app.route('/viewcart')
def viewcart():
    if not session.get('user'):
        return redirect(url_for('login'))
    items=session.get(session.get('user')) if session.get(session.get('user')) else 'empty'
    if items=='empty':
        return 'No productd added go and shop now'
    return render_template('viewcart.html',items=items)

@app.route('/deletecart/<item>')
def deletecart(item):
    if session.get('user'):
        session[session.get('user')].pop(item)
        return redirect(url_for('viewcart'))
    flash('Quantity 1 is removed')
    return redirect(url_for('login'))

@app.route('/pay/<itemid>/<name>/<int:q>/<int:price>', methods=['POST'])
def pay(itemid, name, q, price):
    if session.get('user'):
        username = session.get('user')
        total = price * q
        
        try:
            checkout_session = stripe.checkout.Session.create(
                success_url=url_for('success', itemid=itemid, name=name, q=q, total=total, _external=True),
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'product_data': {
                                'name': name,
                            },
                            'unit_amount': price * 100,
                            'currency': 'inr',
                        },
                        'quantity': q,
                    },
                ],
                mode='payment',
            )
            return redirect(checkout_session.url)
        except Exception as e:
            return str(e)
    else:
        return redirect(url_for('login'))
    
@app.route('/success/<itemid>/<name>/<q>/<total>')
def success(itemid,name,q,total):
    if session.get('user'):
        user=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,item_name,qyt,total_price,user) value (uuid_to_bin(%s),%s,%s,%s,%s)',[itemid,name,q,total,user])
        mydb.commit()
        cursor.close()
        flash(f'Your {name} Order is Placed ')
        return redirect(url_for('orders'))
    return redirect(url_for('login'))

@app.route('/orders')
def orders():
    if session.get('user'):
        user=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from orders where user=%s',[user])
        items=cursor.fetchall()
        cursor.close()
        return render_template('orders.html',items=items)
    return render_template('orders.html')

@app.route('/cancel/<name>')
def cancel(name):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from orders where item_name=%s',[name])
        mydb.commit()
        cursor.close()
        return redirect(url_for('orders'))
    return redirect(url_for('orders'))

app.run(debug=True,use_reloader=True)