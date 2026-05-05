import matplotlib.pyplot as plt

methods = ["Fixed", "Adaptive"]
avg_wait = [18.5, 11.2]      # replace with your actual outputs
avg_queue = [6.8, 3.9]       # replace with your actual outputs
throughput = [120, 165]      # replace with your actual outputs

plt.figure(figsize=(8, 5))
plt.bar(methods, avg_wait)
plt.title("Average Waiting Time Comparison")
plt.ylabel("Seconds")
plt.show()

plt.figure(figsize=(8, 5))
plt.bar(methods, avg_queue)
plt.title("Average Queue Length Comparison")
plt.ylabel("Vehicles")
plt.show()

plt.figure(figsize=(8, 5))
plt.bar(methods, throughput)
plt.title("Throughput Comparison")
plt.ylabel("Vehicles")
plt.show()