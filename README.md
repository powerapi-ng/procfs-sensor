# Procfs-Sensor

The Proc Filesystem Sensor is a tool that monitor the CPU usage of cgroup via
the linux's proc filesystem.
It use `pidstat` to retreive the percentage of CPU usage of each process.
It then use the `/sys/fs/perf_event` directory to find the appartenance of
processes to cgroup.

The sensor need the cgroup version 1. The version 2 is not supported yet.

# About

Procfs Sensor is an open-source project developed by the [Spirals research
group](https://team.inria.fr/spirals) (University of Lille 1 and Inria).

The documentation is not available yet.

## Contributing

If you would like to contribute code you can do so through GitHub by forking the
repository and sending a pull request.
You should start by reading the [contribution guide](https://github.com/powerapi-ng/procfs-sensor/blob/main/contributing.md)

When submitting code, please check that it is conform by using `pylint` and
`flake8` with the configurations files at the root of the project.

## Acknowledgments

Procfs Sensor is written in [Python](https://www.python.org/) (under [PSF
license](https://docs.python.org/3/license.html)).
It also use [`pidstat`](https://github.com/sysstat/sysstat)
