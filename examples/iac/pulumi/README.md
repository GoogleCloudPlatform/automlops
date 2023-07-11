
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
Checking stack:
![image](https://github.com/lexopsangels/automlops/assets/54945914/574ae1a7-9629-4533-b673-b78de22a0863)


Once stack is create you should be up the environment.

**IMPORTANT**: Make sure you are logged in.
```shell
$ gcloud auth application-default login
```

