"""
نظام فِرَح الرقمي - النواة الأساسية
إصدار 0.1.0 - الهيكل الأساسي
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

class FirahDatabase:
    """فئة لإدارة قاعدة بيانات فِرَح"""
    
    def __init__(self, db_name='firah_system.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
    
    def create_tables(self):
        """إنشاء الجداول الأساسية"""
        cursor = self.conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                fitra_type TEXT DEFAULT 'مستكشف',
                consciousness_level REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                journey_data TEXT DEFAULT '{}'
            )
        ''')
        
        # جدول الدوائر الجماعية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS circles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                circle_type TEXT DEFAULT 'عام',
                collective_intention TEXT,
                admin_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_user_id) REFERENCES users (id)
            )
        ''')
        
        # جدول انضمام المستخدمين للدوائر
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS circle_members (
                circle_id INTEGER,
                user_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role TEXT DEFAULT 'عضو',
                PRIMARY KEY (circle_id, user_id),
                FOREIGN KEY (circle_id) REFERENCES circles (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # جدول الأنشطة والممارسات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS practices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                practice_type TEXT NOT NULL,
                content TEXT,
                duration_minutes INTEGER,
                target_level REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول سجلات الممارسة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS practice_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                practice_id INTEGER,
                duration_actual INTEGER,
                notes TEXT,
                consciousness_before REAL,
                consciousness_after REAL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (practice_id) REFERENCES practices (id)
            )
        ''')
        
        # جدول البصائر والاكتشافات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                circle_id INTEGER,
                title TEXT,
                content TEXT,
                insight_type TEXT,
                is_shared BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (circle_id) REFERENCES circles (id)
            )
        ''')
        
        self.conn.commit()
        print("✅ تم إنشاء جداول قاعدة البيانات بنجاح")

class FirahUser:
    """فئة تمثل مستخدم نظام فِرَح"""
    
    def __init__(self, db: FirahDatabase, user_id=None):
        self.db = db
        self.user_id = user_id
        self.user_data = {}
        
        if user_id:
            self.load_user_data()
    
    def load_user_data(self):
        """تحميل بيانات المستخدم"""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (self.user_id,))
        user = cursor.fetchone()
        
        if user:
            columns = [desc[0] for desc in cursor.description]
            self.user_data = dict(zip(columns, user))
    
    def register(self, username: str, email: str, fitra_type: str = "مستكشف") -> bool:
        """تسجيل مستخدم جديد"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, fitra_type, consciousness_level, journey_data)
                VALUES (?, ?, ?, 1.0, ?)
            ''', (username, email, fitra_type, json.dumps({"بداية_الرحلة": str(datetime.now())})))
            
            self.user_id = cursor.lastrowid
            self.load_user_data()
            self.db.conn.commit()
            
            print(f"✅ تم تسجيل المستخدم {username} بنجاح")
            return True
            
        except sqlite3.IntegrityError:
            print("❌ اسم المستخدم أو البريد الإلكتروني موجود مسبقاً")
            return False
    
    def authenticate(self, username: str) -> bool:
        """مصادقة المستخدم (مبسطة للإيضاح)"""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result:
            self.user_id = result[0]
            self.load_user_data()
            return True
        return False
    
    def update_consciousness(self, new_level: float):
        """تحديث مستوى الوعي"""
        if not self.user_id:
            print("❌ يجب تسجيل الدخول أولاً")
            return
        
        cursor = self.db.conn.cursor()
        cursor.execute(
            'UPDATE users SET consciousness_level = ? WHERE id = ?',
            (new_level, self.user_id)
        )
        self.db.conn.commit()
        self.user_data['consciousness_level'] = new_level
        print(f"✅ تم تحديث مستوى الوعي إلى {new_level}")
    
    def add_insight(self, title: str, content: str, insight_type: str = "بصيرة"):
        """إضافة بصيرة جديدة"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO insights (user_id, title, content, insight_type)
            VALUES (?, ?, ?, ?)
        ''', (self.user_id, title, content, insight_type))
        
        self.db.conn.commit()
        print(f"✅ تم إضافة بصيرة: {title}")
    
    def get_journey_summary(self) -> Dict:
        """الحصول على ملخص الرحلة"""
        cursor = self.db.conn.cursor()
        
        # عدد البصائر
        cursor.execute('SELECT COUNT(*) FROM insights WHERE user_id = ?', (self.user_id,))
        insights_count = cursor.fetchone()[0]
        
        # عدد الممارسات
        cursor.execute('SELECT COUNT(*) FROM practice_logs WHERE user_id = ?', (self.user_id,))
        practices_count = cursor.fetchone()[0]
        
        # متوسط مستوى الوعي
        cursor.execute('SELECT consciousness_level FROM users WHERE id = ?', (self.user_id,))
        consciousness = cursor.fetchone()[0]
        
        return {
            "المستخدم": self.user_data.get('username', 'غير معروف'),
            "نوع_الفطرة": self.user_data.get('fitra_type', 'غير محدد'),
            "مستوى_الوعي": consciousness,
            "عدد_البصائر": insights_count,
            "عدد_الممارسات": practices_count,
            "تاريخ_التسجيل": self.user_data.get('created_at', 'غير معروف')
        }

