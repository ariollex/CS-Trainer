import pymysql
import json


def get_dict_users():
    query = f"SELECT * FROM users;"  # Запрос для получения всех данных из таблицы
    cursor.execute(query)
    data = cursor.fetchall()
    records = from_data_to_dct(data)
    return records

def save_user(email, password, nickname, verified, verification_code):
    try:
        query = f"""insert users(email, password, nickname, verified, verification_code)
            values ('{email}', '{password}', '{nickname}', {verified}, '{verification_code}')"""
        cursor.execute(query)
        connection.commit()
    except pymysql.MySQLError as e:
        return f"Ошибка подключения: {e}"
    finally:
        return 'success'

def change_db_users(email, *args):
    try:
        for i in args:
            query = f"""UPDATE users 
                SET {i[0]} = '{i[1]}'
                WHERE email = '{email}';"""
            cursor.execute(query)
        connection.commit()
    except pymysql.MySQLError as e:
        return f"Ошибка подключения: {e}"
    finally:
        return 'success'

def user_information(email):
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}';")
    data = cursor.fetchall()
    if len(data) == 0:
        return 'not_found'
    if len(data) > 1:
        return 'found_more'
    return from_data_to_dct(data)

def from_data_to_dct(data):
    records = dict()
    for i in data:
        records[i[1]] = {'email': i[1],
               'password': i[2],
               'nickname': i[3],
               'achievement': i[4],
               'avatar': i[5],
               'fundamentals': i[6],
               'algorithms': i[7],
               'verified': i[8],
               'verification_code': i[9]}
    return records

with open('database_user.json') as file:
    file_json_data = json.load(file)
try:
    connection = pymysql.connect(
        host=file_json_data['host'],
        user=file_json_data['user'],
        password=file_json_data['password'],
        database=file_json_data['database']
    )
    cursor = connection.cursor()
except pymysql.MySQLError as e:
    print(f"Ошибка подключения: {e}")
# finally:
#     if 'connection' in locals():
#         connection.close()