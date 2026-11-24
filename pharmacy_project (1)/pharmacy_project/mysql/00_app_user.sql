-- Optional: a limited account for the Python menu application (run as root AFTER 01_schema.sql)
CREATE USER IF NOT EXISTS 'pharmacy_app'@'localhost' IDENTIFIED BY 'pharmacy123';
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON pharmacy_db.* TO 'pharmacy_app'@'localhost';
FLUSH PRIVILEGES;
