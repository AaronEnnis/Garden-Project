import MySQLdb, datetime, hashlib
from flask import Flask, session, render_template, request, redirect, url_for
from collections import Counter

app = Flask(__name__)

config = MySQLdb.connect("127.0.0.1", "root", "wowgamer1", "GardenProject")

conn = config.cursor()

def add_to_user(name, email, password, plot):

    plot_available = float(plot) * 929.03      #converts square foot to square centimetre
    
    conn.execute("INSERT INTO user (Name, Email, Password, PlotSize, PlotAvailable) VALUES  (%s,%s,%s,%s,%s)", (name, email, password, plot, int(plot_available)))

    config.commit()

#############################################################################################################################################################
def LogIn(email,password):

    conn.execute("SELECT * FROM user WHERE Email = %s and Password = %s", (email,password))
    data = conn.fetchall()
    
    if len(data) > 0:
        return True
    return False

#############################################################################################################################################################

def get_space(vegID, vegName):                                  #gets space required for a vegetable

    conn.execute("SELECT SpaceRequired FROM vegetable WHERE ID = %s OR Name = %s", (vegID,vegName))
    size = conn.fetchall()
    size = [(int(row[0])) for row in size]
    return size[0]

#############################################################################################################################################################

def get_plot(userID):           #gets the plot available for a user
    
    conn.execute("SELECT PlotAvailable FROM user WHERE ID = %s", (userID,))
    plot = conn.fetchall()
    plot = [(int(row[0])) for row in plot]
    return plot[0]
    
    

#############################################################################################################################################################
def add_a_schedule(userID, vegID, quantity, sowDate):
    conn.execute("INSERT INTO schedule (UserID, VegID, Quantity, SowDate) VALUES (%s,%s,%s,%s)", (userID, vegID, quantity, sowDate)) #dont forget to add in the sow date
    config.commit()

    size = get_space(vegID,'')
    plot = get_plot(userID)
    
    value = plot - (size * int(quantity))  #subtracts space available from user

    conn.execute("UPDATE user SET PlotAvailable = %s WHERE ID = %s", (int(value), userID))
    config.commit()

#############################################################################################################################################################    
def delete_a_schedule(userID, vegID, quantity, scheduleID):
    conn.execute("DELETE FROM schedule WHERE ID = %s", (scheduleID,)) 
    config.commit()

    size = get_space(vegID,'')
    plot = get_plot(userID)
    
    value = plot + (size * int(quantity))  #gives back space available to the user

    conn.execute("UPDATE user SET PlotAvailable = %s WHERE ID = %s", (int(value), userID))
    config.commit()
    
#############################################################################################################################################################
def is_a_veg(name):

    conn.execute("SELECT * FROM vegetable WHERE Name = %s", (name,))                #checks to see if vegetables exists in database
    data = conn.fetchall()

    if len(data) > 0:
        return True
    return False


#############################################################################################################################################################
def get_plant(name):

    conn.execute("SELECT * FROM vegetable WHERE Name = %s", (name,))
    data = conn.fetchall()
    data = [(row[0], row[1], row[2], row[3],row[4]) for row in data]

    return data


#############################################################################################################################################################
def get_plant_name(pID):

    conn.execute("SELECT * FROM vegetable WHERE ID = %s", (pID,))
    data = conn.fetchall()
    data = [(row[1]) for row in data]

    return data[0]

#############################################################################################################################################################
def get_week(date):

    a = datetime.date.today()                           #finds which week of growth a user is from the sowdate of the schedule
    b = a - date
    if b < datetime.timedelta(7):
        c = 0
    elif b >= datetime.timedelta(7) and b < datetime.timedelta(14):
        c = 7

    elif  b >= datetime.timedelta(14) and b < datetime.timedelta(21):
        c = 14
    elif  b >= datetime.timedelta(21) and b < datetime.timedelta(28):
        c = 21
    elif  b >= datetime.timedelta(28) and b < datetime.timedelta(35):
        c = 28
    elif  b >= datetime.timedelta(35) and b < datetime.timedelta(42):
        c = 35
    elif  b >= datetime.timedelta(42) and b < datetime.timedelta(49):
        c = 42
    elif  b >= datetime.timedelta(49) and b < datetime.timedelta(56):
        c = 49
    elif  b >= datetime.timedelta(56) and b < datetime.timedelta(63):
        c = 56
    elif  b >= datetime.timedelta(63) and b < datetime.timedelta(70):
        c = 63
    elif  b >= datetime.timedelta(70) and b < datetime.timedelta(77):
        c = 70
    elif  b >= datetime.timedelta(77) and b < datetime.timedelta(84):
        c = 77
    elif  b >= datetime.timedelta(84):
        c = 84

    return c