class ConsciousCircle:
    """فئة تمثل دائرة وعي جماعية"""
    
    def __init__(self, db: FirahDatabase):
        self.db = db
    
    def create_circle(self, name: str, description: str, admin_user_id: int, 
                     circle_type: str = "عام") -> int:
        """إنشاء دائرة جديدة"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO circles (name, description, circle_type, admin_user_id)
            VALUES (?, ?, ?, ?)
        ''', (name, description, circle_type, admin_user_id))
        
        circle_id = cursor.lastrowid
        self.db.conn.commit()
        
        # إضافة المنشئ كعضو
        self.add_member(circle_id, admin_user_id, "منشئ")
        
        print(f"✅ تم إنشاء الدائرة '{name}' بنجاح")
        return circle_id
    
    def add_member(self, circle_id: int, user_id: int, role: str = "عضو"):
        """إضافة عضو للدائرة"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO circle_members (circle_id, user_id, role)
            VALUES (?, ?, ?)
        ''', (circle_id, user_id, role))
        
        self.db.conn.commit()
        print(f"✅ تم إضافة العضو {user_id} للدائرة {circle_id}")
    
    def set_collective_intention(self, circle_id: int, intention: str):
        """تحديد النية الجماعية للدائرة"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            UPDATE circles SET collective_intention = ? WHERE id = ?
        ''', (intention, circle_id))
        
        self.db.conn.commit()
        print(f"✅ تم تحديد النية الجماعية للدائرة {circle_id}")
    
    def get_circle_info(self, circle_id: int) -> Dict:
        """الحصول على معلومات الدائرة"""
        cursor = self.db.conn.cursor()
        
        # معلومات الدائرة
        cursor.execute('SELECT * FROM circles WHERE id = ?', (circle_id,))
        circle = cursor.fetchone()
        
        if not circle:
            return {}
        
        columns = [desc[0] for desc in cursor.description]
        circle_info = dict(zip(columns, circle))
        
        # عدد الأعضاء
        cursor.execute('SELECT COUNT(*) FROM circle_members WHERE circle_id = ?', (circle_id,))
        member_count = cursor.fetchone()[0]
        
        # متوسط مستوى وعي الأعضاء
        cursor.execute('''
            SELECT AVG(u.consciousness_level) 
            FROM circle_members cm 
            JOIN users u ON cm.user_id = u.id 
            WHERE cm.circle_id = ?
        ''', (circle_id,))
        avg_consciousness = cursor.fetchone()[0] or 0
        
        circle_info.update({
            "عدد_الأعضاء": member_count,
            "متوسط_الوعي_الجماعي": round(avg_consciousness, 2)
        })
        
        return circle_info

