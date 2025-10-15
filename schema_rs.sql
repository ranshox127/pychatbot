-- =========================================================
-- schema_rs.sql (lightly optimized with helpful indexes)
-- Source: original schema_rs.sql :contentReference[oaicite:10]{index=10}
-- Note: db_preflight.sql 未直接涵蓋 RS，但此處補充查詢常用索引（不影響語意/唯一性）。
-- =========================================================

CREATE TABLE `review_publish` (
  `id` int NOT NULL AUTO_INCREMENT,
  `context_title` varchar(255) NOT NULL,
  `context_id` int NOT NULL,
  `contents_name` varchar(255) NOT NULL,
  `contents_id` varchar(191) NOT NULL,
  `lesson_date` datetime NOT NULL,
  `publish_flag` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_review_publish_ctx` (`context_title`),
  KEY `idx_review_publish_ctx_content` (`context_title`,`contents_name`),
  KEY `idx_review_publish_date` (`lesson_date`)
) ENGINE=InnoDB AUTO_INCREMENT=267 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
