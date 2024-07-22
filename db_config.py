import pymysql

host = "danilcwr.beget.tech"
user = "danilcwr_ds_bot"
db_name = "danilcwr_ds_bot"
password = "Danil890408"


def connect() -> pymysql.connect:
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name
        )
        # print("=============== MySQL DB successfully connected ===============")
        # print("=" * 69 + "\n")

        return connection

    except Exception as ex:
        print("=============== MySQL DB connection failed ===============")
        print(ex)


def execute_query(query):
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            connection.commit()
            print(f"{query} successfully executed!")
    finally:
        connection.close()


def read_query(query):
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            return rows
    finally:
        connection.close()
