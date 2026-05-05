import matplotlib.pyplot as plt

methods = ["Fixed", "Adaptive", "Q-Learning"]

# 🔴 Replace with YOUR values
avg_wait = [10.54, 0.88, 0.65]
avg_queue = [24.06, 7.09, 5.2]
throughput = [296, 382, 410]

plt.figure()
plt.bar(methods, avg_wait)
plt.title("Average Waiting Time Comparison")
plt.ylabel("Seconds")
plt.show()

plt.figure()
plt.bar(methods, avg_queue)
plt.title("Average Queue Length Comparison")
plt.ylabel("Vehicles")
plt.show()

plt.figure()
plt.bar(methods, throughput)
plt.title("Throughput Comparison")
plt.ylabel("Vehicles")
plt.show()