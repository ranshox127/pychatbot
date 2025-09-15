-- 一位學生：jz1452896（也會測 username LIKE 'jz1452896@%' 的分支）
INSERT INTO mdl_user (username, lastname, firstname)
VALUES ('jz1452896', '王', '小明')
ON CONFLICT (username) DO NOTHING;

-- 兩門課
INSERT INTO mdl_course (fullname) VALUES ('1234_程式設計-Python_黃鈺晴教師') ON CONFLICT DO NOTHING;

-- 建 context（簡化，直接取 course id）
INSERT INTO mdl_context (contextlevel, instanceid)
SELECT 50, c.id
FROM mdl_course c
WHERE c.fullname = '1234_程式設計-Python_黃鈺晴教師'
  AND NOT EXISTS (
    SELECT 1 FROM mdl_context ctx WHERE ctx.instanceid = c.id
  );

-- 讓學生被指派到該課的 context（roleid=5 假設是學生，可依你系統調整）
INSERT INTO mdl_role_assignments (roleid, contextid, userid)
SELECT 5, ctx.id, u.id
FROM mdl_user u
JOIN mdl_course c   ON c.fullname = '1234_程式設計-Python_黃鈺晴教師'
JOIN mdl_context ctx ON ctx.instanceid = c.id
WHERE u.username = 'jz1452896'
  AND NOT EXISTS (
    SELECT 1 FROM mdl_role_assignments ra
    WHERE ra.roleid = 5 AND ra.contextid = ctx.id AND ra.userid = u.id
  );
