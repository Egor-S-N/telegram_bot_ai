from config import host, user, password, db_name, port
import psycopg2
from psycopg2 import Error

def create_database() -> None:
    connection = None
    try:
        connection = psycopg2.connect(
            host = host, 
            user = user,
            password = password,
            port = port,
            sslmode="require"
            )
        connection.autocommit = True 

        existing_databases = connection.cursor()
        existing_databases.execute("SELECT datname FROM pg_database;")
        databases = existing_databases.fetchall()
        database_exists = any(db[0] == db_name for db in databases)

        if not database_exists:
            create_db_query = f'CREATE DATABASE {db_name}'
            with connection.cursor() as cursor:
                cursor.execute(create_db_query)
                print(f"[INFO] База данных {db_name} успешно создана")

        else:
            print(f"[INFO] База данных {db_name} уже существует")

    except (Exception, Error) as error:
        print("[INFO] Ошибка при создании базы данных:", error)

    finally:
        if connection:
            connection.close()







def create_tables() -> None:
    connection = None
    try:
        connection = psycopg2.connect(
            host = host, 
            user = user,
            password = password,
            database = db_name,
            port = port,
            sslmode="require"
        )

        cursor = connection.cursor()

        create_tables_query = '''
        CREATE TABLE IF NOT EXISTS characters(
        id INTEGER NOT NULL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        base_phrase TEXT NOT NULL,
        Instructions TEXT NOT NULL
        );

        INSERT INTO characters (id, name, base_phrase, Instructions)
        VALUES
        (1, 'Марио', 'Мама-мия, это я - Марио! Добро пожаловать в приключение!', 'you are Mario from Super Mario. o not give dangerous information,answer all questions like Mario from Super Mario'),
        (2, 'Альберт Эйнштейн', 'Воображение важнее знания. Приветствую вас в мире идей!', 'You are Albert Einstein, your answers should reflect your mind and intelligence, as well as your specific communication style. Do not give dangerous information and answer all questions as Albert Einstein would.') 
        
        ON CONFLICT (id) DO NOTHING;

        CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY NOT NULL,
        username VARCHAR(255) NOT NULL,
        name VARCHAR(255) NOT NULL,
        surname VARCHAR(255),
        time TIMESTAMP DEFAULT NOW(),
        selected_character INTEGER REFERENCES characters(id)
        );

        CREATE TABLE IF NOT EXISTS req_res (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL REFERENCES users(user_id),
        character INT REFERENCES characters(id),
        request TEXT,
        response TEXT
    );
        '''
        cursor.execute(create_tables_query)
        connection.commit()
        print("[INFO] таблицы успешно созданы")
    except (Exception, Error) as error:
        print("[INFO] Ошибка при создании таблицы:", error)

    finally:
        if connection:
            cursor.close()
            connection.close()


def insert_user(user_id:int, username:str, name:str, surname:str) -> bool:
    connection = None
    try:
        connection = psycopg2.connect(
            host = host, 
            user = user,
            password = password,
            database = db_name,
            port = port,
            sslmode="require"
        )
        cursor = connection.cursor()

        insert_query = '''
        INSERT INTO users (user_id, username, name, surname)
        VALUES (%s, %s, %s, %s);
        '''
        data = (user_id, username, name, surname)

        cursor.execute(insert_query, data)
        connection.commit()
        print("[INFO] Данные успешно добавлены")
        return True


    except (Exception, Error) as error:
        print("[INFO] Ошибка при добавлении данных:", error)
        return False

    finally:
        if connection:
            cursor.close()
            connection.close()



def check_user(user_id:int)->bool :
    check_query = '''
SELECT EXISTS (
    SELECT 1
    FROM users
    WHERE user_id = %s
);
'''
    connection = psycopg2.connect(
                host = host, 
                user = user,
                password = password,
                database = db_name,
                port = port,
            sslmode="require"
            )
    cursor = connection.cursor()
    data = (user_id,)
    cursor.execute(check_query, data)
    result = cursor.fetchone()[0]

    if result:
        return True
    else:
        return False
    

