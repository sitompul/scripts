#!/usr/bin/env python3
import os

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
        processor_used = f"""{i} {i+1}"""
        if i % 2 != 0:
            processor_used = f"""{i-1} {i}"""
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
    if os.geteuid() != 0:
        print("must run with sudo")
        return

    redis_instance_count = os.cpu_count()
    if redis_instance_count is None:
        redis_instance_count = 1
    # check how many threads, number of redis instance will be based on number of threads.
    if redis_instance_count == 0:
        print("no threads is detected, threads is 0")
        print("no cluster is configured")
        return

    # for HA and queing this is needed.
    # Default configuration is half of the threads are service as slave.
    number_of_replica: int = 0
    # number_of_replica: int = int(redis_instance_count / 2)

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
    with open("./scripts/connect_cluster_run_once.sh", "w") as file:
        file.write(run_once)
    with open("./scripts/start_systemd.sh", "w") as file:
        file.write(start_script)
    with open("./scripts/stop_systemd.sh", "w") as file:
        file.write(stop_script)

main()
