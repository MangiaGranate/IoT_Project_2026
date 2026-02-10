import sqlite3
import os
import matplotlib.pyplot as plt
import time


class DatabaseManager:

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection = None
        self.cursor = None


    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_name)
            print(f"[DATABASE] Path database: {os.path.abspath(self.db_name)}")
            self.cursor = self.connection.cursor()
            print("[DATABASE] Database connection established.")
        except sqlite3.Error as e:
            print(f"[DATABASE] Error connecting to database: {e}")


    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("[DATABASE] Database connection closed.")


    def add_data(self, name: str, value, time):  #!!! Non c'è controllo del datatype
        if self.connection:
            try:
                #name = f'"{name}"'
                self.create_table_if_not_exists(name)  # Assicurati che la tabella esista prima di inserire i dati
                self.cursor.execute(f"INSERT INTO {name} (value, time) VALUES (?, ?)", (value, time))
                self.connection.commit()
                print("[DATABASE] Data added successfully.")
            except sqlite3.Error as e:
                print(f"[DATABASE] Error adding data: {e}")
        else:
            print("[DATABASE] No database connection. Please connect to the database first.")
    
    
    def add_data_blitz(self, name, value, time):
        # Metodo rapido per aggiungere dati senza dover gestire manualmente la connessione al database
        # aggiungo questo metodo perchè devo gestire l'errore del thread che non può accedere al database se non è stato lui a creare l'oggetto sqlite3.Connection
        self.connect()
        self.add_data(name, value, time)
        self.disconnect()


    def get_all_data(self, name):
        if self.connection:
            try:
                self.cursor.execute(f"SELECT * FROM {name}")
                data = self.cursor.fetchall()
                return data
            except sqlite3.Error as e:
                print(f"[DATABASE] Error retrieving data: {e}")
                return []
        else:
            print("[DATABASE] No database connection. Please connect to the database first.")
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
            print(f"[DATABASE] Database {db_path} deleted successfully.")
            return True
        else:
            print(f"[DATABASE] File {db_path} not found.")
            return False



    def get_all_tables(self):
        #restituisce l'elenco di tutte le tabelle presenti nel database
        if self.connection:
            try:
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = self.cursor.fetchall()
                return [table[0] for table in tables]
            except sqlite3.Error as e:
                print(f"[DATABASE] Error retrieving tables: {e}")
                return []
        else:
            print("[DATABASE] No database connection. Please connect to the database first.")
            return []


    def generate_grap(self, name):

        if self.connection:
            try:
                name = f'"{name}"'
                self.cursor.execute(f"SELECT * FROM {name}")
                data = self.cursor.fetchall()
                x=[]
                y=[]
                for row in data:
                    x.append(row[0])
                    y.append(row[1])

                print("[DATABASE] Show grap")
                plt.figure(figsize=(10, 5))
                plt.plot(x, y, marker='o', color='b')
                plt.title(name)
                plt.xlabel("time")
                plt.ylabel(name)
                plt.grid()
                plt.show()

            except sqlite3.Error as e:
                print(f"[DATABASE] Error generate_graf: {e}")
                return []
        else:
            print("[DATABASE] No database connection. Please connect to the database first.")
            return None



    def menu(self):
        while True:
            print("\n\n[DATABASE] Database Manager Menu:")
            if self.connection == None:
                print("[DATABASE] Disconnected")
                input("Press Enter to connect to the database...")
                self.connect()
            else:
                print("\t[0] exit")
                tables = self.get_all_tables()
                for i, table in enumerate(tables):
                    print(f'\t[{i+1}]  "{table}"')

                choice = input("Select: ")
                try:
                    choice = int(choice)
                    
                    
                    if choice == 0:
                        self.disconnect()
                        break
                    elif choice <= len(tables):
                        self.generate_grap(tables[choice-1])
                    else:
                        pass
                except Exception as e:  
                    print(e)
                    pass
                

                
