# Scripts

## Redis Cluster

- Only works on Ubuntu (typically you just need to change the path if your OS is linux based and supports systemd)
    - To support other **non-linux** os, you need to use `daemonize yes` configuration
    - Then run each node using `redis-server` command manually
- Run `cluster.py` with sudo. And then scripts will be generated.
- Run `start_systemd.sh` to run all the generated redis configuration on systemd.
- Run `connect_cluster_run_once.sh` to connect all the generated redis nodes, you need to run this once if there is no master/slave added/removed
- Stop using `stop_systemd.sh`
