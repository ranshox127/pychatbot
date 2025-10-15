-- =========================================================
-- schema_verify.sql (improved based on db_preflight.sql)
-- Sources: db_preflight.sql :contentReference[oaicite:5]{index=5}, original schema_verify.sql :contentReference[oaicite:6]{index=6}
-- Changes:
-- 1) TeacherFeedbacks → indexes on (SubmissionId) and (SubmissionType). :contentReference[oaicite:7]{index=7}
-- 2) CodeSubmissions_v2 → indexes on (StudentId), (ProblemId), (LineID), (context_title). :contentReference[oaicite:8]{index=8}
-- 3) SummarySubmissions → indexes on (StudentId), (context_title), (LineID), (summary_gradding_log_id). Optional cross-DB FK is commented. :contentReference[oaicite:9]{index=9}
-- =========================================================

CREATE TABLE `CodeSubmissions_v1` (
  `SubmissionId` int NOT NULL DEFAULT '0',
  `StudentId` varchar(255) DEFAULT NULL,
  `StudentName` varchar(255) DEFAULT NULL,
  `ProblemId` varchar(255) DEFAULT NULL,
  `StudentCode` text,
  `Error_testcases` text,
  `GPT_Feedback` text,
  `SubmitTime` datetime DEFAULT (now()),
  `verify_status` varchar(255) DEFAULT NULL,
  `error_status` varchar(255) DEFAULT NULL,
  `context_title` varchar(255) DEFAULT NULL,
  `LineID` varchar(255) DEFAULT NULL,
  `question_content` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `CodeSubmissions_v2` (
  `SubmissionId` int NOT NULL AUTO_INCREMENT,
  `StudentId` varchar(255) DEFAULT NULL,
  `StudentName` varchar(255) DEFAULT NULL,
  `ProblemId` varchar(255) DEFAULT NULL,
  `StudentCode` text,
  `Error_testcases` text,
  `GPT_Feedback_Student` text,
  `SubmitTime` datetime DEFAULT (now()),
  `verify_status` varchar(255) DEFAULT NULL,
  `error_status` varchar(255) DEFAULT NULL,
  `context_title` varchar(255) DEFAULT NULL,
  `LineID` varchar(255) DEFAULT NULL,
  `question_content` text,
  `GPT_Feedback_Assistant` text,
  PRIMARY KEY (`SubmissionId`),
  KEY `idx_csv2_student` (`StudentId`),
  KEY `idx_csv2_problem` (`ProblemId`),
  KEY `idx_csv2_line` (`LineID`),
  KEY `idx_csv2_ctx` (`context_title`)
) ENGINE=InnoDB AUTO_INCREMENT=198 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `SummarySubmissions` (
  `SubmissionId` int NOT NULL AUTO_INCREMENT,
  `StudentId` varchar(255) DEFAULT NULL,
  `TopicId` varchar(255) DEFAULT NULL,
  `GPT_Feedback` text,
  `SubmitTime` datetime DEFAULT (now()),
  `verify_status` varchar(255) DEFAULT NULL,
  `context_title` varchar(255) DEFAULT NULL,
  `student_summary` text,
  `summary_gradding_log_id` int DEFAULT NULL,
  `basic_feedback` text,
  `LineID` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`SubmissionId`),
  KEY `idx_sums_student` (`StudentId`),
  KEY `idx_sums_ctx` (`context_title`),
  KEY `idx_sums_line` (`LineID`),
  KEY `idx_sumsub_sgl` (`summary_gradding_log_id`)
  -- 若你決定要跨庫 FK，取消下面註解（需要 linebot_test 資料庫同一伺服器上且皆為 InnoDB）
  -- ,CONSTRAINT `fk_sumsub_linebot_sgl`
  --   FOREIGN KEY (`summary_gradding_log_id`)
  --   REFERENCES `linebot_test`.`summary_gradding_log` (`log_id`)
  --   ON UPDATE CASCADE
  --   ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=650 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `TeacherFeedbacks` (
  `FeedbackId` int NOT NULL AUTO_INCREMENT,
  `SubmissionId` int DEFAULT NULL,
  `SubmissionType` enum('Summary','Code') DEFAULT NULL,
  `Feedback` text,
  `FeedbackTime` datetime DEFAULT (now()),
  `context_title` varchar(255) DEFAULT NULL,
  `LineID` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`FeedbackId`),
  KEY `idx_tf_sub` (`SubmissionId`),
  KEY `idx_tf_type` (`SubmissionType`)
) ENGINE=InnoDB AUTO_INCREMENT=779 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `FeedbackEvaluations` (
  `EvaluationId` int NOT NULL AUTO_INCREMENT,
  `FeedbackId` int DEFAULT NULL,
  `Accuracy` tinyint(1) DEFAULT '0',
  `Readability` tinyint(1) DEFAULT '0',
  `Clarity` tinyint(1) DEFAULT '0',
  `Consistency` tinyint(1) DEFAULT '0',
  `Answerability` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`EvaluationId`),
  KEY `FeedbackId` (`FeedbackId`),
  CONSTRAINT `FeedbackEvaluations_ibfk_1` FOREIGN KEY (`FeedbackId`) REFERENCES `TeacherFeedbacks` (`FeedbackId`)
) ENGINE=InnoDB AUTO_INCREMENT=368 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `FeedbackEvaluations_v1` (
  `EvaluationId` int NOT NULL DEFAULT '0',
  `FeedbackId` int DEFAULT NULL,
  `Accuracy` tinyint(1) DEFAULT '0',
  `Readability` tinyint(1) DEFAULT '0',
  `Clarity` tinyint(1) DEFAULT '0',
  `Consistency` tinyint(1) DEFAULT '0',
  `Answerability` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `FeedbackEvaluations_v2` (
  `EvaluationId` int NOT NULL AUTO_INCREMENT,
  `FeedbackId` int DEFAULT NULL,
  `execution_result` varchar(50) DEFAULT NULL,
  `correctness_rate` int DEFAULT NULL,
  `adheres_section_scope` tinyint(1) DEFAULT NULL,
  `personalized_modifications` tinyint(1) DEFAULT NULL,
  `suggestion_correctness` tinyint(1) DEFAULT NULL,
  `suggestion_completeness` tinyint(1) DEFAULT NULL,
  `suggestion_without_code` tinyint(1) DEFAULT NULL,
  `consistent_suggestions` tinyint(1) DEFAULT NULL,
  `remarks` text,
  PRIMARY KEY (`EvaluationId`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