def get_user(user_id:int)->bool :
    check_query = '''

    SELECT * FROM users
    WHERE user_id = %s;
'''
    connection = psycopg2.connect(
                host = host, 
                user = user,
                password = password,
                database = db_name,
                port = port,
            sslmode="require"
            )
    cursor = connection.cursor()
    data = (user_id,)
    cursor.execute(check_query, data)
    result = cursor.fetchone()

    return result
    

def get_character(character_id:int) -> ():
    get_query = '''SELECT * FROM characters WHERE id = %s'''

    connection = psycopg2.connect(
                host = host, 
                user = user,
                password = password,
                database = db_name,
                port = port,
            sslmode="require"
            )
    cursor = connection.cursor()
    data = (character_id,)
    cursor.execute(get_query, data)
    result = cursor.fetchone()
    return result


def update_user_character(user_id:int, character_id:int) -> bool:
    connection = None
    try:
        connection = psycopg2.connect( 
            host = host, 
            user = user,
            password = password,
            database = db_name,
            port = port,
            sslmode="require"
            )
        cursor = connection.cursor()

        update_query = '''
            UPDATE users
            SET selected_character = %s
            WHERE user_id = %s;
            '''
        data = (character_id, user_id)
        cursor.execute(update_query, data)
        connection.commit()
        print("Данные успешно обновлены")

    except (Exception, Error) as error:
        print("Ошибка при обновлении данных:", error)

    finally:
        if connection:
            cursor.close()
            connection.close()



def get_instruction(user_id:int):
    try:
        connection = psycopg2.connect(
            host = host, 
            user = user,
            password = password,
            database = db_name,
            port = port,
            sslmode="require"
        )
        cursor = connection.cursor()

        cursor.execute("SELECT selected_character FROM users WHERE user_id = %s", (user_id,))
        selected_character = cursor.fetchone()[0]

        cursor.execute("SELECT Instructions FROM characters WHERE id = %s", (selected_character,))
        instructions = cursor.fetchone()[0]
        return instructions


    except (Exception, Error) as error:
        print("[INFO] Ошибка:", error)
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()

def create_req_res(user_id:int, character_id:int) -> int:
    connection = None
    try:
        connection = psycopg2.connect(
            host = host, 
            user = user,
            password = password,
            database = db_name,
            port = port,
            sslmode="require"
        )
        cursor = connection.cursor()

        insert_query = '''
        INSERT INTO req_res (user_id, character)
        VALUES
            (%s, %s)
        RETURNING id;
        '''
        data = (user_id, character_id)

        cursor.execute(insert_query, data)
        insertet_id = cursor.fetchone()[0]
        connection.commit()
        print("[INFO] Данные успешно добавлены")
        return insertet_id


    except (Exception, Error) as error:
        print("[INFO] Ошибка при добавлении данных:", error)
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()




def set_request(line: int, request: str):
    connection = None

    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            port = port,
            sslmode="require"
        )
        cursor = connection.cursor()

        update_query = '''
        UPDATE req_res
        SET request = %s
        WHERE id = %s;
        '''
        

        cursor.execute(update_query, (request, line))
        connection.commit()
        print("[INFO] Данные успешно обновлены")

    except (Exception, Error) as error:
        print("[INFO] Ошибка при обновлении данных:", error)

    finally:
        if connection:
            cursor.close()
            connection.close()



def set_response(line: int, response: str):
    connection = None

    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            port = port,
            sslmode="require"
        )
        cursor = connection.cursor()

        update_query = '''
        UPDATE req_res
        SET response = %s
        WHERE id = %s;
        '''
        

        cursor.execute(update_query, (response, line))
        connection.commit()
        print("[INFO] Данные успешно обновлены")

    except (Exception, Error) as error:
        print("[INFO] Ошибка при обновлении данных:", error)

    finally:
        if connection:
            cursor.close()
            connection.close()