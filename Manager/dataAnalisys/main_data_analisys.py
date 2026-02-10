from database_manager import DatabaseManager
import random
import time

''' da runnare per debug, non serve nel funzionamento del progetto'''

def main():
    
    DBM = DatabaseManager("data_analisys.db")
    #DBM.delete_database_file()
    #DBM.menu()


    DBM.connect()
    tables = DBM.get_all_tables()
    print(tables)
    

    DBM.add_data("temperature", random.uniform(10, 30), time.time())
    DBM.add_data("v", random.uniform(10, 30), time.time())
    DBM.add_data("v", random.uniform(10, 30), time.time())
    DBM.add_data("v", random.uniform(10, 30), time.time())
    DBM.add_data("temperature", random.uniform(10, 30), time.time())
    DBM.add_data("temperature", random.uniform(10, 30), time.time())
    DBM.add_data("temperature", random.uniform(10, 30), time.time())


    DBM.generate_grap("inverter[W] of device dev003")
    DBM.generate_grap("non_esiste")
    DBM.generate_grap("v")


    DBM.disconnect()



if __name__ == "__main__":
    main()

