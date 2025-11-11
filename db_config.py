import pymysql

mysql = {
    "host": "localhost",
    "user": "PRM01_HAIC",
    "port" : 3306,
    "password": "hanyangai@",
    "db": "gwai_cymechs",
    "charset": "utf8",
    "autocommit": True ,
    "cursorclass": pymysql.cursors.DictCursor
}