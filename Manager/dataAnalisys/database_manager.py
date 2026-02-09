import sqlite3
import os
import matplotlib.pyplot as plt
import time



class DatabaseManager:

    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None
        self.cursor = None


    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_name)
            print(f"Path database: {os.path.abspath(self.db_name)}")
            self.cursor = self.connection.cursor()
            print("Database connection established.")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")


    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Database connection closed.")


    def add_data(self, name, value, time):  #!!! Non c'è controllo del datatype
        if self.connection:
            try:
                self.create_table_if_not_exists(name)  # Assicurati che la tabella esista prima di inserire i dati
                self.cursor.execute(f"INSERT INTO {name} (value, time) VALUES (?, ?)", (value, time))
                self.connection.commit()
                print("Data added successfully.")
            except sqlite3.Error as e:
                print(f"Error adding data: {e}")
        else:
            print("No database connection. Please connect to the database first.")
    

    def get_all_data(self, name):
        if self.connection:
            try:
                self.cursor.execute(f"SELECT * FROM {name}")
                data = self.cursor.fetchall()
                return data
            except sqlite3.Error as e:
                print(f"Error retrieving data: {e}")
                return []
        else:
            print("No database connection. Please connect to the database first.")
            return []


    def create_table_if_not_exists(self, table_name):
        #Crea la tabella se non esiste con time come PRIMARY KEY
        self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                time TEXT PRIMARY KEY,  -- ← Time è la chiave primaria
                value REAL NOT NULL     -- ← Rinominato da 'data' a 'value'
            )
        """)
        self.connection.commit()

    def delete_database_file(self):
        db_path = self.db_name
        # Elimina il file del database se esiste 

        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Database {db_path} deleted successfully.")
            return True
        else:
            print(f"File {db_path} not found.")
            return False

    def generate_grap(self, name):

        if self.connection:
            try:
                self.cursor.execute(f"SELECT * FROM {name}")
                data = self.cursor.fetchall()
                x=[]
                y=[]
                for row in data:
                    x.append(row[0])
                    y.append(row[1])

                plt.figure(figsize=(10, 5))
                plt.plot(x, y, marker='o', color='b')
                plt.title(name)
                plt.xlabel("time")
                plt.ylabel(name)
                plt.grid()
                plt.show()

            except sqlite3.Error as e:
                print(f"Error retrieving data: {e}")
                return []
        else:
            print("No database connection. Please connect to the database first.")
            return None

