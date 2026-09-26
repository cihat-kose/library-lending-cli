USE library_lending;
INSERT INTO books (isbn, title, author, publisher, publication_year, page_count) VALUES
  ('9780141439518', 'Pride and Prejudice', 'Jane Austen', 'Penguin Classics', 1813, 480),
  ('9780241252086', 'The Trial', 'Franz Kafka', 'Penguin Classics', 1925, 208);
INSERT INTO copies (isbn, copy_number) VALUES
  ('9780141439518', 1), ('9780141439518', 2), ('9780241252086', 1);
INSERT INTO borrowers (first_name, last_name, email) VALUES
  ('Ada', 'Lovelace', 'ada@example.test'), ('Grace', 'Hopper', 'grace@example.test');
