from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import traceback


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    # Extra Credit: Add strong password guideline
    letters_and_nums = any(c.isalpha() for c in password) and any(c.isdigit() for c in password)
    upps_and_lows = any(c.isupper() for c in password) and any(c.islower() for c in password)
    has_special = any(sc in password for sc in ['!', '@', '#', '?'])
    if len(password) < 8 or not letters_and_nums or not upps_and_lows or not has_special:
        print("Please choose a stronger password!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return
    
    # Extra Credit: Add strong password guideline
    letters_and_nums = any(c.isalpha() for c in password) and any(c.isdigit() for c in password)
    upps_and_lows = any(c.isupper() for c in password) and any(c.islower() for c in password)
    has_special = any(sc in password for sc in ['!', '@', '#', '?'])
    if len(password) < 8 or not letters_and_nums or not upps_and_lows or not has_special:
        print("Please choose a stronger password!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False

def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False

def login_patient(tokens):
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    """
    : Part 2
    """
    # If no user (Patient or caregiver) is logged in, print “Please login first!”
    global current_patient
    global current_caregiver
    if current_caregiver is None and current_patient is None:
        print('Please login first!')
        return
    
    if len(tokens) != 2:
        print('Input Format Incorrect. Please try again!')
        return

    # Check if date in correct format
    date = tokens[1]

    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    d = datetime.datetime(year, month, day)

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    # create sql statement that gets all available caregivers
    # for the input date from token, order by username
    select_available_caregivers = """
        select Username from Availabilities
        where Time = %s order by Username
    """
    select_available_vaccines = """
        select Name, Doses from Vaccines
    """

    # check if cursor execution is correct by testing with data
    try:
        cursor.execute(select_available_caregivers, d)
        result = cursor.fetchall()
        if not result:
            print('No available caregivers on this date!')
            return
        for row in result:
            print("Caregiver Name: " + str(row['Username']))
        cursor.execute(select_available_vaccines)
        for row in cursor:
            print(f"Vaccine Name: {str(row['Name'])}, Doses Left: {str(row['Doses'])}")
    except pymssql.Error as e:
        print("Check Availability Failed")
        print("Db-Error:", e)
        quit()

    # what is a ValueError? its not in the pymssql doc
    # it is from the datetime module
    except ValueError:
        print("Please enter a valid date!")
        return
    
    # if any python error occurs
    except Exception as e:
        print("Error occurred when checking availability")
        print('Please try again!')
        print("Error:", e)
        return









def reserve(tokens):
    """
    TODO: Part 2
    """
    if len(tokens) != 3:
        print('Input Format Incorrect. Please try again!')
        return
    
    global current_patient, current_caregiver
    # check if patient is logged in
    if current_patient is None:
        print('Please login first!')
        if current_caregiver:
            print('Please login as a patient!')
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)


    ## Check if date in correct format
    date = tokens[1]
    print('original date: ', date)
    vaccine = tokens[2]

    ## assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    d = datetime.datetime(year, month, day)
    print('datetime transformed d: ', d)

    select_caregiver_on_date = "select Username from Availabilities where Time = %s order by Username ASC"
    select_doses_for_vaccine = 'select * from Vaccines where Name = %s and Doses != 0'
    reserve_appt = """
        insert into Appointments Values(%s, %s, %s, %s)
    """ #date, caregiver, patient, vaccine in order
    select_appointment = "select appointment_id from appointments where caregiver = %s and date = %s"
    delete_caregiver_avai = "delete from availabilities where username = %s and time = %s"
    try:
        # TODO check caregiver availability
        cursor.execute(select_caregiver_on_date, d)
        caregiver_result = cursor.fetchone()
        print('caregiver_result', caregiver_result)
        if not caregiver_result:
            print('No Caregiver is available!')
            return
        selected_caregiver = caregiver_result['Username']

        # TODO check vaccine availability
        cursor.execute(select_doses_for_vaccine, vaccine)
        if not cursor.fetchone():
            print('Not enough available doses!')
            return

        # TODO QUES make appointment id- how do you do that?
        # DONE maintain a database of current ids, auto increment
        d, selected_caregiver, patient_name, vaccine = str(d), str(selected_caregiver), str(current_patient.username), str(vaccine)
        print(d, selected_caregiver, patient_name, vaccine)
        cursor.execute(reserve_appt, (d, selected_caregiver, patient_name, vaccine))
        cursor.execute(select_appointment, (selected_caregiver, d))
        appt_id = cursor.fetchone()['appointment_id']
        print(f'Appointment ID: {appt_id}, Caregiver username: {selected_caregiver}')
        cursor.execute(delete_caregiver_avai, (selected_caregiver, d))
        print('Deleted Caregiver availability')

        # commit to cloud database
        conn.commit()



    # catches all errors according to pymssql doc
    except pymssql.Error as e:
        print("Check Availability Failed")
        print("Db-Error:", e)
        quit()
    
    # QUES why is this catching errors for valid dates
    # except ValueError:
    #     print("Please enter a valid date!")
    #     return

    except Exception as e: 
        print("Error occurred when uploading availability")
        print("Error:", e)
        print("Error type", type(e))
        traceback.print_exc()
        return


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day) # can throw a valueerror
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    # general case
    except Exception as e: 
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    pass


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    '''
    : Part 2
    '''
    if len(tokens) != 1:
        print('Input Format Incorrect. Please try again!')
        return
    # check if patient/caregiver logged in
    global current_caregiver, current_patient
    user1 = ''
    username = ''
    select_scheduled_appt = """"""
    select_scheduled_appt_patient = """
        select Appointment_id, Vaccine, Date, Caregiver
        from Appointments
        where Patient = %s
        order by Appointment_id
    """
    select_scheduled_appt_caregiver = """
        select Appointment_id, Vaccine, Date, Patient
        from Appointments
        where Caregiver = %s
        order by Appointment_id
    """
    if current_caregiver is None and current_patient is None:
        print('Please login first!')
        return
    elif current_caregiver is not None:
        select_scheduled_appt = select_scheduled_appt_caregiver
        username = current_caregiver.username
        user1 = 'Patient'
    else:
        select_scheduled_appt = select_scheduled_appt_patient
        username = current_patient.username
        user1 = 'Caregiver'

    # output scheduled appointments for current user ordered by appointment_id
    #

    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_scheduled_appt, username)
        result = cursor.fetchall()
        for row in result:
            print(f"Appointment_ID: {str(row['Appointment_id'])}, Vaccine Name: {str(row['Vaccine'])}, Date: {str(row['Date'])}, {user1} Name: {str(row[user1])}")
    # what exception should I do to catch all errors
    except pymssql.Error as e:
        print("Please try again!")
        print("Error: ", e)
        traceback.print_exc()
        return
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        traceback.print_exc()
        return



def logout(tokens):
    """
    : Part 2
    """
    if len(tokens) != 1:
        print('Input Format Incorrect. Please try again!')
        return
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print('Please login first!')
        return
    elif current_caregiver is not None:
        current_caregiver = None
    else:
        current_patient = None
    print('Successfully logged out!')


def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break
        notlowered_response = response
        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(notlowered_response.split(" "))
        elif operation == "create_caregiver":
            create_caregiver(notlowered_response.split(" "))
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
