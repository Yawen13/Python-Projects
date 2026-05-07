import sqlite3
import subprocess
import socket
import threading
import platform

def init_db():
    conn = sqlite3.connect("device.db")
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS device (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        ip TEXT,
        model TEXT,
        position TEXT,
        status TEXT,
        remark TEXT
    )''')

    conn.commit()
    conn.close()


def add_device(name, type, ip, model, position, status, remark):
   
    status = check_device_status(ip)
    
    conn = sqlite3.connect("device.db")
    cur = conn.cursor()
    cur.execute('''
    INSERT INTO device (name, type, ip, model, position, status, remark)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, type, ip, model, position, status, remark))
    conn.commit()
    conn.close()


def get_all_devices():
    conn = sqlite3.connect("device.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM device")
    devices = cur.fetchall()
    conn.close()
    return devices


def delete_device(id):
    conn = sqlite3.connect("device.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM device WHERE id=?", (id,))
    conn.commit()
    conn.close()


def update_device(id, name, type, ip, model, position, status, remark):
    status = check_device_status(ip)
    
    conn = sqlite3.connect("device.db")
    cur = conn.cursor()
    cur.execute('''
    UPDATE device SET
    name=?, type=?, ip=?, model=?, position=?, status=?, remark=?
    WHERE id=?
    ''', (name, type, ip, model, position, status, remark, id))
    conn.commit()
    conn.close()

def check_device_status(ip):
    try:
        cmd = ["ping", "-n", "1", "-w", "300", ip]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if "Reply from" in res.stdout or "来自" in res.stdout:
            return "Online"
        else:
            return "Offline"
    except:
        return "Offline"
    

def refresh_all_device_status():
    conn = sqlite3.connect("device.db")
    cur = conn.cursor()
    cur.execute("SELECT id, ip FROM device")
    all_dev = cur.fetchall()

    for dev_id, ip in all_dev:
        new_status = check_device_status(ip)
        cur.execute("UPDATE device SET status = ? WHERE id = ?", (new_status, dev_id))

    conn.commit()
    conn.close()

def get_local_prefix():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("1.1.1.1", 80))
        local_ip = s.getsockname()[0]
    except:
        local_ip = "192.168.1.2"
    s.close()
    prefix = ".".join(local_ip.split(".")[:3]) + "."
    return prefix

def scan_lan_devices():
    prefix = get_local_prefix()
    online_ips = []
    def ping_one(ip):
        if check_device_status(ip) == "Online":
            online_ips.append(ip)
    threads = []
    for i in range(1, 255):
        ip = prefix + str(i)
        t = threading.Thread(target=ping_one, args=(ip,))
        t.daemon = True
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return online_ips