-- Демо-студент для просмотра из кабинета инструктора. Идемпотентно: удаление по id (CASCADE снесёт зависимые).
DELETE FROM users WHERE id = 'demo-student-0001';

INSERT INTO users (id, name, email, role)
VALUES ('demo-student-0001', 'Иван Петров (демо)', 'demo-student@onlinetlabs.local', 'student');

INSERT INTO learning_sessions (id, user_id, lab_slug, status, started_at, ended_at) VALUES
 ('demo-sess-1', 'demo-student-0001', 'lan-static-ip',        'ended',  now() - interval '3 days',  now() - interval '3 days' + interval '40 minutes'),
 ('demo-sess-2', 'demo-student-0001', 'inter-subnet-routing', 'active', now() - interval '2 hours', NULL);

INSERT INTO lab_progress (id, user_id, lab_slug, status, score, current_step, started_at, completed_at, updated_at) VALUES
 ('demo-lp-1', 'demo-student-0001', 'lan-static-ip',        'completed',   92,   2,    now() - interval '3 days',  now() - interval '3 days' + interval '40 minutes', now() - interval '3 days' + interval '40 minutes'),
 ('demo-lp-2', 'demo-student-0001', 'inter-subnet-routing', 'in_progress', NULL, 1,    now() - interval '2 hours', NULL,                                              now() - interval '1 hour'),
 ('demo-lp-3', 'demo-student-0001', 'dhcp-basics',          'not_started', NULL, NULL, NULL,                       NULL,                                              now() - interval '1 day');

INSERT INTO step_attempts (id, user_id, lab_slug, step_slug, attempt_number, result, score, started_at, ended_at) VALUES
 ('demo-sa-1', 'demo-student-0001', 'lan-static-ip',        'pc-ips',    1, 'fail', NULL, now() - interval '3 days',                    now() - interval '3 days' + interval '2 minutes'),
 ('demo-sa-2', 'demo-student-0001', 'lan-static-ip',        'pc-ips',    2, 'pass', 100,  now() - interval '3 days' + interval '10 minutes', now() - interval '3 days' + interval '11 minutes'),
 ('demo-sa-3', 'demo-student-0001', 'inter-subnet-routing', 'r1-config', 1, 'fail', NULL, now() - interval '2 hours',                   NULL);

INSERT INTO behavioral_events (id, session_id, user_id, lab_slug, timestamp, event_type, action, success, severity, message, metadata, created_at) VALUES
 ('demo-hint-1', 'demo-sess-1', 'demo-student-0001', 'lan-static-ip',        now() - interval '3 days' + interval '5 minutes', 'intervention', 'hint',  true, 'info', 'Проверь IP на PC1: он вне нужной подсети 192.168.1.0/24.', '{"hint_level": 2, "struggle_type": "repeating_errors"}', now() - interval '3 days' + interval '5 minutes'),
 ('demo-hint-2', 'demo-sess-1', 'demo-student-0001', 'lan-static-ip',        now() - interval '3 days' + interval '8 minutes', 'intervention', 'hint',  true, 'info', 'Маска /24 задаёт диапазон адресов .1-.254.',               '{"hint_level": 2}',                                       now() - interval '3 days' + interval '8 minutes'),
 ('demo-hint-3', 'demo-sess-2', 'demo-student-0001', 'inter-subnet-routing', now() - interval '1 hour',                        'intervention', 'tutor', true, 'info', 'На R1 не хватает маршрута до второй подсети.',             '{"hint_level": 1, "struggle_type": "stuck"}',             now() - interval '1 hour');

-- Диалог студента с тьютором, переплетённый по времени с интервенциями выше.
INSERT INTO chat_messages (id, session_id, role, parts, created_at) VALUES
 ('demo-msg-1', 'demo-sess-1', 'user',      '[{"type":"text","text":"PC1 не пингует PC2, что не так?"}]',            now() - interval '3 days' + interval '4 minutes'),
 ('demo-msg-2', 'demo-sess-1', 'assistant', '[{"type":"text","text":"Проверь IP-адреса обоих узлов и маску подсети."}]', now() - interval '3 days' + interval '4 minutes 30 seconds'),
 ('demo-msg-3', 'demo-sess-1', 'user',      '[{"type":"text","text":"А, у PC1 был .99 вместо .11. Исправил, пинг пошёл."}]', now() - interval '3 days' + interval '12 minutes'),
 ('demo-msg-4', 'demo-sess-2', 'user',      '[{"type":"text","text":"Как добавить маршрут между подсетями на R1?"}]', now() - interval '90 minutes');