#############################################################################################################################################################
def maintenance(schedules):
    c = []
    values = []
    for v in schedules:                 #makes a list of tuples of the veg name and current week we are on of growth
        a = get_plant_name(v[0])
        b = get_week(v[1]) 
        c.append((a,b))

    for v in c:
        conn.execute("SELECT * FROM maintenance WHERE VegName = %s", (v[0],))
        data = conn.fetchall()
        data = [(row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9]) for row in data]
        index = 0
        weeks = []
        for k in data:
            while index < len(k):
                weeks.append(k[index])
                index = index + 1
        current_job = [i for i,x in enumerate(weeks) if x == v[1]]
        if len(current_job) == 0:
            tuple_data = (v[0],-1)
            values.append((tuple_data))
        else:
            tuple_data = (v[0],)
            L = list(tuple_data)
            for x in current_job:
                L.append(x)
            values.append((L))      #returns a tuple with the veg name and the task required to do this week
        
    return values


#############################################################################################################################################################
def secure_password(word):

    hash_object = hashlib.md5(word.encode())        #secures the password in the data base in non plain text
    hashed_password = hash_object.hexdigest()

    return hashed_password

#############################################################################################################################################################


@app.route('/')
@app.route('/LogIn')
def Index():

    global user_id                  #global user id
    user_id = -1

    return render_template('log_in.html',
                           title='Garden Project')
        
@app.route('/Home',methods=['GET', 'POST'])   
def Home():

    if request.method == 'POST':
        session['email'] = request.form['email']
        session['password'] = request.form['password']
        session['password'] = secure_password(session['password'])

        if LogIn(session['email'],session['password']):
            conn.execute("SELECT ID FROM user WHERE Email = %s and Password = %s", (session['email'],session['password']))  #gets information of who just logged in
            ID = conn.fetchall()
            ID = [(row[0]) for row in ID]
            global user_id
            user_id = ID[0]
            conn.execute("SELECT Name FROM user WHERE ID = %s", (user_id,))
            name = conn.fetchall()       
            name = [(row[0]) for row in name]
            return render_template('home.html',
                                   title='Garden Project',
                                   name= "Hello " + name[0])        
            
        else:
            return render_template('log_in_error.html',
                                   title='Garden Project')
    else:
        if user_id == -1:
                    return render_template('not_logged_in.html',        #this only allows user who are logged in to enter this page
                                   title='Garden Project')
        else:
            return render_template('home.html',
                                   title='Garden Project',
                                   name = "Main Menu")

@app.route('/CreateAccount')
def Create_Account():
 
    return render_template('create_account.html',
                            title='Garden Project')

@app.route('/AccountCreated', methods=['POST'])
def Account_Created():

    session['name'] = request.form['name']
    session['email'] = request.form['email']
    session['password'] = request.form['password']
    session['plot'] = request.form['plot']

    conn.execute("SELECT * FROM user WHERE Email = %s", (session['email'],))
    data = conn.fetchall()

    if len(data) == 0:
        session['password'] = secure_password(session['password'])

        add_to_user(session['name'],session['email'],session['password'],session['plot'])

        return render_template('account_created.html',
                               title='Garden Project')
    else:
        return render_template('create_account_error.html',
                               title='Garden Project')


@app.route('/DeleteAccount', methods=['POST'])
def Delete_Account():
    if user_id == -1:
        return render_template('not_logged_in.html',
                               title='Garden Project') 
    else:
        session['user_id'] = request.form['user_id']

        return render_template('delete_account.html',
                               title='Garden Project',
                               user_id = session['user_id'])


@app.route('/AccountDeleted', methods=['POST'])
def Account_Deleted():
    if user_id == -1:
        return render_template('not_logged_in.html',
                               title='Garden Project')
    else:
        session['user_id'] = request.form['user_id']
        conn.execute("DELETE FROM schedule WHERE UserID = %s", (session['user_id'],)) 
        config.commit()
        conn.execute("DELETE FROM user WHERE ID = %s", (session['user_id'],)) 
        config.commit()
        

        return render_template('account_deleted.html',
                               title='Garden Project')



