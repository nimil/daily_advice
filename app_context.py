from flask import Flask

app = Flask(__name__)

# 蓝图注册将在应用启动时进行，避免循环导入 