# praetorian-ssh-proxy

Hi. I am Maximus ⚔️, the commander of the emperor's army. My main task is to send our ideals and solutions to
unexplored places 🌄 ... like someone's archaic debian 🖥️.

## Introduction

Praetorian SSH Proxy server is used for maintaining communication between praetorian api user (client) and remote device
over SSH protocol. Main purpose of this solution is to manage secure commands to remote's shell.

## Installation

```python
# pip
pip install praetorian-api-client

# pipenv
pipenv install praetorian-api-client

# poetry
poetry add praetorian-api-client
```

## SSH Proxy server startup

- usage: `python run.py [HOST] [PORT]`
- example: `python run.py localhost 22`

## Usage

### Praetorian-API user (no remote specified)

- `ssh username@praetorian.sk@localhost -p 22`

> After successful authentication (password provided),
> SSH server will ask for specific remote name

```
------------------------------------
| Welcome to Praetorian SSH proxy  |
------------------------------------
| test-remote-west               1 |
| test-remote-south              2 |
| test-remote-east               3 |
------------------------------------
| exit                           4 |
------------------------------------
Choose your remote:
```

### Praetorian-API user (remote specified)

-  `ssh username@praetorian.sk+remotename@localhost -p 22`

### Fabric run example (temporary users only)

- usage: `fab deploy [DESTINATION] [USERNAME] [PASSWORD]`
- example: `fab deploy production PQWsMyD@praetorian.sk MX7EATyS6X`

---
Developed with 💙 and ☕️ by [Adam Žúrek](https://zurek11.github.io/), Erik Belák
with the support of [BACKBONE s.r.o.](https://www.backbone.sk/), 2023 (C)
