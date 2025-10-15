-- 確保使用正確 DB 名稱（若你是別的 DB 名，請調整）
SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS `linebot_test`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE `linebot_test`;

-- 依你提供的定義：主鍵是 context_title
CREATE TABLE IF NOT EXISTS `course_info` (
  `context_title` char(50) NOT NULL,
  `status` text,
  `present_url` text,
  `mails_of_TAs` text,
  `leave_notice` int DEFAULT NULL,
  `day_of_week` int DEFAULT NULL,
  `OJ_contest_title` text,
  `reserved` text,
  PRIMARY KEY (`context_title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 目標課程資料（idempotent）
INSERT INTO `course_info` (
  `context_title`, `status`, `present_url`, `mails_of_TAs`,
  `leave_notice`, `day_of_week`, `OJ_contest_title`, `reserved`
) VALUES (
  '1234_程式設計-Python_黃鈺晴教師',
  'in_progress',
  'https://docs.google.com/spreadsheets/d/demo/edit#gid=1894751741',
  'jz1452896@gmail.com',
  1,
  2,
  '中央_1234',
  ''
)
ON DUPLICATE KEY UPDATE
  `status` = VALUES(`status`),
  `present_url` = VALUES(`present_url`),
  `mails_of_TAs` = VALUES(`mails_of_TAs`),
  `leave_notice` = VALUES(`leave_notice`),
  `day_of_week` = VALUES(`day_of_week`),
  `OJ_contest_title` = VALUES(`OJ_contest_title`),
  `reserved` = VALUES(`reserved`);
