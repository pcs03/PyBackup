# PyBackup
#### Video Demo: <>
#### Description:
This project serves as a tool to backup important data running on servers. My
motivation comes from the server that I host many services on, which requires a
versatile backup tool that can backup specific directories on a Linux server.
Some directories contain files for the databases of some services, these have
to be stopped before backup up the file, else you risk file corruption. All in
all, this resulted in the idea to write such a tool using Python and my newly
gained experience in computer science.

This tool is capable of backup up directories that contain docker compose
stacks. Docker compose is a tool that allows the running of multiple docker
containers using a configuration file called `docker-compose.yml`. For this
project, the assumption is made that any mounted docker volumes for any of the
containers in the stack are mounted in the directory containing the
`docker-compose.yml` file. Before these mounted directories can be backed up,
the docker containers they are mounted on need to be stopped, thus requiring
the need of a more specialized backup solution.

Any directories that are not docker compose stacks can also be backed up using
PyBackup. In the end, a compressed archive file is made of every specified
docker compose stack and/or other directories.

#### The file structure
The two main files of the project are as follows:
- backup.py
- config.yml

`backup.py` contains the Python code behind the project. It first loops through all docker compose stacks contained in a given directory. Every stack is compressed into a separate compressed archive. It then loops through any other directories that are not docker compose stacks, which are also compress into separate archives. All archives are stored in a given directory.

`config.yml` contains the configuration for the backup tool. Yaml is used for this, as it's a convenient and readable format for configuration files. The options in this file are explained below.

#### Backup Configuration
The `config.yml` file contains the following configuration options:
- docker-dir: This directory contains all directories with docker-compose stacks in them.
- docker-backup-ignore: To ignore a docker-compose stack, specify it here. This can be useful if a stack contains big files that can be easily re-downloaded, thus rendering a backup unnecessary.
- backup-dirs: Other directories that need to be backed up besides docker-compose stacks can be listed here. An archive will be made per directory.
- target-dir: All backup archives will be stored in this directory. For every backup run a new directory will be created in here, named as the current date and time. In this directory all created compressed archives are placed.
- compress: what compression algorithm to use
- compress_level: How much to compress it, a higher level takes up less storage, but takes longer.
- retention: How long to keep backups, in days.


#### How to run PyBackup
First the dependencies need to be installed. It is recommended to use a virtual environment for this. Create and activate one as follows (UNIX only):
```bash
python -m venv venv
source venv/bin/activate
```

Now install the dependencies:
```
pip install -r requirements.txt
```

Make sure all your configuration options are set in `config.yml`, then run it:
```
python backup.py
```

It will do it's thing, and will exit when everything is backup up. Compressed archives should now be stored in the given target directory.

#### How to automate the usage of PyBackup
To minimize data loss when catastrophe strikes, it is preferrable to have daily backups. There are multiple ways to automate the running of PyBackup. Among others these are:
- Cron job
- Systemd timer

##### Cron
Make sure cron is installed on your system, then open the cron configuration:
```
crontab -e
```

Add a new line for running this python script:
```
0 0 * * * /path/to/pybackup/venv/bin/python /path/to/pybackup/backup.py
```

The 0's and *'s denote on what interval to run the script, more info [here](https://crontab.guru/). In this case, the script is ran daily at 00:00.

##### Systemd timer
This method is more involved, but provides greater configuration and control. First create a systemd service file called `pybackup.service` in `/etc/systemd/system`:
```
[Unit]
Description=Run PyBackup

[Service]
Type=oneshot
WorkingDirectory=/path/to/pybackup
ExecStart=venv/bin/python backup.py
StandardOutput=journal
StandardError=journal
```

Then create a systemd timer file called `pybackup.timer` in `/etc/systemd/system`:
```
[Unit]
Description=Run PyBackup daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

When both files are created, reload the systemd configuration:
```bash
sudo systemctl daemon-reload
```

Then enable the timer:
```bash
sudo systemctl enable pybackup.timer
sudo systemctl start pybackup.timer
```

There are some benefits to using this method over a cronjob:
- You can set a working directory for running the script.
- Output and errors are logged to the journal which can be accesssed with the `journalctl` command.
- The configuration is structured and separated from other services.
- A "dry run" of the service can be performed without waiting on the configured time:
```bash
sudo systemctl start pybackup.service
sudo systemctl status pybackup.service
sudo journalctl -u pybackup.service
```