@app.route('/UpdateAccount')
def Update_Account():
    if user_id == -1:
        return render_template('not_logged_in.html',
                               title='Garden Project') 
    else:
        return render_template('update_account.html',
                           title='Garden Project')

@app.route('/AccountUpdated', methods=['POST'])
def Account_Updated():

    if user_id == -1:
        return render_template('not_logged_in.html',
                               title='Garden Project')    
    else:
        session['name'] = request.form['name']                      #updates the users account settings
        session['email'] = request.form['email']
        session['password1'] = request.form['password1']
        session['password2'] = request.form['password2']
        session['new_password'] = request.form['new_password']

        if session['password1'] == session['password2']:
            
            conn.execute("SELECT Password FROM user WHERE ID = %s", (user_id,))
            session['data'] = conn.fetchall()
            session['data'] = [(row[0]) for row in session['data']]        
            
            if session['data'][0] == secure_password(session['password1']):
                
                if session['name'] != '':
                    conn.execute("UPDATE user SET Name = %s WHERE ID = %s", (session['name'], user_id)) #only updates the users information if the field was filled out
                    config.commit()
                    
                if session['email'] != '':
                    conn.execute("UPDATE user SET Email = %s WHERE ID = %s", (session['email'], user_id))
                    config.commit()
                    
                if session['new_password'] != '':
                    conn.execute("UPDATE user SET Password = %s WHERE ID = %s", (secure_password(session['new_password']), user_id))
                    config.commit()

                return render_template('account_updated.html',
                                       title='Garden Project')
            else:
                session['message'] = 'Wrong password entered'
                return render_template('update_account_error.html',
                                       title='Garden Project',
                                       message = session['message'])
        else:
            session['message'] = 'The passwords entered did not matched'
            return render_template('update_account_error.html',
                                   title='Garden Project',
                                   message = session['message'])

@app.route('/Profile')
def Profile():

    if user_id == -1:
            return render_template('not_logged_in.html',
                           title='Garden Project')
    else:
        conn.execute("SELECT * FROM user WHERE ID = %s",(user_id,))
        user_data = conn.fetchall()
        user_data = [(row[1],row[2],row[3],row[4]) for row in user_data]

        conn.execute("SELECT * FROM schedule WHERE UserID = %s",(user_id,))
        schedule_data = conn.fetchall()

        num_of_schedules = len(schedule_data)

        d =[]

        for v in user_data[0]:
            d.append(v)

        t = (d[0],d[3],num_of_schedules,d[1],d[2])      #list of profile information
        data = [t]
        
        return render_template('profile.html',
                               title='Garden Project',
                               profile = data,
                               user_id = user_id)

    


@app.route('/MakeSchedule')
def Make_Schedule():
    if user_id != -1:
        names = []
        conn.execute("SELECT Name FROM vegetable") 
        veg_names = conn.fetchall()
        for v in veg_names:
            names.append(v[0])
        return render_template('make_schedule.html',
                               title='Garden Project',
                               veg_names = names)
    else:
        return render_template('not_logged_in.html',
                                   title='Garden Project')

@app.route('/ScheduleCreated', methods=['POST'])
def Schedule_Created():
    if user_id == -1:
        return render_template('not_logged_in.html',        
                       title='Garden Project')
    else:
        session['plant'] = request.form['plants']
        session['quantity'] = request.form['quantity']
        session['sow_date'] = datetime.date.today()

        if is_a_veg(session['plant']):
            
            size = get_space('', session['plant'])
            plot = get_plot(user_id)
            
            value = plot - (size * int(session['quantity']))

            if value > 0:
                if is_a_veg(session['plant']):
                    session['description'] = get_plant(session['plant'])

                for row in session['description']:
                    session['veg_id'] = row[0]

                add_a_schedule(user_id, session['veg_id'], session['quantity'], session['sow_date'])

                return render_template('schedule_created.html',
                                       title='Garden Project')
            else:
                return render_template('schedule_not_created.html',
                                       title='Garden Project')
        else:
                return render_template('make_schedule.html',
                               title='Garden Project')

