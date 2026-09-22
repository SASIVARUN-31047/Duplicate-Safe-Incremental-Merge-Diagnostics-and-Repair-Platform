import os

with open('backend/requirements.txt', 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')

# Remove any weird null bytes
content = content.replace('\x00', '')
if 'pandas' not in content:
    content += "\npandas>=2.0.0\nopenpyxl>=3.1.0\npython-multipart>=0.0.9\n"

with open('backend/requirements.txt', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
