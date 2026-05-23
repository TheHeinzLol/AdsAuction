from time import perf_counter

elapses = []
for i in range(30):
    start_global = perf_counter()
    for _ in range(1000):
 #       start_local = perf_counter()
        for foo in range(100):
            pass
  #      end_local = (perf_counter() - start_local) * 1000
    elapses.append((perf_counter() - start_global) * 1000)
print(f"mean elapse time {sum(elapses)/30}")

