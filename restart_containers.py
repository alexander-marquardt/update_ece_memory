# This script has NOT BEEN TESTED, and is not complete.
# Docker 18 reports "health" of each container,  but earlier versions may not -- if health is not reported
# then this script will not work correctly.
# Additionally, using "docker ps" is not a _nice_ way of gathering docker information.
# This should be rewritten to use "docker inspect --format='{{json .State.Health}}' <container_name>"



# script to be used for restarting ECE components
import subprocess
import re
import time
import sys

TEST_MODE=True


CONTAINER_NAMES = ["frc-allocators-allocator",
                   "frc-proxies-proxy",
                   "frc-directors-director",
                   "frc-admin-consoles-admin-console"
                   "frc-zookeeper-servers-zookeeper",
                   "frc-constructors-constructor"]

SIMULATE_DOCKER_PS_OUTPUT_FILE = "docker_ps.txt"

def get_docker_ps():
    if not TEST_MODE:
        sub_proc = subprocess.Popen(["docker", "ps"], stdout=subprocess.PIPE)
        (response, err) = sub_proc.communicate()
        return response

    else:
        f=open(SIMULATE_DOCKER_PS_OUTPUT_FILE, "r")
        response = f.read()
        f.close()

        return response

def get_container_id_and_full_line(container_name):
    response = get_docker_ps()
    for line in response.splitlines():
        list_of_vals = line.split()
        if re.search(container_name, line):
            return list_of_vals[0], line
    return None, None

def wait_for_container_to_restart(container_name):
    print "Waiting for %s to start" % container_name
    healthy = False
    while not healthy:
        container_id, full_line_from_docker_ps = get_container_id_and_full_line(container_name)

        if container_id:
            print "\nFound container %s with id %s - waiting for healthy" % (
                container_name, container_id)
            while not healthy:
                container_id, full_line_from_docker_ps = get_container_id_and_full_line(container_name)
                if re.search("\(healthy\)", full_line_from_docker_ps):
                    print "Healthy container %s with id %s" % (
                        container_name, container_id)
                    healthy = True
                else:
                    print ".",; sys.stdout.flush(); time.sleep(2)


        else:
            print ".", ; sys.stdout.flush(); time.sleep(2)

    print "\nContainer %s is now running and healthy with id: %s!" % (container_name, container_id)


def remove_container(container_name):
    container_id, full_line_from_docker_ps = get_container_id_and_full_line(container_name)
    if container_id:
        print "Removing %s" % container_id
        subprocess.call(["docker", "rm", "-f", container_id])
        wait_for_container_to_restart(container_name)


def main():
    for container_name in CONTAINER_NAMES:
        remove_container(container_name)


if __name__ == '__main__':
    main()
