import requests
import json

# API 基础 URL
BASE_URL = "http://127.0.0.1:8000"

# 1. 先登录获取认证token
def login():
    """登录获取token"""
    login_url = f"{BASE_URL}/login"
    login_data = {
        "username": "Test",
        "password": "secret123"
    }
    response = requests.post(login_url, data=login_data)
    print(f"登录状态码: {response.status_code}")
    print(f"登录响应: {response.text}\n")
    
    if response.status_code == 200:
        try:
            result = response.json()
            return result.get("access_token")
        except:
            return None
    return None

# 2. 测试上传题目（纯文本）
def test_upload_text_problem(token):
    """测试上传纯文本题目"""
    upload_url = f"{BASE_URL}/problems/upload"
    
    # 准备form-data数据
    data = {
        "raw": "求解方程：2x + 3 = 7",
        "source_type": "text",
        "subject": "数学",
        "course": "高等数学",
        "problem_type": "解答",
        "knowledge_tags": json.dumps(["一次方程", "代数"]),
        "difficulty": 2,
        "tags": json.dumps(["基础", "必做"]),
        "notes": "这是一个基础的一次方程问题"
    }
    
    # 设置认证header
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(upload_url, data=data, headers=headers)
    print(f"上传文本题目状态码: {response.status_code}")
    print(f"上传响应: {response.text}\n")
    return response

# 3. 测试上传题目（仅必需字段）
def test_upload_minimal_problem(token):
    """测试上传最少参数的题目"""
    upload_url = f"{BASE_URL}/problems/upload"
    
    data = {
        "raw": "这是最简单的题目"
    }
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(upload_url, data=data, headers=headers)
    print(f"上传最少参数题目状态码: {response.status_code}")
    print(f"上传响应: {response.text}\n")
    return response

# 4. 测试上传题目（带文件）
def test_upload_file_problem(token, file_path):
    """测试上传带文件的题目"""
    upload_url = f"{BASE_URL}/problems/upload"
    
    data = {
        "source_type": "image",
        "subject": "物理",
        "course": "力学",
        "problem_type": "选择",
        "knowledge_tags": json.dumps(["牛顿定律", "力"]),
        "difficulty": 3,
        "tags": json.dumps(["重要", "常考"]),
        "notes": "图片形式的物理题"
    }
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 上传文件
    try:
        with open(file_path, 'rb') as f:
            files = {
                "file": f
            }
            response = requests.post(upload_url, data=data, files=files, headers=headers)
            print(f"上传文件题目状态码: {response.status_code}")
            print(f"上传响应: {response.text}\n")
            return response
    except FileNotFoundError:
        print(f"文件不存在: {file_path}\n")
        return None

# 5. 测试错误情况（缺少必填参数）
def test_upload_error_no_content(token):
    """测试错误情况：既不提供raw也不提供file"""
    upload_url = f"{BASE_URL}/problems/upload"
    
    data = {
        "subject": "数学",
        "course": "高等数学"
    }
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(upload_url, data=data, headers=headers)
    print(f"测试缺少必填参数状态码: {response.status_code}")
    print(f"响应: {response.text}\n")
    return response

# 6. 测试错误情况（无效的JSON标签）
def test_upload_error_invalid_json(token):
    """测试错误情况：提供无效的JSON格式标签"""
    upload_url = f"{BASE_URL}/problems/upload"
    
    data = {
        "raw": "题目内容",
        "knowledge_tags": "这不是有效的JSON"  # 无效的JSON
    }
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(upload_url, data=data, headers=headers)
    print(f"测试无效JSON标签状态码: {response.status_code}")
    print(f"响应: {response.text}\n")
    return response

# 主函数
if __name__ == "__main__":
    print("=" * 60)
    print("开始测试 /problems/upload API")
    print("=" * 60 + "\n")
    
    # 第一步：登录获取token
    token = login()
    
    if not token:
        print("登录失败，无法继续测试")
        exit(1)
    
    print("=" * 60)
    print("开始各个测试用例")
    print("=" * 60 + "\n")
    
    # # 测试 1: 上传纯文本题目
    # print("【测试 1】上传纯文本题目（完整参数）")
    # print("-" * 60)
    # test_upload_text_problem(token)
    
    # # 测试 2: 上传最少参数题目
    # print("【测试 2】上传最少参数题目（仅raw）")
    # print("-" * 60)
    # test_upload_minimal_problem(token)
    
    # 测试 3: 上传带文件的题目
    print("【测试 3】上传带文件的题目")
    print("-" * 60)
    test_upload_file_problem(token, "problem.png")
    
    # # 测试 4: 错误情况 - 缺少必填参数
    # print("【测试 4】错误情况：缺少必填参数（raw和file都为空）")
    # print("-" * 60)
    # test_upload_error_no_content(token)
    
    # # 测试 5: 错误情况 - 无效的JSON标签
    # print("【测试 5】错误情况：知识点标签JSON格式无效")
    # print("-" * 60)
    # test_upload_error_invalid_json(token)
    
    # print("=" * 60)
    # print("测试完成！")
    # print("=" * 60)
