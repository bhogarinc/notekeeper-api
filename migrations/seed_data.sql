-- ============================================
-- Seed Data
-- Description: Initial data for development/testing
-- ============================================

-- Note: Run this after running the migration

-- Sample user (password: 'TestPass123!')
INSERT INTO users (id, email, username, password_hash, is_active, is_verified)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'demo@notekeeper.app',
    'demo_user',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1S',
    TRUE,
    TRUE
);

-- Sample categories
INSERT INTO categories (id, user_id, name, color, icon) VALUES
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Work', '#6366f1', 'briefcase'),
    ('b2eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Personal', '#10b981', 'user'),
    ('b3eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Ideas', '#f59e0b', 'lightbulb');

-- Sample tags
INSERT INTO tags (id, user_id, name, color) VALUES
    ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'important', '#ef4444'),
    ('c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'todo', '#3b82f6'),
    ('c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'meeting', '#8b5cf6');

-- Sample notes
INSERT INTO notes (id, user_id, category_id, title, content, is_pinned, search_vector) VALUES
    ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 
     'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 
     'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a12',
     'Project Kickoff Meeting',
     '# Project Kickoff\n\nDate: April 26, 2026\n\n## Attendees\n- John Doe\n- Jane Smith\n\n## Agenda\n1. Introductions\n2. Project scope\n3. Timeline discussion\n4. Next steps',
     TRUE,
     setweight(to_tsvector('english', 'Project Kickoff Meeting'), 'A') ||
     setweight(to_tsvector('english', 'Project Kickoff Date April 26 2026 Attendees John Doe Jane Smith Agenda Introductions Project scope Timeline discussion Next steps'), 'B')
    );

-- Link note to tag
INSERT INTO note_tags (note_id, tag_id) VALUES
    ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a17');
