
# coding: utf-8

import subprocess
import csv
import argparse
import time
import numpy as np


def get_process_stdout(inputs):
    process = subprocess.Popen(inputs, stdout=subprocess.PIPE)
    raw = process.stdout.readlines()
    return raw


def get_num_gpu():
    inputs = ['nvidia-smi', '--query-gpu=count', '--format=csv,noheader,nounits']
    stdout = get_process_stdout(inputs)
    gpu_num = int(stdout[0].decode('utf-8').rstrip())
    return gpu_num


def parse_stdout(num_gpu, stdout):
    values = []
    for i in range(num_gpu):
        val_i = float(stdout[i].decode('utf-8').rstrip())
        values.append(val_i)
    return values


def get_gpu_property(num_gpu, query_string):
    inputs = ['nvidia-smi', '--query-gpu='+str(query_string), '--format=csv,noheader,nounits']
    raw_properties = get_process_stdout(inputs)
    properties = parse_stdout(num_gpu, raw_properties)
    return properties


def get_states(num_gpu):
    utilization = get_gpu_property(num_gpu, 'utilization.gpu')
    temperatures = get_gpu_property(num_gpu, 'temperature.gpu')
    fan_usages = get_gpu_property(num_gpu, 'fan.speed')
    power_usages = get_gpu_property(num_gpu, 'power.draw')
    return zip(utilization, temperatures, fan_usages, power_usages)


def write_header(num_gpu, filename="gpu-state.csv"):
    headings = ['GPU_ID', 'UTIL', 'TEMP', 'FAN', 'PWR']
    header = ['TIME']
    for i in range(num_gpu):
        header.extend(headings)
    with open(filename, 'w') as file:
        writer = csv.writer(file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        

def write_state(time, state, filename="gpu-state.csv"):
    with open(filename, 'a') as file:
        writer = csv.writer(file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csv_line = [str(time)]
        for gpu_id, state_details in enumerate(state):
            entry = [str(gpu_id)]
            entry.extend([str(x) for x in state_details])
            csv_line.extend(entry)
        writer.writerow(csv_line)
            

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--time', default='10')
    parser.add_argument('--maxtime', default='600')
    parser.add_argument('--csvfile', default='gpu-state.csv')
    parser.add_argument('--overwrite', default='True')
    args = parser.parse_args()
    return args


def run_gpu_states(num_gpu, time, output_file):
    states = get_states(num_gpu)
    write_state(time, states, output_file)


if __name__ == "__main__":
    # Parse arguments
    args = parse_args()
    
    # Get the number of active GPUs on the node
    num_gpu = get_num_gpu()
    
    # Write out the csv file header if not appending
    if args.overwrite == "True":
        write_header(num_gpu)
    
    # Write state and then wait until time has elapsed
    # Convert time to seconds
    wait_time = float(args.time) * 60.0
    max_time = float(args.maxtime) * 60.0
    
    # Number of iterations required
    iterations = int(np.floor(max_time / wait_time))
    
    # Run first state
    run_gpu_states(num_gpu, 0.0, args.csvfile)
    
    # Loop over iterations
    for i in range(iterations):
        current_time = ((i+1.0) * wait_time) / 60.0
        time.sleep(wait_time)
        run_gpu_states(num_gpu, current_time, args.csvfile)

