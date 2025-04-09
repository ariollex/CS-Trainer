import pymysql
import json


def get_dict_users():
    query = "SELECT * FROM users;" 
    cursor.execute(query)
    data = cursor.fetchall()
    records = from_data_to_dct(data)
    return records


def save_user(email, password, nickname, verified, verification_code):
    try:
        cursor.execute(
            f"insert into users values ([{email}], {password}, {nickname}, {verified}, {verification_code}) ")
        connection.commit()
    except pymysql.MySQLError as e:
        return f"Ошибка подключения: {e}"
    finally:
        return 'success'


def change_db_users(email, *args):
    try:
        for i in args:
            cursor.execute(
                f"UPDATE users SET {
                    args[i][0]} = '{
                    args[i][1]}' WHERE email = '{email}';")
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
    if len(data) == 1:
        records = {'email': data[0][1],
                   'password': data[0][2],
                   'nickname': data[0][3],
                   'verified': data[0][4],
                   'verification_code': data[0][5]}
    else:
        records = list()
        for i in data:
            new_record = {i[1]: {'email': i[1],
                                 'password': i[2],
                                 'nickname': i[3],
                                 'verified': i[4],
                                 'verification_code': i[5]}}
            records.append(new_record)
    return records


with open('database_user_home.json') as file:
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
