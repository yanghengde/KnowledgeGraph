import time
import sys
import requests

# 强制将标准输出设置为 utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE = "http://127.0.0.1:5050"  # 由于 server.py 运行在 5050 或 5050+

def run_benchmark():
    print("开始对已优化的 API 接口进行时延基准测试...\n")
    
    # 1. 测试 /api/stats (Cypher 合并 RTT)
    try:
        start_time = time.time()
        r = requests.get(f"{API_BASE}/api/stats")
        elapsed = (time.time() - start_time) * 1000
        if r.status_code == 200:
            print(f"✅ [SUCCESS] /api/stats 接口测试成功")
            print(f"   └─ 接口耗时: {elapsed:.2f} ms")
            print(f"   └─ 返回数据: {r.json()}")
        else:
            print(f"❌ [FAILED] /api/stats 返回错误: {r.status_code}")
    except Exception as e:
        print(f"❌ [ERROR] 无法连接到 /api/stats: {e}")

    # 2. 测试 /api/graph/overview (热路径零磁盘 I/O 内存缓存)
    try:
        print("\n--------------------------------------------------")
        print("进行 /api/graph/overview 并发/重复加载性能测试:")
        for round_idx in range(1, 4):
            start_time = time.time()
            r = requests.get(f"{API_BASE}/api/graph/overview")
            elapsed = (time.time() - start_time) * 1000
            
            if r.status_code == 200:
                data = r.json()
                node_cnt = len(data.get("nodes", []))
                edge_cnt = len(data.get("edges", []))
                print(f"✅ 第 {round_idx} 轮加载 ➔ 耗时: {elapsed:.2f} ms | 节点数: {node_cnt} | 关系数: {edge_cnt}")
            else:
                print(f"❌ 第 {round_idx} 轮加载失败 ➔ 状态码: {r.status_code}")
    except Exception as e:
        print(f"❌ [ERROR] 无法连接到 /api/graph/overview: {e}")

if __name__ == "__main__":
    run_benchmark()
