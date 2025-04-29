import mysql.connector

# Connect to MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="root",     # <-- Your MySQL username here
    password="Az@y8848", # <-- Your MySQL password here
    database="hospital"
)
cursor = conn.cursor()

def add_patient():
    name = input("Enter Patient Name: ")
    age = int(input("Enter Patient Age: "))
    gender = input("Enter Patient Gender: ")
    address = input("Enter Patient Address: ")
    phone = input("Enter Patient Phone: ")

    query = "INSERT INTO Patient (name, age, gender, address, phone_number) VALUES (%s, %s, %s, %s, %s)"
    values = (name, age, gender, address, phone)

    cursor.execute(query, values)
    conn.commit()
    print("✅ Patient added successfully!")

def view_patients():
    cursor.execute("SELECT * FROM Patient")
    for patient in cursor.fetchall():
        print(patient)

def update_patient():
    patient_id = int(input("Enter Patient ID to update: "))
    print("What do you want to update?")
    print("1. Name")
    print("2. Age")
    print("3. Gender")
    print("4. Address")
    print("5. Phone Number")
    choice = input("Choose field (1-5): ")

    field_map = {
        '1': 'name',
        '2': 'age',
        '3': 'gender',
        '4': 'address',
        '5': 'phone_number'
    }

    if choice in field_map:
        new_value = input(f"Enter new {field_map[choice]}: ")
        sql = f"UPDATE Patient SET {field_map[choice]} = %s WHERE patient_id = %s"
        cursor.execute(sql, (new_value, patient_id))
        conn.commit()
        print("✅ Patient updated successfully!")
    else:
        print("Invalid choice.")

def delete_patient():
    patient_id = int(input("Enter Patient ID to delete: "))
    sql = "DELETE FROM Patient WHERE patient_id = %s"
    cursor.execute(sql, (patient_id,))
    conn.commit()
    print("✅ Patient deleted successfully!")

def main_menu():
    while True:
        print("\n=== Hospital Management CLI ===")
        print("1. Add Patient")
        print("2. View Patients")
        print("3. Update Patient")
        print("4. Delete Patient")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            add_patient()
        elif choice == '2':
            view_patients()
        elif choice == '3':
            update_patient()
        elif choice == '4':
            delete_patient()
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main_menu()
