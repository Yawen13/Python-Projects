import tkinter as tk
from tkinter import ttk, messagebox
from database import add_device, get_all_devices, update_device, delete_device, refresh_all_device_status, scan_lan_devices

class DeviceSystemUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Device Record System")
        self.root.geometry("1000x650")

        # 记录当前选中设备ID
        self.selected_id = None

        self.create_input_area()
        self.create_button_area()
        self.create_table_area()
        # 绑定表格点击事件：选中自动回填
        self.table.bind("<<TreeviewSelect>>", self.fill_selected_data)
        self.load_data()

    def create_input_area(self):
        frame_input = tk.Frame(self.root)
        frame_input.pack(pady=10)

        labels_text = [
            "Device Name:", "Device Type:", "IP Address:",
            "Model:", "Position:", "Status:", "Remark:"
        ]
        self.entry_list = []

        for idx, text in enumerate(labels_text):
            tk.Label(frame_input, text=text).grid(row=idx, column=0, padx=5, pady=3, sticky="w")
            entry = tk.Entry(frame_input, width=30)
            entry.grid(row=idx, column=1, padx=5, pady=3)
            self.entry_list.append(entry)

    def create_button_area(self):
        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=5)

        ttk.Button(frame_btn, text="Add", command=self.add_data).grid(row=0, column=0, padx=8)
        ttk.Button(frame_btn, text="Update", command=self.update_data).grid(row=0, column=1, padx=8)
        ttk.Button(frame_btn, text="Delete", command=self.delete_data).grid(row=0, column=2, padx=8)
        ttk.Button(frame_btn, text="Refresh", command=self.load_data).grid(row=0, column=3, padx=8)
        ttk.Button(frame_btn, text="Scan LAN", command=self.scan_lan_ip).grid(row=0, column=4, padx=8)
        

    def create_table_area(self):
        column_names = ["ID", "Name", "Type", "IP", "Model", "Position", "Status", "Remark"]
        self.table = ttk.Treeview(self.root, columns=column_names, show="headings")

        for col in column_names:
            self.table.heading(col, text=col)
            self.table.column(col, width=110)

        self.table.pack(expand=True, fill="both", padx=15, pady=15)

    # 选中表格行 → 自动回填到输入框
    def fill_selected_data(self, event):
        selected = self.table.focus()
        if not selected:
            return
        row_data = self.table.item(selected)["values"]
        self.selected_id = row_data[0]
        # 依次填入输入框（跳过ID，从第2项开始）
        for i in range(7):
            self.entry_list[i].delete(0, tk.END)
            self.entry_list[i].insert(0, str(row_data[i+1]))

    def load_data(self):
    # 关键：先一键全局刷新所有设备状态
     refresh_all_device_status()
    
    # 再重新加载表格
     for row in self.table.get_children():
        self.table.delete(row)
     data_list = get_all_devices()
     for row in data_list:
        self.table.insert("", "end", values=row)

    def add_data(self):
        data = [e.get().strip() for e in self.entry_list]
        if not data[0]:
            messagebox.showwarning("Warning", "Device Name cannot be empty.")
            return
        add_device(*data)
        self.load_data()
        self.clear_entry()
        self.selected_id = None
        messagebox.showinfo("Success", "Device added successfully.")

    def update_data(self):
        if not self.selected_id:
            messagebox.showwarning("Warning", "Please select a device first.")
            return
        data = [e.get().strip() for e in self.entry_list]
        if not data[0]:
            messagebox.showwarning("Warning", "Device Name cannot be empty.")
            return
        update_device(self.selected_id, *data)
        self.load_data()
        self.clear_entry()
        self.selected_id = None
        messagebox.showinfo("Success", "Device updated successfully.")

    def delete_data(self):
        selected = self.table.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a device first.")
            return
        device_id = self.table.item(selected)["values"][0]
        delete_device(device_id)
        self.load_data()
        self.clear_entry()
        self.selected_id = None
        messagebox.showinfo("Success", "Device deleted successfully.")

    def clear_entry(self):
        for entry in self.entry_list:
            entry.delete(0, tk.END)

# 一键扫描局域网设备
    def scan_lan_ip(self):
      import threading
      def run_scan():
        try:
            messagebox.showinfo("Scanning", "Scanning LAN, please wait...")
            online_list = scan_lan_devices()
            if online_list:
                for ip in online_list:
                    add_device("LAN_Device", "Device", ip, "Auto", "LAN", "", "Auto Scan")
            self.load_data()
            messagebox.showinfo("Success", f"Found: {len(online_list)} online devices")
        except:
            messagebox.showerror("Error", "Scan failed")
    
      threading.Thread(target=run_scan).start()


if __name__ == "__main__":
    main_window = tk.Tk()
    app = DeviceSystemUI(main_window)
    main_window.mainloop()