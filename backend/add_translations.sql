-- add_translations.sql
-- Добавляем колонки для переводов в таблицу questions

ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS text_en VARCHAR(500),
    ADD COLUMN IF NOT EXISTS text_he VARCHAR(500);

-- Проверяем, что колонки добавлены
\d questions