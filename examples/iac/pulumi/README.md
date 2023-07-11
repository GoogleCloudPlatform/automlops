
# Pulumi
## Local developmet

Setting up local environment for testing.

### Setup

- Pulumi setup

```shell
brew install pulumi

# Login Pulumi Cloud
pulumi login
```

- Python 3.x
- Install the requirements:

```shell
pip3 install virtualenv

#Create virtualenv
python3 -m venv .venv


#Activate virtualenv:
. .venv/bin/activate
```

### Creating Pulumi  stack

```shell
$ pulumi stack init opsangels/dev
Created stack 'opsangels/dev'
```