import subprocess
import sys

def install_packages():
    packages = [
        "pyautogui",
        "pillow",
        "requests",
        "mss"
        "opencv-python"
        "numpy"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"✗ {package} 安装失败")

if __name__ == "__main__":
    print("正在安装依赖包...")
    install_packages()
    print("依赖包安装完成!")
