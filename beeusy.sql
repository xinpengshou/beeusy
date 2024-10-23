-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS beeusy;
USE beeusy;

-- Create service_categories table
CREATE TABLE IF NOT EXISTS service_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Create services table
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT,
    name VARCHAR(255) NOT NULL,
    FOREIGN KEY (category_id) REFERENCES service_categories(id)
);

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS user_promotions;
DROP TABLE IF EXISTS user_addresses;
DROP TABLE IF EXISTS Tasker;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS users;

-- Recreate the users table with the correct structure
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    userAvatar VARCHAR(255) DEFAULT 'defaultAvatar.png'
);

-- Recreate the bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    service_id INT,
    booking_date DATE,
    booking_time TIME,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- Recreate the user_promotions table
CREATE TABLE IF NOT EXISTS user_promotions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    promotion_id INT,
    is_used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (promotion_id) REFERENCES promotions(id)
);

-- Recreate the user_addresses table
CREATE TABLE IF NOT EXISTS user_addresses (
    user_id INT PRIMARY KEY,
    address VARCHAR(255),
    postal_code VARCHAR(10),
    city VARCHAR(100),
    province VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Recreate the Tasker table
CREATE TABLE IF NOT EXISTS Tasker (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    service_categories TEXT,
    rating DECIMAL(3, 2),
    comments TEXT,
    userAvatar VARCHAR(255) DEFAULT 'defaultTaskerAvatar.png',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Insert sample data for service_categories
INSERT INTO service_categories (name) VALUES
('家电维修'),
('家具组装'),
('搬家服务'),
('家政清洁'),
('机场接送'),
('宠物寄养'),
('家教辅导'),
('物品寄存'),
('幼儿托管'),
('母婴护理'),
('园艺服务'),
('更多');

-- Insert sample data for services
INSERT INTO services (category_id, name) VALUES
(1, '冰箱维修'),
(1, '洗衣机维修'),
(2, '宜家家具组装'),
(3, '小型搬家'),
(4, '深度清洁');

-- Insert sample data for users
INSERT INTO users (username, phone_number, userAvatar) VALUES
('User1234', '7786770215', 'user1234Avatar.png'),
('User5678', '6331140514', 'user5678Avatar.png');

-- Insert sample data for bookings
INSERT INTO bookings (user_id, service_id, booking_date, booking_time) VALUES
(1, 1, '2023-05-01', '14:00:00'),
(2, 3, '2023-05-02', '10:00:00');

-- Insert sample data for promotions
INSERT INTO promotions (title, description, discount_percentage, valid_from, valid_to) VALUES
('新用户优惠', '新用户首次预约可享受8折优惠', 20.00, '2023-04-01', '2023-12-31'),
('夏季特惠', '夏季清洁服务9折优惠', 10.00, '2023-06-01', '2023-08-31');

-- Insert sample data for user_promotions
INSERT INTO user_promotions (user_id, promotion_id, is_used) VALUES
(1, 1, FALSE),
(2, 1, FALSE),
(2, 2, FALSE);

-- Insert sample data for user_addresses
INSERT INTO user_addresses (user_id, address, postal_code, city, province) VALUES
(1, '1385 Woodroffe Ave', 'K1Z8G9', 'Ottawa', 'ON'),
(2, '1359 Summerville Ave', 'K2G1V8', 'Nepean', 'ON');

-- Insert sample data for Tasker
INSERT INTO Tasker (user_id, name, phone, service_categories, rating, comments, userAvatar) VALUES
(1, '张三', '7786770215', '1,2,4', 4.8, '很专业的服务', 'tasker1Avatar.png'),
(2, '李四', '6331140514', '3,4,5', 4.9, '非常满意，下次还会选择', 'tasker2Avatar.png');
