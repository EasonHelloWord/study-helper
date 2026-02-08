import requests

# 目标 URL
url = "http://127.0.0.1:8000/login"

# 请求体（form-data 格式：application/x-www-form-urlencoded）
data ={
    "username": "Test",
    "password": "secret123"
}

# 发送 POST 请求（自动设置 Content-Type: application/x-www-form-urlencoded）
response = requests.post(url, data=data)

# 打印响应状态码和内容
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.text}")
