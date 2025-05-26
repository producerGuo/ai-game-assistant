import os
import subprocess

def build_executable():
    print("开始打包程序...")
    
    # PyInstaller命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=AI游戏助手",
        "--icon=icon.ico",  # 如果有图标文件
        "main.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ 程序打包成功!")
        print("可执行文件位于: dist/AI游戏助手.exe")
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")

if __name__ == "__main__":
    # 确保已安装pyinstaller
    try:
        subprocess.run(["pip", "install", "pyinstaller"], check=True)
    except:
        print("PyInstaller安装失败")
        exit(1)
    
    build_executable()
