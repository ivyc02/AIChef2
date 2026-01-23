import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

api_key = os.getenv("SILICONFLOW_API_KEY")
# 注意：SiliconFlow 官方文档的 Base URL 通常是 https://api.siliconflow.cn/v1
# 我们优先用 .env 里的，如果没配或者配的是 deepseek 专用地址，可能需要调整。
# 这里为了保险，针对生图直接使用硬编码的官方生图 Endpoint 也是一种选择，
# 但为了尊重配置，我们先读 .env，如果 .env 里是 deepseek 的地址 (如 https://api.deepseek.com)，则强制覆盖为 SiliconFlow。
env_base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")

# 简单判断一下，如果 base url 明显是别的厂商的，强行纠正为 SiliconFlow (因为 Kwai-Kolors 只有 SiliconFlow 有)
if "siliconflow" not in env_base_url and "localhost" not in env_base_url:
    print(f"⚠️ Notice: The configured base URL '{env_base_url}' might not support Kwai-Kolors.")
    print("👉 Switching to default SiliconFlow endpoint: https://api.siliconflow.cn/v1")
    base_url = "https://api.siliconflow.cn/v1"
else:
    base_url = env_base_url

if not api_key:
    # 尝试从 user 只有 GEMINI_API_KEY 的情况？不，用户明确有 SILICONFLOW_API_KEY
    print("❌ Error: SILICONFLOW_API_KEY not found in .env")
    exit(1)

print(f"✅ API Key found: {api_key[:5]}******")
print(f"🚀 Testing Image Generation with Kwai-Kolors/Kolors...")

url = f"{base_url.rstrip('/')}/images/generations"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 测试 Prompt: 一道诱人的菜肴
prompt = "Professional food photography of Kung Pao Chicken, peanuts, chili peppers, glossy sauce, 8k resolution, cinematic lighting, appetizing"

payload = {
    "model": "Kwai-Kolors/Kolors",
    "prompt": prompt,
    "image_size": "1024x1024",
    "batch_size": 1,
    "num_inference_steps": 20,
    "guidance_scale": 7.5
}

try:
    print(f"📡 Sending request to {url}...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Success!")
        # print(json.dumps(data, indent=2))
        
        images = data.get("images", [])
        if images:
            print(f"\n🖼️ Generated Image URL: {images[0].get('url')}")
            print("\n(You can copy this URL to a browser to verify the image)")
        else:
            print("⚠️ No image URL found in response.")
    else:
        print(f"\n❌ Failed with status code: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\n❌ Exception occurred: {e}")
