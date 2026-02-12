from database_manager import DatabaseManager
import random
import time

''' da runnare per debug o lettura DB, non serve nel funzionamento del progetto'''

def main():
    
    DBM = DatabaseManager("data_analisys.db")
    DBM.delete_database_file()
    #DBM.menu()


    DBM.connect()
    tables = DBM.get_all_tables()
    print(f"tables: {tables}")

    DBM.add_data("v", 14, 12)
    DBM.add_data("v", 14, 12)
    
    DBM.add_data("temperature", random.uniform(10, 30), time.time())
    DBM.add_data("v", random.uniform(10, 30), time.time())
    DBM.add_data("v", random.uniform(10, 30), time.time())
    DBM.add_data("v", random.uniform(10, 30), time.time())
    DBM.add_data("temperature", random.uniform(10, 30), time.time())
    DBM.add_data("temperature", random.uniform(10, 30), time.time())
    DBM.add_data("temperature", random.uniform(10, 30), time.time())


    DBM.generate_grap('inverter[m^2] unità of device 001')
    DBM.generate_grap("non_esiste")
    DBM.generate_grap("v")


    DBM.disconnect()


def init():
    DBM = DatabaseManager("data_analisys.db")
    #DBM.delete_database_file()
    DBM.connect()

    return DBM




if __name__ == "__main__":
    #main()
    DBM = init()


    #DBM.delete_database_file()

    DBM.menu()