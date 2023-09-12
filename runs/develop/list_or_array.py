import time
import array
import numpy as np

n = 40_000_000

# creation
print("creation")
print("################")
start = time.process_time()
list_ = [0] * n
end = time.process_time()
print("[0]*n", end-start)

# start = time.process_time()
# list_2 = [0 for _ in range(n)]
# end = time.process_time()
# print("list_comprehend", end-start)
# del list_2
# time.sleep(0.2)

# start = time.process_time()
# list_3 = []
# for _ in range(n):
#     list_3.append(0)
# end = time.process_time()
# print("append", end-start)
# del list_3
# time.sleep(0.2)

# start = time.process_time()
# a = array.array('l')
# for _ in range(n):
#     a.append(0)
# end = time.process_time()
# print("array append", end-start)

start = time.process_time()
a = array.array("l", [0] * n)
end = time.process_time()
print("array from list", end-start)

# start = time.process_time()
# nm = np.array([], dtype="int32")
# for _ in range(n):
#     np.append(nm, 0)
# end = time.process_time()
# print("numpy append", end-start)


start = time.process_time()
nm = np.array([0] * n, dtype="int32")
end = time.process_time()
print("numpy from list", end-start)

print("list size: ", list_.__sizeof__(), n * list_[0].__sizeof__())
print("array size: ", a.__sizeof__(), n * a[0].__sizeof__())
print("np size: ", nm.__sizeof__(), n * nm[0].__sizeof__())



# looping
print()
print("looping")
print("##########")

start = time.process_time()
for i in list_:
    i += 1
end = time.process_time()
print("list loop", end-start)

start = time.process_time()
for i in a:
    i += 1
end = time.process_time()
print("array loop", end-start)

start = time.process_time()
for i in nm:
    i += 1
end = time.process_time()
print("numpy loop", end-start)


start = time.process_time()
for i in list_:
    list_[i] += 1
end = time.process_time()
print("list add inplace", end-start)

start = time.process_time()
for i in a:
    a[i] += 1
end = time.process_time()
print("array add inplace", end-start)

start = time.process_time()
for i in nm:
    nm[i] += 1
end = time.process_time()
print("numpy add inplace", end-start)

start = time.process_time()
nm += 1
end = time.process_time()
print("numpy add inplace no loop", end-start)


"""
creation
################
[0]*n 0.140625
array from list 1.921875
numpy from list 2.0625
list size:  320000040 960000000
array size:  160000064 960000000
np size:  160000112 1120000000

looping
##########
list loop 3.015625
array loop 3.0625
numpy loop 6.515625
list add inplace 5.703125
array add inplace 8.9375
numpy add inplace 17.453125
numpy add inplace no loop 0.03125

"""