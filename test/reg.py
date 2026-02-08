import requests

# 目标 URL
url = "http://127.0.0.1:8000/register"

# 请求体（请求参数）
data ={
    "username": "Test",
    "password": "secret123",
    "nickname": "John Doe"
}

# 发送 POST 请求
response = requests.post(url, json=data)

# 打印响应状态码和内容
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.text}")
