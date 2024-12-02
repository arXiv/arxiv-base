#!/bin/sh
sudo mysql -e "CREATE DATABASE testdb;"
sudo mysql -e "CREATE USER 'testuser'@'localhost' IDENTIFIED BY 'testpassword';"
sudo mysql -e "GRANT ALL PRIVILEGES ON testdb.* TO 'testuser'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"