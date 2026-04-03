# backend/reset_database_fixed.py
"""
修复版数据库重置脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base, get_db
from app.models import User, Conversation, Thread, Message
from app.core.security import get_password_hash, get_password_hash_simple
from sqlalchemy.orm import Session
import traceback

def reset_database():
    """重置数据库，删除所有表并重新创建"""
    print("正在重置数据库...")
    
    # 删除SQLite数据库文件（如果存在）
    db_path = "sql_app.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除旧数据库文件: {db_path}")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    # 创建15个初始用户
    db: Session = next(get_db())
    try:
        for i in range(1, 16):
            username = f"user{i}"
            email = f"user{i}@example.com"
            
            # 检查用户是否已存在
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if not existing_user:
                # 尝试使用bcrypt，如果失败则使用回退方法
                try:
                    password_hash = get_password_hash("123456")
                except Exception as e:
                    print(f"bcrypt失败，使用回退方法: {e}")
                    password_hash = get_password_hash_simple("123456")
                
                user = User(
                    username=username,
                    email=email,
                    hashed_password=password_hash,
                    is_active=True,
                    need_password_change=True
                )
                db.add(user)
                print(f"✅ 创建用户: {username} (密码: 123456)")
        
        db.commit()
        print("✅ 15个用户初始化完成")
        print("\n初始用户列表:")
        for i in range(1, 16):
            print(f"  user{i}: 密码 123456 (首次登录需修改)")
        
        # 测试登录验证
        print("\n测试密码验证:")
        test_user = db.query(User).filter(User.username == "user1").first()
        if test_user:
            from app.core.security import verify_password
            success = verify_password("123456", test_user.hashed_password)
            print(f"  用户user1密码验证: {'✅ 成功' if success else '❌ 失败'}")
            
    except Exception as e:
        print(f"❌ 用户初始化失败: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("这将重置数据库并删除所有数据。确定吗？(y/N): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("操作已取消")