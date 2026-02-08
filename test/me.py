import requests

BASE_URL = "http://127.0.0.1:8000"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJUZXN0IiwiZXhwIjoxNzcxMTY5NjkyfQ.d_h6sJFgQQ3kf-Hi7QNHnYvDmX6b5Y3tKDFFXMQnH3I"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

response = requests.get(f"{BASE_URL}/users/me", headers=headers)

# 打印响应状态码和内容
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.text}")
