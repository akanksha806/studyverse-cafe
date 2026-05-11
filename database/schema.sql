-- =============================================================
-- schema.sql — Studyverse Café | MySQL Database Schema
-- =============================================================
-- HOW TO RUN:
--   Option 1 (terminal):
--     mysql -u root -p < database/schema.sql
--
--   Option 2 (MySQL Workbench):
--     Open this file → Run All
--
-- This creates the database and all 4 tables fresh.
-- Safe to re-run: uses IF NOT EXISTS everywhere.
-- =============================================================


-- ── Create & select the database ────────────────────────────
CREATE DATABASE IF NOT EXISTS studyverse_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE studyverse_db;


-- =============================================================
-- TABLE 1: reservations
-- Stores every seat booking made via the website modal.
-- =============================================================
CREATE TABLE IF NOT EXISTS reservations (
    id            INT          AUTO_INCREMENT PRIMARY KEY,

    -- Customer details
    full_name     VARCHAR(100) NOT NULL,
    phone         VARCHAR(20)  NOT NULL,
    email         VARCHAR(150) DEFAULT NULL,   -- optional but used for confirmation email

    -- Booking details
    visit_date    DATE         NOT NULL,
    arrival_time  TIME         NOT NULL,
    zone          ENUM(
                    'Silent Hall',
                    'Midnight Corner',
                    'Reader''s Lounge',
                    'Solo Study Booth',
                    'Creator Workspace'
                  )            NOT NULL DEFAULT 'Silent Hall',

    -- Plan chosen
    plan          ENUM(
                    'Daily Pass',
                    'Weekly Pass',
                    'Monthly Member'
                  )            NOT NULL DEFAULT 'Daily Pass',

    -- Booking status lifecycle
    status        ENUM(
                    'pending',     -- just submitted
                    'confirmed',   -- staff confirmed
                    'cancelled',   -- customer/staff cancelled
                    'completed'    -- visit done
                  )            NOT NULL DEFAULT 'pending',

    special_note  TEXT         DEFAULT NULL,   -- any extra request
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Prevent double-booking the same zone at the same time
    UNIQUE KEY no_double_book (visit_date, arrival_time, zone)
);


-- =============================================================
-- TABLE 2: menu_items
-- Stores all café drinks/food with pricing.
-- =============================================================
CREATE TABLE IF NOT EXISTS menu_items (
    id           INT           AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100)  NOT NULL,
    description  TEXT          DEFAULT NULL,
    price        DECIMAL(8,2)  NOT NULL,
    category     ENUM(
                   'hot_drinks',
                   'cold_drinks',
                   'shakes',
                   'food',
                   'specials'
                 )             NOT NULL DEFAULT 'hot_drinks',
    emoji        VARCHAR(10)   DEFAULT '☕',
    is_available TINYINT(1)    NOT NULL DEFAULT 1,   -- 1=on menu, 0=hidden
    is_signature TINYINT(1)    NOT NULL DEFAULT 0,   -- 1=featured on homepage
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- =============================================================
-- TABLE 3: memberships
-- Tracks which customers bought which membership plan.
-- =============================================================
CREATE TABLE IF NOT EXISTS memberships (
    id           INT          AUTO_INCREMENT PRIMARY KEY,

    -- Customer details
    full_name    VARCHAR(100) NOT NULL,
    phone        VARCHAR(20)  NOT NULL,
    email        VARCHAR(150) NOT NULL,   -- required for membership emails

    -- Plan details
    plan         ENUM(
                   'Daily Pass',
                   'Weekly Pass',
                   'Monthly Member'
                 )            NOT NULL,
    amount_paid  DECIMAL(8,2) NOT NULL,

    -- Validity window
    start_date   DATE         NOT NULL,
    end_date     DATE         NOT NULL,   -- calculated by server based on plan

    -- Status
    status       ENUM(
                   'active',
                   'expired',
                   'cancelled'
                 )            NOT NULL DEFAULT 'active',

    payment_ref  VARCHAR(100) DEFAULT NULL,  -- future: Razorpay/UPI ref
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_email  (email),
    INDEX idx_status (status)
);


-- =============================================================
-- TABLE 4: contact_messages
-- Stores every form submission from the contact/footer form.
-- =============================================================
CREATE TABLE IF NOT EXISTS contact_messages (
    id         INT          AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL,
    subject    VARCHAR(200) DEFAULT NULL,
    message    TEXT         NOT NULL,
    is_read    TINYINT(1)   NOT NULL DEFAULT 0,   -- 0=unread, 1=read by staff
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);


-- =============================================================
-- SEED DATA — Pre-fill the menu with Studyverse signature items
-- =============================================================
INSERT IGNORE INTO menu_items (name, description, price, category, emoji, is_signature)
VALUES
  ('3AM Mocha',          'Dark espresso, bittersweet chocolate, steamed milk and a whisper of sea salt.',            180.00, 'hot_drinks',  '☕', 1),
  ('Deadline Espresso',  'Triple shot, zero mercy. Clean, brutal, effective.',                                       120.00, 'hot_drinks',  '⚡', 1),
  ('Focus Fuel',         'Matcha, lion\'s mane extract, oat milk, and raw honey. Calm energy for hours.',            220.00, 'cold_drinks', '🧠', 1),
  ('Dark Academia Latte','Cinnamon-dusted espresso with brown sugar syrup and warm vanilla cream.',                  200.00, 'hot_drinks',  '📖', 1),
  ('Night Owl Shake',    'Cold brew, dark cocoa, toffee crumble, and thick cold cream.',                             250.00, 'shakes',      '🦉', 1),
  ('Sunrise Americano',  'Double shot diluted with still water, clean and powerful.',                                100.00, 'hot_drinks',  '🌅', 0),
  ('Scholar\'s Chai',    'Spiced masala chai brewed strong with full-fat milk.',                                      80.00, 'hot_drinks',  '🫖', 0),
  ('Coder Cold Brew',    '18-hour steeped cold brew served over crystal ice.',                                       190.00, 'cold_drinks', '🧊', 0);
