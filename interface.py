import tkinter as tk
import os

def run_fixed():
    os.system("python fixed_control.py")

def run_adaptive():
    os.system("python adaptive_control.py")

def run_qlearning():
    os.system("python qlearning_control.py")

def show_graph():
    os.system("python compare_result.py")

root = tk.Tk()
root.title("AI Traffic Signal Control System")
root.geometry("400x400")

title = tk.Label(root, text="Traffic Control Dashboard", font=("Arial", 16))
title.pack(pady=20)

btn1 = tk.Button(root, text="Run Fixed Signal", command=run_fixed, width=25)
btn1.pack(pady=10)

btn2 = tk.Button(root, text="Run Adaptive Signal", command=run_adaptive, width=25)
btn2.pack(pady=10)

btn3 = tk.Button(root, text="Run Q-Learning AI", command=run_qlearning, width=25)
btn3.pack(pady=10)

btn4 = tk.Button(root, text="Show Comparison Graph", command=show_graph, width=25)
btn4.pack(pady=20)

root.mainloop()