class FirahPractice:
    """فئة لإدارة الممارسات والتمارين"""
    
    def __init__(self, db: FirahDatabase):
        self.db = db
    
    def add_practice(self, title: str, practice_type: str, content: str, 
                    duration_minutes: int, target_level: float = 1.0):
        """إضافة ممارسة جديدة"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO practices (title, practice_type, content, duration_minutes, target_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, practice_type, content, duration_minutes, target_level))
        
        self.db.conn.commit()
        print(f"✅ تم إضافة الممارسة: {title}")
    
    def log_practice(self, user_id: int, practice_id: int, duration_actual: int,
                    notes: str = "", consciousness_before: float = 1.0):
        """تسجيل ممارسة قام بها مستخدم"""
        
        # حساب تأثير الممارسة (معادلة مبسطة)
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT target_level, duration_minutes FROM practices WHERE id = ?', 
                      (practice_id,))
        practice = cursor.fetchone()
        
        if not practice:
            print("❌ الممارسة غير موجودة")
            return
        
        target_level, target_duration = practice
        
        # حساب مستوى الوعي بعد الممارسة (محاكاة)
        effectiveness = min(duration_actual / target_duration, 1.5)
        consciousness_after = consciousness_before + (target_level * effectiveness * 0.1)
        
        # تسجيل الممارسة
        cursor.execute('''
            INSERT INTO practice_logs 
            (user_id, practice_id, duration_actual, notes, consciousness_before, consciousness_after)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, practice_id, duration_actual, notes, consciousness_before, consciousness_after))
        
        # تحديث مستوى وعي المستخدم
        cursor.execute('UPDATE users SET consciousness_level = ? WHERE id = ?',
                      (consciousness_after, user_id))
        
        self.db.conn.commit()
        
        print(f"✅ تم تسجيل الممارسة. مستوى الوعي الجديد: {consciousness_after:.2f}")
        
        return consciousness_after

# ====== المثال الرئيسي لتشغيل النظام ======
def main_demo():
    """تشغيل نموذج توضيحي للنظام"""
    
    print("\n" + "="*50)
    print("🚀 بدء تشغيل نظام فِرَح الرقمي - الإصدار التجريبي")
    print("="*50 + "\n")
    
    # 1. تهيئة قاعدة البيانات
    db = FirahDatabase('firah_demo.db')
    
    # 2. إنشاء مدير الممارسات
    practice_manager = FirahPractice(db)
    
    # إضافة بعض الممارسات الأساسية
    practices = [
        ("التأمل الفطري", "تأمل", "اجلس بوضعية مريحة وركز على أنفاسك...", 10, 1.5),
        ("الوعي الجماعي", "مجتمع", "اجتمع مع دائرة وانطلقوا في تأمل موجه...", 20, 2.0),
        ("البصيرة اليومية", "تفكر", "اكتب ثلاثة أمور لاحظتها اليوم...", 5, 1.2)
    ]
    
    for practice in practices:
        practice_manager.add_practice(*practice)
    
    # 3. تسجيل مستخدم جديد
    user_manager = FirahUser(db)
    user_manager.register("أحمد_المستكشف", "ahmed@firah.demo", "مستكشف")
    
    # 4. إنشاء دائرة جماعية
    circle_manager = ConsciousCircle(db)
    circle_id = circle_manager.create_circle(
        "دائرة الحكمة الأولى",
        "دائرة لاستكشاف الفطرة وتنمية الوعي الجماعي",
        user_manager.user_id,
        "تأمل"
    )
    
    # 5. تحديد النية الجماعية
    circle_manager.set_collective_intention(circle_id, "نشر السلام الداخلي والتعلم المشترك")
    
    # 6. تسجيل بعض الممارسات
    user_id = user_manager.user_id
    
    # ممارسة التأمل الفطري
    practice_manager.log_practice(
        user_id=user_id,
        practice_id=1,
        duration_actual=15,
        notes="تجربة عميقة مع التركيز على الصمت الداخلي",
        consciousness_before=1.0
    )
    
    # 7. إضافة بصيرة
    user_manager.add_insight(
        title="اكتشاف الفطرة",
        content="اليوم أدركت أن الفطرة هي البوصلة الداخلية التي توجهنا نحو الحكمة",
        insight_type="اكتشاف"
    )
    
    # 8. عرض النتائج
    print("\n" + "="*50)
    print("📊 تقرير الأداء والنتائج")
    print("="*50)
    
    # معلومات المستخدم
    user_summary = user_manager.get_journey_summary()
    print("\n📋 ملخص رحلة المستخدم:")
    for key, value in user_summary.items():
        print(f"  • {key}: {value}")
    
    # معلومات الدائرة
    circle_info = circle_manager.get_circle_info(circle_id)
    print("\n👥 معلومات الدائرة الجماعية:")
    for key, value in circle_info.items():
        if key not in ['description', 'admin_user_id']:
            print(f"  • {key}: {value}")
    
    print("\n" + "="*50)
    print("✅ اكتمل التشغيل التجريبي بنجاح!")
    print("="*50)

# ====== واجهة سطر الأوامر البسيطة ======
def simple_cli():
    """واجهة تفاعلية بسيطة"""
    
    db = FirahDatabase()
    
    print("\n🌟 نظام فِرَح - الواجهة التفاعلية البسيطة")
    print("1. تسجيل مستخدم جديد")
    print("2. تسجيل الدخول (مبسط)")
    print("3. إنشاء دائرة جديدة")
    print("4. إضافة بصيرة")
    print("5. عرض التقارير")
    print("0. خروج")
    
    while True:
        choice = input("\nاختر خياراً (0-5): ")
        
        if choice == "1":
            username = input("اسم المستخدم: ")
            email = input("البريد الإلكتروني: ")
            fitra_type = input("نوع الفطرة (مستكشف/شافع/مبدع/قائد): ")
            
            user = FirahUser(db)
            user.register(username, email, fitra_type)
            
        elif choice == "2":
            username = input("اسم المستخدم: ")
            user = FirahUser(db)
            if user.authenticate(username):
                print(f"✅ مرحباً {username}!")
            else:
                print("❌ المستخدم غير موجود")
                
        elif choice == "3":
            if not hasattr(user, 'user_id'):
                print("❒ يجب تسجيل الدخول أولاً")
                continue
                
            name = input("اسم الدائرة: ")
            description = input("وصف الدائرة: ")
            
            circle = ConsciousCircle(db)
            circle_id = circle.create_circle(name, description, user.user_id)
            print(f"✅ تم إنشاء الدائرة برقم: {circle_id}")
            
        elif choice == "4":
            if not hasattr(user, 'user_id'):
                print("❒ يجب تسجيل الدخول أولاً")
                continue
                
            title = input("عنوان البصيرة: ")
            content = input("محتوى البصيرة: ")
            
            user.add_insight(title, content)
            
        elif choice == "5":
            if not hasattr(user, 'user_id'):
                print("❒ يجب تسجيل الدخول أولاً")
                continue
                
            summary = user.get_journey_summary()
            print("\n📊 تقريرك الشخصي:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
                
        elif choice == "0":
            print("شكراً لاستخدامك نظام فِرَح! 🌟")
            break

# ====== نقطة الدخول الرئيسية ======
if __name__ == "__main__":
    # تشغيل النموذج التوضيحي الكامل
    main_demo()
    
    # أو تشغيل الواجهة التفاعلية البسيطة
    # simple_cli()