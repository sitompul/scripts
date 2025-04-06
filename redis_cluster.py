#!/usr/bin/env python3
import os
import stat

def redis_conf_template(port: int) -> str:
    return f"""
port {port}
bind 0.0.0.0
cluster-enabled yes
cluster-config-file /var/lib/redis/nodes-{port}.conf
cluster-node-timeout 5000
appendonly yes
daemonize no 
""".lstrip()

def generate_run_shell_script(
    number_of_replica: int,
    port_start: int,
    redis_instance_count: int,
) -> tuple[dict[str, str], str, str, str] :

    systemd_config: dict[str, str] = {}

    instance_address_list: list[str] = []

    start_script: list[str] = []
    stop_script: list[str] = []

    for i in range (redis_instance_count):
        current_port = port_start + i
        instance_address_list.append(f"127.0.0.1:{current_port}")
        processor_used = i

        command = f"""
# /etc/systemd/system/redis-{current_port}.service

[Unit]
Description=Redis Cluster Node {current_port}
After=network.target

[Service]
User=redis
Group=redis
ExecStart=/usr/bin/redis-server /etc/redis/{current_port}/redis.conf
ExecStop=/usr/bin/redis-cli -p {current_port} shutdown
Restart=always
CPUAffinity={processor_used}
WorkingDirectory=/var/lib/redis

[Install]
WantedBy=multi-user.target"""
        systemd_config[str(current_port)] = command
        start_script.append(f"sudo systemctl enable --now redis-{current_port}")
        stop_script.append(f"sudo systemctl stop redis-{current_port}")

    instance_address_script = " ".join(instance_address_list)
    run_cluster_command = f"""# Run this only once, there is no need to run this after restarting the service, redis will automatically connect between node inside the cluster
redis-cli --cluster create {instance_address_script} --cluster-replicas {number_of_replica} --cluster-yes
"""
    start_redis_systemd_command = " && ".join(start_script)
    stop_redis_systemd_command = " && ".join(stop_script)

    return (systemd_config, run_cluster_command, start_redis_systemd_command, stop_redis_systemd_command)

def main() -> None:
    # The only configuration needed
    is_ha = False

    is_ha_question = input("Do you want to enable High Availability (Lesser masters will be generated)? (y/N): ").strip().lower()
    if is_ha_question == "y":
        is_ha = True

    if os.geteuid() != 0:
        print("must run with sudo")
        return

    redis_instance_count = os.cpu_count()
    if redis_instance_count is None:
        redis_instance_count = 1
    number_of_replica: int = 0
    if is_ha:
        number_of_replica: int = int(redis_instance_count / 2) + 1 # number of replica must be larger than number of instance
        number_of_master =  redis_instance_count - number_of_replica
        print(f"\nHA is enabled, {number_of_master} master(s) will be created and {number_of_replica} replica(s) will be created\n")
    else:
        print("\nHA is disabled, no replica(s) will be created\n")

    # check how many threads, number of redis instance will be based on number of threads.
    if redis_instance_count < 3:
        print("min 3 threads are required, thread count is:", redis_instance_count)
        print("no cluster is configured")
        return


    # Default starting port for redis.
    port_start: int = 7000

    # Create configuration for each ports
    for i in range(redis_instance_count):
        port = port_start + i
        # Create folder for each
        conf_path = f"/etc/redis/{port}"
        os.makedirs(f"/etc/redis/{port}", exist_ok=True)
        with open(conf_path + "/redis.conf", "w") as file:
            file.write(redis_conf_template(port))

    # Generate shell script to run multiple instance on cluster mode.
    script_content, run_once, start_script, stop_script = generate_run_shell_script(
        number_of_replica,
        port_start,
        redis_instance_count,
    )
    
    for key, value in script_content.items():
        file_path = f"/etc/systemd/system/redis-{key}.service"
        with open(file_path, "w") as file:
            file.write(value)

    # Generate script that will connect all the cluster, if there is no change in number of cluster
    # nodes, then no need to run it again.
    os.makedirs("./scripts", exist_ok=True)

    connect_cluster_script_path = "./scripts/connect_cluster_run_once.sh"
    with open(connect_cluster_script_path, "w") as file:
        file.write(run_once)
    os.chmod(connect_cluster_script_path, os.stat(connect_cluster_script_path).st_mode | stat.S_IXUSR)

    start_systemd_script_path = "./scripts/start_systemd.sh"
    with open(start_systemd_script_path, "w") as file:
        file.write(start_script)
    os.chmod(start_systemd_script_path, os.stat(start_systemd_script_path).st_mode | stat.S_IXUSR)

    stop_systemd_script_path = "./scripts/stop_systemd.sh"
    with open(stop_systemd_script_path, "w") as file:
        file.write(stop_script)
    os.chmod(stop_systemd_script_path, os.stat(stop_systemd_script_path).st_mode | stat.S_IXUSR)

main()
