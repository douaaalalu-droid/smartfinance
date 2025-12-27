#!/bin/bash

# 1️⃣ إنشاء ملف .gitignore
cat > .gitignore <<EOL
# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# IDE / Editor
.vscode/
.idea/
*.swp
*.swo

# Django logs, env, virtualenv
*.log
*.pot
*.coverage
*.mo
*.env
*.venv
env/
venv/
ENV/

# Static files (optional)
staticfiles/
media/
EOL

echo ".gitignore created."

# 2️⃣ إزالة الملفات غير المرغوب فيها من Git
git rm -r --cached __pycache__ 2>/dev/null
git rm --cached *.pyc 2>/dev/null

echo "Unnecessary files removed from Git tracking."

# 3️⃣ إضافة جميع الملفات المهمة
git add .
echo "All important files added to Git."

# 4️⃣ إنشاء commit
git commit -m "Initial commit: add project with database"
echo "Commit created."

# 5️⃣ ربط المستودع بمستودع GitHub (استبدل الرابط برابط مستودعك)
git remote add origin https://github.com/douaaalalu-droid/smartfinance.git 2>/dev/null
git remote set-url origin https://github.com/douaaalalu-droid/smartfinance.git
echo "GitHub repository linked."

# 6️⃣ رفع المشروع على GitHub
git branch -M main
git push -u origin main
echo "Project pushed to GitHub successfully!"
