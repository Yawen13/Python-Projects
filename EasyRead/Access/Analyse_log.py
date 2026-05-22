from collections import Counter

with open("access.log","r") as file:
    logs = file.readlines()

total_visits=0
status_counter= Counter()
ip_counter = Counter()

for log in logs:
    parts = log.split()

    ip = parts[2]
    status = parts[-1]

    total_visits += 1

    
    status_counter[status] += 1

    
    ip_counter[ip] += 1

print("===== 日志分析结果 =====")

print(f"\n总访问次数: {total_visits}")

print("\n状态码统计:")
for status, count in status_counter.items():
    print(f"状态码 {status}: {count} 次")

print("\n来源IP统计:")
for ip, count in ip_counter.items():
    print(f"{ip}: {count} 次")


print("\n异常访问检测:")

for ip, count in ip_counter.items():
    if count >= 4:
        print(f"警告: {ip} 访问次数异常 ({count} 次)")