
CREATE TABLE audits (
	id INTEGER NOT NULL AUTO_INCREMENT,
	actor VARCHAR(100),
	action VARCHAR(200),
	created VARCHAR(40),
	PRIMARY KEY (id)
)

;


CREATE TABLE pivots (
	id INTEGER NOT NULL AUTO_INCREMENT,
	name VARCHAR(100),
	row_dim VARCHAR(30),
	col_dim VARCHAR(30),
	state VARCHAR(20),
	result JSON,
	error TEXT,
	PRIMARY KEY (id)
)

;


CREATE TABLE settlements (
	id INTEGER NOT NULL AUTO_INCREMENT,
	code VARCHAR(60) NOT NULL,
	day VARCHAR(10),
	venue VARCHAR(40),
	play VARCHAR(60),
	channel VARCHAR(30),
	gross_cents BIGINT,
	refund_cents BIGINT,
	fee_cents BIGINT,
	seats INTEGER,
	checked INTEGER,
	PRIMARY KEY (id),
	UNIQUE (code)
)

;


CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT,
	email VARCHAR(100) NOT NULL,
	password VARCHAR(200),
	`role` VARCHAR(20),
	PRIMARY KEY (id),
	UNIQUE (email)
)

;


CREATE TABLE reviews (
	id INTEGER NOT NULL AUTO_INCREMENT,
	pivot_id INTEGER,
	row_key VARCHAR(100),
	col_key VARCHAR(100),
	book_cents BIGINT,
	expected_cents BIGINT,
	difference_cents BIGINT,
	note TEXT,
	status VARCHAR(20),
	PRIMARY KEY (id),
	FOREIGN KEY(pivot_id) REFERENCES pivots (id)
)

;


CREATE TABLE show_sessions (
	id INTEGER NOT NULL AUTO_INCREMENT,
	code VARCHAR(60) NOT NULL,
	play VARCHAR(60) NOT NULL,
	venue VARCHAR(40) NOT NULL,
	show_day DATE NOT NULL,
	capacity INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (code)
)

;


CREATE TABLE sales_reports (
	id INTEGER NOT NULL AUTO_INCREMENT,
	session_id INTEGER NOT NULL,
	report_day DATE NOT NULL,
	sold_total INTEGER NOT NULL,
	available_seats INTEGER NOT NULL,
	received_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	UNIQUE KEY uq_session_report_day (session_id, report_day),
	FOREIGN KEY(session_id) REFERENCES show_sessions (id)
)

;


CREATE TABLE warning_batches (
	id INTEGER NOT NULL AUTO_INCREMENT,
	name VARCHAR(100),
	cutoff_at DATETIME NOT NULL,
	state VARCHAR(20),
	result JSON,
	error TEXT,
	PRIMARY KEY (id)
)

;
