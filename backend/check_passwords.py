# backend/check_passwords.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session
from app.core.security import verify_password

def check_user_passwords():
    db: Session = next(get_db())
    
    for i in range(1, 6):  # 只检查前5个用户
        username = f"user{i}"
        user = db.query(User).filter(User.username == username).first()
        
        if user:
            print(f"\n用户: {username}")
            print(f"ID: {user.id}")
            print(f"哈希密码长度: {len(user.hashed_password)}")
            print(f"哈希密码前50字符: {user.hashed_password[:50]}")
            print(f"需要修改密码: {user.need_password_change}")
            
            # 测试验证
            test_result = verify_password("123456", user.hashed_password)
            print(f"验证 '123456': {test_result}")
        else:
            print(f"\n用户 {username} 不存在")

if __name__ == "__main__":
    check_user_passwords()