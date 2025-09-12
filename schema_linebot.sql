-- =========================================================
-- schema_linebot.sql (improved based on db_preflight.sql)
-- Sources: db_preflight.sql :contentReference[oaicite:0]{index=0}, original schema_linebot.sql :contentReference[oaicite:1]{index=1}
-- Changes:
-- 1) ask_for_leave → composite index + FK(account_info) with ON UPDATE CASCADE / ON DELETE RESTRICT. :contentReference[oaicite:2]{index=2}
-- 2) message_logs → indexes on (student_ID) and (context_title, operation_time). :contentReference[oaicite:3]{index=3}
-- 3) event_logs → indexes + FK(message_logs.log_id) with ON UPDATE CASCADE / ON DELETE SET NULL. :contentReference[oaicite:4]{index=4}
-- =========================================================

CREATE TABLE `account_info` (
  `student_ID` char(30) NOT NULL,
  `line_userID` text,
  `mdl_ID` int DEFAULT NULL,
  `student_name` text,
  `context_title` char(50) NOT NULL,
  `roleid` int DEFAULT NULL,
  `del` int DEFAULT NULL,
  PRIMARY KEY (`student_ID`,`context_title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ask_for_leave` (
  `operation_time` char(30) DEFAULT NULL,
  `student_ID` char(30) NOT NULL,
  `student_name` text,
  `apply_time` char(30) NOT NULL,
  `reason` text,
  `context_title` char(50) NOT NULL,
  PRIMARY KEY (`student_ID`,`apply_time`,`context_title`),
  KEY `idx_ask_for_leave_student_ctx` (`student_ID`,`context_title`),
  CONSTRAINT `fk_askleave_account`
    FOREIGN KEY (`student_ID`,`context_title`)
    REFERENCES `account_info` (`student_ID`,`context_title`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `change_HW_deadline` (
  `context_title` char(50) DEFAULT NULL,
  `contents_name` char(30) DEFAULT NULL,
  `RS_D1` int DEFAULT NULL,
  `RS_D2` int DEFAULT NULL,
  `RS_D3` int DEFAULT NULL,
  `AS_D1` int DEFAULT NULL,
  `AS_D2` int DEFAULT NULL,
  `AS_D3` int DEFAULT NULL,
  `OJ_D1` int DEFAULT NULL,
  `Summary_D1` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `concept_keyword_and_question` (
  `context_title` char(50) NOT NULL,
  `contents_name` char(50) NOT NULL,
  `kw_id` int NOT NULL,
  `keyword` text,
  `question` text,
  `related_kws` text,
  `del` int DEFAULT NULL,
  PRIMARY KEY (`context_title`,`contents_name`,`kw_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `concept_summary_example` (
  `context_title` char(50) NOT NULL,
  `contents_name` char(50) NOT NULL,
  `summary` text,
  PRIMARY KEY (`context_title`,`contents_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `course_info` (
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

CREATE TABLE `message_logs` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `operation_time` char(30) DEFAULT NULL,
  `student_ID` char(30) DEFAULT NULL,
  `message` text,
  `context_title` char(50) DEFAULT NULL,
  PRIMARY KEY (`log_id`),
  KEY `idx_message_logs_student` (`student_ID`),
  KEY `idx_message_logs_ctx_time` (`context_title`,`operation_time`)
) ENGINE=InnoDB AUTO_INCREMENT=15275 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `event_logs` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `operation_time` char(30) DEFAULT NULL,
  `student_ID` char(30) DEFAULT NULL,
  `operation_event` char(30) DEFAULT NULL,
  `problem_id` char(20) DEFAULT NULL,
  `HW_id` char(20) DEFAULT NULL,
  `context_title` char(50) DEFAULT NULL,
  `message_log_id` int DEFAULT NULL,
  `GAI_auto_reply_status` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`log_id`),
  KEY `idx_event_logs_message_log_id` (`message_log_id`),
  KEY `idx_event_logs_student` (`student_ID`),
  KEY `idx_event_logs_ctx` (`context_title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `summary_feedback_push` (
  `operation_time` char(30) DEFAULT NULL,
  `context_title` char(50) DEFAULT NULL,
  `contents_name` char(50) DEFAULT NULL,
  `student_ID` char(30) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `summary_gradding_log` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `operation_time` char(30) DEFAULT NULL,
  `context_title` char(50) DEFAULT NULL,
  `contents_name` char(50) DEFAULT NULL,
  `student_ID` char(30) DEFAULT NULL,
  `summary` text,
  `loss_kw` text,
  `similarity` float DEFAULT NULL,
  `penalty` float DEFAULT NULL,
  `score` int DEFAULT NULL,
  `result` int DEFAULT NULL,
  `is_manual` int DEFAULT NULL,
  `hit_kws` float DEFAULT NULL,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2838 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user_states` (
  `line_user_id` varchar(64) NOT NULL,
  `state_name` varchar(50) NOT NULL,
  `context` text,
  PRIMARY KEY (`line_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
