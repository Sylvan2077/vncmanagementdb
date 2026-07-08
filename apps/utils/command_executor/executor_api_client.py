import requests

class ExecutorAPIClient:
    def __init__(self, base_url="http://localhost:10001"):
        self.base_url = base_url.rstrip("/")

    def set_base_url(self, base_url):
        self.base_url = base_url.rstrip("/")

    def execute_shell_command(self, command):
        endpoint = f"{self.base_url}/execute_command"
        response = requests.post(endpoint, json={"command": command})
        return response.json()

# 使用示例
if __name__ == "__main__":
    base_url = "http://your-fastapi-url"  # 替换成你的 FastAPI 服务的地址
    client = ExecutorAPIClient(base_url)

    command = "ls -l"
    result = client.execute_shell_command(command)

    print("Standard Output:\n", result["output"])
    print("Standard Error:\n", result["error"])
