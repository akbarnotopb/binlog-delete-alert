Python binlog basic listener and `hard delete` email alert using `smtplib`. It is created by using [python-mysql-replication](https://github.com/julien-duponchelle/python-mysql-replication) package.

# Note
Based on [python-mysql-replication](https://github.com/julien-duponchelle/python-mysql-replication) package, you might need to run this with `pypy` for better performance & optimization. 

# Setup
1. Install required package. `pypy -m pip install -r requirements.txt`
2. You might need to install mysql connector
3. adjust your environment in `.env` , you can copy from `.env.example`
4. adjust event & alert configuration `listener.json`
5. run `pypy main.py`

# Alert Configuration
| key               | description                                                                                                                                                                                           |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `only_schemas`    | List of string of schema/database you want to listen.  The default is `true` which means all schema of current user                                                                                   |
| `ignored_schemas` | List of string of schema/database you want to ignore. The default is `null` which means you do not ignore any database.                                                                               |
| `only_tables`     | List of string of table you want to listen. The default is `true` which means all table of database(s).                                                                                               |
| `ignored_tables` | List of string of table you want to ignore. The default is `null` which means you do not ignore any table                                                                                             |
| `only_events`     | List of event you want to listen. The default value is `true` which means you want to listen all available events.  Available value: `deleterows` , `writerows` , `updaterows` , `tablemap`, `query`. |
| `ignore_events`   | List of event you want to ignore. The default value is `null` which means you do not ignore any event.  Available value: `deleterows` , `writerows` , `updaterows` , `tablemap`, `query`.             |
| `recipient`       | List of email that you want to send `deleterows` notification                                                                                                                                         |
| `cc`              | List of email that you want to send `deleterows` notification as `cc`                                                                                                                                 |
| `bcc`             | List of email that you want to send `deleterows` notification as `bcc`      


# Tested on
- python 3.10
- pypy3.9
- mysql 8.0 (docker)
- windows
