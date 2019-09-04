# script to be used for restarting ECE components
import subprocess
import re


CONTAINER_NAMES = ["frc-allocators-allocator",
                   "frc-proxies-proxy",
                   "frc-directors-director",
                   "frc-admin-consoles-admin-console"
                   "frc-zookeeper-servers-zookeeper",
                   "frc-constructors-constructor"]

CONTAINER_NAMES = ["mysql/mysql-server"]


def get_docker_ps():
    sub_proc = subprocess.Popen(["docker", "ps"], stdout=subprocess.PIPE)
    (response, err) = sub_proc.communicate()
    return response


def get_container_id_and_status(container_name):
    response = get_docker_ps()
    for line in response.splitlines():
        list_of_vals = line.split()
        if re.search(container_name, list_of_vals[1]):
            return list_of_vals[0], line
    return None, None

def wait_for_container_to_restart(container_name):
    print "Waiting for %s to start" % container_name
    healthy = False
    while not healthy:
        container_id, full_line_from_docker_ps = get_container_id_and_status(container_name)

        if container_id:
            print "\nFound container %s with id %s - waiting for healthy" % (
                container_name, container_id)
            while not healthy:
                container_id, full_line_from_docker_ps = get_container_id_and_status(container_name)
                if re.search("\(healthy\)", full_line_from_docker_ps):
                    print "Healthy container %s with id %s" % (
                        container_name, container_id)
                    healthy = True
                else:
                    print ".",
        else:
            print ".",

    print "\nContainer %s is now running and healthy with id: %s!" % (container_name, container_id)


def remove_container(container_name):
    container_id, container_status = get_container_id_and_status(container_name)
    if container_id:
        print "Removing %s" % container_id
        subprocess.call(["docker", "rm", "-f", container_id])
        wait_for_container_to_restart(container_name)


def main():
    for container_name in CONTAINER_NAMES:
        remove_container(container_name)



if __name__ == '__main__':
    main()
