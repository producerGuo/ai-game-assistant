import os

def fix_workflow_file():
    """修复工作流文件中的批处理语法错误"""
    
    workflow_content = '''name: Build Windows Executable

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyautogui pillow requests mss pyinstaller opencv-python numpy
        
    - name: Build executable
      run: |
        pyinstaller --onefile --windowed --name=AI-Game-Assistant main_enhanced.py
        
    - name: Check dist folder
      shell: cmd
      run: |
        echo "All files in dist folder:"
        dir dist
        
    - name: Upload executable
      uses: actions/upload-artifact@v4
      with:
        name: AI-Game-Assistant-Windows
        path: dist/AI-Game-Assistant.exe
        if-no-files-found: warn
        retention-days: 30
'''

    os.makedirs('.github/workflows', exist_ok=True)
    with open('.github/workflows/build.yml', 'w') as f:
        f.write(workflow_content)
    
    print("✅ 工作流文件已修复")
    
    return True

def main():
    """主函数"""
    fix_workflow_file()
    
    print("修复完成，请提交更改到GitHub:")
    print("git add .github/workflows/build.yml")
    print('git commit -m "Fix batch syntax in workflow"')
    print("git push origin main")

if __name__ == "__main__":
    main()