@app.route('/DeleteSchedule', methods=['POST'])
def Delete_Schedule():
    if user_id == -1:
        return render_template('not_logged_in.html',        
                       title='Garden Project')

    else:
        veg_id = request.form['veg_id']
        schedule_id = request.form['schedule_id']
        quantity = request.form['quantity']
        sow_date = request.form['sDate']
        
        veg_name  = get_plant_name(veg_id)

        return render_template('delete_schedule.html',
                               title='Garden Project',
                               veg_name = veg_name,
                               veg_id = veg_id,
                               quantity = quantity,
                               sDate = sow_date,
                               sID = schedule_id)

@app.route('/ScheduleDeleted', methods=['POST'])
def Schedule_Deleted():
    if user_id == -1:
        return render_template('not_logged_in.html',        
                       title='Garden Project')
    else:
        schedule_id = request.form['schedule_id']
        veg_id = request.form['veg_id']
        quantity = request.form['quantity']

        delete_a_schedule(user_id, veg_id, quantity, schedule_id)

        return render_template('schedule_deleted.html',
                               title='Garden Project') 

@app.route('/Schedules')        
def Schedules():
    
    if user_id != -1:
        conn.execute("SELECT VegID, Quantity, SowDate, ID FROM schedule WHERE UserID = %s", (user_id,)) 
        data = conn.fetchall()
        data = [(row[0], row[1],row[2], int(row[3])) for row in data]     
        
        if len(data) > 0:
            word = ''
        else:
            word = 'No schedules'

        return render_template('schedules.html',
                               word = word,
                               schedule = data,
                               title='Garden Project')
    else:
        return render_template('not_logged_in.html',
                                   title='Garden Project')

@app.route('/Calender')
def Calender():
    if user_id != -1:
        conn.execute("SELECT VegID, SowDate FROM schedule WHERE UserID = %s", (user_id,))
        data = conn.fetchall()
        data = [(row[0], row[1]) for row in data]

        if len(data) > 0:
            word = ''
        else:
            word = 'No schedules'
            
        maintenance_data = maintenance(data)
        list_of_schedules = []

        for v in maintenance_data:          #gives instructions on what the user is required to do this week
            c = Counter(v)
            description = ''
            if -1 in c:
                description = description + 'There is nothing to do this week.'
            if 0 in c or 1 in c or 2 in c:
                description = description + 'You need to water the ' + v[0] + 's. '
                
            if 3 in c or 4 in c or 5 in c:
                description = description + 'You need to weed the ' + v[0] + 's. '
                
            if 6 in c:
                if v[0] == 'Carrot':
                    description = description + 'If you harvest the ' + v[0] + 's now you get baby Carrots. '

            if 7 in c:
                description = description + 'You need to harvest the ' + v[0] + 's. You can delete this schedule when ready. '

            list_of_schedules.append((v[0], description))

        return render_template('calender.html',
                               title='Garden Project',
                               word = word,
                               schedules = list_of_schedules)
    else:
        return render_template('not_logged_in.html',
                                   title='Garden Project')

@app.route('/Plants')
def Plants():

    if user_id != -1:

        names = []
        conn.execute("SELECT Name FROM vegetable") 
        veg_names = conn.fetchall()
        for v in veg_names:
            names.append(v[0])
                      
        return render_template('plants.html',
                               title='Garden Project',
                               veg_names = names)
    else:
        return render_template('not_logged_in.html',
                                   title='Garden Project')


@app.route('/PlantsDescription', methods=['POST'])
def Plants_Description():
    if user_id == -1:
        return render_template('not_logged_in.html',        
                       title='Garden Project')
    else:
        session['plant'] = request.form['plants']               #shows selected plants description

        if is_a_veg(session['plant']):
            session['description'] = get_plant(session['plant'])

            for row in session['description']:
                session['plant_name'] = row[1]
                session['sowing'] = row[2]
                session['growing'] = row[3]
                session['harvesting'] = row[4]

            return render_template('plants_description.html',
                                   plant = session['plant_name'],
                                   sowing = session['sowing'],
                                   growing = session['growing'],
                                   harvesting = session['harvesting'],
                                   description = session['description'],
                                   title='Garden Project')
        else:
            return render_template('plants.html',
                               title='Garden Project')

@app.route('/LogOut')
def Log_Out():

    global user_id
    user_id = -1

    return render_template('log_out.html',
                           title='Garden Project')



app.secret_key = 'kjvHVYIuypmpjRDHgdflrDTy'

if __name__ == '__main__':
    app.run(debug = True)
