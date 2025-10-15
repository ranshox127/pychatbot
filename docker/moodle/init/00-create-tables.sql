-- DB: moodle（由 POSTGRES_DB 建）
-- 表結構：盡量貼近你查詢用到的欄位

CREATE TABLE IF NOT EXISTS mdl_user (
  id         SERIAL PRIMARY KEY,
  username   TEXT UNIQUE NOT NULL,
  lastname   TEXT NOT NULL,
  firstname  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mdl_course (
  id        SERIAL PRIMARY KEY,
  fullname  TEXT NOT NULL
);

-- 在 Moodle 正常是很多 contextlevel，這裡只做最少欄位
CREATE TABLE IF NOT EXISTS mdl_context (
  id           SERIAL PRIMARY KEY,
  contextlevel INTEGER NOT NULL,        -- 50=course，在這裡不嚴格檢查
  instanceid   INTEGER NOT NULL         -- 對應 mdl_course.id
);

CREATE TABLE IF NOT EXISTS mdl_role_assignments (
  id         SERIAL PRIMARY KEY,
  roleid     INTEGER NOT NULL,
  contextid  INTEGER NOT NULL,          -- 對應 mdl_context.id
  userid     INTEGER NOT NULL           -- 對應 mdl_user.id
);

-- 最小索引（依查詢情境）
CREATE INDEX IF NOT EXISTS idx_user_username ON mdl_user (username);
CREATE INDEX IF NOT EXISTS idx_ctx_instanceid ON mdl_context (instanceid);
CREATE INDEX IF NOT EXISTS idx_ra_user ON mdl_role_assignments (userid);
CREATE INDEX IF NOT EXISTS idx_ra_context ON mdl_role_assignments (contextid);
