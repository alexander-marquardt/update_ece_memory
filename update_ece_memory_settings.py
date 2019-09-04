import json
import subprocess
import datetime
import shlex
import re

# Set the following to False for "real" execution, otherwise this script will simulate a curl request by reading locally
# stored json
TEST_MODE=True

ADMIN="admin"
ADMIN_PWD="XXXXX"
ECE_URL="https://ECE_endpoint:12443"

# Set the memory for each component based on recommendations at
# https://www.elastic.co/guide/en/cloud-enterprise/current/ece-topology-example3.html
COMPONENTS= (("allocators", "allocator", "ALLOCATOR_MEMORY_OPTIONS", "1023M"),
             ("zookeeper-servers", "zookeeper", "ZOOKEEPER_MEMORY_OPTIONS", "4095M"),
             ("proxies", "proxy", "PROXY_MEMORY_OPTIONS", "8191M"),
             ("directors", "director", "DIRECTOR_MEMORY_OPTIONS", "1023M"),
             ("constructors", "constructor", "CONSTRUCTOR_MEMORY_OPTIONS", "4095M"),
             ("admin-consoles", "admin-console", "ADMINCONSOLE_MEMORY_OPTIONS", "4095M"))

SIMULATE_ECE_RESPONSE_JSON_FILE="simulate_json_response.json"

timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


def execute_curl_command(curl_string):

    print "Running command: %s" % curl_string

    try:
        curl_args = shlex.split(curl_string)
        sub_proc = subprocess.Popen(curl_args, stdout=subprocess.PIPE)
        (ece_response, err) = sub_proc.communicate()
        return ece_response, err
    except:
        print "Problem executing: %s\nExiting!!" % curl_string
        exit(1)


def get_json_from_server(service_name):

    curl_string = 'curl -s -k -u "{0}:{1}" "{2}/api/v0/regions/ece-region/container-sets/{3}" '.format(
        ADMIN, ADMIN_PWD, ECE_URL, service_name)

    (ece_response, err) = execute_curl_command(curl_string)
    return ece_response, err


def extract_sub_object_from_json_string(json_string, sub_object_identifier):

    # print "Processing the following json string: \n" + json_string + "\n\n"

    json_obj = json.loads(json_string)
    sub_obj = json_obj["containers"][sub_object_identifier]["data"]
    return sub_obj


def overwrite_memory_settings_in_sub_obj(sub_obj, memory_key, memory_value):
    env_array = sub_obj["container_config"]["Env"]
    memory_key_regex = memory_key + ".*"
    idx_of_memory_setting = [idx for idx, item in enumerate(env_array) if re.search(memory_key_regex, item)][0]
    print "Previous memory setting was %s" % env_array[idx_of_memory_setting]
    env_array[idx_of_memory_setting] = "{0}=-Xms{1} -Xmx{1}".format(memory_key, memory_value)
    print "Setting memory to %s" % env_array[idx_of_memory_setting]


def write_sub_obj_to_file(service_name, sub_obj):

    file_name = "%s.%s.json" % (service_name, timestamp)
    print "Writing %s\n" % file_name
    f = open(file_name, "w")
    f.write(json.dumps(sub_obj, indent=4, sort_keys=True))
    f.close()
    return file_name


def return_test_json():
    # This return json that would have been returned from the ECE deployment - used for local testing.
    f = open(SIMULATE_ECE_RESPONSE_JSON_FILE, "r")
    json_obj = json.load(f)
    f.close()
    json_string = json.dumps(json_obj)
    return json_string, None

def post_update_to_ece(service_name, endpoint_identifier, file_name):
    curl_string = 'curl -s -XPOST -k -u "{0}:{1}" "{2}/api/v0/regions/ece-region/container-sets/{3}/containers/{4}" -d @{5}'.format(
        ADMIN, ADMIN_PWD, ECE_URL, service_name, endpoint_identifier, file_name)
    (ece_response, err) = execute_curl_command(curl_string)
    print "Server responded with: %s" % ece_response


def main():

    for current_tuple in COMPONENTS:
        print "processing: %s" % current_tuple[0]

        if not TEST_MODE:
            (ece_response, err) = get_json_from_server(service_name=current_tuple[0])
        else:
            print "***** Warning - Running in test mode *****\n"
            (ece_response, err) = return_test_json()

        if ece_response and not err:
            sub_obj = extract_sub_object_from_json_string(json_string=ece_response, sub_object_identifier=current_tuple[1])
            overwrite_memory_settings_in_sub_obj(sub_obj, memory_key=current_tuple[2], memory_value=current_tuple[3])
            file_name = write_sub_obj_to_file(service_name=current_tuple[0], sub_obj=sub_obj)
            post_update_to_ece(service_name=current_tuple[0], endpoint_identifier=current_tuple[1], file_name=file_name)

        else:
            print "Invalid json returned from server. Got ece_response=%s and err=%s" % (ece_response, err)

        # If this is test mode, then no reason to continue looping
        if TEST_MODE:
            exit(0)


if __name__ == '__main__':
    main()
