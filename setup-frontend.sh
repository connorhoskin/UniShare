#!/bin/bash

# Update Ubuntu software packages.
sudo yum update -y

# Install Python3 and pip3
sudo yum install -y python3 python3-pip
pip3 install pymysql

# Install Flask and other necessary Python packages
pip3 install Flask flask_sqlalchemy flask_migrate flask_login

python3 main_app.py



