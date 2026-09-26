CREATE DATABASE IF NOT EXISTS library_lending
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE library_lending;

CREATE TABLE IF NOT EXISTS books (
  isbn CHAR(13) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  author VARCHAR(200) NOT NULL,
  publisher VARCHAR(200) NOT NULL,
  publication_year SMALLINT NOT NULL,
  page_count INT UNSIGNED NOT NULL,
  CONSTRAINT chk_isbn CHECK (isbn REGEXP '^[0-9]{13}$'),
  CONSTRAINT chk_publication_year CHECK (publication_year BETWEEN 1000 AND 2100),
  CONSTRAINT chk_page_count CHECK (page_count > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS copies (
  isbn CHAR(13) NOT NULL,
  copy_number INT UNSIGNED NOT NULL,
  CONSTRAINT chk_copy_number CHECK (copy_number > 0),
  PRIMARY KEY (isbn, copy_number),
  CONSTRAINT fk_copies_book FOREIGN KEY (isbn) REFERENCES books (isbn)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS borrowers (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS loans (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  isbn CHAR(13) NOT NULL,
  copy_number INT UNSIGNED NOT NULL,
  borrower_id INT UNSIGNED NOT NULL,
  loan_date DATE NOT NULL,
  returned_at DATE NULL,
  open_copy_number INT UNSIGNED GENERATED ALWAYS AS
    (CASE WHEN returned_at IS NULL THEN copy_number ELSE NULL END) STORED,
  CONSTRAINT fk_loans_copy FOREIGN KEY (isbn, copy_number)
    REFERENCES copies (isbn, copy_number) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_loans_borrower FOREIGN KEY (borrower_id)
    REFERENCES borrowers (id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_return_date CHECK (returned_at IS NULL OR returned_at >= loan_date),
  UNIQUE KEY ux_one_open_loan_per_copy (isbn, open_copy_number),
  INDEX ix_loans_borrower (borrower_id)
) ENGINE=InnoDB;
