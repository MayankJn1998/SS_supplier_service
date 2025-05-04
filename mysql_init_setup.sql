drop database "suppliers_db"
create database "suppliers_db"

use suppliers_db;

CREATE TABLE suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address VARCHAR(255)
);

INSERT INTO suppliers (name, contact_person, email, phone, address) VALUES ('Acme Corp', 'John Doe', 'john.doe@example.com', '555-1234', '123 Main St');
INSERT INTO suppliers (name, contact_person, email, phone, address) VALUES ('Global Tech', 'Sarah Johnson', 's.johnson@globaltech.com', '555-9876', '450 Tech Park Blvd');
INSERT INTO suppliers (name, contact_person, email, phone, address) VALUES ('Summit Supplies', 'Michael Chen', 'michael.chen@summitsupplies.net', '555-2345', '789 Industrial Way');
INSERT INTO suppliers (name, contact_person, email, phone, address) VALUES ('Oceanic Foods', 'Lisa Wong', 'lisa.wong@oceanicfoods.org', '555-8765', '321 Harbor Drive');
INSERT INTO suppliers (name, contact_person, email, phone, address) VALUES ('Pinnacle Manufacturing', 'Robert Davis', 'rdavis@pinnacle-mfg.com', '555-3456', '100 Factory Lane');
INSERT INTO suppliers (name, contact_person, email, phone, address) VALUES ('Green Earth Organics', 'Emily Wilson', 'emily@greenearth.org', '555-6543', '55 Farm Road');
INSERT INTO suppliers (name, contact_person, email, phone, address) VALUES ('Metro Office Solutions', 'James Rodriguez', 'j.rodriguez@metrosolutions.com', '555-7890', '200 Business Center Ave');

