import os, subprocess, time,boto3
import logging,binascii,csv
import agent_settings
from scapy.all import *
from datetime import date
import pathlib
import re

capture_running = True

def monitor_file_size(file_name):
    global capture_running
    limit_size = agent_settings.capture_file_size_limit
    size = os.path.getsize(file_name)
    if size >= limit_size:
        print("{0} reached size of {1} bytes".format(file_name, limit_size))
        capture_running = False
        return 0

def upload_to_s3(file_name, bucket):
    object_name = os.path.basename(file_name)
    s3_client = boto3.client('s3', aws_access_key_id=agent_settings.access_key, aws_secret_access_key=agent_settings.secret_access_key)
    try:
        response = s3_client.upload_file(file_name,bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def packets_decoding(capture_file):
    payloads = []
    packets = rdpcap(capture_file)
    for packet in packets:
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst  
        if TCP in packet:
            data = packet[TCP].payload
            data = binascii.hexlify(bytes(data))
            if len(data) != 0:
                tcp_sport=packet.sport
                tcp_dport=packet.dport
                packet_time = packet.time
                payloads.append(tuple((packet_time,src_ip,tcp_sport,dst_ip,tcp_dport,data)))
    print("{0} packets decoded".format(len(payloads)))

    return payloads
   

# --- Create file for packets storing ---   
def file_creation():
    today = date.today()
    abs_path = os.getcwd()
    file_pattern = "[0-9]+\."
    matched_files = []
    for file in os.listdir(abs_path):
        match = re.search(file_pattern, file)
        if match:
            matched_files.append(int(match.group(0)[:-1]))  # works only until 10 (double digits)
    
    if not matched_files:
        capture_file = "capture({0})_0.pcap".format(today) 
        print("Creating empty file {0} for packets capture".format(capture_file))
        open(capture_file, "a").close()
    else: 
        file_num = max(matched_files) + 1
        capture_file = "capture({0})_{1}.pcap".format(today,file_num)
        print("Creating empty file {0} for packets capture".format(capture_file))
        open(capture_file, "a").close()
    return capture_file

def create_packets_csv(packets_array, filename):
    filename = "packets_csv/"+filename[:len(filename) - 5] + ".csv"
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        for packet in packets_array:
            writer.writerow(packet)
    return filename


def main():
    
    global capture_running
    capture_file = file_creation()
    shell_file = "{0}/tcpdump_execute.sh".format(os.getcwd())
    packets_bucket = agent_settings.bucket_name 

    # --- Start capture process ---
    python_proc = subprocess.Popen(["sudo", "sh", shell_file, capture_file])

    
    while capture_running:
        monitor_file_size(capture_file)
        time.sleep(5)
    tcp_proc = subprocess.run(['pgrep', 'tcpdump'],capture_output=True) # get ID of tcpdump process
    tcp_proc = tcp_proc.stdout
    py_subproc = "sudo kill -9 {0}".format(python_proc.pid)
    tcpdump_proc = "sudo kill -9 {0}".format(int(tcp_proc.decode('UTF-8')))
    os.system(py_subproc)
    os.system(tcpdump_proc) 
    print("finished")

    packets_array = packets_decoding(capture_file)
    csv_filename = create_packets_csv(packets_array, capture_file)

    S3_upload_status = upload_to_s3(csv_filename, packets_bucket) 
    if S3_upload_status:
        print("{0} uploaded successfully to {1} S3 bucket".format(csv_filename, packets_bucket))
    else:
        print("{0} upload failed to {1} S3 bucket".format(csv_filename, packets_bucket))



if __name__ == "__main__":
    main()
