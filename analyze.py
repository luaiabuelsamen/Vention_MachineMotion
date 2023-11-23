import re
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

def hex_to_int(hex_string, type):
    value = int(hex_string, 16)
    
    if type == 'signed integer':
        bit_length = len(hex_string) * 4
        if value >= 2 ** (bit_length - 1):
            return value - (2 ** bit_length)
        return value
    
    elif type == 'unsigned integer':
        return value

    else:
        raise ValueError(f"Unknown type: {type}")

def load_can(log, dbc):
    with open(log, 'r') as file:
        data = {}
        for line in file:
            match = re.search(log_pattern, line)
            if match:
                timestamp_str, pod, data_hex = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                channel = (int(pod) // 10) * 10 
                node = int(pod) - channel
                if channel in dbc:
                    for range, type in dbc[channel].items():
                        nibbles = data_hex.split()[range[0]: range[1]]
                        data_point = (timestamp, hex_to_int(''.join(nibbles[::-1]), type['type']))
                        if type['name'] in data:
                            if node in data[type['name']]:
                                data[type['name']][node].append(data_point)
                            else:
                                data[type['name']][node] = [data_point]
                        else:
                            data[type['name']] = {node : [data_point]}
        return data

def prepare_data(key, node, data):
    times, values = zip(*data[key][node])
    return np.array(times), np.array(values)

def plot_single_scatter(key, ylabel, unit, dataSets):
    for name, data in dataSets.items():
        for node in data[key]:
            plt.clf()
            x, y = prepare_data(key, node, data)
            plt.scatter(x, y, label=key, s=5)
            plt.xlabel('Time')
            plt.ylabel(f'{ylabel} ({unit}) for node {node}')
            plt.title(key)
            plt.legend()
            plt.gcf().autofmt_xdate()
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
            plt.savefig(f'singlefigs/{name}_{key}_{node}.png')

def combined_plot_per_node(keys, nodes, title, unit, dataSets):
    for node in nodes:
        plt.clf()
        for key in keys:
            for name, data in dataSets.items():
                x, y = prepare_data(key, node, data)
                datum = [x, y]
                if unit == 'Normalized':
                    datum[1] = datum[1].astype('float64') / float(max(abs(datum[1])))
                plt.scatter(datum[0], datum[1], label=f'{key} {name}', s=5)
        plt.xlabel('Time')
        plt.ylabel(f'{title} ({unit})')
        plt.title(f'{title} for node {node}')
        plt.legend()
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        plt.savefig(f'combinedfigs/{title}_node_{node}.png')

def combined_plot_per_value(key, nodes, title, unit, dataSets):
    plt.clf()
    for node in nodes:
            for name, data in dataSets.items():
                x, y = prepare_data(key, node, data)
                datum = [x, y]
                if unit == 'Normalized':
                    datum[1] = datum[1].astype('float64') / float(max(abs(datum[1])))
                plt.scatter(datum[0], datum[1], label=f'{name} {node}', s=5)
    plt.xlabel('Time')
    plt.ylabel(f'{title} ({unit})')
    plt.title(f'{title} for nodes {nodes}')
    plt.legend()
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.savefig(f'combinedfigs/{title}_{nodes}.png')

if __name__ == "__main__":
    log_pattern = r'\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})\)  can0  (\d{3})   \[\d\]  ((?:[0-9A-F]{2} ){7}[0-9A-F]{2})'

    dbc = {
        180: {
            (0, 1): {'name': 'statusword', 'type': 'unsigned integer'},
            (2, 3): {'name': 'Actual Torque', 'type': 'signed integer'},
            (4, 7): {'name': 'Control Effort', 'type': 'signed integer'}
        },
        280: {
            (0, 3): {'name': 'Desired Position', 'type': 'signed integer'},
            (4, 7): {'name': 'Actual Position', 'type': 'signed integer'}
        },
        380: {
            (0, 3): {'name': 'Desired Speed', 'type': 'signed integer'},
            (4, 7): {'name': 'Actual Speed', 'type': 'signed integer'}
        }
    }
    
    dataSets = {'loaded': load_can('logs/unloaded.log', dbc), 'unloaded': load_can('logs/loaded.log', dbc)}

    plot_single_scatter('statusword', 'Status', 'unit', dataSets)
    plot_single_scatter('Actual Torque', 'Torque', 'unit', dataSets)
    plot_single_scatter('Control Effort', 'Torque', 'unit', dataSets)
    plot_single_scatter('Desired Position', 'Position', 'unit', dataSets)
    plot_single_scatter('Actual Position', 'Position', 'unit', dataSets)
    plot_single_scatter('Desired Speed', 'Speed', 'unit/s', dataSets)
    plot_single_scatter('Actual Speed', 'Speed', 'unit/s', dataSets)

    combined_plot_per_node(['Actual Torque', 'Control Effort'], [1, 2, 3, 4], 'Effort', 'Normalized', dataSets)
    combined_plot_per_node(['Actual Speed', 'Desired Speed'], [1, 2, 3], 'Speed', 'Unit', dataSets)
    combined_plot_per_node(['Actual Position', 'Desired Position'], [1, 2, 3], 'Position', 'Unit', dataSets)
    
    combined_plot_per_value('Actual Position', [1, 3], 'Position', 'Unit', dataSets)
    combined_plot_per_value('Actual Speed', [1, 3], 'Speed', 'Unit', dataSets)
    combined_plot_per_value('Actual Torque', [1, 3], 'Torque', 'Unit', dataSets)

    combined_plot_per_value('Desired Position', [1, 3], 'Desired Position', 'Unit', dataSets)
    combined_plot_per_value('Desired Speed', [1, 3], 'Desired Speed', 'Unit', dataSets)
    combined_plot_per_value('Control Effort', [1, 3], 'Desired Effort', 'Unit', dataSets)

    #status analysis
    combined_plot_per_value('statusword', [1, 3], 'State change', 'Unit', dataSets)
    combined_plot_per_node(['Actual Torque', 'Control Effort', 'statusword'], [1, 2, 3, 4], 'Effort with status', 'Normalized', dataSets)
    combined_plot_per_node(['Actual Torque', 'Control Effort', 'statusword'], [1, 2, 3, 4], 'Effort with status', 'Normalized', dataSets)
    combined_plot_per_node(['Actual Position', 'Desired Position', 'statusword'], [1, 2, 3], 'Position with Status', 'Normalized', dataSets)
    

    print('Start time unloaded')
    print(dataSets['unloaded']['Desired Position'][3][0])
    print(dataSets['unloaded']['Desired Position'][1][0])
    
    print('End time unloaded')
    print(dataSets['unloaded']['Desired Position'][3][-1])
    print(dataSets['unloaded']['Desired Position'][1][-1])

    print('Start time loaded')
    print(dataSets['loaded']['Desired Position'][3][0])
    print(dataSets['loaded']['Desired Position'][1][0])
    
    print('End time loaded')
    print(dataSets['loaded']['Desired Position'][3][-1])
    print(dataSets['loaded']['Desired Position'][1][-1])

    print('Start time unloaded')
    print(dataSets['unloaded']['Actual Position'][3][0])
    print(dataSets['unloaded']['Actual Position'][1][0])
    
    print('End time unloaded')
    print(dataSets['unloaded']['Actual Position'][3][-1])
    print(dataSets['unloaded']['Actual Position'][1][-1])

    print('Start time loaded')
    print(dataSets['loaded']['Actual Position'][3][0])
    print(dataSets['loaded']['Actual Position'][1][0])
    
    print('End time loaded')
    print(dataSets['loaded']['Actual Position'][3][-1])
    print(dataSets['loaded']['Actual Position'][1][-1])