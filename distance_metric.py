#Alec Rosentrater
#Feb 2026
#Program that takes a formula and violating trace
#and computes the minimum distance between that trace and a satisfying trace
import subprocess
import sys
import math
import ast

def get_regexs(formula):

    # Run WEST and capture the output
    result = subprocess.run(['./WEST/bin/west', formula], capture_output=True, text=True, check=True)

    # Check the return code
    if result.returncode != 0:
        print("Error: WEST returned nonzero")
        exit(1)

    output =result.stdout.split('=======================================================')[1].strip().split()
    return output

def compute_distance_1_to_1(trace, regex):
    regex_arr = regex.split(',')
    # print("Trace: ", trace)
    distance = 0
    mintime = min(len(trace),len(regex_arr))
    num_APs = len(trace[0])
    # print("Num APs: ", num_APs)
    # print("regex: ", regex_arr)
    # print("regex[0]: ", regex_arr[0])
    for i,AP in enumerate(trace): #Time 
        if i >= mintime:
            return distance
        for j, var in enumerate(AP):
            if regex_arr[i][j] == 's':
                 continue
            elif int(regex_arr[i][j]) == int(trace[i][j]):

                 continue
            else:
                # print("regex_arr[i][j]: ", regex_arr[i][j])
                # print("trace[i][j]: ", trace[i][j])
                distance = distance +1
    return distance

def compute_distance_1_to_many(trace, regexs):
    min_dist = math.inf
    min_regex = ""
    for regex in regexs:
        _placeholder = 0
        distance = compute_distance_1_to_1(trace,regex)
        if distance < min_dist:
            min_dist = distance
            min_regex = regex

    return min_dist, min_regex

#Main

if len(sys.argv) < 3:
    print("Error: not enough arguments")
    exit(1)
else:
    formula = sys.argv[1]
    trace_str = sys.argv[2]
#print("Trace str: ", trace_str)
trace = ast.literal_eval(trace_str)
#formula = "G [0,2] (p0 & p1)"
#trace = [[0,1],[1,0],[1,0]]
print("Formula: ", formula)
print("Trace: ", trace)
regexs = get_regexs(formula)
min_dist, min_regex = compute_distance_1_to_many(trace, regexs)
print("Minium distance: ", min_dist)
print("Regex for minimum distance trace: ", min_regex)