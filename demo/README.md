This is a project to show how to use `xbot.plugins.ssh`.

Install the project from the repository root:

```shell
python -m pip install .
```

To run it, modify the `ip`, `user`, and `password` values in
`testbeds/mytestbed.yml`, then run:

```shell
xbot run -b testbeds/mytestbed.yml -s testsets/mytestset.yml
```
