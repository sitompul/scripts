# Scripts

## Redis Cluster

- Only works on Ubuntu (you need to manage the folder/path for redis configuration to support other OS/systemd)
- Run "start_systemd.sh" to run all the generated redis configuration on systemd.
- Run "connect_cluster_run_once.sh" to connect all the generated redis nodes, you need to run this once if there is no master/slave added/removed
- Stop using "stop_systemd"
