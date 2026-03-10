"""
数据库初始化脚本 - 修复版
创建优化的表结构和索引
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app import models
from sqlalchemy import text  # 导入text函数
import sqlite3

def init_database(drop_existing: bool = False):
    """初始化数据库"""
    print("正在初始化数据库...")
    
    db_path = "sql_app.db"
    
    if drop_existing and os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除旧数据库: {db_path}")
    
    # 创建新表
    Base.metadata.create_all(bind=engine)
    
    # 启用外键约束和优化设置
    with engine.connect() as conn:
        # SQLite优化设置 - 使用text()包装SQL语句
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.execute(text("PRAGMA journal_mode = WAL"))
        conn.execute(text("PRAGMA synchronous = NORMAL"))
        conn.execute(text("PRAGMA cache_size = -2000"))
        conn.execute(text("PRAGMA temp_store = MEMORY"))
        conn.commit()
    
    print("数据库初始化完成")
    print("优化设置已应用:")
    print("  - 外键约束: 启用")
    print("  - 日志模式: WAL")
    print("  - 同步模式: NORMAL")
    print("  - 缓存大小: 2MB")
    print("  - 临时存储: 内存")
    
    # 验证表结构
    print("\n数据库表结构验证:")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        
        for table in tables:
            print(f"  - {table}")
            
            # 获取表的列信息
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            columns = result.fetchall()
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = "NOT NULL" if col[3] else "NULL"
                pk = "PRIMARY KEY" if col[5] else ""
                print(f"      {col_name} {col_type} {not_null} {pk}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="初始化数据库")
    parser.add_argument("--drop", action="store_true", help="删除已存在的数据库")
    
    args = parser.parse_args()
    
    confirm = input("这将初始化数据库。确定吗？(y/N): ")
    if confirm.lower() == 'y':
        try:
            init_database(args.drop)
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            print("\n建议的解决方案:")
            print("1. 确保已安装SQLAlchemy: pip install sqlalchemy")
            print("2. 确保数据库文件没有被其他程序占用")
            print("3. 尝试手动删除数据库文件: rm backend/sql_app.db")
    else:
        print("操作已取消")