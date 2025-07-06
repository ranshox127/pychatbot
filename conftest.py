# tests/conftest.py
import pytest
import pymysql

# 這是測試用的資料庫設定
TEST_DB_CONFIG = {
    "host": "140.115.53.151",
    "user": "kslab",
    "password": "Kslab35356!",
    "db": "linebot_test", # <<<<< 指向測試資料庫
    "cursorclass": pymysql.cursors.DictCursor
}

@pytest.fixture(scope="session")
def db_connection():
    """建立一個在整個測試期間共享的資料庫連線"""
    conn = pymysql.connect(**TEST_DB_CONFIG)
    
    # 在所有測試開始前，可以在這裡建立所有 table (如果測試資料庫是空的)
    # create_all_tables(conn)
    
    yield conn
    
    # 在所有測試結束後，關閉連線
    conn.close()

@pytest.fixture()
def db_session(db_connection):
    """
    為每一個測試函式提供一個 transaction，並在結束後 rollback。
    這就是實現隔離的關鍵！
    """
    # 開始一個 transaction
    db_connection.begin()
    
    yield db_connection # 將帶有 transaction 的連線物件交給測試函式使用
    
    # 測試結束後，回滾 transaction，清除所有測試資料
    db_connection.rollback()